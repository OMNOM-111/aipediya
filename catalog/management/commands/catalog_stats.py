import json

from django.core.management.base import BaseCommand

from catalog.aggregates import compute


class Command(BaseCommand):
    help = "Print verifiable aggregates over published records (JSON). Read-only."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="")

    def handle(self, *args, **options):
        text = json.dumps(compute(), ensure_ascii=False, indent=1)
        if options["out"]:
            with open(options["out"], "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
        self.stdout.write(text)
