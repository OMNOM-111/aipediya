"""Dynamic-catalog translation pipeline.

English is the canonical source. This module keeps machine/reviewed
translations of the localizable catalog fields in
:class:`catalog.models.ContentTranslation`, bound to the sha-256 hash of the
English source so a source change automatically marks a translation outdated.
Rendering still reads the model JSON fields, so only ``current``/``reviewed``
translations are stored there and anything missing or outdated safely falls
back to English.

Translation runs once when data is added or changed (a command, an import hook,
or an explicit call), never on page view, and a provider failure is contained so
it can neither break a model save nor the site.
"""
import hashlib
import threading
from contextlib import contextmanager

from .i18n import SUPPORTED_CODES

SOURCE_LANGUAGE = "en"
# Russian is existing human-authored content, managed manually, not machine
# translated. English is the source. Everything else is pipeline-managed.
MANUAL_LANGUAGES = frozenset({"en", "ru"})
MODEL_FIELDS = ("description", "suitable", "limitations", "origin", "philosophy")
# ``ecosystem`` is a list of product / model brand names (e.g. "Jurassic /
# Jamba"), which must never be machine-translated, so only the prose
# ``description`` is pipeline-managed for tools.
TOOL_FIELDS = ("description",)

_suppress_state = threading.local()


def translations_suppressed():
    return getattr(_suppress_state, "active", False)


@contextmanager
def suppress_auto_translation():
    """Disable the per-save auto-translate hook inside a bulk block.

    Bulk imports create or update many rows; translating each one on save would
    cause a provider call storm. Such commands run their writes inside this
    block and then trigger one batched ``translate_catalog`` / :func:`backfill`
    pass, which is deduplicated and fits the free tier.
    """
    previous = getattr(_suppress_state, "active", False)
    _suppress_state.active = True
    try:
        yield
    finally:
        _suppress_state.active = previous


def source_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def english_source(value):
    if isinstance(value, dict):
        return (value.get(SOURCE_LANGUAGE) or "").strip()
    return ""


def _is_tool(obj):
    return obj.__class__.__name__ == "Tool"


def _entity_type(obj):
    return "tool" if _is_tool(obj) else "model"


def _fields_for(obj):
    return TOOL_FIELDS if _is_tool(obj) else MODEL_FIELDS


def target_languages(languages=None):
    codes = [code for code in SUPPORTED_CODES if code not in MANUAL_LANGUAGES]
    if languages:
        wanted = set(languages)
        codes = [code for code in codes if code in wanted]
    return codes


def plan(obj, languages=None):
    """Return the desired state per ``(field, language)``. No side effects, no API."""
    from .models import ContentTranslation

    entity_type = _entity_type(obj)
    rows = {
        (row.field, row.language): row
        for row in ContentTranslation.objects.filter(entity_type=entity_type, object_id=obj.pk)
    }
    items = []
    for field in _fields_for(obj):
        source = english_source(getattr(obj, field, None))
        digest = source_hash(source)
        for language in target_languages(languages):
            row = rows.get((field, language))
            if not source:
                # No English source to translate: not a gap, just nothing to do.
                state = "not_applicable"
            elif row is None:
                state = "missing"
            elif row.source_hash == digest and row.text:
                state = "reviewed" if row.state == "reviewed" else "current"
            else:
                state = "outdated"
            items.append(
                {"field": field, "language": language, "state": state,
                 "source": source, "hash": digest, "row": row}
            )
    return items


def translate_object(obj, provider=None, languages=None, states=("missing", "outdated"), save=True, memory=None):
    """Translate the requested states for one object and persist results.

    A provider error for one field/language is caught so neither the save nor
    the site breaks; that field simply stays on the English fallback.

    ``memory`` is an optional translation-memory cache keyed by
    ``(source_hash, language)``. Identical English sources (shared across many
    historical records) are then translated once and reused, which keeps the
    provider character volume at the deduplicated minimum.
    """
    from .models import ContentTranslation
    from .translation_providers import TranslationError, get_provider

    provider = provider or get_provider()
    entity_type = _entity_type(obj)
    summary = {"translated": 0, "reused": 0, "skipped": 0, "failed": 0}
    wanted = set(states)
    changed_fields = set()
    for item in plan(obj, languages):
        if item["state"] not in wanted or not item["source"]:
            continue
        cache_key = (item["hash"], item["language"])
        text = memory.get(cache_key) if memory is not None else None
        reused = bool(text)
        if not reused:
            try:
                text = provider.translate(item["source"], item["language"], SOURCE_LANGUAGE)
            except TranslationError:
                summary["failed"] += 1
                continue
            if not text:
                summary["skipped"] += 1
                continue
            if memory is not None:
                memory[cache_key] = text
        ContentTranslation.objects.update_or_create(
            entity_type=entity_type, object_id=obj.pk,
            field=item["field"], language=item["language"],
            defaults={"source_hash": item["hash"], "text": text,
                      "state": "current", "provider": provider.name},
        )
        value = getattr(obj, item["field"], None)
        if isinstance(value, dict):
            value[item["language"]] = text
            changed_fields.add(item["field"])
        summary["translated"] += 1
        if reused:
            summary["reused"] += 1
    if save and changed_fields:
        # Persisting machine translations is not an editorial change: the
        # ContentTranslation rows are their own audit trail, so this flag keeps
        # the write out of the Revision history log.
        obj._aipedia_translation_write = True
        try:
            obj.save(update_fields=sorted(changed_fields))
        finally:
            obj._aipedia_translation_write = False
    return summary


