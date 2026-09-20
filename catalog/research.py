"""Lossless research staging helpers; nothing here publishes catalog facts."""
import json
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

OPENROUTER_URL = "https://openrouter.ai/api/v1/models?output_modalities=all"
OPENROUTER_DOCS = "https://openrouter.ai/docs/guides/overview/models"
ENTITY_TYPES = {"model", "product", "service", "api_service", "runtime"}
PRICE_FIELDS = {
    "input_usd_per_million_tokens": "prompt",
    "output_usd_per_million_tokens": "completion",
    "cached_input_usd_per_million_tokens": "input_cache_read",
}


class ResearchError(ValueError):
    pass


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ResearchError(f"Non-finite JSON number: {value}")


def read_document(path):
    try:
        document = json.loads(
            Path(path).read_text(encoding="utf-8-sig"),
            object_pairs_hook=_object, parse_constant=_invalid_constant,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise ResearchError(f"Cannot read research JSON: {exc}") from exc
    validate_document(document)
    return document


def summarize(document):
    rows = document["records"]
    names = {row["name"] for row in rows}
    return {
        "offers": len(rows),
        "distinct_entry_names": len(names),
        "distinct_model_names": len({r["name"] for r in rows if r["entity_type"] == "model"}),
        "distinct_other_names": len({r["name"] for r in rows if r["entity_type"] != "model"}),
        "distinct_entities": len({(r["entity_type"], r["developer"], r["name"]) for r in rows}),
        "offers_by_entity_type": dict(sorted(Counter(r["entity_type"] for r in rows).items())),
        "distinct_names_by_entity_type": {
            kind: len({r["name"] for r in rows if r["entity_type"] == kind})
            for kind in sorted({r["entity_type"] for r in rows})
        },
    }


def validate_document(document):
    if not isinstance(document, dict):
        raise ResearchError("Research JSON must be an object with records.")
    try:
        json.dumps(document, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ResearchError("Research JSON contains invalid numeric values.") from exc
    if not isinstance(document.get("project"), str) or not document["project"].strip():
        raise ResearchError("A nonempty project is required.")
    try:
        date.fromisoformat(document["snapshot_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResearchError("snapshot_date must be an ISO date.") from exc
    rows = document.get("records")
    if not isinstance(rows, list) or not rows:
        raise ResearchError("records must be a nonempty list.")
    sources = document.get("sources")
    if not isinstance(sources, list):
        raise ResearchError("sources must be a list.")
    source_ids = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            raise ResearchError("Every source must have a string id.")
        if not source["id"] or source["id"] in source_ids:
            raise ResearchError("Source IDs must be nonempty and unique.")
        source_ids.add(source["id"])
    seen = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ResearchError(f"Record {index} must be an object.")
        for key in ("record_id", "name", "entity_type"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ResearchError(f"Record {index}: nonempty {key} is required.")
        # An unknown developer is an explicit unknown research fact, not a reason
        # to discard a non-public staging record.
        developer = row.get("developer")
        if developer is not None and (not isinstance(developer, str) or not developer.strip()):
            raise ResearchError(f"Record {index}: developer must be a nonempty string or null.")
        if row["record_id"] in seen:
            raise ResearchError(f"Duplicate record_id: {row['record_id']}")
        seen.add(row["record_id"])
        if row["entity_type"] not in ENTITY_TYPES:
            raise ResearchError(f"Unknown entity_type: {row['entity_type']}")
        if row.get("publication_state") != "review_required":
            raise ResearchError(f"{row['record_id']}: publication_state must be review_required.")
        refs = row.get("source_ids")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in source_ids for ref in refs):
            raise ResearchError(f"{row['record_id']}: invalid source_ids.")
    summary = summarize(document)
    declared = {
        "row_count": summary["offers"],
        "unique_entry_names": summary["distinct_entry_names"],
        "unique_model_names": summary["distinct_model_names"],
        "unique_other_names": summary["distinct_other_names"],
        "source_count": len(sources),
    }
    for key, actual in declared.items():
        if key in document and (type(document[key]) is not int or document[key] != actual):
            raise ResearchError(f"{key} disagrees with records: declared {document[key]}, actual {actual}.")
    return summary


def prepare_records(document, batch=None):
    summary = validate_document(document)
    batch = batch if batch is not None else f"{document['project']}:{document['snapshot_date']}"
    if not isinstance(batch, str) or not batch.strip() or len(batch) > 200:
        raise ResearchError("batch must contain 1..200 characters.")
    metadata = {key: value for key, value in document.items() if key != "records"}
    prepared = []
    for row in document["records"]:
        external_id = row.get("external_id") or f"{batch}:{row['record_id']}"
        if not isinstance(external_id, str) or not external_id.strip():
            raise ResearchError(f"Invalid external_id: {row['record_id']}")
        if len(external_id) > 200:
            raise ResearchError(f"Namespaced external_id exceeds 200 characters: {row['record_id']}")
        prepared.append({
            "external_id": external_id,
            "source_record_id": row["record_id"],
            "batch": batch,
            "payload": {"record": row, "dataset": metadata},
            "state": "review_required",
        })
    return batch, prepared, summary


def _per_million(value):
    if value is None:
        return None
    try:
        price = Decimal(str(value))
    except InvalidOperation as exc:
        raise ResearchError("Invalid OpenRouter price.") from exc
    if not price.is_finite():
        raise ResearchError("Non-finite OpenRouter price.")
    if price < 0:
        return None
    with localcontext() as context:
        context.prec = max(50, len(price.as_tuple().digits) + 10)
        return format(price * Decimal(1_000_000), "f")


def openrouter_evidence(document, snapshot, checked_at):
    """Compare exact IDs only. Provider listings never establish independent audits."""
    validate_document(document)
    rows = snapshot.get("data") if isinstance(snapshot, dict) else None
    if not isinstance(rows, list) or not rows or snapshot.get("error"):
        raise ResearchError("Invalid or empty OpenRouter snapshot.")
    links = snapshot.get("links")
    if links is not None and (not isinstance(links, dict) or links.get("next")):
        raise ResearchError("OpenRouter snapshot is paginated.")
    if "total_count" in snapshot and (
        type(snapshot["total_count"]) is not int or snapshot["total_count"] != len(rows)
    ):
        raise ResearchError("Incomplete OpenRouter snapshot.")
    by_id = {}
    by_repository = {}
    for model in rows:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str) or not model["id"]:
            raise ResearchError("OpenRouter model is missing its exact ID.")
        if model["id"] in by_id:
            raise ResearchError("Duplicate OpenRouter model ID.")
        if not isinstance(model.get("pricing"), dict):
            raise ResearchError("OpenRouter model is missing pricing.")
        by_id[model["id"]] = model
        repository = model.get("hugging_face_id")
        if isinstance(repository, str) and repository:
            by_repository.setdefault(repository, []).append(model)

    evidence = []
    observed = {}
    for row in document["records"]:
        exact_id = row.get("openrouter_id")
        model = by_id.get(exact_id) if isinstance(exact_id, str) else None
        repository = row.get("repository_id")
        candidates = by_repository.get(repository, []) if isinstance(repository, str) else []
        fields = {
            "openrouter_id": {
                "status": "exact_id_listed" if model else (
                    "not_listed_in_snapshot" if exact_id else "not_verifiable_missing_exact_id"
                ),
                "value": exact_id,
            },
        }
        if repository:
            fields["repository_id"] = {
                "status": "exact_repository_reference" if candidates else "not_listed_in_snapshot",
                "value": repository,
                "openrouter_ids": [candidate["id"] for candidate in candidates],
                "scope": "Repository reference only; runtime, quantization and provider equivalence unverified.",
            }
        comparable = bool(
            model and row.get("supplier", "").casefold() == "openrouter"
            and row.get("currency") == "USD" and "API" in row.get("access", [])
        )
        for field, api_key in PRICE_FIELDS.items():
            raw_price = model["pricing"].get(api_key) if model else None
            official = _per_million(raw_price)
            research = row.get(field)
            if not comparable:
                status = "not_comparable_provider_or_id"
            elif research is None or official is None:
                status = "unknown"
            else:
                try:
                    value = Decimal(str(research))
                except InvalidOperation as exc:
                    raise ResearchError(f"Invalid research price: {row['record_id']}") from exc
                status = "numeric_match_only" if value == Decimal(official) else "numeric_difference"
            fields[field] = {"status": status, "research_value": research, "openrouter_usd_per_million": official}
        for item in ([model] if model else []) + candidates:
            observed[item["id"]] = {
                "id": item["id"],
                "canonical_slug": item.get("canonical_slug"),
                "hugging_face_id": item.get("hugging_face_id"),
                "raw_pricing": item["pricing"],
                "usd_per_million_tokens": {
                    key: _per_million(item["pricing"].get(key))
                    for key in ("prompt", "completion", "input_cache_read", "input_cache_write")
                },
                "per_request_limits": item.get("per_request_limits"),
                "architecture": item.get("architecture"),
                "top_provider": item.get("top_provider"),
            }
        evidence.append({"record_id": row["record_id"], "fields": fields, "publication_state": "review_required"})
    return {
        "source_url": OPENROUTER_URL,
        "pricing_documentation": OPENROUTER_DOCS,
        "checked_at": checked_at,
        "snapshot_count": len(rows),
        "full_snapshot": True,
        "research_snapshot_date": document["snapshot_date"],
        "research_summary": summarize(document),
        "limitations": [
            "OpenRouter listing is provider evidence, not an independent benchmark or audit.",
            "No model executions, regional access or complete pricing conditions were verified.",
            "Names are never used to infer exact IDs; all catalog variants remain separate.",
            "Repository equality does not verify local quantization, runtime or a different supplier's price.",
            "Numeric price equality alone does not confirm equivalent plans, context tiers or fees.",
            "Unknown prices and limits remain null. Negative API price sentinels remain in raw_pricing.",
            "This is a research sample and one provider snapshot, not complete worldwide coverage.",
        ],
        "observed_openrouter_models": [observed[key] for key in sorted(observed)],
        "records": evidence,
    }
