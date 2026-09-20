"""Run with a Python environment containing Playwright and Chromium."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts"
BASE = "http://127.0.0.1:18810"


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until="networkidle")
        page.locator(".model-name").first.wait_for()
        assert page.locator(".model-name").count() == 7
        assert page.locator("svg.lucide").count() > 5
        page.screenshot(path=str(OUT / "catalog-desktop.png"), full_page=True)
        page.get_by_role("searchbox").fill("Qwen")
        page.get_by_role("button", name="Найти", exact=True).click()
        assert page.locator(".model-name").count() == 1
        page.locator(".model-name").click()
        page.wait_for_url("**/models/qwen3-8b?**")
        assert page.locator("h1").inner_text() == "Qwen3-8B"
        page.goto(BASE + "/?category=image")
        assert page.locator(".model-name").count() == 1
        assert "$0.003" in page.locator("tbody").inner_text()
        page.goto(BASE)
        page.select_option('select[name="price"]', "budget")
        page.wait_for_url("**price=budget**")
        assert page.locator(".model-name").count() == 2
        page.goto(BASE)
        page.select_option('select[name="sort"]', "price_asc")
        page.wait_for_url("**sort=price_asc**")
        assert page.locator(".model-name").first.inner_text() == "Gemini 2.5 Flash-Lite"
        page.locator(".column-picker summary").click()
        page.get_by_role("checkbox", name="Контекст").check()
        page.locator(".column-picker button").click()
        page.wait_for_url("**col=context**")
        assert "Контекст" in page.locator("thead").inner_text()
        page.goto(BASE + "/models/gemini-2-5-pro")
        page.screenshot(path=str(OUT / "model-desktop.png"), full_page=True)
        page.locator(".evaluation details summary").first.click()
        assert page.locator(".evaluation details").first.get_attribute("open") is not None
        page.goto(BASE + "/?q=nothing-matches-this")
        assert page.get_by_role("heading", name="Модели не найдены").is_visible()
        page.goto(BASE + "/?lang=en")
        assert page.locator("html").get_attribute("lang") == "en"
        assert "The AI model encyclopedia" in page.locator("h1").inner_text()
        for width in (390, 320):
            page.set_viewport_size({"width": width, "height": 844})
            page.goto(BASE)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            first = page.locator("tbody .model-col").first
            x_before = first.bounding_box()["x"]
            page.locator(".table-scroll").evaluate("el => el.scrollLeft = 200")
            assert abs(first.bounding_box()["x"] - x_before) < 2
            page.locator(".table-scroll").evaluate("el => el.scrollLeft = 0")
            page.screenshot(path=str(OUT / f"catalog-mobile-{width}.png"), full_page=True)
            page.goto(BASE + "/models/gemini-2-5-pro")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(OUT / f"model-mobile-{width}.png"), full_page=True)
        nojs = browser.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
        static_page = nojs.new_page()
        static_page.goto(BASE + "/?q=Qwen")
        assert static_page.locator(".model-name").count() == 1
        static_page.locator(".model-name").click()
        assert static_page.locator("h1").inner_text() == "Qwen3-8B"
        assert not errors, errors
        browser.close()
    print(json.dumps({"status": "PASS", "screenshots": 6, "javascript_errors": errors}))


if __name__ == "__main__":
    main()
