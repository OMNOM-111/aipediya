"""Public dataset projections (GSD-07).

Two datasets are generated from published records only, through an explicit
field allowlist:

* ``AIpediya Global AI Models Dataset`` (``models``)
* ``AIpediya AI Tools Dataset`` (``tools``)

Deliberately excluded (see docs/SEARCH_DISCOVERY.md, "Datasets"): unpublished
records and anything linked only to them, descriptive prose (description,
suitability, limitations - provenance/reuse rights not established), third-party
benchmark scores (reuse rights not established for bulk redistribution; only a
count of shown evaluations is exported), internal notes, research records,
revision history, translation state and the catalog master.

Output is deterministic: rows sorted by record id, keys in schema order,
decimals as strings, dates as ISO strings, unknown as ``null`` (JSON) or an
empty cell (CSV). ``dataset_version`` is derived from the data (latest check
date + content digest), independent of the application code revision.
Generating a dataset never writes to the database and never translates.
"""
import csv
import hashlib
import io
import json
from datetime import date
from decimal import Decimal

from django.conf import settings

from . import readiness
from .comparison import developer_countries
from .i18n import SUPPORTED_CODES
from .locale_urls import absolute

SCHEMA_VERSION = "1.0.0"
LICENSE_STATUS = "not-granted"  # the owner has not chosen a data license yet
DOCS_LANGS = ("en",)  # field documentation is written in English only

DATASETS = {
    "models": {
        "name": "AIpediya Global AI Models Dataset",
        "slug": "aipediya-global-ai-models",
    },
    "tools": {
        "name": "AIpediya AI Tools Dataset",
        "slug": "aipediya-ai-tools",
    },
}

# (field, type, meaning). Order = JSON key order = CSV column order.
MODEL_FIELDS = [
    ("record_id", "string", "Stable AIpediya record identifier (URL slug). Never changes."),
    ("catalog_number", "integer|null", "Public chronological catalog number at export time; can be renumbered when an earlier release is added. Use record_id for identity."),
    ("name", "string", "Model name as published."),
    ("version", "string|null", "Version label when it differs from the name."),
    ("developer", "string", "Developer organization."),
    ("origin_countries", "list[ISO 3166-1 alpha-2]", "Documented countries of the developer organization."),
    ("category", "string", "Catalog category: text, image, video, audio or other."),
    ("use_cases", "list[string]", "Use-case codes (e.g. code, reasoning, image_generation)."),
    ("input_modalities", "list[string]", "Accepted input modalities."),
    ("output_modalities", "list[string]", "Produced output modalities."),
    ("context_window_tokens", "integer|null", "Documented context window in tokens; null when unknown."),
    ("release_date", "date|null", "Exact, source-confirmed release date (YYYY-MM-DD)."),
    ("approximate_release_date", "date|null", "Earliest reliable date of public existence when no exact date is confirmed."),
    ("release_date_precision", "string|null", "exact-day, approximate-month, approximate-day, or null when unknown."),
    ("status", "string", "Catalog lifecycle status: active, deprecated, retired or archived."),
    ("open_weights", "boolean", "Weights downloadable under the developer's license. Not the same as open source."),
    ("license", "string|null", "License name as recorded; null when not recorded."),
    ("access", "list[object]", "Access routes: kind (api/web/app/download/cli/ide), provider, url."),
    ("prices", "list[object]", "Active list prices: provider, service_kind, amount_usd (decimal string), unit, billing_unit, conditions (English), source_url, checked."),
    ("shown_evaluations_count", "integer", "Number of evaluations shown on the card (scores themselves are not redistributed)."),
    ("source_url", "string", "Primary source for the record."),
    ("last_checked", "date", "Date an editor last checked the primary source (not a release date)."),
    ("page_url", "string", "Canonical English AIpediya page."),
]

