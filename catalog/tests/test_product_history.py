from django.test import SimpleTestCase, override_settings
from pathlib import Path
import json
import re

from tools.build_product_history import build


class ProductHistoryTests(SimpleTestCase):
    def test_local_history_and_sources(self):
        page = self.client.get("/ru/history/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "История AIpediya")
        self.assertContains(page, "GSD-1.0")
        self.assertContains(page, "Каноническая база каталога")
        self.assertContains(page, "ed103a3ff163")
        self.assertContains(page, 'aria-haspopup="dialog"', count=12)
        # The current Local catalog/CSP stage awaits owner review.
        self.assertContains(page, 'class="ph-legend-dot is-review"', count=1)
        self.assertContains(page, 'Ожидает подтверждения владельца')
        self.assertContains(page, 'class="ph-milestone ph-review ph-open"', count=1)
        self.assertContains(page, '61adedd6ea5e6a0955d51d87374fa2fa9bcc7799')
        self.assertContains(page, 'PLANNED')
        self.assertContains(page, 'кампания не создана и не запущена.')
        self.assertContains(page, 'class="ph-milestone ph-done ph-open"', count=1)
        self.assertContains(page, 'class="ph-milestone ph-planned ph-open"', count=1)
        self.assertContains(page, 'Согласованность Tools и CSP Cloudflare')
        self.assertContains(page, 'ГОТОВО В LOCAL')
        self.assertContains(page, 'class="ph-environment ph-local"', count=1)
        self.assertContains(page, 'class="ph-environment ph-production"', count=1)
        self.assertNotContains(page, 'class="ph-environment ph-git"')
        self.assertContains(page, 'class="ph-git-detail"', count=2)
        self.assertEqual(page["Cache-Control"], "private, no-store")
        self.assertEqual(self.client.get("/ru/history/source/release").status_code, 200)
        self.assertEqual(self.client.get("/history/source/GSD-1.0-release-scope").status_code, 200)
        self.assertContains(
            self.client.get("/ru/history/source/2026-09-27-tools-count-cloudflare-csp-local"),
            "143",
        )
        self.assertEqual(self.client.get("/ru/history/source/secret").status_code, 404)

    def test_english_and_rtl_routes(self):
        self.assertContains(self.client.get("/history/"), "AIpediya history")
        arabic = self.client.get("/ar/history/")
        self.assertEqual(arabic.status_code, 200)
        self.assertContains(arabic, 'dir="rtl"')
        self.assertContains(arabic, 'lang="en"')

    def test_paid_search_stays_planned_and_separate_from_organic_releases(self):
        registry = json.loads((Path(__file__).resolve().parents[2] / "docs/timeline.json").read_text(encoding="utf-8"))
        entries = {row["release_id"]: row for row in registry["entries"]}
        paid_id = "PAID-SEARCH-EXPERIMENT-GOOGLE-ADS-2026-09-26"
        self.assertEqual(entries[paid_id]["stage"], "planned")
        self.assertEqual(entries[paid_id]["status"], "PLANNED")
        self.assertEqual(entries[paid_id]["planned_after"], "2026-09-30")
        self.assertEqual(entries[paid_id]["monthly_budget_usd_max"], 15)
        self.assertEqual(entries["GSD-1.0"]["stage"], "released")
        organic_id = "release-2026-09-26-search-visibility-optimization-v2"
        self.assertEqual(entries[organic_id]["stage"], "released")
        self.assertEqual(registry["product_history"]["current_production"]["release_tag"],
                         "release-2026-09-27-adaptive-ui")
        paid_card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == paid_id)
        self.assertTrue(paid_card["open"])
        self.assertEqual(paid_card["progress"], "planned")
        self.assertIsNone(paid_card["revision"])
        self.assertIn("paid clicks", " ".join(paid_card["capabilities_en"]))

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
        self.assertEqual(registry["product_history"]["current_production"]["release_tag"], "release-2026-09-27-adaptive-ui")

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
        self.assertEqual(page.count('data-history-open='), 24)
        self.assertEqual(page.count('class="ph-milestone ph-review ph-open"'), 2)
        self.assertEqual(page.count('class="ph-legend-dot is-review"'), 2)
        self.assertIn('.ph-review .ph-dot', page)
        self.assertIn('Утверждено владельцем', page)
        self.assertEqual(page.count('class="ph-status-legend"'), 2)
        self.assertEqual(page.count('class="ph-milestone ph-done ph-open"'), 2)
        self.assertEqual(page.count('class="ph-milestone ph-planned ph-open"'), 2)
        self.assertEqual(page.count('class="ph-milestone ph-in_progress ph-open"'), 0)
        self.assertIn('ГОТОВО В LOCAL', page)
        self.assertIn('.ph-in_progress .ph-dot', page)
        self.assertEqual(page.count('data-history-source-template='), 18)
        self.assertEqual(page.count('class="ph-environment ph-local"'), 2)
        self.assertEqual(page.count('class="ph-environment ph-production"'), 2)
        self.assertIn("Номер обращения на экране не показан", page)
        self.assertNotIn("1916383264", page)
        self.assertNotRegex(page, r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
        self.assertNotRegex(page, r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b")
        self.assertNotRegex(page, r"<(?:script|link)[^>]+(?:src|href)=['\"]https?://")
        self.assertNotIn('src="/static/', page)
        self.assertIn("docs/timeline.json", page)
        self.assertIn("634778807b2e82ca52dea1de150ea0810950d644", page)
        self.assertIn("GSD-01", page)
        self.assertIn("Offline history viewer", page)
        self.assertIn('id="theme"', page)
        self.assertIn('data-theme="dark"', page)
        self.assertIn('id="edition-toggle"', page)
        self.assertIn('class="ph-theme-icon"', page)
        self.assertIn('class="ph-theme-label"', page)
        self.assertEqual(page.count('class="ph-release-card"'), 24)
        self.assertEqual(page.count('role="button" tabindex="0" aria-haspopup="dialog"'), 24)
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
        self.assertEqual(page.count("data-change-card"), 118)
        self.assertIn('data-history-open="PAID-SEARCH-EXPERIMENT-GOOGLE-ADS-2026-09-26"', page)
        self.assertIn('Кампания не создана и не запущена.', page)
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
