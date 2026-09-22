from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from django.db import migrations


PAYLOAD = Path(__file__).with_name("data") / "global_catalog_20260922.json"
PAYLOAD_SHA256 = "5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2"


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def digest(values):
    text = "\n".join(sorted(canonical(value) for value in values))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_counts(models, using):
    return {
        "catalog_source": models["Source"].objects.using(using).count(),
        "catalog_organization": models["Organization"].objects.using(using).count(),
        "catalog_modelfamily": models["ModelFamily"].objects.using(using).count(),
        "catalog_modelversion": models["ModelVersion"].objects.using(using).count(),
        "catalog_tool": models["Tool"].objects.using(using).count(),
        "catalog_service": models["Service"].objects.using(using).count(),
        "catalog_access": models["Access"].objects.using(using).count(),
        "catalog_offer": models["Offer"].objects.using(using).count(),
        "catalog_evaluation": models["Evaluation"].objects.using(using).count(),
        "catalog_researchrecord": models["ResearchRecord"].objects.using(using).count(),
        "catalog_researchrevision": models["ResearchRevision"].objects.using(using).count(),
        "catalog_revision": models["Revision"].objects.using(using).count(),
        "catalog_publicationrevision": models["PublicationRevision"].objects.using(using).count(),
        "catalog_toolpublicationrevision": models["ToolPublicationRevision"].objects.using(using).count(),
    }


def get_models(apps):
    names = [
        "Access",
        "Benchmark",
        "Country",
        "Evaluation",
        "Fact",
        "ModelFamily",
        "ModelOriginCountry",
        "ModelVersion",
        "Offer",
        "Organization",
        "Platform",
        "PublicationRevision",
        "ResearchRecord",
        "ResearchRevision",
        "Revision",
        "Service",
        "Source",
        "Tool",
        "ToolModelSupport",
        "ToolPlatform",
        "ToolPublicationRevision",
    ]
    return {name: apps.get_model("catalog", name) for name in names}


def check_baseline(models, payload, using):
    counts = current_counts(models, using)
    if counts["catalog_modelversion"] == 0 and counts["catalog_researchrecord"] == 0:
        return "empty"
    expected = payload["expected"]
    if (
        counts["catalog_modelversion"] == expected["model_versions_total"]
        and counts["catalog_tool"] == expected["tools_published"]
        and counts["catalog_offer"] == expected["offers"]
        and counts["catalog_access"] == expected["accesses"]
        and counts["catalog_evaluation"] == expected["evaluations"]
        and counts["catalog_source"] == expected["sources"]
        and counts["catalog_researchrecord"] == expected["research_records"]
    ):
        return "desired"
    if counts != payload["guard"]["counts"]:
        raise RuntimeError(
            "Production baseline counts do not match the authorized catalog release: "
            + canonical(counts)
        )
    checks = {
        "model_slugs_sha256": digest(
            models["ModelVersion"].objects.using(using).values_list("slug", flat=True)
        ),
        "tool_slugs_sha256": digest(
            models["Tool"].objects.using(using).values_list("slug", flat=True)
        ),
        "source_urls_sha256": digest(
            models["Source"].objects.using(using).values_list("url", flat=True)
        ),
        "offer_keys_sha256": digest(
            models["Offer"].objects.using(using).values_list("research_key", flat=True)
        ),
        "research_external_ids_sha256": digest(
            models["ResearchRecord"].objects.using(using).values_list(
                "external_id", flat=True
            )
        ),
    }
    for key, actual in checks.items():
        if actual != payload["guard"][key]:
            raise RuntimeError(f"Production baseline fingerprint mismatch: {key}")
    return "baseline"


def service_key(provider, name, kind, url, compute_location):
    return digest([[provider, name, kind, url, compute_location]])


def benchmark_key(name, protocol):
    return digest([[name, protocol]])


def set_created(model, using, pk, field, value):
    model.objects.using(using).filter(pk=pk).update(
        **{field: datetime.fromisoformat(value)}
    )


