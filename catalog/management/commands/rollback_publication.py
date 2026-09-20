from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal
from datetime import date

from catalog.models import Offer, PublicationRevision, ResearchRecord


class Command(BaseCommand):
    help = "Reverse one public research promotion without deleting its audit trail."

    def add_arguments(self, parser):
        parser.add_argument("revision_id", type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        revision = PublicationRevision.objects.select_for_update().filter(pk=options["revision_id"]).first()
        if revision is None:
            raise CommandError("Unknown publication revision.")
        model = revision.model
        before = revision.before if isinstance(revision.before, dict) else {}
        after = revision.after if isinstance(revision.after, dict) else {}
        for key in after.get("new_offer_keys", []):
            Offer.objects.filter(model=model, research_key=key).update(active=False, primary=False)
        if revision.action in {"update", "verified_price_update"}:
            for item in before.get("offers", []):
                snapshot = item.get("offer", item)
                key = snapshot.get("research_key") if isinstance(snapshot, dict) else None
                if not key:
                    key = item.get("record_id", "") + ":unit"
                offer = Offer.objects.filter(model=model, research_key=key).first()
                if offer is None:
                    continue
                if snapshot is None:
                    offer.active = False
                    offer.primary = False
                    offer.save(update_fields=["active", "primary"])
                    continue
                offer.amount = Decimal(snapshot["amount"])
                offer.unit = snapshot["unit"]
                offer.billing_unit = snapshot.get("billing_unit", "")
                offer.conditions = snapshot["conditions"]
                offer.checked = date.fromisoformat(snapshot["checked"])
                offer.save(update_fields=["amount", "unit", "billing_unit", "conditions", "checked"])
        if revision.action in {"create", "republish"}:
            model.published = False
            model.save(update_fields=["published"])
        elif revision.action == "link":
            model.research_entity_id = before.get("research_entity_id")
            model.published = before.get("published", model.published)
            model.save(update_fields=["research_entity_id", "published"])
        ResearchRecord.objects.filter(source_record_id__in=revision.source_record_ids, state="accepted").update(
            state="review_required", review_reason="publication rollback " + str(revision.pk))
        PublicationRevision.objects.create(entity_id=revision.entity_id, model=model, action="rollback",
            source_record_ids=revision.source_record_ids, before=after,
            after={"published": model.published, "research_entity_id": model.research_entity_id})
        self.stdout.write(f"Rolled back publication {revision.entity_id}.")
