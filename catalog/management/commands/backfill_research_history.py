from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import ResearchRecord, ResearchRevision


class Command(BaseCommand):
    help = "Add immutable creation-history entries only for legacy staged records that have no history."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for record in ResearchRecord.objects.all().iterator():
            if record.revisions.exists():
                continue
            ResearchRevision.objects.create(
                record=record, batch=record.batch, action="history_backfill",
                before={"created": True, "state": "rejected"},
                after={"batch": record.batch, "external_id": record.external_id,
                       "source_record_id": record.source_record_id, "state": record.state,
                       "payload": record.payload},
            )
            created += 1
        self.stdout.write(f"Added {created} legacy research history entries.")
