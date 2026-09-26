"""Catalogue numbers of published entries.

Owner rule 2026-09-26 (D-2026-09-26-catalog-master-package): Public Number is
the chronological position of a *public, dated* record; Models and Tools are
numbered independently; the hidden reserve and undated records have no number.
The chronological plan is computed in the catalog master and applied by
``catalog_master sync-local``. The helpers below only give a provisional next
number to a newly published *dated* record between two syncs.

Identity is the slug (Record ID), never the number. Existing numbers are
preserved here; missing ones of dated records are filled deterministically (by
name, then slug). Sorting and filtering never recompute numbers.
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
            .exclude(released__isnull=True, approx_released__isnull=True)
        )
        if not unnumbered:
            return {"assigned": 0}
        # public_number is unique across the whole table (legacy tool rows too)
        start = ModelVersion.objects.using(using).aggregate(
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
            .exclude(released__isnull=True, approx_released__isnull=True)
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
