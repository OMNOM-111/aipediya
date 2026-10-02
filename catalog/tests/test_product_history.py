from django.test import SimpleTestCase, override_settings
from pathlib import Path
import json
import re

from tools.build_product_history import build


class ProductHistoryTests(SimpleTestCase):
    def test_audited_card_states_are_unique_and_baseline_is_stable(self):
        registry = json.loads((Path(__file__).resolve().parents[2] / "docs/timeline.json").read_text(encoding="utf-8"))
        product = registry["product_history"]
        cards = product["milestones"]
        by_id = {row["release_id"]: row for row in cards}
        self.assertEqual(len(by_id), len(cards))
        self.assertEqual(len(cards), 31)
        self.assertEqual(product["current_production"]["release_sequence"], 22)
        self.assertEqual(product["current_production"]["app_version"], "v0.19.0")
        self.assertEqual(by_id["release-2026-09-28-reconciliation-cleanup"]["revision"],
                         "5ba1e566338fc17d9b8965d3be180bc1df268e2e")
        self.assertEqual(product["current_local"]["release_sequence"], 22)
        self.assertEqual(product["current_local"]["app_version"], "v0.19.0")
        locale_switch = by_id["LANGUAGE-SWITCH-2026-09-28"]
        self.assertEqual((locale_switch["app_version"], locale_switch["local_verified"],
                          locale_switch["owner_approved"]), ("v0.13.1", True, True))
        self.assertEqual((locale_switch["progress"], locale_switch["production_released"],
                          locale_switch["production_verified"]), ("done", True, True))
        performance = by_id["PERFORMANCE-AUDIT-2026-09-28"]
        self.assertEqual((performance["release_sequence"], performance["app_version"],
                          performance["progress"], performance["local_verified"],
                          performance["production_released"]),
                         (15, "v0.13.2", "done", True, True))
        self.assertTrue(performance["owner_approved"])
        versions = by_id["VERSION-HISTORY-2026-09-27"]
        self.assertEqual((versions["progress"], versions["local_verified"],
                          versions["owner_approved"], versions["production_verified"]),
                         ("done", True, True, False))
        analytics = by_id["TRAFFIC-ANALYTICS-AUDIT-2026-09-27"]
        self.assertEqual((analytics["progress"], analytics["production_verified"],
                          analytics["revision"]),
                         ("done", True, "cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3"))
        self.assertEqual(analytics["source"], "2026-09-27-tools-chronology-csp-release")
        self.assertEqual((by_id["release-2026-09-28-reconciliation-cleanup"]["progress"],
                          by_id["UNSUPPORTED-MASTER-PROD-AUDIT-2026-09-28"]["progress"]),
                         ("done", "done"))
        audit = by_id["EVAL-EVIDENCE-AUDIT-2026-09-27"]
        self.assertEqual((audit["progress"], audit["owner_approved"], audit["production_released"], audit["release_sequence"]),
                         ("done", True, True, 12))
        daily = by_id["DAILY-CATALOG-UPDATE-2026-09-29"]
        self.assertEqual((daily["release_sequence"], daily["app_version"], daily["progress"], daily["executor"],
                  daily["production_verified"]),
                 (16, "v0.14.0", "done", "GitHub Copilot", True))
        universal = by_id["UNIVERSAL-CATALOG-RELEASE-2026-09-29"]
        self.assertEqual((universal["release_sequence"], universal["app_version"], universal["progress"],
                          universal["local_verified"], universal["owner_approved"], universal["production_released"]),
                         (17, "v0.15.0", "done", True, True, False))
        freshness = by_id["CATALOG-FRESHNESS-INDICATOR-2026-09-29"]
        self.assertEqual((freshness["release_sequence"], freshness["app_version"], freshness["progress"],
                  freshness["local_verified"], freshness["owner_approved"], freshness["production_released"]),
                 (18, "v0.16.0", "done", True, True, True))
        polish = by_id["CATALOG-FRESHNESS-UI-POLISH-2026-09-30"]
        self.assertEqual((polish["release_sequence"], polish["app_version"], polish["progress"],
                          polish["local_verified"], polish["owner_approved"], polish["production_released"]),
                         (19, "v0.16.1", "done", True, True, True))
        daily_twenty = by_id["DAILY-CATALOG-UPDATE-2026-09-30"]
        self.assertEqual((daily_twenty["release_sequence"], daily_twenty["app_version"], daily_twenty["progress"],
                          daily_twenty["local_verified"], daily_twenty["production_released"]),
                         (20, "v0.17.0", "done", True, True))
        self.assertTrue(daily_twenty["owner_approved"])
        self.assertTrue(daily_twenty["production_verified"])
        daily_twenty_one = by_id["DAILY-CATALOG-UPDATE-2026-10-01"]
        self.assertEqual((daily_twenty_one["release_sequence"], daily_twenty_one["app_version"],
                          daily_twenty_one["progress"], daily_twenty_one["local_verified"],
                          daily_twenty_one["owner_approved"], daily_twenty_one["production_released"]),
                         (21, "v0.18.0", "done", True, True, True))
        self.assertTrue(daily_twenty_one["production_verified"])
        daily_twenty_two = by_id["DAILY-CATALOG-UPDATE-2026-10-02"]
        self.assertEqual((daily_twenty_two["release_sequence"], daily_twenty_two["app_version"],
                          daily_twenty_two["progress"], daily_twenty_two["local_verified"],
                          daily_twenty_two["owner_approved"], daily_twenty_two["production_released"]),
                         (22, "v0.19.0", "done", True, True, True))
        self.assertEqual([row["release_id"] for row in cards if row["progress"] == "planned"],
                         ["PAID-SEARCH-EXPERIMENT-GOOGLE-ADS-2026-09-26",
                          "ORGANIC-SEARCH-GROWTH-CHECK-2026-10-07"])

    def test_local_history_and_sources(self):
        page = self.client.get("/ru/history/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "История AIpediya")
        self.assertEqual(page.content, (Path(__file__).resolve().parents[2] / "timeline.html").read_bytes())
        self.assertEqual(page.content.count(b'data-history-open='), 46)  # 22 numbered releases + one open planned card in two editions
        self.assertIn(b'Release #001', page.content)
        self.assertIn(b'Release #015', page.content)
        self.assertIn(b'Release #016', page.content)
        self.assertIn(b'Release #017', page.content)
        self.assertIn(b'Release #018', page.content)
        self.assertIn(b'Release #019', page.content)
        self.assertIn(b'Release #020', page.content)
        self.assertIn(b'Release #021', page.content)
        self.assertIn(b'Release #022', page.content)
        self.assertNotIn("Контрольный замер органического поиска".encode("utf-8"), page.content)
        self.assertIn("Повторный контроль органического роста".encode("utf-8"), page.content)
        self.assertIn(b"Organic search follow-up /", page.content)
        self.assertIn(b'PLANNED', page.content)
        self.assertNotIn(b'class="site-header"', page.content)
        self.assertNotIn(b'class="site-footer"', page.content)
        self.assertNotIn(b'role="search"', page.content)
        self.assertEqual(page.content.count(b'class="ph-environment ph-local"'), 2)
        self.assertEqual(page.content.count(b'class="ph-environment ph-production"'), 2)
        self.assertEqual(page["Cache-Control"], "private, no-store")
        self.assertEqual(self.client.get("/ru/history/source/release").status_code, 200)
        self.assertEqual(self.client.get("/history/source/GSD-1.0-release-scope").status_code, 200)
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-27-tools-count-cloudflare-csp-local"),
            "143",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-27-tools-chronology-csp-release"),
            "cf4ac9a33f8d",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-28-unsupported-master-production-audit"),
            "954",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-28-language-switch"),
            "22 locales",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-28-performance-audit"),
            "Release #015",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-29-internal-history-local"),
            "Local-only",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-29-universal-catalog-release"),
            "universal",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-29-catalog-freshness-indicator"),
            "freshness",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-30-catalog-freshness-ui-polish"),
            "Local review",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-10-01-daily-catalog-update-021"),
            "Release #021",
        )
        self.assertContains(
            self.client.get("/ru/history/source/2026-10-07-organic-search-growth-check"),
            "775 impressions",
        )
        self.assertEqual(self.client.get("/ru/history/source/secret").status_code, 404)

    def test_local_only_release_done_does_not_claim_production_publication(self):
        page = build().read_text(encoding="utf-8")
        details = re.findall(r'<template id="ph-detail-UNIVERSAL-CATALOG-RELEASE-2026-09-29">(.*?)</template>', page, re.S)
        self.assertEqual(len(details), 2)
        self.assertTrue(any("Завершено и принято владельцем" in detail for detail in details))
        self.assertTrue(any("No separate Production deploy was required" in detail for detail in details))
        for detail in details:
            self.assertNotIn("Опубликовано и проверено", detail)
            self.assertNotIn("Published and checked", detail)
            self.assertNotIn("Tag:", detail)

    def test_english_and_rtl_routes(self):
        self.assertContains(self.client.get("/history/"), "AIpediya history")
        arabic = self.client.get("/ar/history/")
        self.assertEqual(arabic.status_code, 200)
        self.assertContains(arabic, '<html lang="en" dir="ltr"')

    def test_paid_search_stays_planned_and_separate_from_organic_releases(self):
        registry = json.loads((Path(__file__).resolve().parents[2] / "docs/timeline.json").read_text(encoding="utf-8"))
        entries = {row["release_id"]: row for row in registry["entries"]}
        paid_id = "PAID-SEARCH-EXPERIMENT-GOOGLE-ADS-2026-09-26"
        followup_id = "ORGANIC-SEARCH-FOLLOWUP-2026-09-30"
        growth_id = "ORGANIC-SEARCH-GROWTH-CHECK-2026-10-07"
        self.assertEqual(entries[paid_id]["stage"], "planned")
        self.assertEqual(entries[paid_id]["status"], "PLANNED")
        self.assertEqual(entries[paid_id]["planned_after"], "separate-future-owner-decision")
        self.assertNotIn("blocked_by", entries[paid_id])
        self.assertEqual(entries[followup_id]["stage"], "done")
        self.assertEqual(entries[followup_id]["status"], "COMPLETED_LOCAL")
        self.assertEqual(entries[followup_id]["planned_after"], "2026-09-30")
        self.assertEqual(entries[growth_id]["stage"], "planned")
        self.assertEqual(entries[growth_id]["status"], "PLANNED")
        self.assertEqual(entries[growth_id]["planned_after"], "2026-10-07")
        self.assertEqual(entries[growth_id]["continues"], followup_id)
        self.assertNotIn("release_sequence", entries[growth_id])
        self.assertNotIn("app_version", entries[growth_id])
        self.assertEqual(entries[paid_id]["monthly_budget_usd_max"], 15)
        self.assertEqual(entries["GSD-1.0"]["stage"], "released")
        organic_id = "release-2026-09-26-search-visibility-optimization-v2"
        self.assertEqual(entries[organic_id]["stage"], "released")
        self.assertEqual(registry["product_history"]["current_production"]["release_tag"],
                 "release-2026-10-02-daily-catalog-update")
        paid_card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == paid_id)
        self.assertFalse(paid_card["open"])
        self.assertEqual(paid_card["progress"], "planned")
        self.assertIsNone(paid_card["revision"])
        self.assertIn("Google Ads was not launched", " ".join(paid_card["capabilities_en"]))
        self.assertIn("paid clicks", " ".join(paid_card["capabilities_en"]))
        followup_card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == followup_id)
        self.assertFalse(followup_card["open"])
        self.assertEqual(followup_card["progress"], "done")
        self.assertTrue(followup_card["local_verified"])
        self.assertIn("34/34 passes", " ".join(followup_card["capabilities_en"]))
        growth_card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == growth_id)
        self.assertTrue(growth_card["open"])
        self.assertEqual(growth_card["progress"], "planned")
        self.assertFalse(growth_card["production_released"])
        self.assertIn("10,720 accepted URLs", " ".join(growth_card["capabilities_en"]))
        self.assertIn("Never launch ads automatically", " ".join(growth_card["capabilities_en"]))

    def test_offline_history_records_owner_visual_check_without_publication(self):
        registry = json.loads((Path(__file__).resolve().parents[2] / "docs/timeline.json").read_text(encoding="utf-8"))
        entry = next(row for row in registry["entries"] if row["release_id"] == "HISTORY-OFFLINE-2026-09-26")
        card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == entry["release_id"])
        task = next(row for row in registry["product_history"]["additional_tasks"] if row["id"] == entry["release_id"])
        self.assertEqual(entry["stage"], "local")
        self.assertIn("completed", entry["owner_visual_review"])
        self.assertTrue(card["open"])
        self.assertEqual(card["progress"], "done")
        self.assertIn("Проверено владельцем", card["tags_ru"])
        self.assertNotIn("Визуальная проверка ожидается", card["tags_ru"])
        self.assertIn("Визуальная проверка", task["owner_ru"])
        self.assertEqual(registry["product_history"]["current_production"]["release_tag"], "release-2026-10-02-daily-catalog-update")

    @override_settings(AIPEDIA_ENV="production", SECURE_SSL_REDIRECT=False)
    def test_history_is_private_in_production(self):
        for url in ("/history/", "/ru/history/", "/history/source/release"):
            self.assertEqual(self.client.get(url, secure=True).status_code, 404)

    def test_standalone_history_contains_both_locales_sources_and_no_network_assets(self):
        output = build()
        page = output.read_text(encoding="utf-8")
        self.assertEqual(output, Path(__file__).resolve().parents[2] / "timeline.html")
        self.assertIn("connect-src 'none'", page)
        self.assertIn('id="edition-ru"', page)
        self.assertIn('id="edition-en"', page)
        self.assertEqual(page.count('data-history-open='), 46)
        self.assertEqual(page.count('class="ph-release-card"'), 46)
        self.assertEqual(page.count('role="button" tabindex="0" aria-haspopup="dialog"'), 46)
        self.assertEqual(page.count('class="ph-status-legend"'), 2)
        self.assertIn('release-2026-09-28-reconciliation-cleanup', page)
        self.assertNotIn('data-history-open="PAID-SEARCH-EXPERIMENT-GOOGLE-ADS-2026-09-26"', page)
        self.assertNotIn('data-history-open="ORGANIC-SEARCH-FOLLOWUP-2026-09-30"', page)
        self.assertIn('data-history-open="ORGANIC-SEARCH-GROWTH-CHECK-2026-10-07"', page)
        self.assertNotIn('data-history-open="HISTORY-LOCAL-SHELL-2026-09-29"', page)
        self.assertNotIn('data-history-open="LOCAL-CANONICAL-2026-10-02"', page)
        self.assertEqual(page.count('data-history-source-template='), 32)
        self.assertEqual(page.count('class="ph-environment ph-local"'), 2)
        self.assertEqual(page.count('class="ph-environment ph-production"'), 2)
        self.assertIn("Номер обращения на экране не показан", page)
        self.assertNotIn("1916383264", page)
        self.assertNotRegex(page, r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
        self.assertNotRegex(page, r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b")
        self.assertNotRegex(page, r"<(?:script|link)[^>]+(?:src|href)=['\"]https?://")
        self.assertNotIn('src="/static/', page)
        self.assertIn("docs/timeline.json", page)
        self.assertIn("GSD-01", page)
        self.assertIn('id="theme"', page)
        self.assertIn('data-theme="dark"', page)
        self.assertIn('id="edition-toggle"', page)
        self.assertIn('class="ph-theme-icon"', page)
        self.assertIn('class="ph-theme-label"', page)
        self.assertIn("20 сентября 2026", page)
        self.assertIn("25 сентября 2026", page)
        feature_lists = re.findall(r'<ol class="ph-feature-list">(.*?)</ol>', page, re.S)
        self.assertEqual(len(feature_lists), 4)
        for feature_list in feature_lists:
            self.assertRegex(feature_list, r'<code>01</code>')
            self.assertRegex(feature_list, r'<code>10</code>')
            self.assertNotRegex(feature_list, r'<code>GSD-\d+</code>')
        self.assertIn('class="ph-title-row"', page)
        self.assertIn('class="ph-change-chips"', page)
        self.assertIn('id="ph-dialog-body"', page)
        self.assertIn('id="ph-close"', page)
        self.assertGreater(page.count("data-change-card"), 100)
        gsd_details = re.findall(r'<template id="ph-detail-GSD-1\.0">(.*?)</template>', page, re.S)
        self.assertEqual(len(gsd_details), 2)
        for details in gsd_details:
            self.assertEqual(details.count("data-change-card"), 10)
            self.assertIn('class="ph-change-number">01</span>', details)
            self.assertIn('class="ph-change-number">02</span>', details)
        self.assertTrue(any("Фактический baseline и паспорт версии" in detail for detail in gsd_details))
        self.assertTrue(any("Baseline and release record" in detail for detail in gsd_details))
        self.assertNotIn("catalog-search", page)
        self.assertNotIn("site-footer", page)
        self.assertNotRegex(page, r"<(?:script|link)[^>]+(?:src|href)=['\"](?:/|https?://)")

    def test_visible_timeline_is_chronological_in_both_editions(self):
        page = build().read_text(encoding="utf-8")
        registry = json.loads((Path(__file__).resolve().parents[2] / "docs/timeline.json").read_text(encoding="utf-8"))
        cards = {row["release_id"]: row for row in registry["product_history"]["milestones"]}
        expected_tail = [
            "CATALOG-FRESHNESS-UI-POLISH-2026-09-30",
            "DAILY-CATALOG-UPDATE-2026-09-30",
            "DAILY-CATALOG-UPDATE-2026-10-01",
            "DAILY-CATALOG-UPDATE-2026-10-02",
            "ORGANIC-SEARCH-GROWTH-CHECK-2026-10-07",
        ]
        ru = re.search(r'<template id="edition-ru">(.*?)</template><template id="edition-en">', page, re.S).group(1)
        en = re.search(r'<template id="edition-en">(.*?)</template>', page, re.S).group(1)
        for edition in (ru, en):
            visible = re.findall(r'data-history-open="([^"]+)"', edition)
            dates = [cards[release_id]["date"] for release_id in visible]
            self.assertEqual(dates, sorted(dates))
            self.assertEqual(visible[-5:], expected_tail)
            for event_date in sorted(set(dates)):
                sequences = [cards[release_id]["release_sequence"] for release_id in visible
                             if cards[release_id]["date"] == event_date and cards[release_id].get("release_sequence") is not None]
                self.assertEqual(sequences, sorted(sequences))

    def test_standalone_history_interaction_hooks_and_reference_layout(self):
        from tools.build_product_history import ROOT

        page = (ROOT / "timeline.html").read_text(encoding="utf-8")
        behavior = (ROOT / "static/product-history.js").read_text(encoding="utf-8")
        style = (ROOT / "static/product-history-offline.css").read_text(encoding="utf-8")
        self.assertIn('data-history-open="{{ milestone.id }}"', (ROOT / "templates/product_history_standalone.html").read_text(encoding="utf-8"))
        self.assertIn('event.key !== "Enter"', behavior)
        self.assertIn('event.key === "Escape"', behavior)
        self.assertIn('close.addEventListener("click", hide)', behavior)
        self.assertIn('scrim.addEventListener("click", hide)', behavior)
        self.assertIn("body.replaceChildren(template.content.cloneNode(true))", behavior)
        self.assertIn("overflow:auto", style)
        self.assertIn("width:min(510px,100vw)", style)
        self.assertIn("grid-auto-flow:column", style)
        self.assertIn('data-theme="dark"', page)
