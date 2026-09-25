"""Single publicity policy and per-locale SEO readiness registry.

Every public channel (pages, hreflang, sitemap, hubs, datasets, IndexNow
notifications) asks this module which records are public and which
entity x locale addresses are indexable. It reads only the database contract
that the release process already maintains: ``published`` (synchronized from
the catalog master through ``data/release_state.json``), the localized JSON
fields and their ``ContentTranslation`` provenance rows. It never reads the
master XLSX, never promotes a record, and never triggers a translation.

Results per entity x locale:

* ``indexable``  - public, primary localized text present and current.
* ``not-ready``  - public, but the locale's primary text is missing/outdated
  (page still renders for people, with ``noindex``; excluded from sitemap and
  hreflang).
* ``not-public`` - unpublished / not a catalog entry: 404 everywhere.

Primary text = ``description`` plus, when an English source exists,
``suitable`` and ``limitations``. Secondary prose (origin, philosophy and the
editorial evaluation-gap notes) may fall back to English, is marked
``lang="en"`` in HTML, and does not block indexing. A field whose English
source is empty is "not applicable", never a missing translation.
"""
from dataclasses import dataclass

from .i18n import DEFAULT_LANG, SUPPORTED_CODES
from .models import ContentTranslation, ModelVersion, Tool
from .translation_pipeline import MANUAL_LANGUAGES, english_source, source_hash

INDEXABLE = "indexable"
NOT_READY = "not-ready"
NOT_PUBLIC = "not-public"

MODEL_PRIMARY = ("description", "suitable", "limitations")
TOOL_PRIMARY = ("description",)
CURRENT_STATES = frozenset({"current", "reviewed"})


def public_models():
    return ModelVersion.objects.filter(published=True, entry_type="model")


def public_tools():
    return Tool.objects.filter(published=True)


def is_public_slug(kind, slug):
    manager = public_tools() if kind == "tool" else public_models()
    return manager.filter(slug=slug).exists()


@dataclass(frozen=True)
class Readiness:
    status: str
    reason: str

    @property
    def indexable(self):
        return self.status == INDEXABLE


def _entity_type(obj):
    return "tool" if isinstance(obj, Tool) else "model"


def _is_public(obj):
    if isinstance(obj, Tool):
        return bool(obj.published)
    return bool(obj.published) and obj.entry_type == "model"


def evaluate(obj, lang, rows):
    """Readiness of one entity in one locale.

    ``rows`` maps ``(field, language) -> (source_hash, state, has_text)`` for
    this entity's ContentTranslation rows.
    """
    if not _is_public(obj):
        return Readiness(NOT_PUBLIC, "unpublished" if not obj.published else "not-a-catalog-model")
    fields = TOOL_PRIMARY if isinstance(obj, Tool) else MODEL_PRIMARY
    source = english_source(getattr(obj, "description", None))
    if not source:
        return Readiness(NOT_READY, "no-english-primary-description")
    for field in fields:
        value = getattr(obj, field, None) or {}
        english = english_source(value)
        if not english:
            if field == "description":
                return Readiness(NOT_READY, "no-english-primary-description")
            continue  # not applicable: nothing to translate
        if lang == DEFAULT_LANG:
            continue
        text = (value.get(lang) or "").strip() if isinstance(value, dict) else ""
        if lang in MANUAL_LANGUAGES:
            if not text:
                return Readiness(NOT_READY, f"missing-manual-{field}")
            continue
        row = rows.get((field, lang))
        if not text or row is None:
            return Readiness(NOT_READY, f"missing-translation-{field}")
        digest, state, has_text = row
        if digest != source_hash(english) or state not in CURRENT_STATES or not has_text:
            return Readiness(NOT_READY, f"outdated-translation-{field}")
    return Readiness(INDEXABLE, "primary-text-current")


def _rows_for(entity_type, ids):
    table = {}
    qs = ContentTranslation.objects.filter(entity_type=entity_type, object_id__in=ids).values_list(
        "object_id", "field", "language", "source_hash", "state", "text"
    )
    for object_id, field, language, digest, state, text in qs:
        table.setdefault(object_id, {})[(field, language)] = (digest, state, bool(text))
    return table


def entity_readiness(obj):
    """``{lang: Readiness}`` for one entity across all 22 locales."""
    rows = _rows_for(_entity_type(obj), [obj.pk]).get(obj.pk, {})
    return {lang: evaluate(obj, lang, rows) for lang in SUPPORTED_CODES}


def ready_locales(obj):
    return [lang for lang, result in entity_readiness(obj).items() if result.indexable]


def registry(include_hidden=True):
    """Yield one row per entity x locale for every model row and tool.

    Hidden rows are included (as ``not-public``) so the registry proves they
    are excluded; their text is never emitted.
    """
    models = ModelVersion.objects.filter(entry_type="model").only(
        "pk", "slug", "published", "entry_type", "description", "suitable", "limitations", "checked"
    )
    tools = Tool.objects.only("pk", "slug", "published", "description", "checked")
    if not include_hidden:
        models = models.filter(published=True)
        tools = tools.filter(published=True)
    for kind, entity_type, objects in (("model", "model", list(models)), ("tool", "tool", list(tools))):
        rows = _rows_for(entity_type, [obj.pk for obj in objects])
        for obj in objects:
            for lang in SUPPORTED_CODES:
                result = evaluate(obj, lang, rows.get(obj.pk, {}))
                yield {
                    "kind": kind,
                    "slug": obj.slug,
                    "lang": lang,
                    "status": result.status,
                    "reason": result.reason,
                    "checked": obj.checked,
                }


def summarize(rows):
    from collections import Counter

    status = Counter()
    reasons = Counter()
    per_lang = {}
    for row in rows:
        key = (row["kind"], row["status"])
        status[key] += 1
        reasons[(row["kind"], row["status"], row["reason"])] += 1
        bucket = per_lang.setdefault(row["lang"], Counter())
        bucket[(row["kind"], row["status"])] += 1
    return {
        "by_status": {f"{kind}:{state}": count for (kind, state), count in sorted(status.items())},
        "by_reason": {f"{kind}:{state}:{reason}": count for (kind, state, reason), count in sorted(reasons.items())},
        "by_locale": {
            lang: {f"{kind}:{state}": count for (kind, state), count in sorted(counter.items())}
            for lang, counter in per_lang.items()
        },
    }