def invalidate_stale(obj):
    """Mark translations outdated when their English source changed.

    Designed for a ``pre_save`` signal: it strips stale translated text from the
    in-memory JSON field (the caller's save persists it) so the site falls back
    to English, and never calls an external API, so a save can't fail here.
    """
    from .models import ContentTranslation

    if not obj.pk:
        return False
    entity_type = _entity_type(obj)
    changed = False
    by_field = {}
    for row in ContentTranslation.objects.filter(entity_type=entity_type, object_id=obj.pk):
        by_field.setdefault(row.field, []).append(row)
    for field, field_rows in by_field.items():
        value = getattr(obj, field, None)
        digest = source_hash(english_source(value))
        for row in field_rows:
            if row.source_hash == digest:
                continue
            if row.state != "outdated":
                ContentTranslation.objects.filter(pk=row.pk).update(state="outdated")
            if isinstance(value, dict) and row.language in value and row.language not in MANUAL_LANGUAGES:
                value.pop(row.language, None)
                changed = True
    return changed


def load_translation_memory(languages=None):
    """Seed a ``(source_hash, language) -> text`` cache from stored translations.

    Reusing already-stored current/reviewed translations makes a re-run
    idempotent (no provider calls when nothing changed) and lets identical
    English sources share one translation.
    """
    from .models import ContentTranslation

    wanted = set(target_languages(languages))
    memory = {}
    rows = ContentTranslation.objects.filter(
        state__in=("current", "reviewed"), language__in=wanted
    ).exclude(text="").values_list("source_hash", "language", "text")
    for digest, language, text in rows:
        memory[(digest, language)] = text
    return memory


def prime_translation_memory(objects, provider, languages=None,
                             states=("missing", "outdated"), memory=None, batch_size=50):
    """Batch-translate every unique missing source once, filling ``memory``.

    Unique ``(source_hash, language)`` pairs are grouped by language and sent to
    the provider in batches, so the provider is called the minimum number of
    times for the deduplicated character volume. A batch failure is contained:
    those pairs simply stay absent and fall back to English. Returns the shared
    ``memory`` cache and a stats dict (requests / translated / failed / chars).
    """
    from .translation_providers import TranslationError

    if memory is None:
        memory = load_translation_memory(languages)
    wanted = set(states)
    pending = {}
    for obj in objects:
        for item in plan(obj, languages):
            if item["state"] not in wanted or not item["source"]:
                continue
            key = (item["hash"], item["language"])
            if key in memory or key in pending:
                continue
            pending[key] = item["source"]
    by_language = {}
    for (digest, language), source in pending.items():
        by_language.setdefault(language, []).append((digest, source))
    stats = {"requests": 0, "translated": 0, "failed": 0, "chars": 0}
    for language, entries in by_language.items():
        for start in range(0, len(entries), batch_size):
            chunk = entries[start:start + batch_size]
            try:
                results = provider.translate_batch([src for _, src in chunk], language, SOURCE_LANGUAGE)
                stats["requests"] += 1
            except TranslationError:
                stats["failed"] += len(chunk)
                continue
            for (digest, source), text in zip(chunk, results):
                if text:
                    memory[(digest, language)] = text
                    stats["translated"] += 1
                    stats["chars"] += len(source)
    return memory, stats


def backfill(queryset, provider=None, languages=None, states=("missing", "outdated"),
             limit=None, memory=None, batch_size=50):
    """Translate many objects; only missing/outdated by default.

    A shared translation-memory cache deduplicates identical English sources
    across the whole queryset, so the provider only ever sees the minimum
    unique character volume. Objects are first primed with one batched pass,
    then each object is filled from the cache without further provider calls.
    """
    from .translation_providers import get_provider

    provider = provider or get_provider()
    objects = list(queryset[:limit]) if limit else list(queryset)
    if memory is None:
        memory = load_translation_memory(languages)
    memory, prime_stats = prime_translation_memory(
        objects, provider, languages=languages, states=states,
        memory=memory, batch_size=batch_size,
    )
    totals = {"objects": 0, "translated": 0, "reused": 0, "skipped": 0, "failed": 0,
              "requests": prime_stats["requests"], "chars": prime_stats["chars"]}
    for obj in objects:
        summary = translate_object(
            obj, provider=provider, languages=languages, states=states, memory=memory
        )
        totals["objects"] += 1
        for key in ("translated", "reused", "skipped", "failed"):
            totals[key] += summary[key]
    return totals


def pending_summary(languages=None):
    """Count states across published models and tools without calling any API.

    ``missing`` means an English source exists but has no current translation;
    ``not_applicable`` means the field has no English source to translate.
    """
    from .models import ModelVersion, Tool

    totals = {"current": 0, "reviewed": 0, "outdated": 0, "missing": 0, "not_applicable": 0}
    for obj in ModelVersion.objects.filter(published=True, entry_type="model"):
        for item in plan(obj, languages):
            totals[item["state"]] += 1
    for obj in Tool.objects.filter(published=True):
        for item in plan(obj, languages):
            totals[item["state"]] += 1
    return totals
