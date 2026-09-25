"""Revert the Local public catalog to the original 304 models.

Models numbered 305+ (the later expansion) are moved to an internal research
layer: published=False so they leave the public table / count / sitemap, while
ALL their data, translations, links, evidence and history stay in the database.
Their public_number is kept as provisional/internal (no renumbering). The
original 1-304 stay published with their existing numbers. Tools are untouched.
Dry-run by default; pass --apply to write. Local only; never Production.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import ModelVersion, PublicationRevision


class Command(BaseCommand):
    help = "Keep only the original 304 public models; hide 305+ in the research layer."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes (default dry-run).")

    def handle(self, apply=False, **opts):
        expansion = list(ModelVersion.objects.filter(
            entry_type="model", published=True, public_number__gt=304))
        with transaction.atomic():
            if apply:
                for m in expansion:
                    PublicationRevision.objects.create(
                        model=m, entity_id=m.research_entity_id or m.slug,
                        action="move_to_research_layer",
                        before={"published": True, "public_number": m.public_number},
                        after={"published": False, "public_number": m.public_number,
                               "reason": "revert to original 304; 305+ provisional/internal"})
                ModelVersion.objects.filter(pk__in=[m.pk for m in expansion]).update(published=False)
        core = ModelVersion.objects.filter(entry_type="model", published=True)
        self.stdout.write("apply=%s | hidden(305+)=%d | remaining public models=%d | max public num=%s"
                          % (apply, len(expansion), core.count(),
                             core.order_by("-public_number").values_list("public_number", flat=True).first()))