def apply_catalog(apps, schema_editor):
    raw = PAYLOAD.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise RuntimeError("Catalog data payload digest mismatch")
    payload = json.loads(raw)
    if payload.get("format") != "aipedia-natural-catalog-v1":
        raise RuntimeError("Unsupported catalog data payload")
    using = schema_editor.connection.alias
    models = get_models(apps)
    state = check_baseline(models, payload, using)
    if state in {"empty", "desired"}:
        return

    Source = models["Source"]
    Organization = models["Organization"]
    ModelFamily = models["ModelFamily"]
    ModelVersion = models["ModelVersion"]
    Country = models["Country"]
    Platform = models["Platform"]
    Tool = models["Tool"]
    Service = models["Service"]
    Access = models["Access"]
    Offer = models["Offer"]
    Benchmark = models["Benchmark"]
    Evaluation = models["Evaluation"]
    Fact = models["Fact"]
    ModelOriginCountry = models["ModelOriginCountry"]
    ToolPlatform = models["ToolPlatform"]
    ToolModelSupport = models["ToolModelSupport"]
    ResearchRecord = models["ResearchRecord"]
    PublicationRevision = models["PublicationRevision"]
    ToolPublicationRevision = models["ToolPublicationRevision"]
    ResearchRevision = models["ResearchRevision"]
    Revision = models["Revision"]

    source_map = {}
    for row in payload["sources"]:
        item, _ = Source.objects.using(using).update_or_create(
            url=row["url"],
            defaults={"title": row["title"], "publisher": row["publisher"]},
        )
        source_map[row["url"]] = item

    organization_map = {}
    for row in payload["organizations"]:
        item, _ = Organization.objects.using(using).update_or_create(
            name=row["name"],
            defaults={
                "country": row["country"],
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
            },
        )
        organization_map[row["name"]] = item

    family_map = {}
    for row in payload["families"]:
        item, _ = ModelFamily.objects.using(using).get_or_create(
            name=row["name"], developer=organization_map[row["developer"]]
        )
        family_map[(row["developer"], row["name"])] = item

    ModelVersion.objects.using(using).update(public_number=None)
    model_map = {}
    model_numbers = {}
    for row in payload["models"]:
        number = row["public_number"]
        defaults = {
            key: row[key]
            for key in [
                "name",
                "version",
                "category",
                "tasks",
                "description",
                "suitable",
                "limitations",
                "origin",
                "philosophy",
                "context",
                "released",
                "release_evidence",
                "license",
                "open_weights",
                "checked",
                "published",
                "catalog_status",
                "entry_type",
                "input_modalities",
                "output_modalities",
                "translations_need_review",
                "research_entity_id",
            ]
        }
        defaults.update(
            family=family_map[(row["developer"], row["family_name"])],
            source=source_map[row["source_url"]],
            public_number=None,
        )
        item, _ = ModelVersion.objects.using(using).update_or_create(
            slug=row["slug"], defaults=defaults
        )
        model_map[row["slug"]] = item
        model_numbers[row["slug"]] = number

    for row in payload["countries"]:
        Country.objects.using(using).update_or_create(
            code=row["code"],
            defaults={"name_ru": row["name_ru"], "name_en": row["name_en"]},
        )
    platform_map = {}
    for row in payload["platforms"]:
        item, _ = Platform.objects.using(using).update_or_create(
            code=row["code"],
            defaults={"labels": row["labels"], "position": row["position"]},
        )
        platform_map[row["code"]] = item

    Tool.objects.using(using).update(public_number=None)
    tool_map = {}
    tool_numbers = {}
    for row in payload["tools"]:
        defaults = {
            key: row[key]
            for key in [
                "name",
                "version",
                "category",
                "purposes",
                "description",
                "ecosystem",
                "local_execution",
                "official_url",
                "released",
                "release_evidence",
                "checked",
                "published",
                "catalog_status",
            ]
        }
        defaults.update(
            legacy_version=model_map.get(row["legacy_slug"]),
            developer=organization_map[row["developer"]],
            source=source_map[row["source_url"]],
            public_number=None,
        )
        item, _ = Tool.objects.using(using).update_or_create(
            slug=row["slug"], defaults=defaults
        )
        tool_map[row["slug"]] = item
        tool_numbers[row["slug"]] = row["public_number"]

    service_map = {}
    for row in payload["services"]:
        expected_key = service_key(
            row["provider"],
            row["name"],
            row["kind"],
            row["url"],
            row["compute_location"],
        )
        if expected_key != row["key"]:
            raise RuntimeError("Service natural key mismatch")
        lookup = {
            "provider": organization_map[row["provider"]],
            "name": row["name"],
            "kind": row["kind"],
            "url": row["url"],
            "compute_location": row["compute_location"],
        }
        item = Service.objects.using(using).filter(**lookup).first()
        if item is None:
            item = Service.objects.using(using).create(**lookup)
        service_map[row["key"]] = item

    for row in payload["accesses"]:
        Access.objects.using(using).update_or_create(
            model=model_map[row["model_slug"]],
            service=service_map[row["service_key"]],
            defaults={
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
            },
        )
    for row in payload["offers"]:
        Offer.objects.using(using).update_or_create(
            research_key=row["research_key"],
            defaults={
                "model": model_map[row["model_slug"]],
                "service": service_map[row["service_key"]],
                "source": source_map[row["source_url"]],
                "amount": Decimal(row["amount"]) if row["amount"] is not None else None,
                "unit": row["unit"],
                "conditions": row["conditions"],
                "checked": row["checked"],
                "active": row["active"],
                "primary": row["primary"],
                "billing_unit": row["billing_unit"],
            },
        )

    benchmark_map = {}
    for row in payload["benchmarks"]:
        expected_key = benchmark_key(row["name"], row["protocol"])
        if expected_key != row["key"]:
            raise RuntimeError("Benchmark natural key mismatch")
        item, _ = Benchmark.objects.using(using).update_or_create(
            name=row["name"],
            protocol=row["protocol"],
            defaults={
                "category": row["category"],
                "unit": row["unit"],
                "higher_is_better": row["higher_is_better"],
            },
        )
        benchmark_map[row["key"]] = item
    for row in payload["new_evaluations"]:
        Evaluation.objects.using(using).update_or_create(
            observation_key=row["observation_key"],
            defaults={
                "model": model_map[row["model_slug"]],
                "benchmark": benchmark_map[row["benchmark_key"]],
                "source": source_map[row["source_url"]],
                "score": Decimal(row["score"]),
                "evaluator": row["evaluator"],
                "independent": row["independent"],
                "public": row["public"],
                "measured": row["measured"],
                "conditions": row["conditions"],
                "checked": row["checked"],
                "configuration": row["configuration"],
                "source_model": row["source_model"],
                "source_record_id": row["source_record_id"],
                "snapshot": row["snapshot"],
                "source_sha256": row["source_sha256"],
                "result_kind": row["result_kind"],
                "confidence_low": Decimal(row["confidence_low"])
                if row["confidence_low"] is not None
                else None,
                "confidence_high": Decimal(row["confidence_high"])
                if row["confidence_high"] is not None
                else None,
            },
        )
    for row in payload["facts"]:
        Fact.objects.using(using).update_or_create(
            model=model_map[row["model_slug"]],
            key=row["key"],
            defaults={
                "value": row["value"],
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
            },
        )
    for row in payload["model_origins"]:
        ModelOriginCountry.objects.using(using).update_or_create(
            model=model_map[row["model_slug"]],
            country_id=row["country_code"],
            defaults={
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
                "position": row["position"],
            },
        )
    for row in payload["tool_platforms"]:
        ToolPlatform.objects.using(using).update_or_create(
            tool=tool_map[row["tool_slug"]],
            platform=platform_map[row["platform_code"]],
            defaults={
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
            },
        )
    for row in payload["tool_model_supports"]:
        ToolModelSupport.objects.using(using).update_or_create(
            tool=tool_map[row["tool_slug"]],
            model=model_map[row["model_slug"]],
            defaults={
                "source": source_map[row["source_url"]],
                "checked": row["checked"],
                "note": row["note"],
            },
        )

    research_map = {
        item.external_id: item
        for item in ResearchRecord.objects.using(using).all()
    }
    for row in payload["new_research_records"]:
        if row["external_id"] in research_map:
            raise RuntimeError("ResearchRecord already exists outside the baseline")
        item = ResearchRecord.objects.using(using).create(
            external_id=row["external_id"],
            source_record_id=row["source_record_id"],
            batch=row["batch"],
            payload=row["payload"],
            state=row["state"],
            review_reason=row["review_reason"],
        )
        set_created(ResearchRecord, using, item.pk, "imported_at", row["imported_at"])
        research_map[row["external_id"]] = item

    for row in payload["new_publication_revisions"]:
        item = PublicationRevision.objects.using(using).create(
            entity_id=row["entity_id"],
            model=model_map[row["model_slug"]],
            action=row["action"],
            source_record_ids=row["source_record_ids"],
            before=row["before"],
            after=row["after"],
        )
        set_created(PublicationRevision, using, item.pk, "created", row["created"])
    for row in payload["new_tool_publication_revisions"]:
        item = ToolPublicationRevision.objects.using(using).create(
            tool=tool_map[row["tool_slug"]],
            action=row["action"],
            before=row["before"],
            after=row["after"],
        )
        set_created(ToolPublicationRevision, using, item.pk, "created", row["created"])
    for row in payload["new_research_revisions"]:
        item = ResearchRevision.objects.using(using).create(
            record=research_map[row["record_external_id"]],
            batch=row["batch"],
            action=row["action"],
            before=row["before"],
            after=row["after"],
        )
        set_created(ResearchRevision, using, item.pk, "created", row["created"])
    for row in payload["new_revisions"]:
        item = Revision.objects.using(using).create(
            model=model_map[row["model_slug"]],
            entity=row["entity"],
            action=row["action"],
            snapshot=row["snapshot"],
        )
        set_created(Revision, using, item.pk, "created", row["created"])

    for slug, number in model_numbers.items():
        if number is not None:
            ModelVersion.objects.using(using).filter(slug=slug).update(public_number=number)
    for slug, number in tool_numbers.items():
        if number is not None:
            Tool.objects.using(using).filter(slug=slug).update(public_number=number)

    expected = payload["expected"]
    actual = {
        "models_published": ModelVersion.objects.using(using).filter(
            published=True, entry_type="model"
        ).count(),
        "tools_published": Tool.objects.using(using).filter(published=True).count(),
        "model_versions_total": ModelVersion.objects.using(using).count(),
        "offers": Offer.objects.using(using).count(),
        "accesses": Access.objects.using(using).count(),
        "evaluations": Evaluation.objects.using(using).count(),
        "sources": Source.objects.using(using).count(),
        "research_records": ResearchRecord.objects.using(using).count(),
        "research_revisions": ResearchRevision.objects.using(using).count(),
        "revisions": Revision.objects.using(using).count(),
        "publication_revisions": PublicationRevision.objects.using(using).count(),
        "tool_publication_revisions": ToolPublicationRevision.objects.using(using).count(),
    }
    if actual != expected:
        raise RuntimeError("Catalog release count mismatch: " + canonical(actual))
    if digest(ModelVersion.objects.using(using).values_list("slug", flat=True)) != digest(
        row["slug"] for row in payload["models"]
    ):
        raise RuntimeError("Catalog model identity mismatch after import")
    if digest(Tool.objects.using(using).values_list("slug", flat=True)) != digest(
        row["slug"] for row in payload["tools"]
    ):
        raise RuntimeError("Catalog tool identity mismatch after import")


def reverse_noop(apps, schema_editor):
    # Production backups are the rollback authority. Deleting imported entities
    # would also delete their preserved provenance and is intentionally forbidden.
    pass


class Migration(migrations.Migration):
    atomic = True

    dependencies = [("catalog", "0013_normalize_generic_platforms")]

    operations = [migrations.RunPython(apply_catalog, reverse_noop)]
