"""Visual smoke checks for Local. Requires Playwright + Chromium and a running Local server.

Run: python tools/browser_check.py
Screenshots: artifacts/
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts"
BASE = "http://127.0.0.1:18810"


def main():
    OUT.mkdir(exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({
            "status": "SKIP",
            "reason": "Playwright is not installed in this Python environment.",
            "local": BASE,
            "note": "Catalog tests and Cursor-browser screenshots remain the Local evidence.",
        }, ensure_ascii=False))
        return

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE + "/?lang=ru", wait_until="networkidle")
        page.locator(".model-name").first.wait_for()
        assert page.locator("#model-panel").count() == 1
        assert "Рейтинг AIpedia" in page.locator("thead").inner_text()
        assert "75%" not in page.locator("tbody .rating-col").inner_text()
        page.screenshot(path=str(OUT / "catalog-desktop.png"))
        page.locator(".model-name").first.click()
        page.wait_for_selector(".model-panel.is-open .panel-inner")
        assert page.get_by_role("button", name="Поделиться").count() == 1
        assert page.get_by_role("button", name="Сохранить").get_attribute("aria-disabled") == "true"
        page.screenshot(path=str(OUT / "model-desktop.png"))
        page.goto(BASE + "/?q=nothing-matches-this")
        assert "Модели не найдены" in page.locator(".empty").inner_text()
        page.goto(BASE + "/?lang=en")
        assert page.locator("html").get_attribute("lang") == "en"
        for width in (390, 320):
            page.set_viewport_size({"width": width, "height": 844})
            page.goto(BASE + "/?lang=ru", wait_until="networkidle")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            page.screenshot(path=str(OUT / f"catalog-mobile-{width}.png"))
        assert not errors, errors
        browser.close()
    print(json.dumps({"status": "PASS", "javascript_errors": errors}))


if __name__ == "__main__":
    main()
