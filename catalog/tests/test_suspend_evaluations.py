from io import StringIO
import json

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Benchmark, Evaluation, ModelVersion, PublicationRevision, Source


class SuspendEvaluationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        model = ModelVersion.objects.first()
        source = Source.objects.create(title="Artificial Analysis", publisher="Artificial Analysis", url="https://artificialanalysis.ai/leaderboards/models")
        benchmark = Benchmark.objects.create(name="AA", protocol="v4.3.2 · xhigh", category=model.category, unit="points")
        cls.evaluation = Evaluation.objects.create(model=model, benchmark=benchmark, score=34, evaluator="Artificial Analysis", independent=True, public=True, source=source, checked=model.checked)

    def run_command(self, *args):
        output = StringIO()
        call_command("suspend_evaluations", *args, stdout=output)
        return json.loads(output.getvalue())

    def test_dry_run_and_suspend_preserve_reversible_history(self):
        args = ("--source-host", "artificialanalysis.ai", "--reason", "terms require permission")
        dry = self.run_command(*args, "--dry-run")
        self.assertEqual(dry["matched"], 1)
        self.evaluation.refresh_from_db()
        self.assertTrue(self.evaluation.public)
        applied = self.run_command(*args)
        self.assertEqual(applied["changed"], 1)
        self.evaluation.refresh_from_db()
        self.assertFalse(self.evaluation.public)
        revision = PublicationRevision.objects.get(action="suspend_evaluation")
        self.assertTrue(revision.before["evaluation"]["public"])
        self.assertFalse(revision.after["evaluation"]["public"])
