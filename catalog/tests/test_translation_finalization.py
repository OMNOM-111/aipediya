"""Finalization tests: the automatic translation path, dedup memory, the
URL-agnostic content layer, and deterministic country localization. All use the
offline mock provider, so no external service is ever called."""
from types import SimpleNamespace
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog import translation_pipeline as pipeline
from catalog import translation_providers as providers
from catalog.comparison import localized
from catalog.countries import country_label
from catalog.models import ContentTranslation, ModelVersion
from catalog.translation_providers import MockTranslationProvider


class _SeededCatalog(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def _isolated_model(self, english):
        model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        model.description = {"en": english, "ru": "Русское описание."}
        model.suitable = {}
        model.limitations = {}
        model.origin = {}
        model.philosophy = {}
        model.save(update_fields=["description", "suitable", "limitations", "origin", "philosophy"])
        return model


class AutoTranslateHookTests(_SeededCatalog):
    def test_saving_model_autotranslates_on_commit_and_renders(self):
        model = self._isolated_model("Baseline capability text.")
        with override_settings(AIPEDIA_AUTO_TRANSLATE=True):
            with self.captureOnCommitCallbacks(execute=True):
                model.description = {"en": "Automatically localized capability.", "ru": "Русский."}
                model.save(update_fields=["description"])
        # translated -> persisted (both the JSON field and the audit row)
        model.refresh_from_db()
        self.assertEqual(model.description.get("fr"), "[fr] Automatically localized capability.")
        self.assertTrue(
            ContentTranslation.objects.filter(object_id=model.pk, language="fr", field="description").exists()
        )
        # rendered in the target locale via a normal page view
        html = self.client.get("/models/" + model.slug, {"lang": "fr", "partial": "panel"}, follow=True).content.decode()
        self.assertIn("[fr] Automatically localized capability.", html)

    def test_disabled_by_default_does_not_translate(self):
        model = self._isolated_model("Text with the hook disabled.")
        with self.captureOnCommitCallbacks(execute=True):
            model.description = {"en": "Still only English and Russian.", "ru": "Русский."}
            model.save(update_fields=["description"])
        model.refresh_from_db()
        self.assertNotIn("fr", model.description)

    def test_bulk_suppression_blocks_the_hook(self):
        model = self._isolated_model("Bulk import baseline.")
        with override_settings(AIPEDIA_AUTO_TRANSLATE=True):
            with pipeline.suppress_auto_translation():
                with self.captureOnCommitCallbacks(execute=True):
                    model.description = {"en": "Loaded in a bulk block.", "ru": "Русский."}
                    model.save(update_fields=["description"])
        model.refresh_from_db()
        self.assertNotIn("fr", model.description)


class PageViewsNeverTranslateTests(_SeededCatalog):
    def test_get_requests_never_call_the_translator(self):
        model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        calls = []
        real = providers.get_provider

        def spy(name=None):
            calls.append(name or "default")
            return real(name)

        # Even with the auto-translate hook enabled, rendering reads stored
        # translations only; no GET path may reach the provider.
        with override_settings(AIPEDIA_AUTO_TRANSLATE=True):
            with mock.patch.object(providers, "get_provider", spy):
                self.assertEqual(self.client.get("/", {"lang": "fr"}, follow=True).status_code, 200)
                self.assertEqual(self.client.get("/", {"lang": "ar"}, follow=True).status_code, 200)
                self.client.get("/models/" + model.slug, {"lang": "ja", "partial": "panel"}, follow=True)
                self.client.get("/models/" + model.slug, {"lang": "uk"}, follow=True)
        self.assertEqual(calls, [])


class TranslationMemoryTests(_SeededCatalog):
    def test_backfill_deduplicates_identical_sources(self):
        shared = "Shared identical English description."
        models = list(ModelVersion.objects.filter(published=True, entry_type="model")[:2])
        for model in models:
            model.description = {"en": shared, "ru": "Русское описание."}
            model.suitable = model.limitations = model.origin = model.philosophy = {}
            model.save(update_fields=["description", "suitable", "limitations", "origin", "philosophy"])
        queryset = ModelVersion.objects.filter(pk__in=[m.pk for m in models])
        totals = pipeline.backfill(queryset, provider=MockTranslationProvider(), languages=["fr"])
        self.assertEqual(totals["translated"], 2)
        self.assertEqual(totals["reused"], 2)
        self.assertEqual(totals["requests"], 1)
        self.assertEqual(
            ContentTranslation.objects.filter(language="fr", field="description").count(), 2
        )


class UrlAgnosticContentTests(_SeededCatalog):
    def test_translation_is_keyed_by_language_code_not_url(self):
        model = self._isolated_model("Content addressed by language code only.")
        pipeline.translate_object(model, provider=MockTranslationProvider(), languages=["uk"])
        model.refresh_from_db()
        # Retrieval takes only a language code; nothing about the request URL,
        # so a future /uk/ route reuses the same stored translation unchanged.
        self.assertEqual(localized(model.description, "uk"), "[uk] Content addressed by language code only.")
        row = ContentTranslation.objects.get(object_id=model.pk, field="description", language="uk")
        self.assertEqual(row.state, "current")


class StateSemanticsTests(_SeededCatalog):
    def test_empty_source_is_not_applicable_not_missing(self):
        model = self._isolated_model("Only description has a source.")
        # description has a source; suitable/limitations/origin/philosophy are empty.
        states = {}
        for item in pipeline.plan(model, languages=["fr"]):
            states.setdefault(item["state"], []).append(item["field"])
        self.assertEqual(states.get("missing"), ["description"])
        self.assertEqual(
            sorted(states["not_applicable"]),
            ["limitations", "origin", "philosophy", "suitable"],
        )

    def test_translated_source_is_current_and_missing_is_zero(self):
        model = self._isolated_model("A translatable description.")
        pipeline.translate_object(model, provider=MockTranslationProvider(), languages=["fr"])
        states = [item["state"] for item in pipeline.plan(model, languages=["fr"])]
        self.assertIn("current", states)
        self.assertNotIn("missing", states)


class CountryLocalizationTests(TestCase):
    def test_country_label_localizes_by_code_with_english_fallback(self):
        gb = SimpleNamespace(code="GB", name_ru="Великобритания", name_en="United Kingdom")
        self.assertEqual(country_label(gb, "en"), "United Kingdom")
        self.assertEqual(country_label(gb, "ru"), "Великобритания")
        self.assertEqual(country_label(gb, "de"), "Vereinigtes Königreich")
        self.assertEqual(country_label(gb, "uk"), "Велика Британія")
        self.assertEqual(country_label(gb, "ja"), "イギリス")
        # An unknown code falls back to the English name, never a raw code.
        unknown = SimpleNamespace(code="ZZ", name_ru="", name_en="Neverland")
        self.assertEqual(country_label(unknown, "de"), "Neverland")
