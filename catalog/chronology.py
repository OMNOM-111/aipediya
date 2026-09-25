"""Permanent catalogue numbers: assigned once per published entry, never changed.

A public number is a stable identity for every published Model / Tool, kept in
two independent sequences (Models, Tools). Existing numbers are preserved;
missing ones are filled deterministically (by name, then slug). Numbers are
never recomputed when a date, price, rating or sort changes — release-date
ordering is a separate, runtime concern.
"""
from django.db import transaction
from django.db.models import Max

from .comparison import alphabet


def _fill_numbers(objects, start, using, cls, revision_cls, revision_kwargs):
    ordered = sorted(objects, key=lambda o: (alphabet(o.name), o.slug))
    for offset, obj in enumerate(ordered, 1):
        number = start + offset
        cls.objects.using(using).filter(pk=obj.pk).update(public_number=number)
        obj.public_number = number
        revision_cls.objects.using(using).create(
            action="assign_catalog_number", before={"public_number": None},
            after={"public_number": number, "identity": obj.slug}, **revision_kwargs(obj))
    return len(ordered)


def assign_catalog_numbers(using="default"):
    """Give every published model a permanent number, preserving existing ones."""
    from .models import ModelVersion, PublicationRevision
    with transaction.atomic(using=using):
        unnumbered = list(
            ModelVersion.objects.using(using).select_for_update()
            .filter(entry_type="model", published=True, public_number__isnull=True)
        )
        if not unnumbered:
            return {"assigned": 0}
        start = ModelVersion.objects.using(using).filter(entry_type="model").aggregate(
            Max("public_number"))["public_number__max"] or 0
        assigned = _fill_numbers(
            unnumbered, start, using, ModelVersion, PublicationRevision,
            lambda m: {"model": m, "entity_id": m.research_entity_id or m.slug})
        return {"assigned": assigned}


def assign_tool_numbers(using="default"):
    """Give every published tool a permanent number, preserving existing ones."""
    from .models import Tool, ToolPublicationRevision
    with transaction.atomic(using=using):
        unnumbered = list(
            Tool.objects.using(using).select_for_update()
            .filter(published=True, public_number__isnull=True)
        )
        if not unnumbered:
            return {"assigned": 0}
        start = Tool.objects.using(using).aggregate(
            Max("public_number"))["public_number__max"] or 0
        assigned = _fill_numbers(
            unnumbered, start, using, Tool, ToolPublicationRevision, lambda t: {"tool": t})
        return {"assigned": assigned}


# Backward-compatible names: behaviour is now assign-missing (stable), not a
# date-based renumber (see docs/DECISIONS.md D-2026-09-23-permanent-catalog-numbers).
renumber_chronologically = assign_catalog_numbers
renumber_tools_chronologically = assign_tool_numbers
