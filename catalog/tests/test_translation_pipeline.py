from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from catalog import translation_pipeline as pipeline
from catalog.models import ContentTranslation, ModelVersion
from catalog.translation_providers import (
    MockTranslationProvider, NullTranslationProvider, TranslationError, get_provider,
)


class FailingProvider(MockTranslationProvider):
    name = "failing"

    def translate(self, text, target_language, source_language="en"):
        raise TranslationError("provider unavailable")


class TranslationPipelineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def setUp(self):
        self.model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        # Isolate to a single localizable field so the pipeline counts are exact.
        self.model.description = {"en": "An advanced English description.", "ru": "Русское описание."}
        self.model.suitable = {}
        self.model.limitations = {}
        self.model.origin = {}
        self.model.philosophy = {}
        self.model.save(update_fields=["description", "suitable", "limitations", "origin", "philosophy"])

    def test_mock_translates_missing_and_stores_current(self):
        summary = pipeline.translate_object(
            self.model, provider=MockTranslationProvider(), languages=["fr", "de"]
        )
        self.assertEqual(summary["translated"], 2)
        self.model.refresh_from_db()
        self.assertEqual(self.model.description["fr"], "[fr] An advanced English description.")
        self.assertEqual(self.model.description["de"], "[de] An advanced English description.")
        rows = ContentTranslation.objects.filter(
            entity_type="model", object_id=self.model.pk, field="description"
        )
        self.assertEqual(rows.count(), 2)
        self.assertTrue(all(row.state == "current" for row in rows))
        # The English source and existing Russian content stay untouched.
        self.assertEqual(self.model.description["en"], "An advanced English description.")
        self.assertEqual(self.model.description["ru"], "Русское описание.")

    def test_source_change_outdates_and_falls_back_to_english(self):
        pipeline.translate_object(self.model, provider=MockTranslationProvider(), languages=["fr"])
        self.model.refresh_from_db()
        self.assertIn("fr", self.model.description)
        self.model.description = {**self.model.description, "en": "A rewritten English description."}
        self.model.save(update_fields=["description"])
        self.model.refresh_from_db()
        self.assertNotIn("fr", self.model.description)
        row = ContentTranslation.objects.get(
            entity_type="model", object_id=self.model.pk, field="description", language="fr"
        )
        self.assertEqual(row.state, "outdated")
        # Re-translation restores a current translation for the new source.
        pipeline.translate_object(self.model, provider=MockTranslationProvider(), languages=["fr"])
        self.model.refresh_from_db()
        self.assertEqual(self.model.description["fr"], "[fr] A rewritten English description.")
        row.refresh_from_db()
        self.assertEqual(row.state, "current")

    def test_retranslate_touches_only_missing_and_outdated(self):
        pipeline.translate_object(self.model, provider=MockTranslationProvider(), languages=["fr"])
        summary = pipeline.translate_object(self.model, provider=MockTranslationProvider(), languages=["fr"])
        self.assertEqual(summary["translated"], 0)

    def test_provider_failure_does_not_break_save_or_site(self):
        summary = pipeline.translate_object(self.model, provider=FailingProvider(), languages=["fr"])
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["translated"], 0)
        self.model.refresh_from_db()
        self.assertNotIn("fr", self.model.description)
        response = self.client.get("/models/" + self.model.slug, {"lang": "fr"}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_null_provider_keeps_english_fallback(self):
        summary = pipeline.translate_object(self.model, provider=NullTranslationProvider(), languages=["fr", "de"])
        self.assertEqual(summary["failed"], 2)
        self.model.refresh_from_db()
        self.assertNotIn("fr", self.model.description)
        self.assertNotIn("de", self.model.description)

    def test_backfill_translates_pipeline_languages(self):
        totals = pipeline.backfill(
            ModelVersion.objects.filter(pk=self.model.pk),
            provider=MockTranslationProvider(), languages=["fr"],
        )
        self.assertEqual(totals["objects"], 1)
        self.assertGreaterEqual(totals["translated"], 1)

    def test_russian_and_english_are_not_pipeline_targets(self):
        self.assertNotIn("en", pipeline.target_languages())
        self.assertNotIn("ru", pipeline.target_languages())
        self.assertIn("fr", pipeline.target_languages())
        self.assertEqual(len(pipeline.target_languages()), 20)

    def test_command_status_and_dry_run_avoid_external_calls(self):
        out = StringIO()
        call_command("translate_catalog", "--status", "--languages=fr", stdout=out)
        self.assertIn("status", out.getvalue())
        out = StringIO()
        call_command(
            "translate_catalog", "--dry-run", "--languages=fr", "--kind=models", "--limit=2", stdout=out
        )
        self.assertIn("dry_run", out.getvalue())

    def test_command_translates_with_mock_provider(self):
        out = StringIO()
        call_command(
            "translate_catalog", "--provider=mock", "--languages=fr", "--kind=models", "--limit=1", stdout=out
        )
        self.assertIn('"translated"', out.getvalue())

    @override_settings(AIPEDIA_TRANSLATION_PROVIDER="mock")
    def test_default_provider_is_offline_mock(self):
        self.assertIsInstance(get_provider(), MockTranslationProvider)


class CheckTranslatorCommandTests(TestCase):
    def test_mock_provider_reports_pass_without_network(self):
        out = StringIO()
        call_command("check_translator", "--provider=mock", "--to=fr", stdout=out)
        self.assertIn("PASS", out.getvalue())
        self.assertIn("provider=mock", out.getvalue())

    @override_settings(AIPEDIA_AZURE_TRANSLATOR_KEY="")
    def test_azure_without_key_fails_safely_without_network(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("check_translator", "--provider=azure")
        message = str(ctx.exception)
        self.assertIn("FAIL", message)
        self.assertNotIn("Ocp-Apim", message)

    def test_null_provider_fails_safely(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("check_translator", "--provider=null")
        self.assertIn("FAIL", str(ctx.exception))

    @override_settings(AIPEDIA_AZURE_TRANSLATOR_KEY="super-secret-value-should-never-leak")
    def test_safe_reason_never_echoes_the_key(self):
        from catalog.management.commands.check_translator import _safe_reason

        redacted = _safe_reason("HTTP 401 with super-secret-value-should-never-leak in the body")
        self.assertNotIn("super-secret-value-should-never-leak", redacted)
        self.assertIn("***", redacted)
