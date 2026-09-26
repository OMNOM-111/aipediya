"""Compare the 45 observed GSC legacy URLs on Local and public HTTPS.

Local runs with the isolated checkout DB and indexing enabled for response
semantics; public mode fetches without following redirects. Writes evidence
outside Git by default. No server mutation or search submission.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def remote_get(opener, url):
    try:
        response = opener.open(Request(url, headers={"User-Agent": "AIpediya-Search-QA/1.0"}), timeout=20)
    except HTTPError as exc:
        response = exc
    with response:
        return response.status, dict(response.headers.items()), response.read().decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Public origin; omit for Local Django client")
    parser.add_argument("--expected", type=Path, help="Local result JSON to compare with public")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    import django
    django.setup()
    from django.test import Client, override_settings
    from catalog.legacy_search_urls import GSC_LEGACY_CARD_URLS
    from catalog.views import robots_allows

    opener = build_opener(NoRedirect())
    base = args.base.rstrip("/") if args.base else None

    def get(path):
        if base:
            return remote_get(opener, base + path)
        response = Client(HTTP_HOST="127.0.0.1").get(path)
        return response.status_code, dict(response.items()), response.content.decode("utf-8", "replace")

    expected = None
    if args.expected:
        expected = {item["url"]: item for item in json.loads(args.expected.read_text(encoding="utf-8"))["results"]}
    results = []
    failures = []
    with override_settings(AIPEDIA_INDEXING_ALLOWED=True):
        for path in GSC_LEGACY_CARD_URLS:
            status, headers, body = get(path)
            headers = {name.lower(): value for name, value in headers.items()}
            raw_location = headers.get("location", "")
            parts = urlsplit(raw_location)
            location = parts.path + ("?" + parts.query if parts.query else "") if raw_location else ""
            noindex = "noindex" in headers.get("x-robots-tag", "").lower() or bool(
                re.search(r'<meta name="robots" content="[^"]*noindex', body))
            record = {"url": path, "status": status, "location": location, "noindex": noindex,
                      "robots_allowed_local_rule": robots_allows(path)}
            if status == 301:
                target = location
                final_status, _, final_body = get(target)
                canonical = re.search(r'<link rel="canonical" href="([^"]+)"', final_body)
                record.update(final_status=final_status,
                              final_canonical=canonical.group(1) if canonical else "")
                if final_status != 200 or not record["final_canonical"].endswith(target):
                    failures.append(f"{path}: bad redirect destination {location} ({final_status})")
            elif status == 200 and not noindex:
                failures.append(f"{path}: indexable fragment or duplicate")
            elif status not in (200, 404):
                failures.append(f"{path}: unexpected HTTP {status}")
            if not record["robots_allowed_local_rule"]:
                failures.append(f"{path}: robots migration exception missing")
            if expected:
                prior = expected[path]
                for key in ("status", "location", "noindex"):
                    if record[key] != prior[key]:
                        failures.append(f"{path}: {key} differs Local {prior[key]!r} vs public {record[key]!r}")
            results.append(record)
    counts = {str(code): sum(item["status"] == code for item in results) for code in (301, 404, 200)}
    report = {"base": base or "Local", "counts": counts, "failures": failures, "results": results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{report['base']}: {len(results)} URLs, HTTP {counts}, failures={len(failures)}; {args.out}")
    for failure in failures[:20]:
        print("FAIL", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
