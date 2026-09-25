import json

from django.core.management.base import BaseCommand

from catalog.discovery import outbox_status


class Command(BaseCommand):
    help = "Read-only IndexNow outbox status: active pending/retry vs historical failed attempts."

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(outbox_status(), indent=1, default=str))
