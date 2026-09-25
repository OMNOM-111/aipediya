"""Post-deploy GSD-1.0 QA against a public origin. Read-only HTTPS GETs, paced.

    python tools/gsd_production_qa.py https://aipediya.com --commit <sha> --out report.json

About 700 sequential requests (0.15 s apart): all 22 locale roots and Tools
listings, legacy redirects, SSR cards, methodology, collections, datasets,
pagination, robots, sitemap index + every child sitemap, and every
unpublished (NEEDS_REVIEW) model slug from data/release_state.json (must be
404 and absent from sitemaps). It never submits anything anywhere.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent
CODES = ["en", "ru", "zh-Hans", "es", "fr", "ar", "pt-BR", "de", "ja", "ko", "hi", "id", "tr", "vi",
         "it", "pl", "uk", "fa", "th", "nl", "bn", "zh-Hant"]
RTL = {"ar", "fa"}
PUBLIC = "https://aipediya.com"
UA = "AIpediya-GSD-production-QA/1.0 (+owner read-only check)"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = build_opener(NoRedirect)


def prefix(code):
    return "" if code == "en" else "/" + code.lower()


class QA:
    def __init__(self, base, pause):
        self.base = base.rstrip("/")
        self.pause = pause
        self.results = []
        self.requests = 0

    def get(self, path):
        time.sleep(self.pause)
        self.requests += 1
        request = Request(self.base + path, headers={"User-Agent": UA})
        for attempt in range(3):
            try:
                with OPENER.open(request, timeout=40) as response:
                    return response.status, dict(response.headers), response.read().decode("utf-8", "replace")
            except HTTPError as error:
                return error.code, dict(error.headers or {}), ""
            except URLError:
                time.sleep(2 * (attempt + 1))
        return 0, {}, ""

    def check(self, group, name, ok, detail=""):
        self.results.append({"group": group, "check": name, "ok": bool(ok), "detail": str(detail)[:300]})

    def head_signals(self, html):
        head = html[: html.find("</head>")] if "</head>" in html else html
        lang_dir = re.search(r'<html lang="([^"]+)" dir="([^"]+)"', html)
        return {
            "canonical": (re.search(r'<link rel="canonical" href="([^"]+)"', head) or [None, None])[1],
            "alternates": re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', head),
            "noindex": 'name="robots" content="noindex' in head,
            "lang_dir": lang_dir.groups() if lang_dir else (None, None),
            "title": (re.search(r"<title>(.*?)</title>", head, re.S) or [None, ""])[1].strip(),
            "h1": len(re.findall(r"<h1[\s>]", html)),
            "ld": re.findall(r'"@type":"([A-Za-z]+)"', " ".join(re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', html, re.S))),
        }

    def indexable_page(self, group, path, code, expect_types=("Organization",)):
        status, _headers, html = self.get(path)
        self.check(group, f"200 {path}", status == 200, status)
        if status != 200:
            return None
        sig = self.head_signals(html)
        want_dir = "rtl" if code in RTL else "ltr"
        self.check(group, f"lang/dir {path}", tuple(sig["lang_dir"]) == (code, want_dir), sig["lang_dir"])
        self.check(group, f"self-canonical {path}", sig["canonical"] == PUBLIC + path, sig["canonical"])
        self.check(group, f"indexable {path}", not sig["noindex"])
        hreflangs = dict(sig["alternates"])
        self.check(group, f"hreflang self+x-default {path}",
                   hreflangs.get(code) == PUBLIC + path and "x-default" in hreflangs, len(hreflangs))
        self.check(group, f"one h1 {path}", sig["h1"] == 1, sig["h1"])
        self.check(group, f"title {path}", bool(sig["title"]))
        for kind in expect_types:
            self.check(group, f"JSON-LD {kind} {path}", kind in sig["ld"], sig["ld"])
        return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", nargs="?", default=PUBLIC)
    parser.add_argument("--commit", default="")
    parser.add_argument("--pause", type=float, default=0.15)
    parser.add_argument("--datasets-enabled", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    qa = QA(args.base, args.pause)
    started = time.time()

    status, _, body = qa.get("/healthz")
    health = json.loads(body) if status == 200 else {}
    qa.check("health", "/healthz 200", status == 200, status)
    if args.commit:
        qa.check("health", "release commit", health.get("release") == args.commit, health.get("release"))
    qa.check("health", "environment production", health.get("environment") == "production", health.get("environment"))

    # Locale roots and Tools listings (22 each).
    for code in CODES:
        qa.indexable_page("locales", prefix(code) + "/", code)
        qa.indexable_page("tools-listing", prefix(code) + "/tools/", code)

    # Legacy redirects: exactly one 301 to the equivalent address.
    state = json.loads((ROOT / "data" / "release_state.json").read_text(encoding="utf-8"))
    public_models = sorted(slug for slug, v in state["models"].items() if v["published"])
    hidden_models = sorted(slug for slug, v in state["models"].items() if not v["published"])
    public_tools = sorted(slug for slug, v in state["tools"].items() if v["published"])
    model, tool = public_models[0], public_tools[0]
    for source, target in [
        ("/?lang=ru", "/ru/"), ("/?lang=en", "/"), ("/?lang=zh-CN&kind=tool&sort=name_asc", "/zh-hans/tools/?sort=name_asc"),
        (f"/models/{model}?lang=de&kind=model&page=1&tab=pricing", f"/de/models/{model}?tab=pricing"),
        (f"/tools/{tool}?lang=ar", f"/ar/tools/{tool}"), ("/privacy?lang=uk", "/uk/privacy"),
        ("/zh-Hans/", "/zh-hans/"), ("/pt_BR/tools/", "/pt-br/tools/"), ("/en/", "/"), ("/ru", "/ru/"),
        ("/?page=1", "/"), ("/?lang=zz", "/"),
    ]:
        status, headers, _ = qa.get(source)
        location = headers.get("Location", "")
        qa.check("legacy-redirects", f"301 {source}", status == 301 and location == target, f"{status} {location}")
        final, _, _ = qa.get(target)
        qa.check("legacy-redirects", f"single hop {source}", final == 200, final)

    # Direct SSR cards (models and tools, LTR/RTL/CJK).
    for code in ("en", "ru", "ar", "zh-Hans", "uk", "fa"):
        for kind, slug in (("models", public_models[len(public_models) // 3]), ("tools", public_tools[len(public_tools) // 2])):
            path = f"{prefix(code)}/{kind}/{slug}"
            html = qa.indexable_page("ssr-cards", path, code, ("Organization", "BreadcrumbList"))
            if html:
                qa.check("ssr-cards", f"panel content {path}", 'class="panel-inner"' in html and 'class="description"' in html
                         and 'id="tab-pricing"' in html)
                qa.check("ssr-cards", f"visible breadcrumb {path}", 'class="breadcrumbs"' in html)

    # Methodology and collections.
    for code in CODES:
        qa.indexable_page("methodology", prefix(code) + "/methodology", code, ("Organization", "BreadcrumbList"))
    hubs = ["coding-models", "video-models", "free-tier-models", "api-models", "open-weight-models",
            "models-from-china", "models-released-2025", "long-context-models", "coding-tools"]
    for code in ("en", "ru", "ar", "ja"):
        qa.indexable_page("hubs", prefix(code) + "/collections/", code, ("Organization", "BreadcrumbList"))
        for hub in hubs:
            qa.indexable_page("hubs", f"{prefix(code)}/collections/{hub}", code, ("Organization", "BreadcrumbList"))
    status, _, html = qa.get("/collections/music-models")
    qa.check("hubs", "thin hub music-models is noindex", status == 200 and 'content="noindex' in html, status)

    # Datasets: gated off in Production until the owner picks a license.
    for path in ("/datasets/", "/datasets/models", "/datasets/aipediya-ai-tools.csv", "/datasets/manifest.json"):
        status, _, _ = qa.get(path)
        expected = 200 if args.datasets_enabled else 404
        qa.check("datasets", f"{path} {expected}", status == expected, status)

    # Pagination and crawlability.
    for path, expected in (("/?page=2", 200), ("/?page=5", 200), ("/?page=6", 404), ("/?page=abc", 404),
                           ("/tools/?page=2", 404), ("/ru/?page=3", 200)):
        status, _, html = qa.get(path)
        qa.check("pagination", f"{path} -> {expected}", status == expected, status)
        if expected == 200 and status == 200:
            sig = qa.head_signals(html)
            qa.check("pagination", f"self-canonical {path}", sig["canonical"] == PUBLIC + path, sig["canonical"])
    status, _, html = qa.get("/?sort=name_asc")
    qa.check("pagination", "sorted listing is noindex without canonical",
             status == 200 and 'content="noindex' in html and 'rel="canonical"' not in html, status)
    status, headers, _ = qa.get("/?partial=rows&page=2")
    qa.check("pagination", "partial fragment X-Robots-Tag noindex", headers.get("X-Robots-Tag", "").startswith("noindex"),
             headers.get("X-Robots-Tag"))

    # robots.txt
    status, _, robots = qa.get("/robots.txt")
    qa.check("robots", "robots 200", status == 200, status)
    qa.check("robots", "sitemap line", f"Sitemap: {PUBLIC}/sitemap.xml" in robots)
    qa.check("robots", "facets blocked", "Disallow: /*?q=" in robots and "Disallow: /*?partial=" in robots)
    qa.check("robots", "card pagination allowed", "Allow: /models/*?page=" in robots)
    qa.check("robots", "no global disallow", "\nDisallow: /\n" not in robots)
    qa.check("robots", "no AI-agent-specific rules (baseline unchanged)",
             not re.search(r"User-agent: (?!\*)", robots))

    # Sitemaps.
    status, _, index = qa.get("/sitemap.xml")
    children = re.findall(r"<loc>([^<]+)</loc>", index)
    qa.check("sitemap", "index 200 with 22 children", status == 200 and len(children) == 22, len(children))
    counts, all_locs = Counter(), []
    hidden = set(hidden_models)
    for child in children:
        status, _, body = qa.get(child.replace(PUBLIC, ""))
        qa.check("sitemap", f"child 200 {child.rsplit('/', 1)[-1]}", status == 200 and len(body.encode()) < 50 * 1024 * 1024, status)
        for loc in re.findall(r"<loc>([^<]+)</loc>", body):
            all_locs.append(loc)
            path = re.sub(r"^" + re.escape(PUBLIC) + r"(/[a-z]{2,3}(-[a-z]{2,4})?(?=/))?", "", loc) or "/"
            if path.startswith("/models/"):
                counts["cards: models"] += 1
            elif re.match(r"^/tools/.+", path):
                counts["cards: tools"] += 1
            elif path.startswith("/collections/") and path != "/collections/":
                counts["hubs"] += 1
            else:
                counts[path] += 1
    qa.check("sitemap", "no duplicate loc", len(all_locs) == len(set(all_locs)), len(all_locs) - len(set(all_locs)))
    qa.check("sitemap", "no hidden record in sitemap", not any(loc.rsplit("/", 1)[-1] in hidden for loc in all_locs))
    qa.check("sitemap", "no localhost", not any("localhost" in loc or "127.0.0.1" in loc for loc in all_locs))

    # Hidden NEEDS_REVIEW models: 404 everywhere, including legacy and locale forms.
    for slug in hidden_models:
        status, _, _ = qa.get(f"/models/{slug}")
        qa.check("hidden", f"404 /models/{slug}", status == 404, status)
    for slug in hidden_models[:10]:
        for path in (f"/ru/models/{slug}", f"/models/{slug}?lang=ru"):
            status, _, _ = qa.get(path)
            qa.check("hidden", f"404 {path}", status == 404, status)

    groups = {}
    for item in qa.results:
        bucket = groups.setdefault(item["group"], {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += item["ok"]
    report = {
        "base": qa.base, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "health": health, "requests": qa.requests, "seconds": round(time.time() - started),
        "passed": sum(item["ok"] for item in qa.results), "total": len(qa.results), "groups": groups,
        "sitemap_loc_by_type": dict(sorted(counts.items())), "sitemap_loc_total": len(all_locs),
        "hidden_checked": len(hidden_models),
        "failures": [item for item in qa.results if not item["ok"]][:100],
    }
    text = json.dumps(report, indent=1, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
