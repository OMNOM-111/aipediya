"""Browser QA for Release #022 (Daily Catalog Update 2026-10-02), including the
owner-fix pass: no unapproved "Max output" card, official marks, ADD/UPD vs
NEW semantics, the recent-releases block and NEW flicker regression.

Usage: python tools/daily_catalog_browser_qa_2026_10_02.py [--base URL] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

MODELS = {
    "clef-bdc7df20": ("Clef", "#341", ["Cloudflare", "65 536", "Apache-2.0"], True),
    "clef-flash-4eaa2224": ("Clef-flash", "#342", ["Cloudflare", "65 536", "Apache-2.0"], True),
    "strands-decider-2b-81831af4": ("Strands Decider 2B", "#343", ["Strands Agents / AWS", "4 096", "Apache-2.0"], True),
    "kev-0-8b-46011d0e": ("Kev-0.8B", "#323", ["Jared Palmer", "8 192", "Apache-2.0"], False),
    "kev-4b-2ab542cc": ("Kev-4B", "#324", ["Jared Palmer", "8 192", "Apache-2.0"], False),
    "kev-27b-v2-59a82a0e": ("Kev-27B v2", "#338", ["Jared Palmer", "65 536", "Apache-2.0"], False),
    "kev-9b-v2-7e1fcef1": ("Kev-9B v2", "#339", ["Jared Palmer", "8 192", "Apache-2.0"], False),
}
PRICES = {"clef-bdc7df20": "$0.24", "clef-flash-4eaa2224": "$0.09"}
SHIFTED_MODELS = {"sarvam-vision-2-1": "#325", "gemini-4-argon-bcdaec0e": "#337",
                  "pplx-embed-v2-context-9b-preview-88e13515": "#340"}
TOOLS = {
    "anythingllm-90d04ca3": ("AnythingLLM", "#60", ["Mintplex Labs Inc", "1.17.0"], True),
    "github-copilot-179ab1d0": ("GitHub Copilot", "#22", ["GitHub", "Windows", "macOS"], True),
    "cloudflare-os-038daad4": ("Cloudflare OS", "#147", ["Cloudflare"], True),
    "cloudflare-web-search-api-0bb0f08e": ("Cloudflare Web Search API", "#158", ["Cloudflare", "beta"], True),
    "grok-speech-to-text-cfab200f": ("Grok Speech to Text", "", ["xAI"], True),
    "grok-speech-to-text-streaming-1109f624": ("Grok Speech to Text Streaming", "", ["xAI"], True),
}
RECENT = {"clef-bdc7df20", "clef-flash-4eaa2224", "strands-decider-2b-81831af4", "cloudflare-web-search-api-0bb0f08e"}
ADD = {"Clef", "Clef-flash", "Strands Decider 2B", "Kev-0.8B", "Kev-4B", "Kev-9B v2", "Kev-27B v2",
       "AnythingLLM", "Cloudflare Web Search API"}
UPD = {"GitHub Copilot"}
NO_MAX_OUTPUT = ("Max output", "Максимум на выходе", "Input context", "Входной контекст", "arrow-up-to-line")

# Records every NEW badge as soon as it is inserted (before page scripts run)
# and any later hide/removal, so a transient NEW on any frame is caught.
OBSERVER = """
(() => {
  window.__newLog = [];
  const record = (el, event) => {
    const link = el.closest && el.closest('a.model-name');
    window.__newLog.push({event, slug: link ? link.dataset.slug : '', hidden: !!el.hidden, t: performance.now()});
  };
  const scan = (node) => {
    if (!(node instanceof Element)) return;
    if (node.matches('.catalog-update-badge')) record(node, 'added');
    node.querySelectorAll && node.querySelectorAll('.catalog-update-badge').forEach((el) => record(el, 'added'));
  };
  new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'childList') {
        m.addedNodes.forEach(scan);
        m.removedNodes.forEach((n) => { if (n instanceof Element && n.matches('.catalog-update-badge')) record(n, 'removed'); });
      } else if (m.type === 'attributes' && m.target.matches('.catalog-update-badge')) {
        record(m.target, 'attr:' + m.attributeName);
      }
    }
  }).observe(document, {subtree: true, childList: true, attributes: true, attributeFilter: ['hidden', 'class', 'style']});
})();
"""


def visible_overflow(page: Page) -> list[dict[str, object]]:
    return page.evaluate(
        """() => [...document.querySelectorAll('body *')]
        .map(el => { const r = el.getBoundingClientRect(); const style = getComputedStyle(el); return {
            tag: el.tagName, cls: String(el.className).slice(0, 60), left: r.left, right: r.right, width: r.width,
            display: style.display, visibility: style.visibility, position: style.position }; })
        .filter(x => x.width && x.display !== 'none' && x.visibility !== 'hidden'
          && x.position !== 'fixed' && (x.right > innerWidth + 1 || x.left < -1))
        .slice(0, 10)"""
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:18810")
    parser.add_argument("--out", default=str(ROOT / "artifacts" / "daily-catalog-20261002-022" / "owner-fix"))
    args = parser.parse_args()
    base = args.base.rstrip("/")
    out = Path(args.out)
    shots = out / "browser"
    shots.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    failed: list[str] = []
    checks: list[dict[str, object]] = []
    flicker: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=EDGE)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_init_script(OBSERVER)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
        page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)

        def set_theme(theme):
            page.evaluate("t => { try { localStorage.setItem('aipedia-theme', t) } catch (e) {} }", theme)

        def visit(path, expected, shot=None, *, theme="dark", viewport=(1440, 900), absent=()):
            page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
            page.goto(base + path, wait_until="networkidle")
            set_theme(theme)
            page.reload(wait_until="networkidle")
            body = page.locator("body").inner_text()
            missing = [item for item in expected if item not in body]
            assert not missing, f"{path}: missing {missing}"
            html = page.content()
            present = [item for item in absent if item in html]
            assert not present, f"{path}: unexpected {present}"
            assert page.locator("html").get_attribute("data-theme") == theme
            offenders = visible_overflow(page)
            assert not offenders, f"{path} {viewport}: visible horizontal overflow: {offenders}"
            if shot:
                page.screenshot(path=str(shots / shot), full_page=False)
            checks.append({"path": path, "theme": theme, "viewport": list(viewport), "expected": expected})
            return body

        def collect_flicker(label):
            log = page.evaluate("window.__newLog || []")
            wrong = [x for x in log if x["slug"] not in RECENT or x["event"] != "added" or x["hidden"]]
            flicker.append({"step": label, "badges": sorted({x["slug"] for x in log}), "wrong": wrong})
            assert not wrong, f"{label}: NEW appeared/changed on a wrong frame: {wrong[:5]}"

        def panel_text():
            return page.locator(".model-panel.is-open").text_content()

        # --- counts, chronology, sorting
        visit("/ru/", ["343", "158", "Модели", "Инструменты"], "01-ru-models-desktop.png")
        visit("/ru/?sort=number_desc", ["Strands Decider 2B", "Clef-flash", "Clef"], "02-ru-newest.png")
        rows = [page.locator("tbody tr").nth(i).inner_text() for i in range(4)]
        assert [re.search(r"\b(3\d\d)\b", r).group(1) for r in rows] == ["343", "342", "341", "340"], rows
        visit("/ru/?sort=number_asc", ["Jurassic-1 Jumbo"], None, theme="light")
        assert "Jurassic-1 Jumbo" in page.locator("tbody tr").first.inner_text()
        visit("/ru/tools/?sort=number_desc", ["Cloudflare Web Search API"], None)
        assert "Cloudflare Web Search API" in page.locator("tbody tr").first.inner_text()
        visit("/ru/tools/?sort=number_asc&q=AnythingLLM", ["AnythingLLM", "60"], None)

        # --- Catalog Freshness: ADD/UPD snapshot and the separate recent-releases block
        visit("/ru/", ["Модели"], None, theme="light")
        page.locator(".catalog-freshness").hover()
        popover = page.locator(".catalog-freshness-popover")
        popover.wait_for(state="visible")
        update = popover.locator(".freshness-update-list .freshness-entry")
        pairs = [(update.nth(i).locator(".freshness-action").inner_text().strip(),
                  update.nth(i).locator(".freshness-name").inner_text().strip()) for i in range(update.count())]
        assert {n for a, n in pairs if a == "ADD"} == ADD, pairs
        assert {n for a, n in pairs if a == "UPD"} == UPD, pairs
        assert not [a for a, _n in pairs if a not in ("ADD", "UPD")], pairs
        recent = popover.locator(".freshness-recent-list .freshness-entry")
        recent_names = {recent.nth(i).locator(".freshness-name").inner_text().strip() for i in range(recent.count())}
        assert recent_names == {"Clef", "Clef-flash", "Strands Decider 2B", "Cloudflare Web Search API"}, recent_names
        assert "Новые релизы за последние 24 часа" in popover.inner_text()
        page.wait_for_timeout(400)  # let the 160 ms fade-in finish before the frame
        page.screenshot(path=str(shots / "03-ru-freshness-popover.png"), full_page=False)
        visit("/", ["Models"], None)
        page.locator(".catalog-freshness").hover()
        assert "New releases in the last 24 hours" in page.locator(".catalog-freshness-popover").inner_text()

        # --- NEW flicker regression: Models <-> Tools, back/forward, infinite load; desktop + mobile
        for viewport in ((1440, 900), (375, 812)):
            page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
            for i in range(3):
                for path in ("/ru/", "/ru/tools/", "/ru/"):
                    page.goto(base + path, wait_until="commit")
                    page.wait_for_load_state("domcontentloaded")
                    collect_flicker(f"{viewport[0]} nav {i} {path} first paint")
                    page.wait_for_load_state("networkidle")
                    collect_flicker(f"{viewport[0]} nav {i} {path} after init")
            page.go_back(wait_until="networkidle")
            collect_flicker(f"{viewport[0]} back")
            page.go_forward(wait_until="networkidle")
            collect_flicker(f"{viewport[0]} forward")
            page.goto(base + "/ru/?q=Kev", wait_until="networkidle")
            collect_flicker(f"{viewport[0]} Kev search")
            page.goto(base + "/ru/?sort=number_desc", wait_until="networkidle")
            page.mouse.wheel(0, 30000)
            page.wait_for_timeout(1500)
            page.wait_for_load_state("networkidle")
            collect_flicker(f"{viewport[0]} infinite load")
            badges = page.evaluate("""() => [...document.querySelectorAll('.catalog-update-badge')]
                .map(b => b.closest('a.model-name').dataset.slug)""")
            assert set(badges) == {"clef-bdc7df20", "clef-flash-4eaa2224", "strands-decider-2b-81831af4"}, badges

        # --- direct URLs: new / changed cards, RU + EN, marks, no Max Output, 3 stat cards
        for slug, (name, number, extra, logo) in MODELS.items():
            visit(f"/ru/models/{slug}", [name, number, "США", "Открытые веса", *extra], None, absent=NO_MAX_OUTPUT)
            panel = page.locator(".model-panel.is-open")
            assert panel.locator(".stat-grid .stat-card").count() == 3, slug
            assert page.evaluate("() => getComputedStyle(document.querySelector('.model-panel.is-open .stat-grid')).gridTemplateColumns.split(' ').length") == 3
            assert (panel.locator(".panel-mark.has-logo").count() == 1) == logo, slug
            text = panel_text()
            assert "Публикуемых независимых результатов для точной версии нет" in text, slug
            if slug in PRICES:
                assert PRICES[slug] in text, slug
            visit(f"/models/{slug}", [name, number, "Context window"], None, theme="light", absent=NO_MAX_OUTPUT)
        for slug in ("gemini-38-live-a959d0c7", "gemini-4-argon-bcdaec0e"):
            for prefix in ("/ru", "", "/de", "/ar"):
                visit(f"{prefix}/models/{slug}", [], None, absent=NO_MAX_OUTPUT)
                assert page.locator(".model-panel.is-open .stat-grid .stat-card").count() == 3
        page.goto(base + "/ru/models/gemini-38-live-a959d0c7", wait_until="networkidle")
        page.screenshot(path=str(shots / "04-ru-gemini-38-live-no-max-output.png"), full_page=False)
        page.goto(base + "/ru/models/clef-bdc7df20", wait_until="networkidle")
        page.screenshot(path=str(shots / "05-ru-clef-card-mark.png"), full_page=False)
        page.goto(base + "/ru/models/kev-27b-v2-59a82a0e", wait_until="networkidle")
        page.screenshot(path=str(shots / "06-ru-kev-27b-fallback.png"), full_page=False)
        for slug, number in SHIFTED_MODELS.items():
            visit(f"/ru/models/{slug}", [number], None)
        for slug, (name, number, extra, logo) in TOOLS.items():
            visit(f"/ru/tools/{slug}", [name, *([number] if number else []), *extra], None)
            assert (page.locator(".model-panel.is-open .panel-mark.has-logo").count() == 1) == logo, slug
            visit(f"/tools/{slug}", [name], None, theme="light")
        page.goto(base + "/ru/tools/anythingllm-90d04ca3?tab=pricing", wait_until="networkidle")
        pricing = panel_text()
        for item in ("$0", "$50", "$99", "Docker", "Cloud", "не бесплатный inference"):
            assert item in pricing, item
        page.screenshot(path=str(shots / "07-ru-anythingllm-pricing.png"), full_page=False)
        page.goto(base + "/ru/tools/cloudflare-web-search-api-0bb0f08e?tab=pricing", wait_until="networkidle")
        pricing = panel_text()
        for item in ("$0.25", "$7", "$5", "1000 запросов"):
            assert item in pricing, item
        page.screenshot(path=str(shots / "08-ru-web-search-pricing.png"), full_page=False)
        page.goto(base + "/tools/github-copilot-179ab1d0", wait_until="networkidle")
        page.screenshot(path=str(shots / "09-en-copilot.png"), full_page=False)

        # --- search
        visit("/ru/?q=Clef", ["Clef", "Clef-flash"], "10-ru-search-clef.png")
        visit("/ru/?q=%40cf%2Fcloudflare%2Fclef", ["Clef"], None)
        visit("/ru/?q=jaredpalmer%2Fkev-9b", ["Kev-9B v2"], None)
        visit("/ru/tools/?q=Web+Search+API", ["Cloudflare Web Search API"], None)

        # --- layouts: tablet, ultrawide, EN desktop, RTL sample, RU mobile
        visit("/", ["343", "Models"], "11-en-models-desktop.png", theme="light")
        visit("/tools/", ["158", "Tools"], None)
        visit("/ru/models/clef-bdc7df20", ["Clef"], "12-tablet-768.png", viewport=(768, 1024), absent=NO_MAX_OUTPUT)
        visit("/ru/models/clef-bdc7df20", ["Clef"], "13-ultrawide-2560.png", viewport=(2560, 1300), theme="light", absent=NO_MAX_OUTPUT)
        visit("/ar/models/kev-4b-2ab542cc", ["Kev-4B"], "14-ar-rtl.png", absent=NO_MAX_OUTPUT)
        visit("/ru/", ["Модели"], "15-ru-mobile-models.png", viewport=(375, 812))
        visit("/ru/tools/", ["Инструменты"], None, viewport=(375, 812), theme="light")
        for slug in ("clef-bdc7df20", "strands-decider-2b-81831af4", "kev-27b-v2-59a82a0e"):
            visit(f"/ru/models/{slug}", [MODELS[slug][0]], None, viewport=(375, 812), absent=NO_MAX_OUTPUT)
        visit("/ru/tools/cloudflare-web-search-api-0bb0f08e", ["Cloudflare Web Search API"], "16-ru-mobile-web-search.png", viewport=(375, 812))

        # --- mobile freshness popover: 320-480 + desktop, RU/EN/AR
        popover_checks = []
        for path in ("/ru/", "/", "/ar/", "/ru/tools/"):
            for width in (320, 360, 375, 414, 480, 1440):
                page.set_viewport_size({"width": width, "height": 812})
                page.goto(base + path, wait_until="networkidle")
                page.locator(".catalog-freshness").click()
                page.locator(".catalog-freshness-popover").wait_for(state="visible")
                box = page.evaluate("""() => { const r = document.querySelector('.catalog-freshness-popover').getBoundingClientRect();
                    return [r.left, r.right, document.documentElement.scrollWidth, innerWidth]; }""")
                ok = box[0] >= 0 and box[1] <= box[3] and box[2] <= box[3]
                popover_checks.append({"path": path, "width": width, "box": box, "ok": ok})
                assert ok, (path, width, box)
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(base + "/ru/", wait_until="networkidle")
        page.locator(".catalog-freshness").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(shots / "17-ru-mobile-freshness.png"), full_page=False)

        context.close()
        browser.close()

    assert not errors, errors
    assert not failed, failed
    report = {
        "status": "PASS", "base": base, "checks": len(checks), "paths": checks,
        "freshness": {"ADD": sorted(ADD), "UPD": sorted(UPD), "recent_releases": sorted(RECENT)},
        "flicker_steps": len(flicker), "flicker": flicker, "popover": popover_checks,
        "counts": {"models": 343, "tools": 158},
        "javascript_errors": errors, "failed_responses": failed,
    }
    path = out / "browser-qa.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("paths", "flicker", "popover")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
