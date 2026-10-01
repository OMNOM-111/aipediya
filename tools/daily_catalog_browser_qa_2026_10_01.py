"""Browser QA for Daily Catalog Update Release #021 on AIpedia Local."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "daily-catalog-20261001-021" / "browser"
BASE = "http://127.0.0.1:18810"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=EDGE)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.on("console", lambda message: errors.append(f"console: {message.text}") if message.type == "error" else None)

        def visit(path: str, expected: list[str], screenshot: str, *, dark: bool = True, full_page: bool = True) -> None:
            page.goto(BASE + path, wait_until="networkidle")
            page.evaluate("theme => localStorage.setItem('aipedia-theme', theme)", "dark" if dark else "light")
            page.reload(wait_until="networkidle")
            body = page.locator("body").inner_text()
            missing = [item for item in expected if item not in body]
            assert not missing, f"{path}: missing {missing}"
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            assert page.locator("html").get_attribute("data-theme") == ("dark" if dark else "light")
            page.screenshot(path=str(OUT / screenshot), full_page=full_page)
            if overflow > 1:
                offenders = page.evaluate("""() => [...document.querySelectorAll('body *')]
                    .map(el => { const r = el.getBoundingClientRect(); return {
                        tag: el.tagName, cls: el.className, text: (el.innerText || '').slice(0, 80),
                        left: r.left, right: r.right, width: r.width, scrollWidth: el.scrollWidth,
                        visibility: getComputedStyle(el).visibility
                    }; })
                    .filter(x => x.width && x.visibility !== 'hidden' && (x.right > innerWidth + 1 || x.left < -1))
                    .sort((a, b) => b.right - a.right).slice(0, 20)""")
                assert not offenders, f"{path}: visible horizontal overflow {overflow}px; offenders={offenders}"
            checks.append({
                "path": path,
                "expected": expected,
                "theme": "dark" if dark else "light",
                "document_overflow": overflow,
                "visible_overflow": False,
            })

        visit("/ru/?q=Gemini+4+Argon", ["Gemini 4 Argon", "Google DeepMind"], "01-models-ru-argon-dark.png")
        visit("/ru/models/gemini-4-argon-bcdaec0e", ["Gemini 4 Argon", "Fairwind"], "02-argon-ru-dark.png")
        visit("/models/pplx-embed-v2-context-9b-preview-88e13515", ["pplx-embed-v2-context-9b-preview", "MIT", "INT8"], "03-pplx-embed-en-light.png", dark=False)
        visit("/ru/models/glm-53-flash-bdc83193", ["GLM-5.3-Flash", "320", "1M", "MIT"], "04-glm-ru-dark.png")
        visit("/ru/tools/cloudflare-os-038daad4", ["Cloudflare OS", "Cloudflare", "2026"], "05-cloudflare-os-ru-dark.png")
        visit("/tools/codex-59301cf4", ["Codex", "0.159.3"], "06-codex-en-light.png", dark=False)
        visit("/ru/tools/perplexity-7a1d922e", ["Perplexity", "Automations"], "07-perplexity-ru-dark.png")
        visit("/ru/tools/sourcecraft?tab=pricing", ["SourceCraft", "9.754098", "20.409836", "45", "94.180328"], "08-sourcecraft-prices-ru-light.png", dark=False)

        page.set_viewport_size({"width": 375, "height": 812})
        visit("/tools/cloudflare-os-038daad4", ["Cloudflare OS", "2026"], "09-cloudflare-os-en-mobile-dark.png", full_page=False)
        assert page.locator(".model-panel.is-open .panel-inner").count() == 1
        visit("/tools/codex-59301cf4", ["Codex", "0.159.3"], "10-existing-codex-en-mobile-dark.png", full_page=False)

        context.close()
        browser.close()

    assert not errors, errors
    report = {"status": "PASS", "base": BASE, "checks": checks, "javascript_errors": errors}
    (OUT.parent / "browser-qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
