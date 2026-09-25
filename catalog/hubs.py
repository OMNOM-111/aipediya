"""Finite registry of intent-based collections (GSD-09).

This is not a filter-combination generator: each collection is written out
here with an explicit, deterministic inclusion rule over *published* records
(through :mod:`catalog.readiness`). A collection is indexable in a locale only
when it has at least ``MIN_ENTRIES`` records and all of its text is localized.
"""
from dataclasses import dataclass

from django.db.models import Q

from . import readiness
from .static_pages import labels_ready, page_ready

MIN_ENTRIES = 5
HUB_LABELS = ("collections", "criterion", "entries_count")


@dataclass(frozen=True)
class Hub:
    slug: str
    kind: str  # "model" | "tool"
    rule: Q
    sort: str = "release_desc"

    @property
    def page(self):
        return f"hub:{self.slug}"


HUBS = {hub.slug: hub for hub in (
    Hub("coding-models", "model", Q(tasks__icontains='"code"') | Q(tasks__icontains='"coding"')),
    Hub("video-models", "model", Q(category="video")),
    Hub("music-models", "model", Q(tasks__icontains='"music"')),
    Hub("free-tier-models", "model", Q(offers__active=True, offers__amount=0)),
    Hub("api-models", "model", Q(accesses__service__kind="api")),
    Hub("open-weight-models", "model", Q(open_weights=True)),
    Hub("models-from-china", "model", Q(origin_country_links__country__code="CN")),
    Hub("models-released-2025", "model", Q(released__year=2025), sort="release_asc"),
    Hub("long-context-models", "model", Q(context__gte=1_000_000)),
    Hub("coding-tools", "tool", Q(category__in=("coding_assistant", "coding_agent", "ide_tool"))),
)}


def members(hub):
    """Primary keys of the published records in a collection (deterministic)."""
    base = readiness.public_tools() if hub.kind == "tool" else readiness.public_models()
    return list(base.filter(hub.rule).order_by("pk").values_list("pk", flat=True).distinct())


def status(hub, lang, count=None):
    """``(state, reason)`` for one collection in one locale."""
    count = len(members(hub)) if count is None else count
    if count == 0:
        return readiness.NOT_READY, "empty"
    if count < MIN_ENTRIES:
        return readiness.NOT_READY, f"thin:{count}<{MIN_ENTRIES}"
    if not page_ready(hub.page, lang) or not labels_ready(HUB_LABELS, lang):
        return readiness.NOT_READY, "text-not-localized"
    return readiness.INDEXABLE, f"{count}-records"


def ready_locales(hub, count=None):
    from .i18n import SUPPORTED_CODES

    count = len(members(hub)) if count is None else count
    return [lang for lang in SUPPORTED_CODES if status(hub, lang, count)[0] == readiness.INDEXABLE]


def listed_hubs(lang):
    """Collections shown in navigation for a locale: only indexable ones."""
    result = []
    for hub in HUBS.values():
        count = len(members(hub))
        if status(hub, lang, count)[0] == readiness.INDEXABLE:
            result.append((hub, count))
    return result
