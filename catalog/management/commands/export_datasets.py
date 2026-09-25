"""Write a reproducible snapshot of both public datasets (GSD-07). Read-only on the DB.

    manage.py export_datasets --out artifacts/datasets/<date> [--check]

Writes <slug>.json, <slug>.csv and manifest.json. ``--check`` generates twice
and fails if any checksum differs (determinism proof). Needs no Excel/openpyxl.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog import datasets


class Command(BaseCommand):
    help = "Export the public Models/Tools datasets (JSON, CSV, manifest) deterministically."

    def add_arguments(self, parser):
        parser.add_argument("--out", required=True)
        parser.add_argument("--check", action="store_true")

    def handle(self, *args, **options):
        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        first = datasets.manifest()
        if options["check"]:
            second = datasets.manifest()
            if first != second:
                raise CommandError("Non-deterministic dataset output: manifests differ between runs.")
        for kind, info in datasets.DATASETS.items():
            for fmt in ("json", "csv"):
                (out / f"{info['slug']}.{fmt}").write_bytes(datasets.build(kind, fmt))
        (out / "manifest.json").write_text(json.dumps(first, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        for name, item in first["files"].items():
            self.stdout.write(f"{name}: {item['records']} records, {item['bytes']} B, sha256 {item['sha256']}")
        self.stdout.write(self.style.SUCCESS(f"Snapshot written to {out}" + (" (determinism check passed)" if options["check"] else "")))
