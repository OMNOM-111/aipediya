import json

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from catalog.benchmark_import import BenchmarkImportError, prepare_observations, read_benchmark_document, summary
from catalog.models import ResearchRecord, ResearchRevision


class Command(BaseCommand):
    help = "Stage third-party benchmark observations for review without writing catalogue evaluations or prices."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("path", help="Benchmark JSON package.")
        parser.add_argument("--batch", help="Immutable staging namespace; defaults to AIpedia-benchmarks:<prepared_on>.")
        parser.add_argument("--dry-run", action="store_true", help="Validate, map against the live catalogue, and write nothing.")

    def handle(self, *args, **options):
        try:
            document = read_benchmark_document(options["path"])
            batch, prepared = prepare_observations(document, options.get("batch"))
        except BenchmarkImportError as exc:
            raise CommandError(str(exc)) from exc
        result = {"batch": batch, **summary(prepared), "dry_run": options["dry_run"], "published": 0, "prices_touched": 0}
        if options["dry_run"]:
            result["database_checked"] = True
            self.stdout.write(json.dumps(result, sort_keys=True))
            return
        created = unchanged = history_entries = 0
        try:
            with transaction.atomic():
                for item in prepared:
                    record = ResearchRecord.objects.filter(source_record_id=item["source_record_id"]).first()
                    if record is None:
                        record = ResearchRecord.objects.filter(external_id=item["external_id"]).first()
                    if record is None:
                        record = ResearchRecord.objects.create(**item)
                        ResearchRevision.objects.create(
                            record=record, batch=batch, action="bench_import_create",
                            before={"created": True, "state": "rejected"},
                            after={"external_id": record.external_id, "source_record_id": record.source_record_id,
                                   "state": record.state, "review_reason": record.review_reason,
                                   "payload": record.payload},
                        )
                        created += 1
                        history_entries += 1
                        continue
                    if record.payload != item["payload"] or record.batch != item["batch"]:
                        raise CommandError(
                            f"Conflicting benchmark observation {record.source_record_id or record.external_id}; "
                            "a revised source snapshot must use a new observation_id and batch."
                        )
                    unchanged += 1
        except DatabaseError as exc:
            raise CommandError("Benchmark staging import failed; no changes committed.") from exc
        result.update(created=created, unchanged=unchanged, history_entries=history_entries, database_checked=True)
        self.stdout.write(json.dumps(result, sort_keys=True))
