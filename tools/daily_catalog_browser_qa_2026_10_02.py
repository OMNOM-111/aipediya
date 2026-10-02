"""Browser QA for Release #022 (Daily Catalog Update 2026-10-02) on AIpedia Local."""
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "daily-catalog-20261002-022" / "browser"
BASE = "http://127.0.0.1:18810"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

MODELS = {
    "clef-bdc7df20": ("Clef", "#341", ["Cloudflare", "65 536", "$0.24", "Apache-2.0"]),
    "clef-flash-4eaa2224": ("Clef-flash", "#342", ["Cloudflare", "65 536", "$0.09", "Apache-2.0"]),
    "strands-decider-2b-81831af4": ("Strands Decider 2B", "#343", ["Strands Agents / AWS", "4 096", "Apache-2.0"]),
    "kev-0-8b-46011d0e": ("Kev-0.8B", "#323", ["Jared Palmer", "8 192", "Apache-2.0"]),
    "kev-4b-2ab542cc": ("Kev-4B", "#324", ["Jared Palmer", "8 192", "Apache-2.0"]),
    "kev-27b-v2-59a82a0e": ("Kev-27B v2", "#338", ["Jared Palmer", "65 536", "Apache-2.0"]),
    "kev-9b-v2-7e1fcef1": ("Kev-9B v2", "#339", ["Jared Palmer", "8 192", "Apache-2.0"]),
}
SHIFTED_MODELS = {"sarvam-vision-2-1": "#325", "gemini-4-argon-bcdaec0e": "#337",
                  "pplx-embed-v2-context-9b-preview-88e13515": "#340"}
