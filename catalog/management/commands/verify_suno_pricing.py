from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import ModelVersion, Offer, Organization, PublicationRevision, ResearchRecord, Service, Source


SOURCE_URL = "https://suno.com/pricing"
CHECKED = date(2026, 9, 19)
PLANS = (
    ("AI-0193", "Free", "0", {"ru": "50 кредитов в день; без коммерческих прав; ограничения выгрузок.",
                                  "en": "50 credits per day; no commercial rights; download limits."}),
    ("AI-0194", "Pro · annual", "8", {"ru": "Оплата за год; 2 500 кредитов и 20 скачиваний песен в месяц.",
                                          "en": "Billed annually; 2,500 credits and 20 song downloads per month."}),
    ("AI-0195", "Premier · annual", "24", {"ru": "Оплата за год; 10 000 кредитов и 60 скачиваний песен в месяц.",
                                              "en": "Billed annually; 10,000 credits and 60 song downloads per month."}),
)


class Command(BaseCommand):
    help = "Apply the independently reviewed official Suno subscription prices with publication history."

    @transaction.atomic
    def handle(self, *args, **options):
        model = ModelVersion.objects.filter(research_entity_id="model_e23f514e930621").first()
        if model is None:
            raise CommandError("Suno research entity has not been published.")
        source, _ = Source.objects.get_or_create(url=SOURCE_URL, defaults={"title": "Suno pricing", "publisher": "Suno"})
        provider, _ = Organization.objects.get_or_create(name="Suno", defaults={"source": source, "checked": CHECKED})
        service, _ = Service.objects.get_or_create(name="Suno · web", provider=provider, kind="web", url=SOURCE_URL,
                                                     defaults={"compute_location": "cloud"})
        before, after = [], []
        for record_id, plan, amount, conditions in PLANS:
            key = record_id + ":unit"
            offer = Offer.objects.filter(research_key=key).first()
            snapshot = None if offer is None else {"amount": str(offer.amount), "unit": offer.unit,
                                                     "conditions": offer.conditions, "active": offer.active}
            if offer is None:
                offer = Offer(research_key=key)
            offer.model, offer.service = model, service
            offer.amount, offer.unit, offer.billing_unit = amount, "month", ""
            offer.conditions, offer.source, offer.checked, offer.active = conditions, source, CHECKED, True
            offer.primary = offer.primary or not model.offers.filter(active=True, primary=True).exclude(pk=offer.pk).exists()
            offer.save()
            before.append({"record_id": record_id, "offer": snapshot})
            after.append({"record_id": record_id, "amount": str(offer.amount), "unit": offer.unit,
                          "conditions": offer.conditions, "source": SOURCE_URL, "checked": CHECKED.isoformat()})
        ResearchRecord.objects.filter(source_record_id__in=[item[0] for item in PLANS]).update(
            state="accepted", review_reason="official Suno pricing reviewed 2026-09-19")
        PublicationRevision.objects.create(entity_id=model.research_entity_id, model=model, action="verified_price_update",
            source_record_ids=[item[0] for item in PLANS], before={"offers": before}, after={"offers": after})
        self.stdout.write(self.style.SUCCESS("Verified Suno Free, Pro annual and Premier annual pricing."))
