"""Repeatable technical search report (GSD-03/04/05/10). Read-only.

    manage.py seo_report --out artifacts/.../seo-report.json [--html all|N] [--crawl] [--registry-csv file]

Sections are kept separate by data source:
* ``registry``      - readiness of every entity x locale (own database);
* ``sitemap``       - sitemap graph built from the registry (own code);
* ``html_audit``    - rendered HTML signals in production mode (own renderer,
                      isolated with override_settings; Local stays protected);
* ``own_crawler``   - robots-respecting crawl of rendered pages (own crawler);
* ``outbox``        - IndexNow outbox state (own database);
* ``server_logs`` / ``search_providers`` / ``ai_referrals`` - not connected
  from Local: reported as null, never as zero.

It never writes to catalog tables, never translates and never sends anything.
"""
import csv
import json
import re
import time
from collections import Counter, deque
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings

from catalog import readiness
from catalog.i18n import SUPPORTED_CODES
from catalog.locale_urls import URL_CODE
from catalog.seo import render_index, render_urlset, sitemap_urlsets

SITEMAP_URL_LIMIT = 50_000
SITEMAP_BYTES_LIMIT = 50 * 1024 * 1024
HREF = re.compile(r'<a\s[^>]*href="([^"#]+)"', re.I)
CANON = re.compile(r'<link rel="canonical" href="([^"]+)"')
ALT = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"')
NOINDEX = re.compile(r'<meta name="robots" content="noindex')
HTML_LANG = re.compile(r'<html lang="([^"]+)" dir="([^"]+)"')
H1 = re.compile(r"<h1[\s>]")
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
ENTITY_LOC = re.compile(r"/(models|tools)/[^/]+$")


