"""Repair stored translations that dropped a technical token.

Re-translates only the affected ``(source, language)`` pairs with the
token-protected provider, so distortions such as Azure rendering ``1M`` as a
word/unit are fixed without a full backfill. By default only the number+unit
class (``1M``/``128K``/``7B``) is repaired, which is the semantic-loss class;
``--all-tokens`` also repairs dropped identifiers/acronyms. Idempotent and
deduplicated; a repair write is kept out of the Revision history log.
"""
import json
import re

from django.core.management.base import BaseCommand

from catalog import token_guard
from catalog.models import ContentTranslation, ModelVersion, Tool
from catalog.translation_pipeline import (
    MODEL_FIELDS, TOOL_FIELDS, english_source, source_hash, target_languages,
)
from catalog.translation_providers import TranslationError, get_provider

UNIT_RE = re.compile(r"\b\d+(?:\.\d+)?[KMBT]\b")


class Command(BaseCommand):
    help = "Re-translate stored translations that dropped a technical token (protected)."

    def add_arguments(self, parser):
        parser.add_argument("--provider", default="")
        parser.add_argument("--languages", default="")
        parser.add_argument("--all-tokens", action="store_true", help="Repair any dropped technical token, not only number+unit.")
        parser.add_argument("--batch-size", type=int, default=50)
        parser.add_argument("--dry-run", action="store_true")

    def _dropped(self, source, translation, all_tokens):
        if all_tokens:
            return token_guard.missing_tokens(source, translation)
        return [t for t in UNIT_RE.findall(source) if t not in (translation or "")]

    def _fields(self):
        for obj in ModelVersion.objects.filter(published=True, entry_type="model"):
            for field in MODEL_FIELDS:
                yield "model", obj, field, getattr(obj, field, None)
        for obj in Tool.objects.filter(published=True):
            for field in TOOL_FIELDS:
                yield "tool", obj, field, getattr(obj, field, None)

    def handle(self, *args, **options):
        provider = get_provider(options["provider"] or None)
        languages = [c.strip() for c in options["languages"].split(",") if c.strip()] or None
        langs = target_languages(languages)
        all_tokens = options["all_tokens"]

        pending = {}          # (source, lang) -> source
        occurrences = {}      # (source, lang) -> [(entity_type, obj, field)]
        for entity_type, obj, field, value in self._fields():
            source = english_source(value)
            if not source or not token_guard.find_tokens(source):
                continue
            for lang in langs:
                translation = value.get(lang)
                if not translation:
                    continue
                if self._dropped(source, translation, all_tokens):
                    key = (source, lang)
                    pending[key] = source
                    occurrences.setdefault(key, []).append((entity_type, obj, field))

        billable = sum(len(s) for s in pending.values())
        result = {"provider": provider.name, "all_tokens": all_tokens,
                  "pairs": len(pending), "billable_chars": billable, "dry_run": options["dry_run"]}
        if options["dry_run"] or not pending:
            self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return

        by_lang = {}
        for (source, lang) in pending:
            by_lang.setdefault(lang, []).append(source)
        memory, requests, failed = {}, 0, 0
        for lang, sources in by_lang.items():
            for start in range(0, len(sources), options["batch_size"]):
                chunk = sources[start:start + options["batch_size"]]
                try:
                    texts = provider.translate_batch(chunk, lang, "en")
                    requests += 1
                except TranslationError:
                    failed += len(chunk)
                    continue
                for src, text in zip(chunk, texts):
                    if text:
                        memory[(src, lang)] = text

        repaired, dirty = 0, {}
        for (source, lang), text in memory.items():
            for entity_type, obj, field in occurrences[(source, lang)]:
                value = getattr(obj, field)
                value[lang] = text
                dirty.setdefault(obj, set()).add(field)
                ContentTranslation.objects.update_or_create(
                    entity_type=entity_type, object_id=obj.pk, field=field, language=lang,
                    defaults={"source_hash": source_hash(source), "text": text,
                              "state": "current", "provider": provider.name},
                )
                repaired += 1
        for obj, changed in dirty.items():
            obj._aipedia_translation_write = True
            try:
                obj.save(update_fields=sorted(changed))
            finally:
                obj._aipedia_translation_write = False

        result.update({"provider_requests": requests, "provider_failed": failed, "repaired": repaired})
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))