TOOL_FIELDS = [
    ("record_id", "string", "Stable AIpediya record identifier (URL slug). Never changes."),
    ("catalog_number", "integer|null", "Public chronological catalog number at export time; use record_id for identity."),
    ("name", "string", "Tool name as published."),
    ("version", "string|null", "Version label when it differs from the name."),
    ("developer", "string", "Developer organization."),
    ("origin_countries", "list[ISO 3166-1 alpha-2]", "Documented countries of the developer organization."),
    ("category", "string", "Tool category code (e.g. ai_app, coding_agent, runtime)."),
    ("use_cases", "list[string]", "Use-case codes."),
    ("platforms", "list[string]", "Platform codes where the tool is available."),
    ("local_execution", "string|null", "yes, no, hybrid, or null when unknown."),
    ("supported_models", "list[string]", "record_id values of published models the tool is documented to support."),
    ("official_url", "string|null", "Official product URL."),
    ("release_date", "date|null", "Exact, source-confirmed release date (YYYY-MM-DD)."),
    ("approximate_release_date", "date|null", "Earliest reliable date of public existence when no exact date is confirmed."),
    ("release_date_precision", "string|null", "exact-day, approximate-month, approximate-day, or null when unknown."),
    ("status", "string", "Catalog lifecycle status."),
    ("access", "list[object]", "Access routes: kind, provider, url."),
    ("prices", "list[object]", "Active list prices: provider, service_kind, amount_usd (decimal string), unit, billing_unit, conditions (English), source_url, checked."),
    ("source_url", "string", "Primary source for the record."),
    ("last_checked", "date", "Date an editor last checked the primary source (not a release date)."),
    ("page_url", "string", "Canonical English AIpediya page."),
]

FIELDS = {"models": MODEL_FIELDS, "tools": TOOL_FIELDS}


def datasets_enabled():
    return bool(getattr(settings, "AIPEDIA_DATASETS_PUBLIC", False))


def dataset_page_langs():
    """Locales where the dataset documentation is fully written (English)."""
    return [code for code in SUPPORTED_CODES if code in DOCS_LANGS]


def _precision(obj):
    if obj.released:
        return "exact-day"
    if obj.approx_released:
        return "approximate-day" if obj.approx_precision == "day" else "approximate-month"
    return None


def _english(value):
    if isinstance(value, dict):
        return (value.get("en") or "").strip() or None
    return (str(value).strip() or None) if value else None


def _accesses(accesses):
    rows = [
        {"kind": access.service.kind, "provider": access.service.provider.name, "url": access.service.url}
        for access in accesses
    ]
    return sorted(rows, key=lambda row: (row["kind"], row["provider"], row["url"]))


def _prices(offers):
    rows = []
    for offer in offers:
        if not offer.active:
            continue
        rows.append({
            "provider": offer.service.provider.name,
            "service_kind": offer.service.kind,
            "amount_usd": None if offer.amount is None else _decimal(offer.amount),
            "unit": offer.unit,
            "billing_unit": offer.billing_unit or None,
            "conditions": _english(offer.conditions),
            "source_url": offer.source.url,
            "checked": offer.checked,
        })
    return sorted(rows, key=lambda row: (row["provider"], row["service_kind"], row["unit"],
                                         row["amount_usd"] or "", row["conditions"] or ""))


def _decimal(value):
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _version(obj):
    return None if not obj.version or obj.version.casefold() == obj.name.casefold() else obj.version


def model_rows():
    qs = readiness.public_models().select_related("family__developer", "source").prefetch_related(
        "accesses__service__provider", "offers__service__provider", "offers__source",
        "evaluations", "origin_country_links__country",
    ).order_by("slug")
    for model in qs:
        yield {
            "record_id": model.slug,
            "catalog_number": model.public_number,
            "name": model.name,
            "version": _version(model),
            "developer": model.family.developer.name,
            "origin_countries": sorted(link.country.code for link in model.origin_country_links.all()),
            "category": model.category,
            "use_cases": sorted(set(model.tasks or [])),
            "input_modalities": sorted(set(model.input_modalities or [])),
            "output_modalities": sorted(set(model.output_modalities or [])),
            "context_window_tokens": model.context,
            "release_date": model.released,
            "approximate_release_date": None if model.released else model.approx_released,
            "release_date_precision": _precision(model),
            "status": model.catalog_status,
            "open_weights": bool(model.open_weights),
            "license": model.license or None,
            "access": _accesses(model.accesses.all()),
            "prices": _prices(model.offers.all()),
            "shown_evaluations_count": sum(1 for item in model.evaluations.all() if item.public),
            "source_url": model.source.url,
            "last_checked": model.checked,
            "page_url": absolute(f"/models/{model.slug}", "en"),
        }


