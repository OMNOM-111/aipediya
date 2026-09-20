from collections import defaultdict
from datetime import date
from decimal import Decimal
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (Access, Benchmark, Category, Evaluation, ModelFamily,
                            ModelVersion, Offer, Organization, PublicationRevision,
                            ResearchRecord, Service, Source)
from catalog.public_text import PUBLIC_ENGLISH
from catalog.research import ResearchError, read_document


TASK_CATEGORY = {
    "image_generation": "image", "image_editing": "image", "vision": "image", "ocr": "image",
    "video_generation": "video", "video_editing": "video", "video_understanding": "video",
    "speech": "audio", "audio_processing": "audio", "music": "audio", "sound_effects": "audio",
}
INTERFACE_KIND = {
    "API": "api", "web": "web", "web-demo": "web", "Discord": "web",
    "desktop": "app", "mobile": "app", "CLI": "cli", "IDE": "ide", "local_runtime": "download",
}
PRICE_FIELDS = (("input_usd_per_million_tokens", "input", "input"),
                ("output_usd_per_million_tokens", "output", "output"),
                ("cached_input_usd_per_million_tokens", "cache_read", "cache_read"),
                ("cached_write_usd_per_million_tokens", "cache_write", "cache_write"))


def is_https(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def primary_category(tasks):
    for key in tasks:
        if key in TASK_CATEGORY:
            return TASK_CATEGORY[key]
    return "text" if any(key in {"text", "code", "reasoning", "translation", "agents"} for key in tasks) else "other"


def offer_unit(record):
    raw = (record.get("billing_unit") or "").strip()
    text = raw.casefold()
    if "1m" in text and ("character" in text or "символ" in text):
        return "million_characters", ""
    if "1000" in text and ("character" in text or "символ" in text):
        return "thousand_characters", ""
    if "month" in text or "\u043c\u0435\u0441\u044f\u0446" in text:
        return "month", ""
    if "hour" in text or "\u0447\u0430\u0441" in text:
        return "hour", ""
    if "megapixel" in text or "\u043c\u0435\u0433\u0430\u043f\u0438\u043a\u0441" in text:
        return "megapixel", ""
    if "image" in text or "\u0438\u0437\u043e\u0431\u0440\u0430\u0436" in text:
        return "image", ""
    if "second" in text or "\u0441\u0435\u043a\u0443\u043d\u0434" in text:
        return "second", ""
    if "minute" in text or "\u043c\u0438\u043d\u0443\u0442" in text:
        return "minute", ""
    if "request" in text or "запрос" in text:
        return "request", ""
    return "other", raw


class Command(BaseCommand):
    help = "Publish only research entities that pass the identity, source, access and date gate."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Validated research JSON package.")
        parser.add_argument("--dry-run", action="store_true", help="Report decisions without writing catalog data.")

    def handle(self, *args, **options):
        try:
            document = read_document(options["path"])
        except ResearchError as exc:
            raise CommandError(str(exc)) from exc
        entities = {item["entity_id"]: item for item in document.get("entities", [])}
        sources = {item["id"]: item for item in document.get("sources", [])}
        records = defaultdict(list)
        for record in document["records"]:
            records[record["entity_id"]].append(record)
        existing = {record.source_record_id: record for record in ResearchRecord.objects.all()}
        eligible, skipped = [], []
        for entity_id, entity in entities.items():
            rows = records.get(entity_id, [])
            reason = self._eligibility(entity, rows, sources, existing)
            (skipped if reason else eligible).append((entity_id, entity, rows, reason))
        result = {"entities": len(entities), "eligible": len(eligible), "skipped": len(skipped),
                  "published_models": sum(item[1]["entity_type"] == "model" for item in eligible),
                  "published_other_entries": sum(item[1]["entity_type"] != "model" for item in eligible),
                  "skipped_reasons": defaultdict(int), "dry_run": options["dry_run"]}
        for _, _, _, reason in skipped:
            result["skipped_reasons"][reason] += 1
        result["skipped_reasons"] = dict(result["skipped_reasons"])
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(str(result)))
            return
        with transaction.atomic():
            self._upsert_categories(document.get("taxonomy", []))
            for _, _, rows, reason in skipped:
                ResearchRecord.objects.filter(source_record_id__in=[row["record_id"] for row in rows],
                                              state="review_required").update(review_reason=reason)
            created = linked = offers = evaluations = unchanged = 0
            for entity_id, entity, rows, _ in eligible:
                model, action, added_offers, added_evaluations = self._promote(entity_id, entity, rows, sources, document, existing)
                created += action == "create"
                linked += action == "link"
                offers += added_offers
                evaluations += added_evaluations
                unchanged += action == "unchanged"
            result.update(created=created, linked_existing=linked, offers_added=offers,
                          evaluations_added=evaluations, unchanged=unchanged)
        self.stdout.write(self.style.SUCCESS(str(result)))

    def _eligibility(self, entity, rows, sources, existing):
        if not rows or not isinstance(entity.get("name"), str) or not entity["name"].strip():
            return "missing_name"
        if not isinstance(entity.get("developer"), str) or not entity["developer"].strip():
            return "missing_developer"
        if not entity.get("categories"):
            return "missing_purpose"
        if not any(is_https(row.get("access_entry_url") or row.get("access_url")) for row in rows):
            return "missing_https_access"
        for row in rows:
            if not isinstance(row.get("checked_at"), str):
                return "missing_checked_date"
            try:
                date.fromisoformat(row["checked_at"])
            except ValueError:
                return "invalid_checked_date"
            if not row.get("source_ids") or not all(source_id in sources and is_https(sources[source_id].get("url")) for source_id in row.get("source_ids", [])):
                return "invalid_source"
            staged = existing.get(row["record_id"])
            if staged is None or staged.state not in {"review_required", "accepted"}:
                return "staging_record_missing"
        return ""

    def _upsert_categories(self, taxonomy):
        for position, item in enumerate(taxonomy):
            code = item.get("id")
            if not isinstance(code, str) or not code:
                continue
            Category.objects.update_or_create(code=code, defaults={
                "position": position,
                "labels": {"ru": item.get("label_ru", code), "en": item.get("label_en", code)},
            })

    def _source(self, source_data, checked):
        return Source.objects.get_or_create(url=source_data["url"], defaults={
            "title": source_data.get("title", source_data["url"])[:200],
            "publisher": source_data.get("title", "Source")[:120],
        })[0]

    def _promote(self, entity_id, entity, rows, sources, document, existing):
        source_ids = [source_id for row in rows for source_id in row.get("source_ids", []) if source_id in sources]
        source_data = sources[source_ids[0]]
        checked = max(date.fromisoformat(row["checked_at"]) for row in rows)
        source = self._source(source_data, checked)
        developer, _ = Organization.objects.get_or_create(name=entity["developer"], defaults={"source": source, "checked": checked})
        family, _ = ModelFamily.objects.get_or_create(name=entity["name"][:120], developer=developer)
        model = ModelVersion.objects.filter(research_entity_id=entity_id).first()
        action = "unchanged"
        before = {}
        if model is None:
            model = ModelVersion.objects.filter(name=entity["name"], family__developer__name=developer.name).first()
        if model is None:
            base = slugify(entity["name"])[:42] or "entry"
            slug = base + "-" + entity_id[-8:]
            model = ModelVersion.objects.create(
                family=family, name=entity["name"][:140], slug=slug,
                version=(rows[0].get("normalized_api_id") or entity["name"])[:150],
                category=primary_category(entity["categories"]), tasks=entity["categories"],
                description={"ru": entity.get("description_ru") or "", "en": entity.get("description_en") or ""},
                license=(entity.get("license") or "")[:200], source=source, checked=checked,
                published=True, entry_type={"service": "api_service"}.get(entity["entity_type"], entity["entity_type"]),
                input_modalities=entity.get("input_modalities_confirmed_subset") or [],
                output_modalities=entity.get("output_modalities_confirmed_subset") or [],
                open_weights=any(row.get("execution_location") == "local" for row in rows), research_entity_id=entity_id,
            )
            action = "create"
        elif not model.research_entity_id:
            before = {"research_entity_id": None, "published": model.published}
            model.research_entity_id = entity_id
            model.save(update_fields=["research_entity_id"])
            action = "link"
        elif not model.published:
            before = {"published": False, "research_entity_id": model.research_entity_id}
            model.published = True
            model.save(update_fields=["published"])
            action = "republish"
        if any(row.get("execution_location") == "local" for row in rows) and not model.open_weights:
            before.setdefault("open_weights", False)
            model.open_weights = True
            model.save(update_fields=["open_weights"])
            action = "update" if action == "unchanged" else action
        offer_keys_before = set(model.offers.filter(research_key__isnull=False).values_list("research_key", flat=True))
        added_offers, added_evaluations, offer_changes = self._offers_and_evaluations(model, rows, sources, document)
        if offer_changes and action == "unchanged":
            action = "update"
            before["offers"] = [change["before"] for change in offer_changes]
        record_ids = [row["record_id"] for row in rows]
        if action != "unchanged" or added_offers or added_evaluations:
            PublicationRevision.objects.create(entity_id=entity_id, model=model, action=action,
                source_record_ids=record_ids, before=before,
                after={"published": model.published, "research_entity_id": model.research_entity_id,
                       "offers": list(model.offers.filter(research_key__isnull=False).values_list("research_key", flat=True)),
                       "new_offer_keys": sorted(set(model.offers.filter(research_key__isnull=False).values_list("research_key", flat=True)) - offer_keys_before),
                       "offer_updates": offer_changes})
        ResearchRecord.objects.filter(source_record_id__in=record_ids, state="review_required").update(
            state="accepted", review_reason="published after identity, source, access and date gate")
        return model, action, added_offers, added_evaluations

    def _offers_and_evaluations(self, model, rows, sources, document):
        offers_added = evaluations_added = 0
        offer_changes = []
        for row in rows:
            source_data = sources[row.get("price_source_id")] if row.get("price_source_id") in sources else sources[row["source_ids"][0]]
            checked = date.fromisoformat(row.get("price_verified_at") or row["checked_at"])
            source = self._source(source_data, checked)
            provider_name = (row.get("supplier") or row.get("developer"))[:120]
            provider, _ = Organization.objects.get_or_create(name=provider_name, defaults={"source": source, "checked": checked})
            url = row.get("access_entry_url") or row.get("access_url")
            interfaces = [item for item in row.get("interface_types", []) if item in INTERFACE_KIND] or ["web"]
            services = {}
            for interface in dict.fromkeys(interfaces):
                kind = INTERFACE_KIND[interface]
                service, service_created = Service.objects.get_or_create(
                    name=(provider_name + " · " + interface)[:150], provider=provider, kind=kind, url=url,
                    defaults={"compute_location": row.get("execution_location") or "cloud"},
                )
                location = row.get("execution_location") or "cloud"
                if not service_created and service.compute_location != location:
                    service.compute_location = location
                    service.save(update_fields=["compute_location"])
                Access.objects.get_or_create(model=model, service=service, defaults={"source": source, "checked": checked})
                services[interface] = service
            price_interface = "API" if row.get("billing_kind") == "usage" and "API" in services else None
            price_interface = price_interface or ("web" if "web" in services else interfaces[0])
            service = services[price_interface]
            if row.get("price_verification") != "published_rates_checked":
                continue
            conditions = self._conditions(row)
            for field, unit, suffix in PRICE_FIELDS:
                amount = row.get(field)
                if amount is not None:
                    offer, added = Offer.objects.get_or_create(research_key=row["record_id"] + ":" + suffix, defaults={
                        "model": model, "service": service, "amount": Decimal(str(amount)), "unit": unit,
                        "billing_unit": "", "conditions": conditions, "source": source, "checked": checked,
                        "active": True, "primary": not model.offers.filter(primary=True).exists(),
                    })
                    if not added:
                        change = self._sync_offer(offer, model, service, Decimal(str(amount)), unit, "", conditions, source, checked)
                        if change:
                            offer_changes.append(change)
                    offers_added += added
            amount = row.get("price_usd_per_unit")
            if amount is not None:
                unit, billing_unit = offer_unit(row)
                offer, added = Offer.objects.get_or_create(research_key=row["record_id"] + ":unit", defaults={
                    "model": model, "service": service, "amount": Decimal(str(amount)), "unit": unit,
                    "billing_unit": billing_unit, "conditions": conditions,
                    "source": source, "checked": checked, "active": True,
                    "primary": not model.offers.filter(primary=True).exists(),
                })
                if not added:
                    change = self._sync_offer(offer, model, service, Decimal(str(amount)), unit, billing_unit, conditions, source, checked)
                    if change:
                        offer_changes.append(change)
                offers_added += added
        for item in document.get("evaluations", []):
            if item.get("entity_id") != model.research_entity_id or item.get("evidence_type") != "independent_benchmark" or item.get("verification") != "source_result_checked":
                continue
            if not is_https(item.get("source_url")) or item.get("value") is None:
                continue
            source = Source.objects.get_or_create(url=item["source_url"], defaults={"title": item.get("metric", "Independent benchmark")[:200], "publisher": item.get("evaluator", "Evaluator")[:120]})[0]
            benchmark, _ = Benchmark.objects.get_or_create(name=item.get("metric", "Independent benchmark")[:150],
                protocol=(item.get("setting") or "default")[:250], defaults={"category": model.category, "unit": "points"})
            _, added = Evaluation.objects.get_or_create(model=model, benchmark=benchmark, defaults={
                "score": Decimal(str(item["value"])), "evaluator": item.get("evaluator", "Independent evaluator")[:140],
                "independent": True, "conditions": {"ru": item.get("scope_ru") or "", "en": "Independent benchmark result"},
                "source": source, "checked": date.fromisoformat(item["checked_at"]),
            })
            evaluations_added += added
        return offers_added, evaluations_added, offer_changes

    def _conditions(self, row):
        plan = (row.get("plan") or "").strip()
        detail = (row.get("conditions_ru") or "").strip()
        ru = " · ".join(part for part in (plan, detail) if part)
        if "annual" in plan.casefold() and "оплата за год" not in ru.casefold():
            ru = " · ".join(part for part in (plan, "Оплата за год") if part)
        en = PUBLIC_ENGLISH.get(plan, plan)
        if "annual" in plan.casefold():
            en = " · ".join(part for part in (plan, "Billed annually") if part)
        return {"ru": ru or plan or "Проверенный опубликованный тариф", "en": en or "Verified published rate"}

    def _sync_offer(self, offer, model, service, amount, unit, billing_unit, conditions, source, checked):
        before = {"research_key": offer.research_key, "amount": str(offer.amount), "unit": offer.unit,
                  "billing_unit": offer.billing_unit, "conditions": offer.conditions, "service": offer.service.name,
                  "checked": offer.checked.isoformat()}
        values = {"model": model, "service": service, "amount": amount, "unit": unit,
                  "billing_unit": billing_unit, "conditions": conditions, "source": source,
                  "checked": checked, "active": True}
        changed = [field for field, value in values.items() if getattr(offer, field) != value]
        if changed:
            for field, value in values.items():
                setattr(offer, field, value)
            if not offer.primary and not model.offers.filter(active=True, primary=True).exists():
                offer.primary = True
                changed.append("primary")
            offer.save(update_fields=changed)
            return {"before": before, "after": {"research_key": offer.research_key, "amount": str(offer.amount),
                    "unit": offer.unit, "billing_unit": offer.billing_unit, "conditions": offer.conditions,
                    "service": offer.service.name, "checked": offer.checked.isoformat()}}
        return None