class Command(BaseCommand):
    help = "Machine-readable search readiness / sitemap / HTML / crawl report (read-only)."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="")
        parser.add_argument("--registry-csv", default="")
        parser.add_argument("--html", default="sample", help="'all', 'sample' or a number of pages per locale")
        parser.add_argument("--crawl", action="store_true")
        parser.add_argument("--crawl-limit", type=int, default=4000)

    def handle(self, *args, **options):
        started = time.time()
        rows = list(readiness.registry())
        report = {
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "public_origin": settings.AIPEDIA_PUBLIC_ORIGIN,
            "registry": self.registry_section(rows),
        }
        if options["registry_csv"]:
            with open(options["registry_csv"], "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["kind", "slug", "lang", "status", "reason"])
                writer.writeheader()
                for row in rows:
                    writer.writerow({key: row[key] for key in writer.fieldnames})
        sets = sitemap_urlsets()
        report["sitemap"] = self.sitemap_section(sets, rows)
        with override_settings(AIPEDIA_INDEXING_ALLOWED=True, ALLOWED_HOSTS=["*"], DEBUG=False):
            client = Client(HTTP_HOST="aipediya.local")
            report["html_audit"] = (self.html_section(client, sets, options["html"]) if options["html"] != "none"
                                    else {"mode": "none", "pages": 0, "problem_count": 0, "problems": []})
            if options["crawl"]:
                report["own_crawler"] = self.crawl_section(client, options["crawl_limit"])
        report["outbox"] = self.outbox_section()
        report["server_logs"] = {"status": "not_connected", "crawled_urls": None, "bot_hits": None,
                                 "note": "Production access logs are not read from Local."}
        report["search_providers"] = {
            name: {"status": "not_connected", "discovered": None, "crawled": None, "indexed": None,
                   "impressions": None, "clicks": None, "queries": None, "countries": None}
            for name in ("google_search_console", "bing_webmaster", "yandex_webmaster", "baidu", "naver", "seznam")
        }
        report["ai_referrals"] = {"status": "not_connected", "referrals": None, "citations": None,
                                  "note": "Referrers cannot prove all AI citations; no provider data connected."}
        report["seconds"] = round(time.time() - started, 1)
        text = json.dumps(report, ensure_ascii=False, indent=1, default=str)
        if options["out"]:
            with open(options["out"], "w", encoding="utf-8") as handle:
                handle.write(text)
        summary = {
            "registry": report["registry"]["totals"],
            "sitemap": {k: report["sitemap"][k] for k in ("loc_count", "alternate_links", "problems")},
            "html_problems": report["html_audit"]["problem_count"],
            "html_pages": report["html_audit"]["pages"],
        }
        if "own_crawler" in report:
            summary["crawl"] = {k: report["own_crawler"][k] for k in ("fetched", "unreached_public_entities", "status_counts")}
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    # ------------------------------------------------------------------ registry
    def registry_section(self, rows):
        summary = readiness.summarize(rows)
        public_models = readiness.public_models().count()
        public_tools = readiness.public_tools().count()
        indexable = sum(1 for row in rows if row["status"] == readiness.INDEXABLE)
        not_ready = sum(1 for row in rows if row["status"] == readiness.NOT_READY)
        not_public = sum(1 for row in rows if row["status"] == readiness.NOT_PUBLIC)
        from catalog.models import ContentTranslation
        return {
            "totals": {
                "public_models": public_models, "public_tools": public_tools,
                "potential_entity_locale_urls": (public_models + public_tools) * len(SUPPORTED_CODES),
                "indexable_entity_urls": indexable, "not_ready_entity_urls": not_ready,
                "not_public_rows": not_public,
                # Reported separately on purpose: translation rows are not URLs.
                "content_translation_rows": ContentTranslation.objects.count(),
            },
            **summary,
        }

    # ------------------------------------------------------------------- sitemap
    def sitemap_section(self, sets, rows):
        problems = []
        locs = []
        alternates = 0
        files = {}
        for lang, entries in sets.items():
            if not entries:
                continue
            body = render_urlset(entries).encode("utf-8")
            files[URL_CODE[lang]] = {"urls": len(entries), "bytes": len(body)}
            if len(entries) > SITEMAP_URL_LIMIT or len(body) > SITEMAP_BYTES_LIMIT:
                problems.append(f"{lang}: sitemap over limits")
            for entry in entries:
                locs.append(entry["loc"])
                alternates += len(entry["alternates"]) + (1 if entry["x_default"] else 0)
                for _code, url in entry["alternates"]:
                    if not url.startswith(settings.AIPEDIA_PUBLIC_ORIGIN + "/"):
                        problems.append(f"foreign alternate {url}")
                if entry["loc"] not in {url for _code, url in entry["alternates"]}:
                    problems.append(f"loc missing self-alternate {entry['loc']}")
                if entry["lastmod"] and entry["lastmod"].isoformat() > time.strftime("%Y-%m-%d", time.gmtime(time.time() + 86400)):
                    problems.append(f"future lastmod {entry['loc']}")
        duplicates = [url for url, count in Counter(locs).items() if count > 1]
        problems += [f"duplicate loc {url}" for url in duplicates]
        bad_hosts = [url for url in locs if "localhost" in url or "127.0.0.1" in url]
        problems += [f"local host in loc {url}" for url in bad_hosts]
        # Entity URLs in the sitemap must equal the registry's indexable rows.
        registry_urls = {
            (row["kind"], row["slug"], row["lang"]) for row in rows if row["status"] == readiness.INDEXABLE
        }
        sitemap_entities = set()
        pattern = re.compile(r"^" + re.escape(settings.AIPEDIA_PUBLIC_ORIGIN) + r"(?:/([a-z-]+))?/(models|tools)/([^/?]+)$")
        from catalog.locale_urls import FROM_URL_CODE
        for url in locs:
            match = pattern.match(url)
            if match:
                lang = FROM_URL_CODE.get(match.group(1)) if match.group(1) else "en"
                sitemap_entities.add(("tool" if match.group(2) == "tools" else "model", match.group(3), lang))
        hidden_slugs = {row["slug"] for row in rows if row["status"] == readiness.NOT_PUBLIC}
        leaked = sorted({url for url in locs for slug in [url.rsplit("/", 1)[-1]] if slug in hidden_slugs})
        problems += [f"hidden record in sitemap {url}" for url in leaked]
        missing = registry_urls - sitemap_entities
        extra = sitemap_entities - registry_urls
        problems += [f"registry indexable but not in sitemap: {item}" for item in sorted(missing)[:20]]
        problems += [f"in sitemap but not indexable: {item}" for item in sorted(extra)[:20]]
        index_body = render_index(sets)
        return {
            "index_bytes": len(index_body.encode("utf-8")),
            "child_files": files,
            "loc_count": len(locs),
            "entity_loc_count": len(sitemap_entities),
            "registry_indexable_entity_urls": len(registry_urls),
            "alternate_links": alternates,
            "hidden_leaks": len(leaked),
            "problems": problems,
        }

    # ---------------------------------------------------------------- HTML audit
    def html_section(self, client, sets, mode):
        by_lang = {lang: [entry for entry in entries] for lang, entries in sets.items()}
        pages = []
        origin = settings.AIPEDIA_PUBLIC_ORIGIN
        for lang, entries in by_lang.items():
            if mode == "all":
                chosen = entries
            else:
                limit = 12 if mode == "sample" else int(mode)
                entity = [e for e in entries if ENTITY_LOC.search(e["loc"])]
                non_entity = [e for e in entries if not ENTITY_LOC.search(e["loc"])]
                step = max(1, len(entity) // max(1, limit))
                chosen = non_entity + entity[::step][:limit]
            pages.extend((lang, entry) for entry in chosen)
        problems = []
        checked = 0
        for lang, entry in pages:
            path = entry["loc"][len(origin):] or "/"
            response = client.get(path)
            checked += 1
            if response.status_code != 200:
                problems.append({"url": entry["loc"], "problem": f"status {response.status_code}"})
                continue
            html = response.content.decode("utf-8")
            head = html[: html.find("</head>")]
            canonical = CANON.search(head)
            if not canonical or canonical.group(1) != entry["loc"]:
                problems.append({"url": entry["loc"], "problem": f"canonical {canonical.group(1) if canonical else None}"})
            if NOINDEX.search(head):
                problems.append({"url": entry["loc"], "problem": "noindex on sitemap URL"})
            alts = sorted(ALT.findall(head))
            expected = sorted(entry["alternates"] + ([("x-default", entry["x_default"])] if entry["x_default"] else []))
            if alts != expected:
                problems.append({"url": entry["loc"], "problem": "hreflang mismatch with sitemap",
                                 "html": len(alts), "sitemap": len(expected)})
            lang_dir = HTML_LANG.search(html)
            want_dir = "rtl" if lang in ("ar", "fa") else "ltr"
            if not lang_dir or lang_dir.group(1) != lang or lang_dir.group(2) != want_dir:
                problems.append({"url": entry["loc"], "problem": f"html lang/dir {lang_dir.groups() if lang_dir else None}"})
            h1_count = len(H1.findall(html))
            if h1_count != 1:
                problems.append({"url": entry["loc"], "problem": f"h1 count {h1_count}"})
            title = TITLE.search(head)
            if not title or not title.group(1).strip():
                problems.append({"url": entry["loc"], "problem": "empty title"})
            if 'name="description"' not in head:
                problems.append({"url": entry["loc"], "problem": "missing meta description"})
        return {"mode": mode, "pages": checked,
                "locales": sorted({lang for lang, _entry in pages}),
                "problem_count": len(problems), "problems": problems[:200]}

    # ------------------------------------------------------------- own crawler
    def crawl_section(self, client, limit):
        from catalog.views import robots_allows, robots_rules
        rules = robots_rules()
        seen, queue = set(), deque(["/", "/tools/"])
        statuses = Counter()
        entity_seen = set()
        blocked_skipped = 0
        noindex_pages = 0
        while queue and len(seen) < limit:
            path = queue.popleft()
            if path in seen:
                continue
            seen.add(path)
            response = client.get(path)
            statuses[response.status_code] += 1
            if response.status_code != 200 or "text/html" not in response.get("Content-Type", ""):
                continue
            html = response.content.decode("utf-8")
            if NOINDEX.search(html[: html.find("</head>")]):
                noindex_pages += 1
            for href in HREF.findall(html):
                # Resolve relative links (e.g. href="?page=2") like a real crawler.
                href = urljoin(path, href.replace("&amp;", "&"))
                parts = urlsplit(href)
                if parts.netloc or not href.startswith("/") or href.startswith(("/static/", "/admin/")):
                    continue
                if parts.path.startswith(("/datasets/aipediya", "/datasets/manifest")):
                    continue
                if not robots_allows(parts.path + ("?" + parts.query if parts.query else ""), rules):
                    blocked_skipped += 1
                    continue
                match = re.match(r"^(?:/[a-z-]+)?/(models|tools)/([^/]+)$", parts.path)
                if match:
                    # Reached only through a crawlable (robots-allowed) link.
                    entity_seen.add((match.group(1), match.group(2)))
                    # Entity pages are leaf pages for reachability; crawl the
                    # English instance only to keep the crawl bounded.
                    if parts.path.count("/") > 2:
                        continue
                if href not in seen:
                    queue.append(href)
        public = {("models", slug) for slug in readiness.public_models().values_list("slug", flat=True)}
        public |= {("tools", slug) for slug in readiness.public_tools().values_list("slug", flat=True)}
        from catalog.models import ModelVersion, Tool
        hidden = {("models", slug) for slug in ModelVersion.objects.filter(
            entry_type="model", published=False).values_list("slug", flat=True)}
        hidden |= {("tools", slug) for slug in Tool.objects.filter(published=False).values_list("slug", flat=True)}
        return {
            "start": ["/", "/tools/"], "limit": limit, "fetched": len(seen), "queue_left": len(queue),
            "terminated": not queue, "status_counts": dict(statuses),
            "robots_blocked_links_skipped": blocked_skipped, "noindex_pages_fetched": noindex_pages,
            "public_entities": len(public), "reached_public_entities": len(public & entity_seen),
            "unreached_public_entities": sorted(f"{k}/{s}" for k, s in public - entity_seen)[:50],
            "hidden_entities_linked": sorted(f"{k}/{s}" for k, s in hidden & entity_seen),
        }

    def outbox_section(self):
        from catalog.models import DiscoveryEvent
        return {
            "by_state": dict(Counter(DiscoveryEvent.objects.values_list("state", flat=True))),
            "by_action": dict(Counter(DiscoveryEvent.objects.values_list("action", flat=True))),
            "sending_enabled": bool(getattr(settings, "AIPEDIA_INDEXNOW_ENABLED", False)),
        }
