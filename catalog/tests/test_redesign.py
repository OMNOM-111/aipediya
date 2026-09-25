from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from catalog.chronology import renumber_chronologically
from catalog.models import Evaluation, ModelVersion


class RedesignCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        ModelVersion.objects.update(released=date(2020, 1, 1))
        renumber_chronologically()

    def test_catalog_has_new_columns_and_empty_aipedia_rating(self):
        response = self.client.get("/", {"lang": "ru"}, follow=True)
        self.assertContains(response, "Модель")
        self.assertContains(response, "Тип")
        self.assertContains(response, "Разработчик")
        self.assertContains(response, "Независимые проверки")
        self.assertContains(response, "Рейтинг AIpediya")
        self.assertContains(response, "Контекст")
        self.assertContains(response, 'class="rating-col"')
        self.assertNotContains(response, "75%")
        self.assertContains(response, 'id="model-panel"')
        self.assertContains(response, "Все")
        self.assertContains(response, "Инструменты")

    def test_visible_brand_matches_public_domain_spelling(self):
        response = self.client.get("/", {"lang": "en"}, follow=True)
        self.assertContains(response, 'aria-label="AIpediya"')
        self.assertContains(response, '<span class="brand-ai">AI</span><span>pediya</span>', html=True)
        self.assertContains(response, "AIpediya</span><span class=\"footer-end\"")
        self.assertContains(response, "AIpediya rating")
        self.assertContains(response, "AI model catalog: prices, access and independent evaluations | AIpediya")

    def test_kind_tabs_use_existing_entry_types(self):
        all_slugs = [model.slug for model in self.client.get("/").context["page"]]
        models = [model.slug for model in self.client.get("/", {"kind": "model"}, follow=True).context["page"]]
        tools = [model.slug for model in self.client.get("/", {"kind": "tool"}, follow=True).context["page"]]
        self.assertTrue(all_slugs)
        self.assertTrue(set(models).issubset(set(all_slugs)))
        self.assertTrue(set(tools).issubset(set(all_slugs)))
        self.assertFalse(set(models) & set(tools))
        for model in self.client.get("/", {"kind": "model"}, follow=True).context["page"]:
            self.assertEqual(model.entry_type, "model")
        for model in self.client.get("/", {"kind": "tool"}, follow=True).context["page"]:
            self.assertNotEqual(model.entry_type, "model")

    def test_release_date_uses_localized_day_month_year(self):
        from catalog.templatetags.catalog_tags import month_year

        released = date(2021, 6, 29)
        self.assertEqual(month_year(released, "ru"), "29 Июн 2021")
        self.assertEqual(month_year(released, "en"), "Jun 29, 2021")
        ModelVersion.objects.filter(slug="qwen3-8b").update(released=released)
        self.assertContains(self.client.get("/?lang=ru", follow=True), "29 Июн 2021")
        self.assertContains(self.client.get("/?lang=en", follow=True), "Jun 29, 2021")

    def test_old_card_url_opens_panel_and_keeps_catalog(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        response = self.client.get("/models/" + model.slug, {"lang": "ru"}, follow=True)
        self.assertContains(response, model.version)
        self.assertContains(response, "Платформа и оценка")
        self.assertContains(response, f"#{model.public_number}")
        self.assertContains(response, 'class="model-table"')
        self.assertContains(response, 'id="model-panel"')
        self.assertContains(response, "is-panel-open")
        self.assertContains(response, "Поделиться")
        self.assertContains(response, "Сохранение станет доступно после запуска личного кабинета.")
        self.assertContains(response, 'aria-disabled="true"')
        self.assertNotContains(response, "Сохранено")
        panel = self.client.get("/models/" + model.slug, {"partial": "panel"})
        self.assertEqual(panel.status_code, 200)
        self.assertEqual(panel["X-Aipedia-Slug"], model.slug)

    def test_unpublished_and_unknown_panel_stay_closed(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        model.published = False
        model.save()
        self.assertEqual(self.client.get("/models/" + model.slug).status_code, 404)
        self.assertEqual(self.client.get("/", {"partial": "panel", "model": model.slug}).status_code, 404)
        catalog = self.client.get("/", {"model": "not-real"})
        self.assertEqual(catalog.status_code, 200)
        self.assertIsNone(catalog.context["selected_model"])

    def test_missing_number_and_context_are_blank_not_zero(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        number_before = model.public_number
        model.released = None
        model.context = None
        model.save()
        model.refresh_from_db()
        # Clearing the date never removes the permanent number.
        self.assertEqual(model.public_number, number_before)
        self.assertIsNotNone(model.public_number)
        response = self.client.get("/")
        html = response.content.decode()
        self.assertNotIn("75%", html)
        row = next(item for item in response.context["page"] if item.slug == model.slug)
        self.assertEqual(row.public_number, number_before)
        self.assertIsNone(row.context)
        self.assertContains(response, 'class="rating-col"')

    def test_input_and_output_prices_can_appear_together(self):
        model = ModelVersion.objects.get(slug="gemini-2-5-flash")
        response = self.client.get("/")
        listed = next(item for item in response.context["page"] if item.slug == model.slug)
        units = {offer.unit for offer in listed.table_offers}
        self.assertTrue("input" in units or listed.table_offers)
        if any(offer.unit == "input" for offer in listed.current_offers) and any(
            offer.unit == "output" for offer in listed.current_offers
        ):
            self.assertIn("input", units)
            self.assertIn("output", units)

    def test_independent_column_does_not_relabel_developer_reports(self):
        evaluation = Evaluation.objects.filter(public=True).first()
        evaluation.result_kind = "developer"
        evaluation.independent = False
        evaluation.save(update_fields=["result_kind", "independent"])
        response = self.client.get("/models/" + evaluation.model.slug, {"lang": "ru"}, follow=True)
        self.assertContains(response, "Данные разработчика")
        table = self.client.get("/")
        listed = next(item for item in table.context["page"] if item.slug == evaluation.model.slug)
        self.assertFalse(any(item.pk == evaluation.pk for item in listed.table_evaluations))

    def test_panel_partial_keeps_close_control(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        panel = self.client.get("/models/" + model.slug, {"partial": "panel"})
        self.assertEqual(panel.status_code, 200)
        # The X control is what the outside-click and Escape handlers reuse to
        # dismiss the panel; without it the panel could only be left by
        # navigating away.
        self.assertContains(panel, 'data-close-panel="true"')

    def test_language_links_on_detail_keep_the_open_entity(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        response = self.client.get("/models/" + model.slug, {"lang": "en"}, follow=True)
        # Switcher links point at the same card in the other locale so changing
        # the language keeps the same model open instead of returning to the list.
        self.assertContains(response, f'href="/ar/models/{model.slug}"')
        self.assertNotContains(response, 'href="/ar/" hreflang="ar"')


class PanelInteractionAssetTests(SimpleTestCase):
    """Guards the shipped panel/dropdown fixes in the static assets so a future
    edit cannot silently drop the outside-click close or the dropdown layering."""

    def _asset(self, name):
        return (Path(settings.BASE_DIR) / "static" / name).read_text(encoding="utf-8")

    def test_site_js_closes_panel_on_outside_click_and_syncs_header(self):
        source = self._asset("site.js")
        self.assertIn("syncHeaderHeight", source)
        self.assertIn("--aip-header-h", source)
        # The outside-click handler must skip the header, row links and column
        # filters, then close the open panel.
        self.assertIn('details.col-filter', source)
        self.assertIn('.site-header', source)
        self.assertIn("closePanel(true)", source)

    def test_site_css_layers_dropdown_above_panel(self):
        source = self._asset("site.css")
        self.assertIn("--z-popover", source)
        self.assertIn("--aip-header-h", source)
        # Header sits above the panel; the language popover sits above both.
        self.assertIn("z-index: var(--z-header)", source)
        self.assertIn("z-index: var(--z-popover)", source)
        # On narrow screens the panel starts below the header so the language
        # selector and its dropdown stay reachable.
        self.assertIn("inset: var(--aip-header-h, 0) 0 0 0", source)
