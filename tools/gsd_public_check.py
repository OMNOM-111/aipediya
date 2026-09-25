"""Read-only GSD-1.0 contract check against a running site (Local or Production).

    python tools/gsd_public_check.py https://aipediya.com [--out file.json]
    python tools/gsd_public_check.py http://127.0.0.1:18810 --local

A small, polite sample (about 25 GETs, sequential): legacy redirects, locale
pages, canonical/hreflang, robots, sitemap index and one child. It never
submits anything and never follows links beyond the sample. Before GSD-1.0 is
deployed, Production is expected to FAIL most checks (it still serves ?lang=).
"""
import argparse
import json
import re
import sys
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

UA = "AIpediya-GSD-check/1.0 (+read-only owner QA)"
PUBLIC = "https://aipediya.com"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = build_opener(NoRedirect)


def get(url):
    request = Request(url, headers={"User-Agent": UA})
    try:
        with OPENER.open(request, timeout=30) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read().decode("utf-8", "replace")
    except HTTPError as error:
        return error.code, {k.lower(): v for k, v in (error.headers or {}).items()}, ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("--local", action="store_true", help="Local: robots must be Disallow: /")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    results = []

    def check(name, ok, detail=""):
        results.append({"check": name, "ok": bool(ok), "detail": detail})

    status, headers, body = get(base + "/sitemaps/en.xml")
    slug = (re.search(r"/models/([a-z0-9-]+)</loc>", body) or [None, None])[1]
    for source, target in (("/?lang=ru", "/ru/"), ("/?lang=en", "/"), ("/?lang=ru&kind=tool", "/ru/tools/"),
                           ("/en/", "/"), ("/zh-Hans/", "/zh-hans/"), ("/ru", "/ru/")):
        code, hdrs, _ = get(base + source)
        location = hdrs.get("location", "")
        check(f"301 {source}", code == 301 and location.endswith(target), f"{code} -> {location}")
        time.sleep(0.3)
    for path, lang in (("/", "en"), ("/ru/", "ru"), ("/ar/tools/", "ar"), ("/zh-hans/methodology", "zh-Hans")):
        code, hdrs, html = get(base + path)
        canonical = (re.search(r'<link rel="canonical" href="([^"]+)"', html) or [None, None])[1]
        check(f"200 {path}", code == 200, str(code))
        check(f"lang {path}", f'<html lang="{lang}"' in html)
        check(f"canonical {path}", canonical == PUBLIC + path, str(canonical))
        check(f"hreflang self {path}", f'href="{PUBLIC}{path}"' in html and 'hreflang="x-default"' in html)
        check(f"no Vary Cookie {path}", "cookie" not in hdrs.get("vary", "").lower(), hdrs.get("vary", ""))
        time.sleep(0.3)
    if slug:
        code, _, html = get(f"{base}/ru/models/{slug}")
        check("card SSR ru", code == 200 and "<h1" in html and "panel-inner" in html, str(code))
        code, hdrs, _ = get(f"{base}/models/{slug}?lang=de")
        check("legacy card 301", code == 301 and hdrs.get("location", "") == f"/de/models/{slug}", hdrs.get("location", ""))
    code, _, _ = get(base + "/models/definitely-not-a-record?lang=ru")
    check("unknown record 404", code == 404, str(code))
    code, _, _ = get(base + "/?page=9999")
    check("out-of-range page 404", code == 404, str(code))
    code, _, robots = get(base + "/robots.txt")
    if args.local:
        check("robots Local disallow", "Disallow: /\n" in robots)
    else:
        check("robots facets blocked", "Disallow: /*?q=" in robots and "Disallow: /*?page=" not in robots)
        check("robots sitemap", f"Sitemap: {PUBLIC}/sitemap.xml" in robots)
    code, _, index = get(base + "/sitemap.xml")
    children = re.findall(r"<loc>([^<]+)</loc>", index)
    check("sitemap index", code == 200 and "<sitemapindex" in index and len(children) >= 2, f"{len(children)} children")
    code, _, child = get(base + "/sitemaps/ru.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", child)
    check("ru sitemap child", code == 200 and locs and all(url.startswith(PUBLIC + "/ru/") for url in locs), f"{len(locs)} locs")
    passed = sum(item["ok"] for item in results)
    report = {"base": base, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "passed": passed, "total": len(results), "results": results}
    text = json.dumps(report, indent=1, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
