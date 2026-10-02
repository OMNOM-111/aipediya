"""Interactive Local/offline history regression using real Chromium controls."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = list(range(1, 16))


def check_page(browser, url, width, screenshot):
    context = browser.new_context(viewport={"width": width, "height": 850})
    page = context.new_page()
    errors = []
    failed = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("requestfailed", lambda request: failed.append(request.url))
    response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
    if response and response.status != 200:
        raise AssertionError(f"HTTP {response.status}: {url}")
    page.locator(".ph-release-card").first.wait_for()
    assert page.locator(".ph-release-card").count() == 15
    assert page.locator(".ph-environment.ph-local").count() == 1
    assert page.locator(".ph-environment.ph-production").count() == 1
    assert page.locator(".ph-env-version").all_text_contents()[0].startswith("Release #015 · AIpediya v0.13.2")
    assert page.locator(".ph-env-version").all_text_contents()[1].startswith("Release #015 · AIpediya v0.13.2")
    assert page.locator(".site-header,.site-footer,form.search").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    numbers = [int(text.split("Release #", 1)[1][:3])
               for text in page.locator(".ph-release-id").all_text_contents()]
    assert numbers == EXPECTED, numbers
    page.screenshot(path=str(screenshot), full_page=True)

    opened = []
    for index, number in enumerate(EXPECTED):
        card = page.locator(".ph-release-card").nth(index)
        card.click()
        assert page.locator("#ph-dialog").is_visible(), number
        assert page.locator("#ph-dialog-title").inner_text().strip(), number
        assert f"Release #{number:03d}" in page.locator("#ph-dialog-body").inner_text(), number
        page.locator("#ph-close").click()
        assert page.locator("#ph-dialog").is_hidden(), number
        assert card.evaluate("el => document.activeElement === el"), number
        opened.append(number)

    first = page.locator(".ph-release-card").first
    first.focus()
    page.keyboard.press("Enter")
    assert page.locator("#ph-dialog").is_visible()
    page.keyboard.press("Escape")
    assert page.locator("#ph-dialog").is_hidden()
    first.focus()
    page.keyboard.press("Space")
    assert page.locator("#ph-dialog").is_visible()
    page.locator("#ph-scrim").click(position={"x": 5, "y": 5})
    assert page.locator("#ph-dialog").is_hidden()

    page.locator("#theme").click()
    assert page.locator("html").get_attribute("data-theme") == "light"
    page.locator("#edition-toggle").click()
    assert page.locator("html").get_attribute("lang") == "en"
    assert page.locator(".ph-release-card").count() == 15
    page.locator("#edition-toggle").click()
    assert page.locator("html").get_attribute("lang") == "ru"
    assert page.locator("html").get_attribute("data-theme") == "light"
    assert not errors and not failed, (errors, failed)
    result = {"url": url, "width": width, "releases_opened": opened,
              "x_escape_outside_keyboard": True, "theme_and_edition": True,
              "console_errors": errors, "failed_requests": failed, "status": "PASS"}
    context.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:18810")
    parser.add_argument("--out", default="artifacts/history-015-browser-qa.json")
    args = parser.parse_args()
    targets = [("live", args.base.rstrip("/") + "/ru/history/"),
               ("offline", (ROOT / "timeline.html").as_uri())]
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cases = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, url in targets:
            for width in (1440, 375):
                screenshot = out.parent / f"history-015-{name}-{width}.png"
                case = check_page(browser, url, width, screenshot)
                case["screenshot"] = str(screenshot)
                cases.append(case)
                print(f"{name} {width}: PASS", flush=True)
        browser.close()
    report = {"cases": cases, "passed": len(cases), "total": 4,
              "release_card_openings": sum(len(case["releases_opened"]) for case in cases)}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "total", "release_card_openings")}))


if __name__ == "__main__":
    main()
