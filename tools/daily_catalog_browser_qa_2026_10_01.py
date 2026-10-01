"""Browser QA for the Release #021 owner fixes on AIpedia Local."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "daily-catalog-20261001-021" / "owner-fixes" / "browser"
BASE = "http://127.0.0.1:18810"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def visible_overflow(page: Page) -> list[dict[str, object]]:
    return page.evaluate(
        """() => [...document.querySelectorAll('body *')]
        .map(el => { const r = el.getBoundingClientRect(); const style = getComputedStyle(el); return {
            tag: el.tagName, cls: String(el.className), text: (el.innerText || '').slice(0, 80),
            left: r.left, right: r.right, width: r.width, display: style.display,
            visibility: style.visibility, position: style.position
        }; })
        .filter(x => x.width && x.display !== 'none' && x.visibility !== 'hidden'
          && x.position !== 'fixed' && (x.right > innerWidth + 1 || x.left < -1))
        .slice(0, 20)"""
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    failed_responses: list[str] = []
    checks: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=EDGE)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.on(
            "console",
            lambda message: errors.append(f"console: {message.text}")
            if message.type == "error"
            else None,
        )
        page.on(
            "response",
            lambda response: failed_responses.append(f"{response.status} {response.url}")
            if response.status >= 400
            else None,
        )

        def visit(
            path: str,
            expected: list[str],
            screenshot: str | None,
            *,
            theme: str,
            viewport: tuple[int, int],
            full_page: bool = True,
        ) -> None:
            page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
            page.goto(BASE + path, wait_until="networkidle")
            page.evaluate("theme => localStorage.setItem('aipedia-theme', theme)", theme)
            page.reload(wait_until="networkidle")
            body = page.locator("body").inner_text()
            missing = [item for item in expected if item not in body]
            assert not missing, f"{path}: missing {missing}"
            assert page.locator("html").get_attribute("data-theme") == theme
            offenders = visible_overflow(page)
            assert not offenders, f"{path}: visible horizontal overflow: {offenders}"
            if screenshot:
                page.screenshot(path=str(OUT / screenshot), full_page=full_page)
            checks.append(
                {
                    "path": path,
                    "expected": expected,
                    "theme": theme,
                    "viewport": list(viewport),
                    "visible_overflow": False,
                }
            )

        # Owner screenshot 1: the repaired model card, Google mark and output limit.
        visit(
            "/ru/models/gemini-4-argon-bcdaec0e",
            ["Gemini 4 Argon", "Google DeepMind", "1M"],
            "01-models-argon-logo-max-output.png",
            theme="dark",
            viewport=(1440, 900),
        )
        panel = page.locator(".model-panel.is-open")
        assert panel.locator(".panel-mark.has-logo svg").count() == 1
        stat_cards = panel.locator(".stat-card")
        assert stat_cards.count() == 4
        assert stat_cards.nth(2).locator(".stat-value").inner_text().strip() == ""
        assert stat_cards.nth(3).locator(".stat-value").inner_text().strip() == "1M"
        essentials = panel.locator(".essentials").inner_text()
        assert "Gemini 4 Argon" in essentials
        # The explicit Version row stays populated; the redundant title-line
        # repeat is intentionally suppressed when version equals the name.
        assert panel.locator(".model-meta").inner_text().count("Gemini 4 Argon") == 0

        page.goto(BASE + "/ru/models/gemini-4-argon-bcdaec0e?tab=pricing", wait_until="networkidle")
        assert page.locator("#tab-pricing:not([hidden])").count() == 1
        assert page.locator("#tab-pricing .detail-prices").count() == 0
        pricing_text = page.locator("#tab-pricing").inner_text()
        assert "$2" not in pricing_text and "$10" not in pricing_text
        assert "$4" not in pricing_text and "$20" not in pricing_text

        # Owner screenshot 2: actual hover state and all six release-snapshot labels.
        visit(
            "/ru/",
            ["Модели", "Инструменты"],
            None,
            theme="light",
            viewport=(1440, 900),
        )
        page.locator(".catalog-freshness").hover()
        popover = page.locator(".catalog-freshness-popover")
        popover.wait_for(state="visible")
        entries = popover.locator(".freshness-entry")
        assert entries.count() == 6
        labels = []
        names = []
        for index in range(entries.count()):
            action = entries.nth(index).locator(".freshness-action")
            assert action.is_visible()
            labels.append(action.inner_text().strip())
            names.append(entries.nth(index).locator(".freshness-name").inner_text().strip())
        assert labels.count("NEW") == 3, labels
        assert labels.count("UPD") == 3, labels
        assert set(names) == {
            "Gemini 4 Argon",
            "pplx-embed-v2-context-9b-preview",
            "GLM-5.3-Flash",
            "Cloudflare OS",
            "Codex",
            "Perplexity",
        }, names
        page.screenshot(path=str(OUT / "02-freshness-hover-new-upd.png"), full_page=False)

        # Owner screenshot 3: an ordinary Tools catalogue view containing Cloudflare OS.
        visit(
            "/ru/tools/?q=Cloudflare+OS",
            ["Cloudflare OS", "Cloudflare"],
            "03-tools-cloudflare-os.png",
            theme="dark",
            viewport=(1440, 900),
        )

        # Required locale/theme/viewport matrix, including the mobile freshness popover.
        visit(
            "/models/gemini-4-argon-bcdaec0e",
            ["Gemini 4 Argon", "Google DeepMind", "Max output", "1M"],
            "04-argon-en-light.png",
            theme="light",
            viewport=(1440, 900),
        )
        visit(
            "/ru/tools/cloudflare-os-038daad4",
            ["Cloudflare OS", "Cloudflare"],
            "05-tools-ru-mobile-light.png",
            theme="light",
            viewport=(375, 812),
            full_page=False,
        )
        visit(
            "/tools/cloudflare-os-038daad4",
            ["Cloudflare OS", "Cloudflare"],
            "06-tools-en-mobile-dark.png",
            theme="dark",
            viewport=(375, 812),
            full_page=False,
        )
        page.goto(BASE + "/ru/", wait_until="networkidle")
        page.locator(".catalog-freshness").click()
        page.locator(".catalog-freshness-popover").wait_for(state="visible")
        mobile_offenders = visible_overflow(page)
        assert not mobile_offenders, f"mobile freshness popover overflows the viewport: {mobile_offenders}"
        assert all(
            page.locator(".freshness-action").nth(index).is_visible()
            for index in range(page.locator(".freshness-action").count())
        )
        page.screenshot(path=str(OUT / "07-freshness-ru-mobile-dark.png"), full_page=False)

        context.close()
        browser.close()

    assert not errors, errors
    assert not failed_responses, failed_responses
    report = {
        "status": "PASS",
        "base": BASE,
        "checks": checks,
        "freshness_labels": {"NEW": 3, "UPD": 3, "visible": 6},
        "argon": {
            "google_svg": True,
            "version": "Gemini 4 Argon",
            "input_context": None,
            "max_output": 1000000,
            "active_prices": 0,
        },
        "javascript_errors": errors,
        "failed_responses": failed_responses,
    }
    report_path = OUT.parent / "browser-qa.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**report, "report": str(report_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