TOOLS = {
    "anythingllm-90d04ca3": ("AnythingLLM", "#60", ["Mintplex Labs Inc", "1.17.0"]),
    "github-copilot-179ab1d0": ("GitHub Copilot", "#22", ["GitHub", "Windows", "macOS"]),
    "cloudflare-os-038daad4": ("Cloudflare OS", "#147", ["Cloudflare"]),
}


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
    failed: list[str] = []
    checks: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=EDGE)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
        page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)

        def visit(path, expected, shot=None, *, theme="dark", viewport=(1440, 900), absent=()):
            page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
            page.goto(BASE + path, wait_until="networkidle")
            page.evaluate("t => localStorage.setItem('aipedia-theme', t)", theme)
            page.reload(wait_until="networkidle")
            body = page.locator("body").inner_text()
            missing = [item for item in expected if item not in body]
            assert not missing, f"{path}: missing {missing}"
            present = [item for item in absent if item in body]
            assert not present, f"{path}: unexpected {present}"
            assert page.locator("html").get_attribute("data-theme") == theme
            offenders = visible_overflow(page)
            assert not offenders, f"{path} {viewport}: visible horizontal overflow: {offenders}"
            if shot:
                page.screenshot(path=str(OUT / shot), full_page=False)
            checks.append({"path": path, "theme": theme, "viewport": list(viewport), "expected": expected})
            return body

        def panel_text():
            # Includes the hidden Pricing / Checks tabs, which are part of the card.
            return page.locator(".model-panel.is-open").text_content()

        def hidden_badges(slugs):
            return page.evaluate(
                """slugs => slugs.map(s => { const a = document.querySelector(`a.model-name[data-slug="${s}"]`);
                    if (!a) return [s, 'absent']; const b = a.querySelector('.catalog-update-badge');
                    return [s, b ? (b.hidden ? 'hidden' : 'visible') : 'none']; })""", slugs)

        # --- RU desktop: counts, numbers, freshness, sorting
        visit("/ru/", ["343", "Модели", "Инструменты"], "01-ru-models-desktop.png")
        visit("/ru/tools/", ["157"], None, theme="light")
        visit("/ru/?sort=number_desc", ["Strands Decider 2B", "Clef-flash", "Clef"], "02-ru-newest.png")
        first = page.locator("tbody tr").first.inner_text()
        assert "343" in first and "Strands Decider 2B" in first, first
        rows = [page.locator("tbody tr").nth(i).inner_text() for i in range(5)]
        assert [re.search(r"\b(3\d\d)\b", r).group(1) for r in rows[:4]] == ["343", "342", "341", "340"], rows
        visit("/ru/?sort=number_asc", ["Jurassic-1 Jumbo"], None, theme="light")
        assert "Jurassic-1 Jumbo" in page.locator("tbody tr").first.inner_text()
        visit("/ru/tools/?sort=number_asc&q=AnythingLLM", ["AnythingLLM", "60"], None)

        # Catalog Freshness: popover = release snapshot (8 NEW); row badges honour real dates.
        visit("/ru/", ["Модели"], None, theme="light")
        page.locator(".catalog-freshness").hover()
        popover = page.locator(".catalog-freshness-popover")
        popover.wait_for(state="visible")
        entries = popover.locator(".freshness-entry")
        names = [entries.nth(i).locator(".freshness-name").inner_text().strip() for i in range(entries.count())]
        labels = [entries.nth(i).locator(".freshness-action").inner_text().strip() for i in range(entries.count())]
        assert entries.count() == 8, names
        assert set(names) == {"Clef", "Clef-flash", "Strands Decider 2B", "Kev-0.8B", "Kev-4B", "Kev-9B v2", "Kev-27B v2", "AnythingLLM"}, names
        assert labels.count("NEW") == 8, labels
        page.screenshot(path=str(OUT / "03-ru-freshness-popover.png"), full_page=False)
        visit("/ru/?q=Kev", ["Kev-0.8B", "Kev-4B", "Kev-9B v2", "Kev-27B v2"], None)
        kev_badges = hidden_badges(["kev-0-8b-46011d0e", "kev-4b-2ab542cc", "kev-9b-v2-7e1fcef1", "kev-27b-v2-59a82a0e"])
        visit("/ru/?q=Clef", ["Clef", "Clef-flash"], "04-ru-search-clef.png")
        clef_badges = hidden_badges(["clef-bdc7df20", "clef-flash-4eaa2224"])
        visit("/ru/tools/?q=AnythingLLM", ["AnythingLLM", "Mintplex Labs Inc"], None)
        tool_badges = hidden_badges(["anythingllm-90d04ca3"])
        badge_state = kev_badges + clef_badges + tool_badges
        assert all(state in ("hidden", "none") for _slug, state in badge_state), badge_state
        visit("/ru/?q=Strands", ["Strands Decider 2B"], None)
        visit("/ru/?q=%40cf%2Fcloudflare%2Fclef", ["Clef"], None)
        visit("/ru/?q=jaredpalmer%2Fkev-9b", ["Kev-9B v2"], None)

        # --- direct URLs: every new / changed card, RU + EN desktop
        for slug, (name, number, extra) in MODELS.items():
            visit(f"/ru/models/{slug}", [name, number, "США", "Открытые веса", *extra], None)
            panel = panel_text()
            assert "Публикуемых независимых результатов для точной версии нет" in panel, slug
            assert page.locator(".model-panel.is-open .flag, .model-panel.is-open img[src*='flags'], .model-panel.is-open svg").count() >= 1
            visit(f"/models/{slug}", [name, number, "Apache-2.0"], None, theme="light")
        page.goto(BASE + "/ru/models/clef-bdc7df20", wait_until="networkidle")
        page.screenshot(path=str(OUT / "05-ru-clef-card.png"), full_page=False)
        page.goto(BASE + "/ru/models/kev-27b-v2-59a82a0e", wait_until="networkidle")
        page.screenshot(path=str(OUT / "06-ru-kev-27b-card.png"), full_page=False)
        for slug, number in SHIFTED_MODELS.items():
            visit(f"/ru/models/{slug}", [number], None)
        for slug, (name, number, extra) in TOOLS.items():
            visit(f"/ru/tools/{slug}", [name, number, *extra], None)
            visit(f"/tools/{slug}", [name, number], None, theme="light")
        page.goto(BASE + "/ru/tools/anythingllm-90d04ca3?tab=pricing", wait_until="networkidle")
        pricing = panel_text()
        for item in ("$0", "$50", "$99", "Docker", "Cloud"):
            assert item in pricing, item
        assert "не бесплатный inference" in pricing
        page.screenshot(path=str(OUT / "07-ru-anythingllm-pricing.png"), full_page=False)
        page.goto(BASE + "/tools/github-copilot-179ab1d0", wait_until="networkidle")
        page.screenshot(path=str(OUT / "08-en-copilot.png"), full_page=False)

        # --- EN desktop listing
        visit("/", ["343", "Models"], "09-en-models-desktop.png", theme="light")
        visit("/tools/", ["157", "Tools"], None)

        # --- RU mobile 375
        visit("/ru/", ["Модели"], "10-ru-mobile-models.png", viewport=(375, 812))
        visit("/ru/tools/", ["Инструменты"], None, viewport=(375, 812), theme="light")
        for slug in ("clef-bdc7df20", "strands-decider-2b-81831af4", "kev-27b-v2-59a82a0e"):
            visit(f"/ru/models/{slug}", [MODELS[slug][0]], None, viewport=(375, 812))
        visit("/ru/tools/anythingllm-90d04ca3", ["AnythingLLM"], "11-ru-mobile-anythingllm.png", viewport=(375, 812))
        visit("/ru/tools/github-copilot-179ab1d0", ["GitHub Copilot"], None, viewport=(375, 812), theme="light")
        page.goto(BASE + "/ru/", wait_until="networkidle")
        page.locator(".catalog-freshness").click()
        page.locator(".catalog-freshness-popover").wait_for(state="visible")
        offenders = visible_overflow(page)
        assert not offenders, f"mobile freshness popover overflows: {offenders}"
        page.screenshot(path=str(OUT / "12-ru-mobile-freshness.png"), full_page=False)

        context.close()
        browser.close()

    assert not errors, errors
    assert not failed, failed
    report = {
        "status": "PASS", "base": BASE, "checks": len(checks), "paths": checks,
        "freshness": {"popover_entries": 8, "NEW": 8, "UPD": 0, "row_badges": badge_state},
        "counts": {"models": 343, "tools": 157},
        "javascript_errors": errors, "failed_responses": failed,
    }
    path = OUT.parent / "browser-qa.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "paths"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
