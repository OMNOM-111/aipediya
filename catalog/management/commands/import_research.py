import json

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from catalog.research import ResearchError, prepare_records, read_document


class Command(BaseCommand):
    help = (
        "Stage research offers for editorial review only. "
        "Identical imports preserve review decisions; conflicting content requires a new --batch. "
        "payload.record is the original row; payload.dataset preserves all root metadata."
    )
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("path", help="Research JSON file with a records array.")
        parser.add_argument("--batch", help="Batch namespace; defaults to project:snapshot_date.")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Validate and count the file without any database access. Does not check stored conflicts.",
        )

    def handle(self, *args, **options):
        try:
            document = read_document(options["path"])
            batch, prepared, summary = prepare_records(document, options.get("batch"))
        except ResearchError as exc:
            raise CommandError(str(exc)) from exc
        result = {
            "batch": batch, **summary, "dry_run": options["dry_run"],
            "published": 0, "updated": 0, "history_entries": 0,
        }
        if options["dry_run"]:
            result["database_checked"] = False
            self.stdout.write(json.dumps(result, sort_keys=True))
            return

        try:
            record_model = apps.get_model("catalog", "ResearchRecord")
        except LookupError as exc:
            raise CommandError("catalog.ResearchRecord and its migration are required.") from exc
        created = updated = history_entries = 0
        unchanged = 0
        try:
            # The whole batch is atomic, including conflicts discovered after new rows.
            with transaction.atomic():
                revision_model = apps.get_model("catalog", "ResearchRevision")
                for item in prepared:
                    record = record_model.objects.filter(source_record_id=item["source_record_id"]).first()
                    if record is None:
                        record = record_model.objects.filter(external_id=item["external_id"]).first()
                    if record is None:
                        record = record_model.objects.create(**item)
                        revision_model.objects.create(
                            record=record, batch=batch, action="import_create",
                            before={"created": True, "state": "rejected"},
                            after={"batch": record.batch, "external_id": record.external_id,
                                   "source_record_id": record.source_record_id,
                                   "state": record.state, "payload": record.payload},
                        )
                        created += 1
                        history_entries += 1
                        continue
                    if record.batch == batch and record.payload != item["payload"]:
                        raise CommandError(
                            f"Conflicting research content for {record.source_record_id or record.external_id}; "
                            "nothing imported. Use a new batch after reviewing the difference."
                        )
                    if record.state != "review_required" and record.payload != item["payload"]:
                        raise CommandError(
                            f"Reviewed record {record.source_record_id or record.external_id} differs; "
                            "nothing imported. Review it explicitly before replacing it."
                        )
                    if (record.batch, record.payload, record.external_id, record.source_record_id) == (
                        item["batch"], item["payload"], item["external_id"], item["source_record_id"]
                    ):
                        unchanged += 1
                        continue
                    before = {"batch": record.batch, "external_id": record.external_id,
                              "source_record_id": record.source_record_id, "state": record.state,
                              "payload": record.payload}
                    record.batch = item["batch"]
                    record.external_id = item["external_id"]
                    record.source_record_id = item["source_record_id"]
                    record.payload = item["payload"]
                    record.state = "review_required"
                    record.save(update_fields=["batch", "external_id", "source_record_id", "payload", "state"])
                    revision_model.objects.create(record=record, batch=batch, action="import_update", before=before,
                                                  after={"batch": record.batch, "external_id": record.external_id,
                                                         "source_record_id": record.source_record_id,
                                                         "state": record.state, "payload": record.payload})
                    updated += 1
                    history_entries += 1
        except DatabaseError as exc:
            raise CommandError(
                "Staging import failed; no batch changes committed. "
                "Ensure the approved ResearchRecord migration has been applied."
            ) from exc
        result.update(created=created, updated=updated, unchanged=unchanged,
                      history_entries=history_entries, database_checked=True)
        self.stdout.write(json.dumps(result, sort_keys=True))
