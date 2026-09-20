import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import Evaluation, ModelVersion, Offer, ResearchRecord, ResearchRevision


def document(observation):
    return {
        "schema_version": "1", "project": "AIpedia", "prepared_on": "2026-09-19",
        "sources": [{"id": "aa", "name": "Artificial Analysis", "reuse_status": "permission_or_licensed_data_route_required"}],
        "observations_count": 1,
        "observations": [observation],
    }


def observation(model):
    return {
        "observation_id": "AIP-EVAL-test-001", "source_id": "aa", "leaderboard_id": "aa_intelligence",
        "catalog_name_candidate": model.name, "catalog_entity_id_candidate": "test-entity",
        "source_model_name": "exact-source-model", "configuration": "xhigh", "benchmark_version": "4.3.2",
        "value": 34, "unit": "index_points", "higher_is_better": True,
        "source_snapshot_date": None, "source_run_date": None, "observed_on": "2026-09-19",
        "source_url": "https://example.org/source", "publication_state": "review_required",
        "factual_status": "selected_source_value_checked", "reuse_status": "permission_or_licensed_data_route_required",
    }


class BenchmarkImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        cls.model = ModelVersion.objects.first()
        cls.model.research_entity_id = "test-entity"
        cls.model.save(update_fields=["research_entity_id"])

    def run_command(self, payload, *args):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump(payload, handle)
            path = Path(handle.name)
        try:
            output = StringIO()
            call_command("import_benchmarks", str(path), *args, stdout=output)
            return json.loads(output.getvalue())
        finally:
            path.unlink(missing_ok=True)

    def test_stages_exact_mapping_without_changing_public_catalogue(self):
        payload = document(observation(self.model))
        before = (Offer.objects.count(), Evaluation.objects.count(), ModelVersion.objects.filter(published=True).count())
        dry = self.run_command(payload, "--dry-run")
        self.assertEqual(dry["published"], 0)
        self.assertEqual(dry["mapping"], {"exact_catalog_entity_and_name": 1})
        self.assertEqual(ResearchRecord.objects.count(), 0)
        first = self.run_command(payload)
        self.assertEqual(first["created"], 1)
        self.assertEqual(first["prices_touched"], 0)
        self.assertEqual(before, (Offer.objects.count(), Evaluation.objects.count(), ModelVersion.objects.filter(published=True).count()))
        record = ResearchRecord.objects.get(source_record_id="AIP-EVAL-test-001")
        self.assertEqual(record.state, "review_required")
        self.assertIn("licensed or written permission", record.review_reason)
        self.assertEqual(record.payload["observation"]["configuration"], "xhigh")
        self.assertEqual(record.payload["live_catalog_mapping"]["model_pk"], self.model.pk)
        self.assertEqual(ResearchRevision.objects.count(), 1)
        repeat = self.run_command(payload)
        self.assertEqual(repeat["unchanged"], 1)
        self.assertEqual(ResearchRevision.objects.count(), 1)

    def test_conflicting_observation_never_overwrites_staging_record(self):
        payload = document(observation(self.model))
        self.run_command(payload)
        payload["observations"][0]["value"] = 35
        with self.assertRaisesMessage(CommandError, "Conflicting benchmark observation"):
            self.run_command(payload)
        self.assertEqual(ResearchRecord.objects.get().payload["observation"]["value"], 34)
