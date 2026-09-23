"""Export current catalog translations as a portable, source-hash-keyed file.

The file is the transport used to carry machine/reviewed translations from one
database (e.g. Local) to another (e.g. Production) *without* re-spending the
translation provider. Every entry is keyed by the stable entity ``slug`` plus
``field`` + ``language`` + the sha-256 ``source_hash`` of the English source it
was produced from. The importer only applies an entry when the destination's
current English source still hashes to the same value, so a translation can
never be written on top of a different English text.

English and Russian are authored manually and are never exported here; only the
pipeline-managed target languages are carried.
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.models import ContentTranslation, ModelVersion, Tool
from catalog.translation_pipeline import (
    MODEL_FIELDS, TOOL_FIELDS, english_source, source_hash,
)

FORMAT = "aipedia-translations"
FORMAT_VERSION = 1


def _source_index():
    """Map ``(entity_type, pk)`` to ``(slug, {field: english_source_hash})``."""
    index = {}
    model_fields = list(MODEL_FIELDS)
    for row in ModelVersion.objects.values("pk", "slug", *model_fields):
        index[("model", row["pk"])] = (
            row["slug"],
            {field: source_hash(english_source(row[field])) for field in model_fields},
        )
    tool_fields = list(TOOL_FIELDS)
    for row in Tool.objects.values("pk", "slug", *tool_fields):
        index[("tool", row["pk"])] = (
            row["slug"],
            {field: source_hash(english_source(row[field])) for field in tool_fields},
        )
    return index


def _git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    commit = result.stdout.strip()
    return commit if len(commit) == 40 else ""


class Command(BaseCommand):
    help = "Export current/reviewed catalog translations to a portable JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", default="outputs/translations-export.json",
            help="Destination JSON file (default: outputs/translations-export.json).",
        )
        parser.add_argument(
            "--indent", type=int, default=None,
            help="Optional JSON indent for a human-readable file.",
        )

    def handle(self, *args, **options):
        index = _source_index()
        entries = []
        skipped_stale = 0
        skipped_orphan = 0
        rows = (
            ContentTranslation.objects
            .filter(state__in=("current", "reviewed"))
            .exclude(text="")
            .values("entity_type", "object_id", "field", "language",
                    "source_hash", "text", "state", "provider")
            .iterator()
        )
        for row in rows:
            key = (row["entity_type"], row["object_id"])
            entity = index.get(key)
            if entity is None:
                skipped_orphan += 1
                continue
            slug, field_hashes = entity
            # Only carry a translation whose English source still matches: a
            # current/reviewed row should already match, but re-checking keeps
            # a hand-edited database from exporting a stale pairing.
            if field_hashes.get(row["field"]) != row["source_hash"]:
                skipped_stale += 1
                continue
            entries.append({
                "entity_type": row["entity_type"],
                "slug": slug,
                "field": row["field"],
                "language": row["language"],
                "source_hash": row["source_hash"],
                "text": row["text"],
                "state": row["state"],
                "provider": row["provider"],
            })

        entries.sort(key=lambda e: (e["entity_type"], e["slug"], e["field"], e["language"]))
        document = {
            "format": FORMAT,
            "version": FORMAT_VERSION,
            "generated": datetime.now(timezone.utc).isoformat(),
            "source_commit": _git_commit(),
            "count": len(entries),
            "entries": entries,
        }

        output = Path(options["output"])
        if output.suffix.lower() != ".json":
            raise CommandError("Output file must end with .json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(document, ensure_ascii=False, indent=options["indent"]),
            encoding="utf-8",
        )

        summary = {
            "output": str(output),
            "exported": len(entries),
            "skipped_stale": skipped_stale,
            "skipped_orphan": skipped_orphan,
        }
        self.stdout.write(json.dumps(summary, ensure_ascii=False))
