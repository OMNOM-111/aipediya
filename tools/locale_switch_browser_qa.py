"""Menu-driven locale regression for Local or read-only public diagnosis.

Run with an installed Python Playwright/Chromium:
  py tools/locale_switch_browser_qa.py --base http://127.0.0.1:18810
The JSON report records every actual menu href, navigation and browser error.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright


CODES = (
    "en", "ru", "zh-Hans", "es", "fr", "ar", "pt-BR", "de", "ja", "ko", "hi",
    "id", "tr", "vi", "it", "pl", "uk", "fa", "th", "nl", "bn", "zh-Hant",
)


def prefix(code):
    return "" if code == "en" else "/" + code.lower()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def menu_click(page, code, expected_path):
    before = page.url
    page.locator("details.lang-menu summary").click()
    link = page.locator(f'a[data-set-lang="{code}"]')
    href = link.get_attribute("href")
    check(urlparse(href).path == expected_path, f"{code}: href {href} != {expected_path}")
    with page.expect_navigation(wait_until="domcontentloaded", timeout=30000) as navigation:
        link.click()
    response = navigation.value
    check(response is not None and response.status == 200, f"{code}: HTTP {response.status if response else None}")
    check(urlparse(page.url).path == expected_path, f"{code}: final URL {page.url}")
    redirects = []
    previous = response.request.redirected_from
    while previous is not None:
        redirects.insert(0, previous.url)
        previous = previous.redirected_from
    return {"before": before, "href": href, "after": page.url, "status": response.status,
            "redirect_chain": redirects}


def page_ok(page, code, expected_path):
    check(urlparse(page.url).path == expected_path, f"wrong URL {page.url}")
    check(page.locator("html").get_attribute("lang") == code, f"wrong html lang: {code}")
    check(page.locator("html").get_attribute("dir") == ("rtl" if code in ("ar", "fa") else "ltr"), f"wrong dir: {code}")
    check(page.locator("#model-rows .model-name").count() > 0, f"empty table: {page.url}")
    check(page.locator("#theme").count() == 1, "JavaScript control missing")
    check(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"),
          f"horizontal page overflow: {page.url}")


def check_case(browser, base, code, kind, width):
    context = browser.new_context(viewport={"width": width, "height": 850})
    if code != "en":
        context.add_cookies([{"name": "aipedia_lang", "value": code, "url": base + "/"}])
    page = context.new_page()
    errors, failed, bad_responses, nav_responses = [], [], [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("requestfailed", lambda request: failed.append({"url": request.url, "error": request.failure})
            if "/cdn-cgi/rum" not in request.url else None)
    page.on("response", lambda response: bad_responses.append({"url": response.url, "status": response.status})
            if response.status >= 400 and "/cdn-cgi/rum" not in response.url else None)
    page.on("response", lambda response: nav_responses.append({"url": response.url, "status": response.status})
            if response.request.is_navigation_request() else None)
    result = {"locale": code, "kind": kind, "width": width, "checks": [], "steps": [], "errors": errors,
              "failed_requests": failed, "http_errors": bad_responses, "navigation_responses": nav_responses}

    def step(name, action):
        try:
            data = action()
            result["checks"].append({"name": name, "status": "PASS"})
            print(f"{width} {code} {kind}: {name} PASS", flush=True)
            if data is not None:
                result["steps"].append({"name": name, "data": data})
        except Exception as exc:
            result["checks"].append({"name": name, "status": "FAIL", "error": str(exc)[:700]})
            print(f"{width} {code} {kind}: {name} FAIL {ascii(str(exc)[:200])}", flush=True)
            raise

    neutral = "/tools/" if kind == "tools" else "/"
    localized = prefix(code) + neutral
    try:
        page.goto(base + neutral, wait_until="domcontentloaded", timeout=30000)
        if code != "en":
            def remembered_offer():
                offer = page.locator("a.lang-offer")
                check(offer.count() == 1, "remembered-language offer missing")
                page.locator("#model-rows .model-name").first.click()
                page.locator("#model-panel.is-open .panel-inner").wait_for(timeout=20000)
                menu_href = page.locator(f'a[data-set-lang="{code}"]').get_attribute("href")
                check(offer.get_attribute("href") == menu_href,
                      f"remembered offer stale: {offer.get_attribute('href')} != {menu_href}")
                page.locator("#model-panel [data-close-panel]").first.click()
                check(urlparse(page.url).path == neutral, "offer test did not return to listing")
            step("remembered language offer follows History API", remembered_offer)
        step("root menu click", lambda: menu_click(page, code, localized))
        step("root rendered", lambda: page_ok(page, code, localized))

        def theme():
            page.locator("#theme").click()
            check(page.locator("html").get_attribute("data-theme") == "light", "light theme did not activate")
            page.locator("#theme").click()
            check(page.locator("html").get_attribute("data-theme") == "dark", "dark theme did not activate")
        step("light and dark", theme)

        def panel_open():
            page.locator("#model-rows .model-name").first.click()
            page.locator("#model-panel.is-open .panel-inner").wait_for(timeout=20000)
            path = urlparse(page.url).path
            check(path.startswith(prefix(code) + ("/tools/" if kind == "tools" else "/models/")), f"wrong card URL {path}")
            check(page.locator("#model-panel").evaluate("el => getComputedStyle(el).direction") ==
                  ("rtl" if code in ("ar", "fa") else "ltr"), f"panel direction wrong: {code}")
            for href in page.locator('a[data-set-lang]').evaluate_all("links => links.map(link => link.getAttribute('href'))"):
                check(not any(key in parse_qs(urlparse(href).query) for key in ("lang", "kind", "partial")),
                      f"unsafe panel language link: {href}")
            return path
        step("panel opens", panel_open)
        panel_path = urlparse(page.url).path
        step("panel menu to English", lambda: menu_click(page, "en", panel_path[len(prefix(code)):] if code != "en" else panel_path))
        neutral_panel = urlparse(page.url).path
        step("panel rendered in English", lambda: check(page.locator("#model-panel.is-open .panel-inner").count() == 1, "English panel absent"))
        step("panel menu return", lambda: menu_click(page, code, prefix(code) + neutral_panel))
        step("panel rendered in target", lambda: check(page.locator("#model-panel.is-open .panel-inner").count() == 1, "target panel absent"))

        def close_with(button):
            if button == "x":
                page.locator("#model-panel [data-close-panel]").first.click()
            elif button == "escape":
                page.keyboard.press("Escape")
            else:
                # .catalog-counts is sr-only since Release #021: click a neutral point of the
                # catalog outside the panel that is not a control (pager summary or toolbar gap).
                point = page.evaluate("""() => {
                    const panel = document.getElementById('model-panel');
                    const neutral = (x, y) => { const el = document.elementFromPoint(x, y);
                        return el && !panel.contains(el) && !el.closest('a, button, input, select, summary, details, label, .site-header, tr[data-slug], dialog'); };
                    for (const sel of ['.page-range', '.catalog-toolbar', '.catalog-column']) {
                        for (const el of document.querySelectorAll(sel)) { const r = el.getBoundingClientRect();
                            for (let y = r.top + 2; y < Math.min(r.bottom, innerHeight); y += 4)
                                for (let x = r.left + 2; x < Math.min(r.right, innerWidth); x += 4)
                                    if (neutral(x, y)) return [x, y]; } }
                    return null; }""")
                check(point is not None, "no neutral point outside the panel")
                page.mouse.click(point[0], point[1])
            check(page.locator("#model-panel.is-open").count() == 0, f"{button} did not close panel")
            check(urlparse(page.url).path == localized, f"{button} close URL {page.url}")
            check(page.locator(f'a[data-set-lang="es"]').get_attribute("href").startswith("/es/"), "language links stale after close")
        step("close X", lambda: close_with("x"))
        step("reopen for Escape", panel_open)
        step("close Escape", lambda: close_with("escape"))
        if width >= 768:
            step("reopen for outside click", panel_open)
            step("close outside click", lambda: close_with("outside"))
        else:
            # Below 768 px the panel is a full-screen fixed sheet under the header and
            # header clicks intentionally keep it open: there is no "outside" to click.
            result["checks"].append({"name": "close outside click", "status": "N/A",
                                     "note": "full-screen mobile panel; closed by X and Escape above"})

        def history():
            page.locator("#model-rows .model-name").first.click()
            page.locator("#model-panel.is-open .panel-inner").wait_for(timeout=20000)
            page.go_back(wait_until="domcontentloaded")
            check(urlparse(page.url).path == localized and page.locator("#model-panel.is-open").count() == 0, "Back failed")
            page.go_forward(wait_until="domcontentloaded")
            page.locator("#model-panel.is-open .panel-inner").wait_for(timeout=20000)
            check(urlparse(page.url).path.startswith(prefix(code) + ("/tools/" if kind == "tools" else "/models/")), "Forward failed")
            page.keyboard.press("Escape")
        step("Back Forward", history)

        def search():
            field = page.locator("#catalog-search")
            field.fill("zz-language-test-no-match")
            with page.expect_navigation(wait_until="domcontentloaded"):
                field.press("Enter")
            check(parse_qs(urlparse(page.url).query).get("q") == ["zz-language-test-no-match"], "search query lost")
            check(page.locator(".empty").count() > 0, "empty search result missing")
        step("search", search)
        page.goto(base + localized, wait_until="domcontentloaded")

        def sort():
            with page.expect_navigation(wait_until="domcontentloaded"):
                if width < 721:
                    page.locator('button[data-sheet-open="sort"]').click()
                    page.locator('dialog[data-sheet="sort"] a[href*="sort=name_asc"]').click()
                else:
                    page.locator('a[data-sort="name"]').first.click()
            check(parse_qs(urlparse(page.url).query).get("sort") in (["name_asc"], ["name_desc"]), "sort not applied")
            page_ok(page, code, localized)
        step("sort", sort)

        def query_switch():
            page.locator("details.lang-menu summary").click()
            href = page.locator('a[data-set-lang="en"]').get_attribute("href")
            check(parse_qs(urlparse(href).query).get("sort") in (["name_asc"], ["name_desc"]), "sort lost from language link")
            check(not any(x in parse_qs(urlparse(href).query) for x in ("lang", "kind", "partial")), "unsafe query retained")
            page.locator("details.lang-menu summary").click()
        step("query preserved", query_switch)

        def filter_status():
            field_name = "status" if kind == "models" else "category"
            if width < 721:
                page.locator('button[data-sheet-open="filters"]').click()
                select = page.locator(f'dialog[data-sheet="filters"] select[name="{field_name}"]').first
            else:
                details = page.locator('details.col-filter').filter(has=page.locator(f'select[name="{field_name}"]')).first
                details.locator("xpath=ancestor::th[1]").hover()
                details.locator("summary").click()
                select = details.locator(f'select[name="{field_name}"]')
            value = "active" if kind == "models" else select.locator('option[value]:not([value=""])').first.get_attribute("value")
            with page.expect_navigation(wait_until="domcontentloaded"):
                select.select_option(value)
                if width < 721:
                    page.locator('dialog[data-sheet="filters"] .sheet-apply').click()
            check(set(parse_qs(urlparse(page.url).query).get(field_name, [])) == {value}, "filter not applied")
            page_ok(page, code, localized)
        step("filter", filter_status)

        if kind == "models":
            def pagination():
                page.goto(base + localized, wait_until="domcontentloaded")
                before = page.locator("#model-rows .model-name").count()
                next_url = page.locator("#infinite-scroll").get_attribute("data-next-url")
                check(next_url, "pagination URL missing")
                page.locator("#infinite-scroll").scroll_into_view_if_needed()
                page.wait_for_function("n => document.querySelectorAll('#model-rows .model-name').length > n", arg=before, timeout=20000)
                return {"before": before, "after": page.locator("#model-rows .model-name").count(), "next": next_url}
            step("infinite loading", pagination)
    except Exception as exc:
        if not result["checks"] or result["checks"][-1]["status"] != "FAIL":
            result["checks"].append({"name": "case setup", "status": "FAIL", "error": str(exc)[:700]})
    finally:
        result["final_url"] = page.url
        result["errors"] = list(errors)
        result["failed_requests"] = list(failed)
        result["http_errors"] = list(bad_responses)
        result["navigation_responses"] = list(nav_responses)
        result["status"] = "PASS" if result["checks"] and all(x["status"] in ("PASS", "N/A") for x in result["checks"]) and not errors and not failed and not bad_responses else "FAIL"
        context.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:18810")
    parser.add_argument("--out", default="artifacts/locale-switch-browser-qa.json")
    parser.add_argument("--code", choices=CODES)
    parser.add_argument("--codes", help="Comma-separated subset for partitioned QA")
    parser.add_argument("--width", type=int, choices=(1440, 375))
    args = parser.parse_args()
    selected_codes = (args.code,) if args.code else tuple(args.codes.split(",")) if args.codes else CODES
    if not selected_codes or any(code not in CODES for code in selected_codes):
        parser.error("--codes must contain supported locale codes")
    report = {"base": args.base, "started_utc": datetime.now(timezone.utc).isoformat(), "cases": []}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in ((args.width,) if args.width else (1440, 375)):
            for code in selected_codes:
                for kind in ("models", "tools"):
                    case = check_case(browser, args.base.rstrip("/"), code, kind, width)
                    report["cases"].append(case)
                    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"width": width, "locale": code, "kind": kind, "status": case["status"],
                                      "failed_checks": [x for x in case["checks"] if x["status"] == "FAIL"]}), flush=True)
        browser.close()
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = sum(case["status"] == "PASS" for case in report["cases"])
    report["failed"] = len(report["cases"]) - report["passed"]
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "passed": report["passed"], "failed": report["failed"]}, ensure_ascii=False))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
