"""Import catalog translations from a portable file, idempotently and offline.

This is the destination half of :mod:`export_translations`. It applies a
translation to a field only when the destination entity's *current* English
source hashes to the same value the translation was produced from, so it can
never overwrite a different English text with a mismatched translation. It is
fully idempotent (re-running changes nothing) and never contacts a translation
provider, so moving translations to Production costs nothing.

Entities are matched by their stable ``slug``; primary keys are intentionally
ignored because they differ between databases.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import ContentTranslation, ModelVersion, Tool
from catalog.translation_pipeline import (
    MANUAL_LANGUAGES, english_source, source_hash, suppress_auto_translation,
)
from catalog.management.commands.export_translations import FORMAT

MODEL_CLASSES = {"model": ModelVersion, "tool": Tool}


class Command(BaseCommand):
    help = "Import translations from an export file without calling any provider."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the translations export JSON file.")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would change without writing anything.",
        )

    def _load(self, path):
        source = Path(path)
        if not source.exists():
            raise CommandError(f"Export file not found: {source}")
        try:
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise CommandError(f"Cannot read export file: {error}")
        if not isinstance(document, dict) or document.get("format") != FORMAT:
            raise CommandError("Unrecognized export file format")
        entries = document.get("entries")
        if not isinstance(entries, list):
            raise CommandError("Export file has no entries list")
        return entries

    def handle(self, *args, **options):
        entries = self._load(options["path"])
        dry_run = options["dry_run"]

        wanted = {"model": set(), "tool": set()}
        for entry in entries:
            if entry.get("entity_type") in wanted and entry.get("slug"):
                wanted[entry["entity_type"]].add(entry["slug"])
        objects = {
            "model": {obj.slug: obj for obj in ModelVersion.objects.filter(slug__in=wanted["model"])},
            "tool": {obj.slug: obj for obj in Tool.objects.filter(slug__in=wanted["tool"])},
        }

        stats = {
            "entries": len(entries), "applied": 0, "unchanged": 0,
            "source_mismatch": 0, "missing_entity": 0, "manual_skipped": 0,
            "invalid": 0, "objects_saved": 0, "dry_run": dry_run,
        }
        changed_by_object = {}

        with suppress_auto_translation(), transaction.atomic():
            for entry in entries:
                entity_type = entry.get("entity_type")
                slug = entry.get("slug")
                field = entry.get("field")
                language = entry.get("language")
                text = entry.get("text")
                digest = entry.get("source_hash")
                if entity_type not in MODEL_CLASSES or not slug or not field \
                        or not language or text in (None, "") or not digest:
                    stats["invalid"] += 1
                    continue
                if language in MANUAL_LANGUAGES:
                    stats["manual_skipped"] += 1
                    continue
                obj = objects[entity_type].get(slug)
                if obj is None:
                    stats["missing_entity"] += 1
                    continue
                value = getattr(obj, field, None)
                if not isinstance(value, dict):
                    stats["invalid"] += 1
                    continue
                if source_hash(english_source(value)) != digest:
                    # The destination English differs from the source this
                    # translation was made for: skip so English keeps showing.
                    stats["source_mismatch"] += 1
                    continue

                state = entry.get("state") if entry.get("state") in ("current", "reviewed") else "current"
                provider = entry.get("provider") or ""
                existing = ContentTranslation.objects.filter(
                    entity_type=entity_type, object_id=obj.pk,
                    field=field, language=language,
                ).first()
                already = (
                    existing is not None
                    and existing.source_hash == digest
                    and existing.text == text
                    and existing.state in ("current", "reviewed")
                    and value.get(language) == text
                )
                if already:
                    stats["unchanged"] += 1
                    continue

                stats["applied"] += 1
                if dry_run:
                    continue
                ContentTranslation.objects.update_or_create(
                    entity_type=entity_type, object_id=obj.pk,
                    field=field, language=language,
                    defaults={"source_hash": digest, "text": text,
                              "state": state, "provider": provider},
                )
                value[language] = text
                changed_by_object.setdefault((entity_type, obj.pk), (obj, set()))[1].add(field)

            if not dry_run:
                for obj, fields in changed_by_object.values():
                    # Machine translations are not editorial edits; the flag
                    # keeps the write out of the Revision history log.
                    obj._aipedia_translation_write = True
                    try:
                        obj.save(update_fields=sorted(fields))
                    finally:
                        obj._aipedia_translation_write = False
                    stats["objects_saved"] += 1

        self.stdout.write(json.dumps(stats, ensure_ascii=False))
