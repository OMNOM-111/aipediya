"""Export Local catalog data as a portable, natural-keyed release payload."""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest(values):
    payload = "\n".join(sorted(canonical(value) for value in values))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_json(value):
    return json.loads(value) if isinstance(value, str) else value


def service_key(provider, name, kind, url, compute_location):
    return digest([[provider, name, kind, url, compute_location]])


def benchmark_key(name, protocol):
    return digest([[name, protocol]])


def consume_new(local_rows, baseline_signatures, signature):
    remaining = Counter(baseline_signatures)
    result = []
    for row in local_rows:
        key = signature(row)
        if remaining[key]:
            remaining[key] -= 1
        else:
            result.append(row)
    if any(remaining.values()):
        raise RuntimeError("Local history is missing rows present in the Production baseline")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--desired", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    baseline_path = Path(args.baseline).resolve()
    desired_path = Path(args.desired).resolve()
    output_path = Path(args.output).resolve()

    os.environ["AIPEDIA_ENV"] = "local"
    os.environ["AIPEDIA_DB"] = str(desired_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
    import django

    django.setup()
    from catalog.models import (
        Access,
        Benchmark,
        Country,
        Evaluation,
        Fact,
        ModelFamily,
        ModelOriginCountry,
        ModelVersion,
        Offer,
        Organization,
        Platform,
        PublicationRevision,
        ResearchRecord,
        ResearchRevision,
        Revision,
        Service,
        Source,
        Tool,
        ToolModelSupport,
        ToolPlatform,
        ToolPublicationRevision,
    )

    baseline = sqlite3.connect(baseline_path.as_uri() + "?mode=ro", uri=True)
    baseline.row_factory = sqlite3.Row
    try:
        baseline_tables = {
            row[0]
            for row in baseline.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        guard_counts = {}
        for table in [
            "catalog_source",
            "catalog_organization",
            "catalog_modelfamily",
            "catalog_modelversion",
            "catalog_tool",
            "catalog_service",
            "catalog_access",
            "catalog_offer",
            "catalog_evaluation",
            "catalog_researchrecord",
            "catalog_researchrevision",
            "catalog_revision",
            "catalog_publicationrevision",
            "catalog_toolpublicationrevision",
        ]:
            guard_counts[table] = (
                baseline.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if table in baseline_tables
                else 0
            )

        baseline_model_slugs = [
            row[0]
            for row in baseline.execute("SELECT slug FROM catalog_modelversion")
        ]
        baseline_tool_slugs = [
            row[0] for row in baseline.execute("SELECT slug FROM catalog_tool")
        ]
        baseline_source_urls = [
            row[0] for row in baseline.execute("SELECT url FROM catalog_source")
        ]
        baseline_offer_keys = [
            row[0] for row in baseline.execute("SELECT research_key FROM catalog_offer")
        ]
        baseline_research_ids = [
            row[0] for row in baseline.execute("SELECT external_id FROM catalog_researchrecord")
        ]
        baseline_observation_keys = {
            row[0]
            for row in baseline.execute(
                "SELECT observation_key FROM catalog_evaluation WHERE observation_key IS NOT NULL"
            )
        }

        sources = [
            {"url": item.url, "title": item.title, "publisher": item.publisher}
            for item in Source.objects.order_by("url")
        ]
        organizations = [
            {
                "name": item.name,
                "country": item.country,
                "source_url": item.source.url,
                "checked": item.checked,
            }
            for item in Organization.objects.select_related("source").order_by("name")
        ]
        families = [
            {"name": item.name, "developer": item.developer.name}
            for item in ModelFamily.objects.select_related("developer").order_by(
                "developer__name", "name"
            )
        ]
        models = []
        for item in ModelVersion.objects.select_related(
            "family__developer", "source"
        ).order_by("slug"):
            models.append(
                {
                    "family_name": item.family.name,
                    "developer": item.family.developer.name,
                    "source_url": item.source.url,
                    "name": item.name,
                    "slug": item.slug,
                    "version": item.version,
                    "category": item.category,
                    "tasks": item.tasks,
                    "description": item.description,
                    "suitable": item.suitable,
                    "limitations": item.limitations,
                    "origin": item.origin,
                    "philosophy": item.philosophy,
                    "context": item.context,
                    "released": item.released,
                    "release_evidence": item.release_evidence,
                    "license": item.license,
                    "open_weights": item.open_weights,
                    "checked": item.checked,
                    "published": item.published,
                    "public_number": item.public_number,
                    "catalog_status": item.catalog_status,
                    "entry_type": item.entry_type,
                    "input_modalities": item.input_modalities,
                    "output_modalities": item.output_modalities,
                    "translations_need_review": item.translations_need_review,
                    "research_entity_id": item.research_entity_id,
                }
            )
        countries = list(
            Country.objects.order_by("code").values("code", "name_ru", "name_en")
        )
        platforms = list(
            Platform.objects.order_by("code").values("code", "labels", "position")
        )
        tools = []
        for item in Tool.objects.select_related(
            "legacy_version", "developer", "source"
        ).order_by("slug"):
            tools.append(
                {
                    "legacy_slug": item.legacy_version.slug if item.legacy_version else None,
                    "developer": item.developer.name,
                    "source_url": item.source.url,
                    "name": item.name,
                    "slug": item.slug,
                    "version": item.version,
                    "category": item.category,
                    "purposes": item.purposes,
                    "description": item.description,
                    "ecosystem": item.ecosystem,
                    "local_execution": item.local_execution,
                    "official_url": item.official_url,
                    "released": item.released,
                    "release_evidence": item.release_evidence,
                    "checked": item.checked,
                    "published": item.published,
                    "public_number": item.public_number,
                    "catalog_status": item.catalog_status,
                }
            )
        services = []
        service_keys = {}
        for item in Service.objects.select_related("provider").order_by("pk"):
            key = service_key(
                item.provider.name,
                item.name,
                item.kind,
                item.url,
                item.compute_location,
            )
            if key in service_keys:
                raise RuntimeError(f"Duplicate natural service key: {item.pk}")
            service_keys[item.pk] = key
            services.append(
                {
                    "key": key,
                    "provider": item.provider.name,
                    "name": item.name,
                    "kind": item.kind,
                    "url": item.url,
                    "compute_location": item.compute_location,
                }
            )
        accesses = [
            {
                "model_slug": item.model.slug,
                "service_key": service_keys[item.service_id],
                "source_url": item.source.url,
                "checked": item.checked,
            }
            for item in Access.objects.select_related("model", "source").order_by("pk")
        ]
        offers = []
        for item in Offer.objects.select_related("model", "source").order_by("research_key"):
            if not item.research_key:
                raise RuntimeError(f"Offer {item.pk} lacks the portable research_key")
            offers.append(
                {
                    "research_key": item.research_key,
                    "model_slug": item.model.slug,
                    "service_key": service_keys[item.service_id],
                    "source_url": item.source.url,
                    "amount": item.amount,
                    "unit": item.unit,
                    "conditions": item.conditions,
                    "checked": item.checked,
                    "active": item.active,
                    "primary": item.primary,
                    "billing_unit": item.billing_unit,
                }
            )
        benchmarks = []
        benchmark_keys = {}
        for item in Benchmark.objects.order_by("name", "protocol"):
            key = benchmark_key(item.name, item.protocol)
            benchmark_keys[item.pk] = key
            benchmarks.append(
                {
                    "key": key,
                    "name": item.name,
                    "protocol": item.protocol,
                    "category": item.category,
                    "unit": item.unit,
                    "higher_is_better": item.higher_is_better,
                }
            )
        new_evaluations = []
        for item in Evaluation.objects.exclude(observation_key__isnull=True).select_related(
            "model", "source"
        ).order_by("pk"):
            if item.observation_key in baseline_observation_keys:
                continue
            new_evaluations.append(
                {
                    "observation_key": item.observation_key,
                    "model_slug": item.model.slug,
                    "benchmark_key": benchmark_keys[item.benchmark_id],
                    "source_url": item.source.url,
                    "score": item.score,
                    "evaluator": item.evaluator,
                    "independent": item.independent,
                    "public": item.public,
                    "measured": item.measured,
                    "conditions": item.conditions,
                    "checked": item.checked,
                    "configuration": item.configuration,
                    "source_model": item.source_model,
                    "source_record_id": item.source_record_id,
                    "snapshot": item.snapshot,
                    "source_sha256": item.source_sha256,
                    "result_kind": item.result_kind,
                    "confidence_low": item.confidence_low,
                    "confidence_high": item.confidence_high,
                }
            )
        facts = [
            {
                "model_slug": item.model.slug,
                "key": item.key,
                "value": item.value,
                "source_url": item.source.url,
                "checked": item.checked,
            }
            for item in Fact.objects.select_related("model", "source").order_by("pk")
        ]
        model_origins = [
            {
                "model_slug": item.model.slug,
                "country_code": item.country_id,
                "source_url": item.source.url,
                "checked": item.checked,
                "position": item.position,
            }
            for item in ModelOriginCountry.objects.select_related("model", "source").order_by("pk")
        ]
        tool_platforms = [
            {
                "tool_slug": item.tool.slug,
                "platform_code": item.platform.code,
                "source_url": item.source.url,
                "checked": item.checked,
            }
            for item in ToolPlatform.objects.select_related(
                "tool", "platform", "source"
            ).order_by("pk")
        ]
        tool_model_supports = [
            {
                "tool_slug": item.tool.slug,
                "model_slug": item.model.slug,
                "source_url": item.source.url,
                "checked": item.checked,
                "note": item.note,
            }
            for item in ToolModelSupport.objects.select_related(
                "tool", "model", "source"
            ).order_by("pk")
        ]

        baseline_research_set = set(baseline_research_ids)
        new_research_records = [
            {
                "external_id": item.external_id,
                "source_record_id": item.source_record_id,
                "batch": item.batch,
                "payload": item.payload,
                "state": item.state,
                "review_reason": item.review_reason,
                "imported_at": item.imported_at,
            }
            for item in ResearchRecord.objects.order_by("pk")
            if item.external_id not in baseline_research_set
        ]

        def publication_signature(row):
            return canonical(
                [
                    row["entity_id"],
                    row["model_slug"],
                    row["action"],
                    row["source_record_ids"],
                    row["before"],
                    row["after"],
                ]
            )

        baseline_publications = []
        for row in baseline.execute(
            "SELECT r.entity_id,m.slug model_slug,r.action,r.source_record_ids,r.before,r.after "
            "FROM catalog_publicationrevision r JOIN catalog_modelversion m ON m.id=r.model_id "
            "ORDER BY r.id"
        ):
            baseline_publications.append(
                publication_signature(
                    {
                        "entity_id": row["entity_id"],
                        "model_slug": row["model_slug"],
                        "action": row["action"],
                        "source_record_ids": parse_json(row["source_record_ids"]),
                        "before": parse_json(row["before"]),
                        "after": parse_json(row["after"]),
                    }
                )
            )
        local_publications = [
            {
                "entity_id": item.entity_id,
                "model_slug": item.model.slug,
                "action": item.action,
                "source_record_ids": item.source_record_ids,
                "before": item.before,
                "after": item.after,
                "created": item.created,
            }
            for item in PublicationRevision.objects.select_related("model").order_by("pk")
        ]
        new_publications = consume_new(
            local_publications, baseline_publications, publication_signature
        )

        def tool_publication_signature(row):
            return canonical([row["tool_slug"], row["action"], row["before"], row["after"]])

        baseline_tool_publications = []
        for row in baseline.execute(
            "SELECT t.slug tool_slug,r.action,r.before,r.after "
            "FROM catalog_toolpublicationrevision r JOIN catalog_tool t ON t.id=r.tool_id "
            "ORDER BY r.id"
        ):
            baseline_tool_publications.append(
                tool_publication_signature(
                    {
                        "tool_slug": row["tool_slug"],
                        "action": row["action"],
                        "before": parse_json(row["before"]),
                        "after": parse_json(row["after"]),
                    }
                )
            )
        local_tool_publications = [
            {
                "tool_slug": item.tool.slug,
                "action": item.action,
                "before": item.before,
                "after": item.after,
                "created": item.created,
            }
            for item in ToolPublicationRevision.objects.select_related("tool").order_by("pk")
        ]
        new_tool_publications = consume_new(
            local_tool_publications,
            baseline_tool_publications,
            tool_publication_signature,
        )

        def research_revision_signature(row):
            return canonical(
                [row["record_external_id"], row["batch"], row["action"], row["before"], row["after"]]
            )

        baseline_research_revisions = []
        for row in baseline.execute(
            "SELECT rr.external_id record_external_id,r.batch,r.action,r.before,r.after "
            "FROM catalog_researchrevision r JOIN catalog_researchrecord rr ON rr.id=r.record_id "
            "ORDER BY r.id"
        ):
            baseline_research_revisions.append(
                research_revision_signature(
                    {
                        "record_external_id": row["record_external_id"],
                        "batch": row["batch"],
                        "action": row["action"],
                        "before": parse_json(row["before"]),
                        "after": parse_json(row["after"]),
                    }
                )
            )
        local_research_revisions = [
            {
                "record_external_id": item.record.external_id,
                "batch": item.batch,
                "action": item.action,
                "before": item.before,
                "after": item.after,
                "created": item.created,
            }
            for item in ResearchRevision.objects.select_related("record").order_by("pk")
        ]
        new_research_revisions = consume_new(
            local_research_revisions,
            baseline_research_revisions,
            research_revision_signature,
        )

        def revision_signature(row):
            return canonical([row["model_slug"], row["entity"], row["action"], row["snapshot"]])

        baseline_revisions = []
        for row in baseline.execute(
            "SELECT m.slug model_slug,r.entity,r.action,r.snapshot "
            "FROM catalog_revision r JOIN catalog_modelversion m ON m.id=r.model_id ORDER BY r.id"
        ):
            baseline_revisions.append(
                revision_signature(
                    {
                        "model_slug": row["model_slug"],
                        "entity": row["entity"],
                        "action": row["action"],
                        "snapshot": parse_json(row["snapshot"]),
                    }
                )
            )
        local_revisions = [
            {
                "model_slug": item.model.slug,
                "entity": item.entity,
                "action": item.action,
                "snapshot": item.snapshot,
                "created": item.created,
            }
            for item in Revision.objects.select_related("model").order_by("pk")
        ]
        new_revisions = consume_new(
            local_revisions, baseline_revisions, revision_signature
        )

        payload = {
            "format": "aipedia-natural-catalog-v1",
            "source": "AIpedia_global_research_master_2026-09-21_applicability_fixed.xlsx",
            "guard": {
                "counts": guard_counts,
                "model_slugs_sha256": digest(baseline_model_slugs),
                "tool_slugs_sha256": digest(baseline_tool_slugs),
                "source_urls_sha256": digest(baseline_source_urls),
                "offer_keys_sha256": digest(baseline_offer_keys),
                "research_external_ids_sha256": digest(baseline_research_ids),
            },
            "sources": sources,
            "organizations": organizations,
            "families": families,
            "models": models,
            "countries": countries,
            "platforms": platforms,
            "tools": tools,
            "services": services,
            "accesses": accesses,
            "offers": offers,
            "benchmarks": benchmarks,
            "new_evaluations": new_evaluations,
            "facts": facts,
            "model_origins": model_origins,
            "tool_platforms": tool_platforms,
            "tool_model_supports": tool_model_supports,
            "new_research_records": new_research_records,
            "new_publication_revisions": new_publications,
            "new_tool_publication_revisions": new_tool_publications,
            "new_research_revisions": new_research_revisions,
            "new_revisions": new_revisions,
            "expected": {
                "models_published": 763,
                "tools_published": 138,
                "model_versions_total": 901,
                "offers": 555,
                "accesses": 1205,
                "evaluations": 881,
                "sources": 343,
                "research_records": 2900,
                "research_revisions": 3590,
                "revisions": 4354,
                "publication_revisions": 3049,
                "tool_publication_revisions": 158,
            },
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "output": str(output_path),
                    "bytes": output_path.stat().st_size,
                    "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                    "counts": {
                        key: len(value)
                        for key, value in payload.items()
                        if isinstance(value, list)
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        baseline.close()


if __name__ == "__main__":
    main()
