from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import ResearchRevision


class Command(BaseCommand):
    help = "Restore a research staging record to the immutable before-state of one import revision."

    def add_arguments(self, parser):
        parser.add_argument("revision_id", type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        revision = ResearchRevision.objects.select_for_update().filter(pk=options["revision_id"]).first()
        if revision is None:
            raise CommandError("Unknown research revision.")
        before = revision.before
        if isinstance(before, dict) and before.get("created") is True:
            record = revision.record
            previous = revision.after
            record.state = "rejected"
            record.save(update_fields=["state"])
            ResearchRevision.objects.create(
                record=record, batch=record.batch, action="rollback_create",
                before=previous, after={"created": True, "state": "rejected"},
            )
            self.stdout.write(f"Rolled back staged creation {record.source_record_id or record.external_id}.")
            return
        required = {"batch", "external_id", "source_record_id", "state", "payload"}
        if not isinstance(before, dict) or not required.issubset(before):
            raise CommandError("Revision has no complete rollback state.")
        record = revision.record
        record.batch = before["batch"]
        record.external_id = before["external_id"]
        record.source_record_id = before["source_record_id"]
        record.state = before["state"]
        record.payload = before["payload"]
        record.save(update_fields=["batch", "external_id", "source_record_id", "state", "payload"])
        ResearchRevision.objects.create(
            record=record, batch=record.batch, action="rollback",
            before=revision.after, after=before,
        )
        self.stdout.write(f"Rolled back research record {record.source_record_id or record.external_id}.")
