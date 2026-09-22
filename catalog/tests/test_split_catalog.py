from datetime import date
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from catalog.chronology import renumber_chronologically, renumber_tools_chronologically
from catalog.models import (
    Country, ModelFamily, ModelOriginCountry, ModelVersion, Organization, Platform,
    Source, Tool, ToolPlatform,
)


class SplitCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(
            title="Fixture source", publisher="Fixture", url="https://example.com/fixture"
        )
        cls.model_org = Organization.objects.create(
            name="Model Lab", source=cls.source, checked=date(2026, 9, 21)
        )
        cls.tool_org = Organization.objects.create(
            name="Tool Company", country="USA/UK", source=cls.source, checked=date(2026, 9, 21)
        )
        family = ModelFamily.objects.create(name="Model family", developer=cls.model_org)
        tool_family = ModelFamily.objects.create(name="Legacy tool", developer=cls.tool_org)
        cls.older_model = ModelVersion.objects.create(
            family=family, name="Older Model", slug="older-model", version="1",
            category="text", tasks=["coding"], released=date(2020, 1, 1),
            source=cls.source, checked=date(2026, 9, 21), entry_type="model",
            catalog_status="retired",
        )
        cls.newer_model = ModelVersion.objects.create(
            family=family, name="Newer Model", slug="newer-model", version="2",
            category="text", tasks=["reasoning"], released=date(2021, 1, 1),
            source=cls.source, checked=date(2026, 9, 21), entry_type="model",
        )
        cls.legacy_tool = ModelVersion.objects.create(
            family=tool_family, name="Fixture Tool", slug="fixture-tool-legacy", version="Tool",
            category="text", tasks=["coding"], released=date(2019, 1, 1),
            source=cls.source, checked=date(2026, 9, 21), entry_type="product",
        )
        cls.tool = Tool.objects.create(
            legacy_version=cls.legacy_tool, name="Fixture Tool", slug="fixture-tool",
            version="Tool", developer=cls.tool_org, category="coding_agent",
            purposes=["coding"], ecosystem={"ru": "Тестовые модели", "en": "Test models"},
            local_execution="hybrid", official_url="https://example.com/tool",
            released=date(2022, 1, 1), source=cls.source, checked=date(2026, 9, 21),
        )
        platform, _ = Platform.objects.update_or_create(
            code="cli", defaults={"labels": {"ru": "CLI", "en": "CLI"}, "position": 1}
        )
        ToolPlatform.objects.create(
            tool=cls.tool, platform=platform, source=cls.source, checked=date(2026, 9, 21)
        )
        country, _ = Country.objects.update_or_create(
            code="US", defaults={"name_ru": "США", "name_en": "United States"}
        )
        ModelOriginCountry.objects.create(
            model=cls.older_model, country=country, source=cls.source,
            checked=date(2026, 9, 21),
        )
        renumber_chronologically()
        renumber_tools_chronologically()

    def test_tabs_are_two_independent_catalogs_with_data_counts(self):
        response = self.client.get("/")
        self.assertEqual(response.context["entity_kind"], "model")
        self.assertContains(response, "Модели <span>2</span>", html=True)
        self.assertContains(response, "Инструменты <span>1</span>", html=True)
        self.assertNotContains(response, ">Все</a>")
        self.assertContains(response, "Независимые проверки")
        self.assertContains(response, "Рейтинг AIpediya")
        self.assertContains(response, "Контекст")
        tools = self.client.get("/", {"kind": "tool"})
        self.assertEqual(tools.context["entity_kind"], "tool")
        self.assertContains(tools, "Модели / экосистема")
        self.assertContains(tools, "Платформы / доступ")
        self.assertNotContains(tools, "Независимые проверки")
        self.assertNotContains(tools, "Рейтинг AIpediya")

    def test_default_chronology_includes_historical_records(self):
        response = self.client.get("/")
        self.assertEqual(response.context["status"], "all")
        self.assertEqual(
            [(item.name, item.public_number) for item in response.context["page"]],
            [("Older Model", 1), ("Newer Model", 2)],
        )
        active = self.client.get("/", {"status": "active"})
        self.assertEqual([item.name for item in active.context["page"]], ["Newer Model"])

    def test_catalog_tabs_clear_foreign_filters_and_card_routes(self):
        model = self.client.get(
            "/models/older-model",
            {"status": "retired", "access": "api", "benchmark": "99"},
        )
        self.assertContains(model, 'href="/?lang=ru&amp;kind=tool"')
        self.assertNotContains(model, 'kind=tool&amp;status=retired')
        tool = self.client.get(
            "/tools/fixture-tool",
            {"platform": "cli", "local": "hybrid", "ecosystem": "Test"},
        )
        self.assertContains(tool, 'href="/?lang=ru&amp;kind=model"')
        self.assertNotContains(tool, 'kind=model&amp;platform=cli')

    def test_chronology_is_independent_and_filter_does_not_renumber(self):
        self.older_model.refresh_from_db()
        self.newer_model.refresh_from_db()
        self.legacy_tool.refresh_from_db()
        self.tool.refresh_from_db()
        self.assertEqual((self.older_model.public_number, self.newer_model.public_number), (1, 2))
        self.assertIsNone(self.legacy_tool.public_number)
        self.assertEqual(self.tool.public_number, 1)
        response = self.client.get("/", {"kind": "tool", "developer": self.tool_org.pk})
        listed = list(response.context["page"])
        self.assertEqual([(item.name, item.public_number) for item in listed], [("Fixture Tool", 1)])

    def test_country_flag_is_local_accessible_and_unknown_is_blank(self):
        response = self.client.get("/", {"kind": "model", "status": "all"})
        html = response.content.decode()
        self.assertIn("flags.svg", html)
        self.assertIn("flag-US", html)
        self.assertIn('aria-label="США"', html)
        newer_row = html.split('data-slug="newer-model"', 1)[1].split("</tr>", 1)[0]
        self.assertNotIn("country-flag", newer_row)
        panel = self.client.get("/models/older-model")
        self.assertContains(panel, "Страна происхождения")
        self.assertContains(panel, "США")
        tools = self.client.get("/", {"kind": "tool"})
        self.assertContains(tools, "flag-US")
        self.assertContains(tools, "flag-GB")

    def test_local_sprite_covers_catalog_country_codes(self):
        sprite = (Path(settings.BASE_DIR) / "static" / "flags.svg").read_text(encoding="utf-8")
        expected = {
            "AE", "AU", "CA", "CH", "CN", "CZ", "DE", "FR", "GB", "IL",
            "IN", "JP", "KR", "NL", "RU", "SA", "SE", "SG", "US",
        }
        self.assertEqual([], sorted(code for code in expected if f'id="flag-{code}"' not in sprite))

    def test_tool_panel_has_only_tool_specific_content_and_closes_by_contract(self):
        response = self.client.get("/tools/fixture-tool", {"lang": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-kind="tool"')
        self.assertContains(response, "Supported models / ecosystem")
        self.assertContains(response, "Platforms / access")
        self.assertContains(response, "Local execution")
        self.assertNotContains(response, "Context window")
        self.assertNotContains(response, "AIpediya rating")
        self.assertNotContains(response, 'data-tab="checks"')
        partial = self.client.get(
            "/tools/fixture-tool", {"lang": "en", "partial": "panel"}
        )
        self.assertEqual(partial["X-Aipedia-Kind"], "tool")
        self.assertEqual(partial["X-Aipedia-Slug"], "fixture-tool")

    def test_search_and_tool_filters_are_type_specific(self):
        model_search = self.client.get("/", {"kind": "model", "q": "Fixture Tool"})
        self.assertEqual(list(model_search.context["page"]), [])
        tool_search = self.client.get("/", {"kind": "tool", "q": "Fixture Tool"})
        self.assertEqual([item.slug for item in tool_search.context["page"]], ["fixture-tool"])
        filtered = self.client.get(
            "/", {"kind": "tool", "category": "coding_agent", "platform": "cli", "local": "hybrid"}
        )
        self.assertEqual([item.slug for item in filtered.context["page"]], ["fixture-tool"])
