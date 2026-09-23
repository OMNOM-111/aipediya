"""Tests for the offline, idempotent translation transfer commands."""
import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from catalog.models import ContentTranslation, ModelVersion
from catalog.translation_pipeline import source_hash


class TranslationTransferTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def setUp(self):
        self.model = ModelVersion.objects.filter(published=True).first()
        self.model.description = {"en": "Alpha source", "fr": "Alpha FR"}
        self.model.save(update_fields=["description"])
        self.hash = source_hash("Alpha source")
        ContentTranslation.objects.update_or_create(
            entity_type="model", object_id=self.model.pk,
            field="description", language="fr",
            defaults={"source_hash": self.hash, "text": "Alpha FR",
                      "state": "current", "provider": "mock"},
        )

    def _export(self):
        tmp = Path(tempfile.mkdtemp()) / "export.json"
        call_command("export_translations", "--output", str(tmp), stdout=StringIO())
        return tmp, json.loads(tmp.read_text(encoding="utf-8"))

    def _import(self, *args):
        out = StringIO()
        call_command("import_translations", *args, stdout=out)
        return json.loads(out.getvalue())

    def _clear_destination_translation(self):
        self.model.description = {"en": "Alpha source"}
        self.model.save(update_fields=["description"])
        ContentTranslation.objects.filter(
            entity_type="model", object_id=self.model.pk,
            field="description", language="fr",
        ).delete()

    def test_export_carries_only_hash_matched_translations(self):
        _, document = self._export()
        self.assertEqual(document["format"], "aipedia-translations")
        entry = next(item for item in document["entries"]
                     if item["slug"] == self.model.slug and item["language"] == "fr")
        self.assertEqual(entry["field"], "description")
        self.assertEqual(entry["text"], "Alpha FR")
        self.assertEqual(entry["source_hash"], self.hash)
        # English/Russian are authored manually and must never be exported.
        self.assertFalse(any(item["language"] in ("en", "ru") for item in document["entries"]))

    def test_import_applies_then_is_idempotent_and_offline(self):
        path, _ = self._export()
        self._clear_destination_translation()

        with mock.patch("catalog.translation_providers.get_provider") as spy:
            stats = self._import(str(path))
        self.assertEqual(spy.call_count, 0)
        self.assertEqual(stats["applied"], 1)
        self.assertEqual(stats["objects_saved"], 1)

        self.model.refresh_from_db()
        self.assertEqual(self.model.description.get("fr"), "Alpha FR")
        row = ContentTranslation.objects.get(
            entity_type="model", object_id=self.model.pk,
            field="description", language="fr")
        self.assertEqual((row.text, row.state, row.source_hash),
                         ("Alpha FR", "current", self.hash))

        repeat = self._import(str(path))
        self.assertEqual(repeat["applied"], 0)
        self.assertEqual(repeat["unchanged"], 1)
        self.assertEqual(repeat["objects_saved"], 0)

    def test_import_skips_when_destination_english_differs(self):
        path, _ = self._export()
        self.model.description = {"en": "A different English source"}
        self.model.save(update_fields=["description"])
        ContentTranslation.objects.filter(
            entity_type="model", object_id=self.model.pk,
            field="description", language="fr").delete()

        stats = self._import(str(path))
        self.assertEqual(stats["applied"], 0)
        self.assertEqual(stats["source_mismatch"], 1)
        self.model.refresh_from_db()
        self.assertNotIn("fr", self.model.description)

    def test_manual_languages_are_never_imported(self):
        path = Path(tempfile.mkdtemp()) / "manual.json"
        path.write_text(json.dumps({
            "format": "aipedia-translations", "version": 1, "entries": [
                {"entity_type": "model", "slug": self.model.slug, "field": "description",
                 "language": "ru", "source_hash": self.hash, "text": "RU override",
                 "state": "current", "provider": "mock"},
            ],
        }), encoding="utf-8")
        stats = self._import(str(path))
        self.assertEqual(stats["manual_skipped"], 1)
        self.assertEqual(stats["applied"], 0)
        self.model.refresh_from_db()
        self.assertNotEqual(self.model.description.get("ru"), "RU override")

    def test_dry_run_reports_but_writes_nothing(self):
        path, _ = self._export()
        self._clear_destination_translation()
        stats = self._import(str(path), "--dry-run")
        self.assertTrue(stats["dry_run"])
        self.assertEqual(stats["applied"], 1)
        self.assertEqual(stats["objects_saved"], 0)
        self.model.refresh_from_db()
        self.assertNotIn("fr", self.model.description)
        self.assertFalse(ContentTranslation.objects.filter(
            entity_type="model", object_id=self.model.pk,
            field="description", language="fr").exists())

    def test_unknown_slug_is_counted_not_fatal(self):
        path = Path(tempfile.mkdtemp()) / "orphan.json"
        path.write_text(json.dumps({
            "format": "aipedia-translations", "version": 1, "entries": [
                {"entity_type": "model", "slug": "no-such-model", "field": "description",
                 "language": "fr", "source_hash": self.hash, "text": "x",
                 "state": "current", "provider": "mock"},
            ],
        }), encoding="utf-8")
        stats = self._import(str(path))
        self.assertEqual(stats["missing_entity"], 1)
        self.assertEqual(stats["applied"], 0)
