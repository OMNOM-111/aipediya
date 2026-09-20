import json

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Offer, PublicationRevision
from catalog.public_text import public_text


class Command(BaseCommand):
    help = "Refresh only explicit public EN labels and retain an auditable before/after revision."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report candidates without writing data.")

    def handle(self, *args, **options):
        changes = []
        for offer in Offer.objects.select_related("model").order_by("pk"):
            conditions = dict(offer.conditions or {})
            ru = conditions.get("ru", "")
            translated = public_text(ru, "en")
            if translated == ru or conditions.get("en") == translated:
                continue
            changes.append((offer, conditions, translated))
        result = {"offers_changed": len(changes), "prices_touched": 0, "dry_run": options["dry_run"]}
        if options["dry_run"]:
            self.stdout.write(json.dumps(result, sort_keys=True))
            return
        revisions = 0
        with transaction.atomic():
            for offer, before_conditions, translated in changes:
                after_conditions = {**before_conditions, "en": translated}
                offer.conditions = after_conditions
                offer.save(update_fields=["conditions"])
                PublicationRevision.objects.create(
                    entity_id=offer.model.research_entity_id or f"model:{offer.model_id}",
                    model=offer.model,
                    action="localize_offer",
                    source_record_ids=[offer.research_key] if offer.research_key else [],
                    before={"offer_pk": offer.pk, "conditions": before_conditions},
                    after={"offer_pk": offer.pk, "conditions": after_conditions},
                )
                revisions += 1
        result["revisions"] = revisions
        self.stdout.write(json.dumps(result, sort_keys=True))
