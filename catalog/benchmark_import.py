"""Staging adapter for third-party benchmark observations.

This module deliberately has no catalogue-writing path.  A benchmark package is
evidence for editorial review, not permission to republish another site's data.
"""
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import ModelVersion


class BenchmarkImportError(ValueError):
    pass


def _reject_duplicate_key(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BenchmarkImportError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value):
    raise BenchmarkImportError(f"Non-finite JSON number: {value}")


def read_benchmark_document(path):
    try:
        document = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_key,
            parse_constant=_reject_non_finite,
        )
    except (OSError, json.JSONDecodeError, BenchmarkImportError) as exc:
        raise BenchmarkImportError(f"Cannot read benchmark JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise BenchmarkImportError("Benchmark JSON must be an object.")
    return document


def _iso_date(value, field, observation_id, allow_null=True):
    if value is None and allow_null:
        return
    if not isinstance(value, str):
        raise BenchmarkImportError(f"{observation_id}: {field} must be an ISO date or null.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise BenchmarkImportError(f"{observation_id}: invalid {field}.") from exc


def _decimal(value, observation_id):
    if isinstance(value, bool) or value is None:
        raise BenchmarkImportError(f"{observation_id}: value must be a finite number.")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BenchmarkImportError(f"{observation_id}: value must be numeric.") from exc
    if not parsed.is_finite():
        raise BenchmarkImportError(f"{observation_id}: value must be finite.")
    return parsed


def validate_benchmark_document(document):
    observations = document.get("observations")
    sources = document.get("sources")
    prepared_on = document.get("prepared_on")
    if not isinstance(observations, list) or not observations:
        raise BenchmarkImportError("Benchmark JSON requires a nonempty observations array.")
    if not isinstance(sources, list) or not sources:
        raise BenchmarkImportError("Benchmark JSON requires a nonempty sources array.")
    _iso_date(prepared_on, "prepared_on", "document", allow_null=False)
    source_by_id = {}
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("id"), str) or not source["id"].strip():
            raise BenchmarkImportError("Every source needs a nonempty id.")
        if source["id"] in source_by_id:
            raise BenchmarkImportError(f"Duplicate source id: {source['id']}")
        source_by_id[source["id"]] = source
    seen = set()
    required = (
        "observation_id", "source_id", "leaderboard_id", "catalog_name_candidate",
        "source_model_name", "unit",
        "higher_is_better", "observed_on", "source_url", "publication_state",
        "factual_status", "reuse_status",
    )
    for observation in observations:
        if not isinstance(observation, dict):
            raise BenchmarkImportError("Every observation must be an object.")
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id:
            raise BenchmarkImportError("Every observation needs a nonempty observation_id.")
        if observation_id in seen:
            raise BenchmarkImportError(f"Duplicate observation_id: {observation_id}")
        seen.add(observation_id)
        for field in required:
            if field not in observation or observation[field] in (None, ""):
                raise BenchmarkImportError(f"{observation_id}: {field} is required.")
        for field in ("configuration", "benchmark_version"):
            if field not in observation or (observation[field] is not None and not isinstance(observation[field], str)):
                raise BenchmarkImportError(f"{observation_id}: {field} must be a string or null.")
        if observation["source_id"] not in source_by_id:
            raise BenchmarkImportError(f"{observation_id}: unknown source_id.")
        if observation["publication_state"] != "review_required":
            raise BenchmarkImportError(f"{observation_id}: package observations must start review_required.")
        if not isinstance(observation["higher_is_better"], bool):
            raise BenchmarkImportError(f"{observation_id}: higher_is_better must be boolean.")
        _decimal(observation.get("value"), observation_id)
        _iso_date(observation.get("observed_on"), "observed_on", observation_id, allow_null=False)
        _iso_date(observation.get("source_snapshot_date"), "source_snapshot_date", observation_id)
        _iso_date(observation.get("source_run_date"), "source_run_date", observation_id)
        if not str(observation["source_url"]).startswith("https://"):
            raise BenchmarkImportError(f"{observation_id}: source_url must use HTTPS.")
    declared = document.get("observations_count")
    if declared is not None and declared != len(observations):
        raise BenchmarkImportError(f"observations_count disagrees with observations: {declared} != {len(observations)}")
    return source_by_id


def _mapping(observation):
    candidate_id = observation.get("catalog_entity_id_candidate")
    candidate_name = observation["catalog_name_candidate"]
    if not isinstance(candidate_id, str) or not candidate_id:
        return {"status": "missing_catalog_entity_candidate", "model_pk": None}
    model = ModelVersion.objects.filter(research_entity_id=candidate_id).only(
        "pk", "name", "version", "published", "research_entity_id"
    ).first()
    if model is None:
        return {"status": "catalog_entity_not_found", "model_pk": None, "candidate_entity_id": candidate_id}
    if model.name != candidate_name:
        return {
            "status": "catalog_name_mismatch", "model_pk": model.pk,
            "candidate_entity_id": candidate_id, "live_model_name": model.name,
            "candidate_name": candidate_name,
        }
    return {
        "status": "exact_catalog_entity_and_name", "model_pk": model.pk,
        "candidate_entity_id": candidate_id, "live_model_name": model.name,
        "live_model_version": model.version, "published": model.published,
    }


def _rights_reason(source_id, observation):
    if source_id == "aa":
        return "publication blocked: Artificial Analysis terms require a licensed or written permission route for commercial republication of site content"
    if source_id == "arena":
        return "publication blocked: Arena terms prohibit automated extraction and commercial reproduction without permission"
    if source_id == "livebench":
        parity = observation.get("live_site_parity_verified")
        parity_reason = "deployed leaderboard snapshot parity is not verified" if not parity else "specific data licence and attribution still need verification"
        return f"publication blocked: {parity_reason}"
    if source_id == "swebench":
        return "publication blocked: specific leaderboard/export licence and attribution are not verified"
    return "publication blocked: source reuse permission is not recorded"


def prepare_observations(document, batch=None):
    source_by_id = validate_benchmark_document(document)
    batch = batch or f"AIpedia-benchmarks:{document['prepared_on']}"
    if not isinstance(batch, str) or not batch or len(batch) > 200:
        raise BenchmarkImportError("batch must contain 1..200 characters.")
    root = {
        key: document[key]
        for key in ("schema_version", "project", "domain", "prepared_on", "purpose_ru", "import_policy", "sources")
        if key in document
    }
    prepared = []
    for observation in document["observations"]:
        mapping = _mapping(observation)
        reasons = [_rights_reason(observation["source_id"], observation)]
        if mapping["status"] != "exact_catalog_entity_and_name":
            reasons.append(f"mapping blocked: {mapping['status']}; no fuzzy matching was used")
        reason = "; ".join(reasons)
        observation_id = observation["observation_id"]
        payload = {
            "kind": "benchmark_observation",
            "dataset": root,
            "source": source_by_id[observation["source_id"]],
            "observation": observation,
            "live_catalog_mapping": mapping,
            "publication": {"allowed": False, "reason": reason},
        }
        prepared.append({
            "external_id": f"{batch}:{observation_id}",
            "source_record_id": observation_id,
            "batch": batch,
            "payload": payload,
            "state": "review_required",
            "review_reason": reason[:300],
        })
    return batch, prepared


def summary(prepared):
    reasons = {}
    mapping = {}
    sources = {}
    for item in prepared:
        observation = item["payload"]["observation"]
        source_id = observation["source_id"]
        sources[source_id] = sources.get(source_id, 0) + 1
        status = item["payload"]["live_catalog_mapping"]["status"]
        mapping[status] = mapping.get(status, 0) + 1
        reason = item["review_reason"]
        reasons[reason] = reasons.get(reason, 0) + 1
    return {"observations": len(prepared), "by_source": sources, "mapping": mapping, "review_reasons": reasons}