def tool_rows():
    public_model_slugs = set(readiness.public_models().values_list("slug", flat=True))
    qs = readiness.public_tools().select_related("developer", "source", "legacy_version").prefetch_related(
        "platform_links__platform", "model_links__model",
        "legacy_version__offers__service__provider", "legacy_version__offers__source",
        "legacy_version__accesses__service__provider",
    ).order_by("slug")
    for tool in qs:
        legacy = tool.legacy_version
        yield {
            "record_id": tool.slug,
            "catalog_number": tool.public_number,
            "name": tool.name,
            "version": _version(tool),
            "developer": tool.developer.name,
            "origin_countries": sorted(item.code for item in developer_countries(tool.developer.country)),
            "category": tool.category,
            "use_cases": sorted(set(tool.purposes or [])),
            "platforms": sorted({link.platform.code for link in tool.platform_links.all()}),
            "local_execution": tool.local_execution or None,
            # Links to unpublished models are dropped: they must not leak.
            "supported_models": sorted({link.model.slug for link in tool.model_links.all()
                                        if link.model.slug in public_model_slugs}),
            "official_url": tool.official_url or None,
            "release_date": tool.released,
            "approximate_release_date": None if tool.released else tool.approx_released,
            "release_date_precision": _precision(tool),
            "status": tool.catalog_status,
            "access": _accesses(legacy.accesses.all()) if legacy else [],
            "prices": _prices(legacy.offers.all()) if legacy else [],
            "source_url": tool.source.url,
            "last_checked": tool.checked,
            "page_url": absolute(f"/tools/{tool.slug}", "en"),
        }


def _plain(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return _decimal(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def records(kind):
    rows = model_rows() if kind == "models" else tool_rows()
    order = [field for field, _type, _meaning in FIELDS[kind]]
    return [{field: _plain(row[field]) for field in order} for row in rows]


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _records_bytes(rows):
    return json.dumps(rows, ensure_ascii=False, sort_keys=False, separators=(",", ":")).encode("utf-8")


def metadata(kind, rows=None):
    rows = records(kind) if rows is None else rows
    data_date = max((row["last_checked"] for row in rows if row["last_checked"]), default=None)
    content = _digest(_records_bytes(rows))
    return {
        "name": DATASETS[kind]["name"],
        "schema_version": SCHEMA_VERSION,
        "dataset_version": f"{data_date or 'undated'}+{content[:12]}",
        "data_as_of": data_date,
        "record_count": len(rows),
        "content_sha256": content,
        "license": LICENSE_STATUS,
        "publisher": "AIpediya",
        "homepage": absolute(f"/datasets/{kind}", "en"),
        "provenance": (
            "Generated from records published in the AIpediya catalog. Each record carries its primary "
            "source_url and last_checked date; prices carry their own source and check date. Unpublished "
            "records, descriptive prose, third-party benchmark scores and internal editorial data are excluded."
        ),
        "unknown_values": "null in JSON, empty cell in CSV. Unknown is never zero or false.",
        "fields": [{"name": name, "type": kind_, "meaning": meaning} for name, kind_, meaning in FIELDS[kind]],
    }


def as_json(kind):
    rows = records(kind)
    document = {"metadata": metadata(kind, rows), "records": rows}
    return json.dumps(document, ensure_ascii=False, indent=1).encode("utf-8") + b"\n"


FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    else:
        text = str(value)
    # Neutralize spreadsheet formula injection (CWE-1236) without altering the
    # stored value: a leading apostrophe makes spreadsheets treat it as text.
    if text.startswith(FORMULA_PREFIXES) and not _is_number(text):
        text = "'" + text
    return text


def _is_number(text):
    try:
        Decimal(text)
    except Exception:
        return False
    return True


def as_csv(kind):
    rows = records(kind)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    order = [field for field, _type, _meaning in FIELDS[kind]]
    writer.writerow(order)
    for row in rows:
        writer.writerow([_cell(row[field]) for field in order])
    return buffer.getvalue().encode("utf-8")


def build(kind, fmt):
    return as_json(kind) if fmt == "json" else as_csv(kind)


def manifest():
    """Checksums of every published file, for reproducibility checks."""
    files = {}
    for kind in DATASETS:
        rows = records(kind)
        meta = metadata(kind, rows)
        for fmt in ("json", "csv"):
            payload = build(kind, fmt)
            files[f"{DATASETS[kind]['slug']}.{fmt}"] = {
                "sha256": _digest(payload), "bytes": len(payload),
                "dataset_version": meta["dataset_version"], "records": meta["record_count"],
            }
    return {"schema_version": SCHEMA_VERSION, "license": LICENSE_STATUS, "files": files}
