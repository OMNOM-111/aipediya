import json

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Evaluation, PublicationRevision


class Command(BaseCommand):
    help = "Hide public evaluations from a source while retaining the row and a before/after publication revision."

    def add_arguments(self, parser):
        parser.add_argument("--source-host", required=True, help="Source hostname fragment, for example artificialanalysis.ai.")
        parser.add_argument("--reason", required=True, help="Verified reason for removing public numerical display.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        evaluations = Evaluation.objects.filter(public=True, source__url__icontains=options["source_host"]).select_related("model", "benchmark", "source")
        result = {"source_host": options["source_host"], "matched": evaluations.count(), "dry_run": options["dry_run"]}
        if options["dry_run"]:
            self.stdout.write(json.dumps(result, sort_keys=True))
            return
        changed = 0
        with transaction.atomic():
            for evaluation in evaluations:
                before = {
                    "evaluation_id": evaluation.pk, "public": evaluation.public, "score": str(evaluation.score),
                    "benchmark": f"{evaluation.benchmark.name} · {evaluation.benchmark.protocol}",
                    "source": evaluation.source.url,
                }
                evaluation.public = False
                evaluation.save(update_fields=["public"])
                PublicationRevision.objects.create(
                    entity_id=evaluation.model.research_entity_id or f"model:{evaluation.model_id}",
                    model=evaluation.model,
                    action="suspend_evaluation",
                    source_record_ids=[],
                    before={"evaluation": before},
                    after={"evaluation": {**before, "public": False}, "reason": options["reason"]},
                )
                changed += 1
        result["changed"] = changed
        self.stdout.write(json.dumps(result, sort_keys=True))
