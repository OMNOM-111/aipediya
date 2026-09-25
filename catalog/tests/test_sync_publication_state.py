import io
import json
import tempfile
from datetime import date
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import (
    ModelFamily, ModelVersion, Organization, PublicationRevision, Revision, Source, Tool,
)


class SyncPublicationStateTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(title="Fixture", publisher="Fixture", url="https://example.com/r")
        self.org = Organization.objects.create(name="Fixture", source=self.source, checked=date(2026, 1, 1))
        self.family = ModelFamily.objects.create(name="Fixture", developer=self.org)
        for i, name in enumerate(("Alpha", "Bravo", "Charlie"), 1):
            ModelVersion.objects.create(
                name=name, slug=name.lower(), family=self.family, version="1",
                released=date(2024, 1, i), source=self.source, checked=date(2026, 1, 1))
        Tool.objects.create(
            name="Tool", slug="tool", version="1", developer=self.org, category="coding_agent",
            purposes=["coding"], released=date(2025, 1, 1), source=self.source, checked=date(2026, 1, 1))
        self.path = Path(tempfile.mkdtemp()) / "state.json"

    def export_with_charlie_hidden(self):
        call_command("sync_publication_state", "export", str(self.path), release="r1", stdout=io.StringIO())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["models"]["charlie"]["published"] = False
        data["public"]["models"] = 2
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def run_apply(self, *extra):
        call_command("sync_publication_state", "apply", str(self.path), *extra, stdout=io.StringIO())

    def test_dry_run_writes_nothing(self):
        self.export_with_charlie_hidden()
        self.run_apply()
        self.assertTrue(ModelVersion.objects.get(slug="charlie").published)

    def test_apply_hides_via_save_keeps_number_and_logs(self):
        self.export_with_charlie_hidden()
        number = ModelVersion.objects.get(slug="charlie").public_number
        revisions = Revision.objects.count()
        self.run_apply("--apply")
        charlie = ModelVersion.objects.get(slug="charlie")
        self.assertFalse(charlie.published)
        self.assertEqual(charlie.public_number, number)
        log = PublicationRevision.objects.get(model=charlie, action="sync_release_state")
        self.assertEqual(log.before, {"published": True, "public_number": number})
        self.assertGreater(Revision.objects.count(), revisions)  # save() kept the history snapshot
        self.run_apply("--apply")  # idempotent
        self.assertEqual(PublicationRevision.objects.filter(action="sync_release_state").count(), 1)

    def test_number_mismatch_aborts_without_writes(self):
        data = self.export_with_charlie_hidden()
        data["models"]["alpha"]["public_number"] = 99
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(CommandError):
            self.run_apply("--apply")
        self.assertTrue(ModelVersion.objects.get(slug="charlie").published)

    def test_unknown_slug_aborts(self):
        data = self.export_with_charlie_hidden()
        data["tools"]["ghost"] = {"published": True, "public_number": 2}
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(CommandError):
            self.run_apply("--apply")
