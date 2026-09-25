"""AIpediya Catalog Master: the canonical registry of every Model and Tool.

The workbook is the working source of truth. A record appears and is verified
here first; only PUBLISHED rows are later synchronised to Local/Production.
`import_from_local` brings Local records into the workbook without
overwriting master data; `validate` enforces the rules and reports drift.
Public Number is derived: chronological by verified release date among
PUBLISHED rows, recomputed on every import, with changes written to the
Changelog. Record ID (slug) never changes. Reads the database only.
"""
import json
import os
import re
import tempfile
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from .comparison import alphabet

WORKBOOK_PATH = Path("AI_CONTEXT") / "AIpediya_Model_Verification_Master.xlsx"
SCHEMA = "aipediya-catalog-master/3"
UPGRADABLE_SCHEMAS = {"aipediya-catalog-master/2"}
PRODUCTION_ORIGIN = "https://aipediya.com"
MAX_VALIDATED_ROW = 5000

STATUSES = ["PUBLISHED", "NEEDS_REVIEW"]
DECISIONS = ["PUBLIC", "ARCHIVE", "NEEDS_REVIEW"]
PRECISIONS = ["day", "month", "year"]
YES_NO = ["YES", "NO"]
MODEL_CATEGORIES = ["text", "image", "video", "audio", "other"]
TOOL_CATEGORIES = [
    "ai_app", "coding_assistant", "coding_agent", "runtime", "api_platform",
    "api_service", "ide_tool", "client", "agent_platform", "creative_app",
]
CATALOG_STATUSES = ["active", "deprecated", "retired", "archived"]
STAGES = ["released", "preview", "beta", "research"]
LOCAL_EXECUTION = ["yes", "no", "hybrid"]

WORKFLOW = [
    "Record ID", "Status", "Publication Decision", "Public Number", "Name", "Developer",
    "Exact Release Date", "Approx Date", "Approx Precision",
]
VERIFICATION = [
    "Missing Data", "Reason", "Canonical / Parent Record ID", "Official Source",
    "Secondary Source", "Last Verified", "On Local", "On Production", "Notes",
]
MODEL_PUBLIC = [
    "Release Stage", "Family", "Version", "Category", "Tasks", "Input Modalities",
    "Output Modalities", "Context", "License", "Open Weights", "Catalog Status",
    "Developer Country", "Origin Countries", "Description EN", "Description RU",
    "Suitable EN", "Suitable RU", "Limitations EN", "Limitations RU",
    "Source Title", "Source URL", "Source Publisher", "Checked (DB)",
    "Release Evidence (JSON)", "Approx Evidence (JSON)", "Origin (JSON)",
    "Philosophy (JSON)", "Description Other Locales (JSON)",
    "Suitable Other Locales (JSON)", "Limitations Other Locales (JSON)",
    "Research Entity ID",
]
TOOL_PUBLIC = [
    "Version", "Category", "Purposes", "Local Execution", "Official URL",
    "Platforms", "Supported Models", "Catalog Status", "Developer Country",
    "Description EN", "Description RU", "Ecosystem EN", "Ecosystem RU",
    "Source Title", "Source URL", "Source Publisher", "Checked (DB)",
    "Release Evidence (JSON)", "Approx Evidence (JSON)",
    "Description Other Locales (JSON)", "Ecosystem Other Locales (JSON)",
    "Legacy Record ID",
]
MODEL_SERVICE = [
    "Local Number", "Local PK", "Offers", "Evaluations", "Access",
    "Research Date Hint", "Import Sources (unverified)", "Import Batch", "Missing Count",
]
TOOL_SERVICE = [
    "Local Number", "Local PK", "Offers", "Access",
    "Research Date Hint", "Import Sources (unverified)", "Import Batch", "Missing Count",
]
MAIN = {
    "Models": WORKFLOW + VERIFICATION + MODEL_PUBLIC + MODEL_SERVICE,
    "Tools": WORKFLOW + VERIFICATION + TOOL_PUBLIC + TOOL_SERVICE,
}
# Public-data columns compared against Local to report pending sync (drift).
PUBLIC = {
    "Models": ["Name", "Developer", "Exact Release Date", "Approx Date"] + MODEL_PUBLIC,
    "Tools": ["Name", "Developer", "Exact Release Date", "Approx Date"] + TOOL_PUBLIC,
}
LOCAL_OWNED = {
    "On Local", "Local Number", "Local PK", "Research Date Hint",
    "Import Sources (unverified)", "Import Batch",
}
AUX = {
    "Offers": [
        "Key", "Record Type", "Record ID", "Service", "Service Kind", "Service URL",
        "Provider", "Compute Location", "Amount", "Unit", "Billing Unit",
        "Conditions EN", "Conditions RU", "Conditions Extra (JSON)", "Primary",
        "Active", "Source URL", "Checked", "Research Key",
    ],
    "Evaluations": [
        "Key", "Record Type", "Record ID", "Benchmark", "Protocol",
        "Benchmark Category", "Unit", "Higher Is Better", "Score", "Evaluator",
        "Result Kind", "Independent", "Public", "Measured", "Configuration",
        "Confidence Low", "Confidence High", "Conditions EN", "Conditions RU",
        "Conditions Extra (JSON)", "Source URL", "Checked", "Observation Key",
        "Source Model", "Source Record ID", "Snapshot", "Source SHA256",
    ],
    "Access": [
        "Key", "Record Type", "Record ID", "Service", "Service Kind", "Service URL",
        "Provider", "Compute Location", "Source URL", "Checked",
    ],
    "Facts": ["Key", "Record Type", "Record ID", "Fact", "Value (JSON)", "Source URL", "Checked"],
    "Origins": ["Key", "Record Type", "Record ID", "Country", "Position", "Source URL", "Checked"],
    "Tool Platforms": ["Key", "Record Type", "Record ID", "Platform", "Source URL", "Checked"],
}
CHANGELOG = ["Timestamp (UTC)", "Sheet", "Record ID", "Field", "Before", "After", "Reason"]
RECORD_TYPE_SHEET = {"model": "Models", "tool": "Tools"}

RECORD_ID = re.compile(r"^[-a-zA-Z0-9_]+$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
APPROX_DATE = re.compile(r"^≈\s?\d{4}(-\d{2}(-\d{2})?)?$")


def _text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if value else ""


def _locales(value):
    value = value or {}
    other = {k: v for k, v in value.items() if k not in ("en", "ru")}
    return _text(value.get("en")), _text(value.get("ru")), _json(other)


def _decimal(value):
    if value is None:
        return ""
    text = format(value.normalize(), "f")
    return text


def _approx(released, precision):
    if not released:
        return ""
    return "≈" + (released.strftime("%Y-%m") if precision == "month" else released.isoformat())


def _valid_iso(value):
    if not ISO_DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- Local rows

def _research_columns(obj):
    evidence = obj.release_evidence or {}
    hint = evidence.get("date_text") or ""
    if hint and evidence.get("precision"):
        hint += " (%s)" % evidence["precision"]
    sources = []
    for url in [evidence.get("source_url"), *(evidence.get("checked_sources") or []),
                obj.source.url if obj.source_id else ""]:
        if url and url not in sources:
            sources.append(url)
    return {
        "Research Date Hint": hint,
        "Import Sources (unverified)": " | ".join(sources),
        "Import Batch": evidence.get("import_batch", ""),
    }


def _verification(obj):
    """Verification metadata for a record first imported from Local.

    Published records carry the audited evidence already used by the site;
    hidden research rows get none, because their imported links are unverified.
    """
    evidence = obj.release_evidence or {}
    if not obj.published:
        notes = ["Hidden in Local (research layer); existence, date and sources are not verified."]
        if evidence.get("reason"):
            notes.append(evidence["reason"])
        audit = evidence.get("audit_notes") or {}
        notes.extend(t for t in (audit.get("text") or []) if t)
        if audit.get("media"):
            notes.append(audit["media"])
        return {"Status": "NEEDS_REVIEW", "Publication Decision": "NEEDS_REVIEW",
                "Official Source": "", "Secondary Source": "",
                "Last Verified": "", "Notes": " ".join(notes)}
    official = evidence.get("source_url") or (obj.source.url if obj.source_id else "")
    secondary = obj.source.url if obj.source_id and obj.source.url != official else ""
    return {"Status": "PUBLISHED", "Publication Decision": "PUBLIC",
            "Official Source": official, "Secondary Source": secondary,
            "Last Verified": evidence.get("checked") or _text(obj.checked), "Notes": ""}


def model_row(model):
    description, description_ru, description_other = _locales(model.description)
    suitable, suitable_ru, suitable_other = _locales(model.suitable)
    limitations, limitations_ru, limitations_other = _locales(model.limitations)
    developer = model.family.developer
    row = {
        "Record ID": model.slug, "Name": model.name, "Developer": developer.name,
        "Exact Release Date": _text(model.released),
        "Approx Date": _approx(model.approx_released, model.approx_precision),
        "On Local": _text(model.published),
        "Release Stage": model.release_stage, "Family": model.family.name,
        "Version": model.version, "Category": model.category,
        "Tasks": "; ".join(model.tasks or []),
        "Input Modalities": "; ".join(model.input_modalities or []),
        "Output Modalities": "; ".join(model.output_modalities or []),
        "Context": _text(model.context), "License": model.license,
        "Open Weights": _text(model.open_weights), "Catalog Status": model.catalog_status,
        "Developer Country": developer.country,
        "Origin Countries": "; ".join(link.country_id for link in model.origin_country_links.all()),
        "Description EN": description, "Description RU": description_ru,
        "Suitable EN": suitable, "Suitable RU": suitable_ru,
        "Limitations EN": limitations, "Limitations RU": limitations_ru,
        "Source Title": model.source.title, "Source URL": model.source.url,
        "Source Publisher": model.source.publisher, "Checked (DB)": _text(model.checked),
        "Release Evidence (JSON)": _json(model.release_evidence),
        "Approx Evidence (JSON)": _json(model.approx_evidence),
        "Origin (JSON)": _json(model.origin), "Philosophy (JSON)": _json(model.philosophy),
        "Description Other Locales (JSON)": description_other,
        "Suitable Other Locales (JSON)": suitable_other,
        "Limitations Other Locales (JSON)": limitations_other,
        "Research Entity ID": model.research_entity_id or "",
        "Local Number": _text(model.public_number), "Local PK": _text(model.pk),
    }
    row.update(_research_columns(model))
    return row


def tool_row(tool):
    description, description_ru, description_other = _locales(tool.description)
    ecosystem, ecosystem_ru, ecosystem_other = _locales(tool.ecosystem)
    row = {
        "Record ID": tool.slug, "Name": tool.name, "Developer": tool.developer.name,
        "Exact Release Date": _text(tool.released),
        "Approx Date": _approx(tool.approx_released, tool.approx_precision),
        "On Local": _text(tool.published),
        "Version": tool.version, "Category": tool.category,
        "Purposes": "; ".join(tool.purposes or []), "Local Execution": tool.local_execution,
        "Official URL": tool.official_url,
        "Platforms": "; ".join(link.platform.code for link in tool.platform_links.all()),
        "Supported Models": "; ".join(link.model.slug for link in tool.model_links.all()),
        "Catalog Status": tool.catalog_status, "Developer Country": tool.developer.country,
        "Description EN": description, "Description RU": description_ru,
        "Ecosystem EN": ecosystem, "Ecosystem RU": ecosystem_ru,
        "Source Title": tool.source.title, "Source URL": tool.source.url,
        "Source Publisher": tool.source.publisher, "Checked (DB)": _text(tool.checked),
        "Release Evidence (JSON)": _json(tool.release_evidence),
        "Approx Evidence (JSON)": _json(tool.approx_evidence),
        "Description Other Locales (JSON)": description_other,
        "Ecosystem Other Locales (JSON)": ecosystem_other,
        "Legacy Record ID": tool.legacy_version.slug if tool.legacy_version_id else "",
        "Local Number": _text(tool.public_number), "Local PK": _text(tool.pk),
    }
    row.update(_research_columns(tool))
    return row


def _owner(model_version, tool_by_legacy):
    """(record type, record id) for a ModelVersion-owned relation."""
    tool = tool_by_legacy.get(model_version.pk)
    if tool is not None:
        return "tool", tool.slug
    return "model", model_version.slug


def _service(service):
    return {
        "Service": service.name, "Service Kind": service.kind, "Service URL": service.url,
        "Provider": service.provider.name, "Compute Location": service.compute_location,
    }


def local_snapshot():
    """Every Local Model/Tool record and relation as master rows."""
    from .models import (
        Access, Evaluation, Fact, ModelOriginCountry, ModelVersion, Offer, Tool, ToolPlatform,
    )

    tools = list(Tool.objects.select_related("developer", "source", "legacy_version")
                 .prefetch_related("platform_links__platform", "model_links__model")
                 .order_by("public_number", "slug"))
    tool_by_legacy = {t.legacy_version_id: t for t in tools if t.legacy_version_id}
    models = list(ModelVersion.objects.filter(entry_type="model")
                  .select_related("family__developer", "source")
                  .prefetch_related("origin_country_links")
                  .order_by("public_number", "slug"))
    snapshot = {
        "Models": {m.slug: (model_row(m), _verification(m)) for m in models},
        "Tools": {t.slug: (tool_row(t), _verification(t)) for t in tools},
    }
    aux = {name: {} for name in AUX}
    for offer in Offer.objects.select_related("model", "service__provider", "source").order_by("pk"):
        kind, record = _owner(offer.model, tool_by_legacy)
        en, ru, extra = _locales(offer.conditions)
        aux["Offers"]["offer-%d" % offer.pk] = {
            "Record Type": kind, "Record ID": record, **_service(offer.service),
            "Amount": _decimal(offer.amount), "Unit": offer.unit, "Billing Unit": offer.billing_unit,
            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
            "Primary": _text(offer.primary), "Active": _text(offer.active),
            "Source URL": offer.source.url, "Checked": _text(offer.checked),
            "Research Key": offer.research_key or "",
        }
    for ev in Evaluation.objects.select_related("model", "benchmark", "source").order_by("pk"):
        kind, record = _owner(ev.model, tool_by_legacy)
        en, ru, extra = _locales(ev.conditions)
        aux["Evaluations"]["evaluation-%d" % ev.pk] = {
            "Record Type": kind, "Record ID": record, "Benchmark": ev.benchmark.name,
            "Protocol": ev.benchmark.protocol, "Benchmark Category": ev.benchmark.category,
            "Unit": ev.benchmark.unit, "Higher Is Better": _text(ev.benchmark.higher_is_better),
            "Score": _decimal(ev.score), "Evaluator": ev.evaluator, "Result Kind": ev.result_kind,
            "Independent": _text(ev.independent), "Public": _text(ev.public),
            "Measured": _text(ev.measured), "Configuration": ev.configuration,
            "Confidence Low": _decimal(ev.confidence_low), "Confidence High": _decimal(ev.confidence_high),
            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
            "Source URL": ev.source.url, "Checked": _text(ev.checked),
            "Observation Key": ev.observation_key or "", "Source Model": ev.source_model,
            "Source Record ID": ev.source_record_id, "Snapshot": ev.snapshot,
            "Source SHA256": ev.source_sha256,
        }
    for access in Access.objects.select_related("model", "service__provider", "source").order_by("pk"):
        kind, record = _owner(access.model, tool_by_legacy)
        aux["Access"]["access-%d" % access.pk] = {
            "Record Type": kind, "Record ID": record, **_service(access.service),
            "Source URL": access.source.url, "Checked": _text(access.checked),
        }
    for fact in Fact.objects.select_related("model", "source").order_by("pk"):
        kind, record = _owner(fact.model, tool_by_legacy)
        aux["Facts"]["fact-%d" % fact.pk] = {
            "Record Type": kind, "Record ID": record, "Fact": fact.key,
            "Value (JSON)": _json(fact.value), "Source URL": fact.source.url,
            "Checked": _text(fact.checked),
        }
    for link in ModelOriginCountry.objects.select_related("model", "source").order_by("pk"):
        aux["Origins"]["origin-%d" % link.pk] = {
            "Record Type": "model", "Record ID": link.model.slug, "Country": link.country_id,
            "Position": _text(link.position), "Source URL": link.source.url,
            "Checked": _text(link.checked),
        }
    for link in ToolPlatform.objects.select_related("tool", "platform", "source").order_by("pk"):
        aux["Tool Platforms"]["platform-%d" % link.pk] = {
            "Record Type": "tool", "Record ID": link.tool.slug, "Platform": link.platform.code,
            "Source URL": link.source.url, "Checked": _text(link.checked),
        }
    return snapshot, aux


def fetch_production(origin=PRODUCTION_ORIGIN, timeout=60):
    """Read-only: slugs listed in the public sitemap plus the live release."""
    def get(path):
        request = urllib.request.Request(origin + path, headers={"User-Agent": "aipedia-catalog-master"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")

    sitemap = get("/sitemap.xml")
    found = {"Models": set(), "Tools": set()}
    for kind, slug in re.findall(r"<loc>[^<]*?/(models|tools)/([^?<]+)", sitemap):
        found["Models" if kind == "models" else "Tools"].add(slug)
    release = ""
    try:
        release = json.loads(get("/healthz")).get("release", "")
    except (OSError, ValueError):
        pass
    return found, release


# ------------------------------------------------------------ master logic

def missing_items(sheet, row):
    if row.get("Publication Decision") == "ARCHIVE":
        # Archived variants need only their identity, source and reason.
        return [key for column, key in (
            ("Reason", "reason"), ("Official Source", "official_source"),
            ("Last Verified", "last_verified")) if not row.get(column)]
    items = []
    if not row.get("Publication Decision"):
        items.append("publication_decision")
    for column, key in (("Name", "name"), ("Developer", "developer"), ("Category", "category")):
        if not row.get(column):
            items.append(key)
    if not row.get("Exact Release Date") and not row.get("Approx Date"):
        items.append("date (exact or ≈)")
    if not row.get("Official Source"):
        items.append("official_source")
    if not row.get("Last Verified"):
        items.append("last_verified")
    if not row.get("Description EN"):
        items.append("description_en")
    return items


def chronology_date(row):
    value = row.get("Exact Release Date") or row.get("Approx Date", "").lstrip("≈").strip()
    if not value:
        return None
    parts = value.split("-")
    try:
        return date(int(parts[0]), int(parts[1]) if len(parts) > 1 else 1,
                    int(parts[2]) if len(parts) > 2 else 1)
    except ValueError:
        return None


def approx_precision(value):
    value = (value or "").lstrip("≈").strip()
    if not value:
        return ""
    return {1: "year", 2: "month", 3: "day"}.get(len(value.split("-")), "")


def chronology_numbers(rows):
    """Record ID -> Public Number for PUBLISHED rows with a verified date."""
    dated = [r for r in rows if r.get("Status") == "PUBLISHED"
             and r.get("Publication Decision") == "PUBLIC" and chronology_date(r)]
    dated.sort(key=lambda r: (chronology_date(r), alphabet(r.get("Name", "")), r["Record ID"]))
    return {r["Record ID"]: str(n) for n, r in enumerate(dated, 1)}


def refresh_derived(workbook_rows, changelog, reason, stamp, quiet_ids=()):
    """Recompute Missing Data, counts and Public Numbers; log number changes."""
    counts = {}
    for aux_sheet in ("Offers", "Evaluations", "Access"):
        for row in workbook_rows.get(aux_sheet, []):
            key = (RECORD_TYPE_SHEET.get(row.get("Record Type"), ""), row.get("Record ID"), aux_sheet)
            counts[key] = counts.get(key, 0) + 1
    changed = 0
    for sheet in MAIN:
        rows = workbook_rows[sheet]
        numbers = chronology_numbers(rows)
        for row in rows:
            row["Approx Precision"] = approx_precision(row.get("Approx Date"))
            items = missing_items(sheet, row)
            row["Missing Data"] = "; ".join(items)
            row["Missing Count"] = str(len(items))
            for aux_sheet in ("Offers", "Evaluations", "Access"):
                if aux_sheet in MAIN[sheet]:
                    row[aux_sheet] = str(counts.get((sheet, row["Record ID"], aux_sheet), 0))
            new = numbers.get(row["Record ID"], "")
            if row.get("Public Number", "") != new:
                if row["Record ID"] not in quiet_ids:
                    changelog.append({
                        "Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": row["Record ID"],
                        "Field": "Public Number", "Before": row.get("Public Number", ""),
                        "After": new, "Reason": reason,
                    })
                    changed += 1
                row["Public Number"] = new
    return changed


def import_from_local(workbook_rows, snapshot, aux, production=None, stamp=None):
    """Merge Local into the master; master data wins for existing records.

    Returns a summary dict. `production` is (found slugs per sheet, release)
    from fetch_production, or None to keep existing On Production values.
    """
    stamp = stamp or now_utc()
    changelog = workbook_rows.setdefault("Changelog", [])
    added_ids, summary = set(), {}
    for sheet, columns in MAIN.items():
        rows = workbook_rows.setdefault(sheet, [])
        known = {r["Record ID"] for r in rows}
        for row in rows:
            local = snapshot[sheet].get(row["Record ID"])
            if local is not None:
                row.update({k: v for k, v in local[0].items() if k in LOCAL_OWNED})
            elif row.get("Record ID"):
                row["On Local"] = "NO"
        added = 0
        for record_id, (local_row, verification) in snapshot[sheet].items():
            if record_id in known:
                continue
            row = {c: "" for c in columns}
            row.update(local_row)
            row.update(verification)
            rows.append(row)
            added_ids.add(record_id)
            added += 1
        if production is not None:
            found = production[0][sheet]
            for row in rows:
                row["On Production"] = "YES" if row["Record ID"] in found else "NO"
        if added:
            changelog.append({
                "Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": "*", "Field": "rows",
                "Before": str(len(rows) - added), "After": str(len(rows)),
                "Reason": "import from Local: added %d records" % added,
            })
        summary[sheet] = {"rows": len(rows), "added": added}
    for sheet in AUX:
        rows = workbook_rows.setdefault(sheet, [])
        known = {r["Key"] for r in rows}
        new = [{"Key": key, **values} for key, values in aux[sheet].items() if key not in known]
        rows.extend(new)
        if new:
            changelog.append({
                "Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": "*", "Field": "rows",
                "Before": str(len(rows) - len(new)), "After": str(len(rows)),
                "Reason": "import from Local: added %d rows" % len(new),
            })
        summary[sheet] = {"rows": len(rows), "added": len(new)}
    summary["renumbered"] = refresh_derived(
        workbook_rows, changelog, "chronology recomputed on import", stamp, quiet_ids=added_ids)
    return summary


def validate(workbook_rows, snapshot=None, aux=None):
    """Return (errors, warnings, drift) for the master workbook."""
    errors, warnings, drift = [], [], {}
    ids = {}
    for sheet in MAIN:
        categories = MODEL_CATEGORIES if sheet == "Models" else TOOL_CATEGORIES
        rows = workbook_rows.get(sheet, [])
        numbers = chronology_numbers(rows)
        seen, parents = {}, []
        for index, row in enumerate(rows, start=2):
            record = row.get("Record ID", "")
            where = "%s row %d (%s)" % (sheet, index, record or row.get("Name") or "?")
            if not record:
                errors.append("%s: empty Record ID" % where)
                continue
            if not RECORD_ID.match(record):
                errors.append("%s: Record ID may contain only letters, digits, '-' and '_'" % where)
            if record in seen:
                errors.append("%s: duplicate Record ID (row %d)" % (where, seen[record]))
            seen[record] = index
            status = row.get("Status", "")
            if status not in STATUSES:
                errors.append("%s: Status must be PUBLISHED or NEEDS_REVIEW" % where)
            exact, approx = row.get("Exact Release Date", ""), row.get("Approx Date", "")
            if exact and not _valid_iso(exact):
                errors.append("%s: Exact Release Date must be YYYY-MM-DD" % where)
            if approx and not APPROX_DATE.match(approx):
                errors.append("%s: Approx Date must look like ≈YYYY, ≈YYYY-MM or ≈YYYY-MM-DD" % where)
            if exact and approx:
                errors.append("%s: fill either Exact Release Date or Approx Date, not both" % where)
            if row.get("Last Verified") and not _valid_iso(row["Last Verified"]):
                errors.append("%s: Last Verified must be YYYY-MM-DD" % where)
            for column in ("On Local", "On Production", "Open Weights"):
                if row.get(column) and row[column] not in YES_NO:
                    errors.append("%s: %s must be YES/NO" % (where, column))
            if row.get("Category") and row["Category"] not in categories:
                errors.append("%s: unknown Category %s" % (where, row["Category"]))
            if row.get("Catalog Status") and row["Catalog Status"] not in CATALOG_STATUSES:
                errors.append("%s: unknown Catalog Status %s" % (where, row["Catalog Status"]))
            if row.get("Release Stage") and row["Release Stage"] not in STAGES:
                errors.append("%s: unknown Release Stage %s" % (where, row["Release Stage"]))
            if row.get("Local Execution") and row["Local Execution"] not in LOCAL_EXECUTION:
                errors.append("%s: unknown Local Execution %s" % (where, row["Local Execution"]))
            decision = row.get("Publication Decision", "")
            if decision not in DECISIONS:
                errors.append("%s: Publication Decision must be PUBLIC, ARCHIVE or NEEDS_REVIEW" % where)
            if status == "PUBLISHED" and decision != "PUBLIC":
                errors.append("%s: PUBLISHED requires Publication Decision PUBLIC" % where)
            if decision == "ARCHIVE":
                lacking = [c for c in ("Reason", "Official Source") if not row.get(c)]
                if lacking:
                    errors.append("%s: ARCHIVE requires %s" % (where, ", ".join(lacking)))
            parent = row.get("Canonical / Parent Record ID", "")
            if parent == record:
                errors.append("%s: Canonical / Parent Record ID points to itself" % where)
            elif parent:
                parents.append((where, parent))
            if status == "PUBLISHED":
                lacking = [c for c in ("Name", "Developer", "Official Source", "Last Verified") if not row.get(c)]
                if lacking:
                    errors.append("%s: PUBLISHED requires %s" % (where, ", ".join(lacking)))
                if not chronology_date(row):
                    warnings.append(("PUBLISHED without verified date: no Public Number", where))
                if row.get("On Local") == "NO":
                    warnings.append(("PUBLISHED but not public on Local: pending sync", where))
                if row.get("On Production") == "NO":
                    warnings.append(("PUBLISHED but not on Production: pending release", where))
            elif status == "NEEDS_REVIEW":
                for column, place in (("On Local", "Local"), ("On Production", "Production")):
                    if row.get(column) == "YES":
                        warnings.append(("not PUBLISHED (%s) but public on %s: hide at next sync"
                                         % (decision or "?", place), where))
            if row.get("Public Number", "") != numbers.get(record, ""):
                errors.append("%s: Public Number %s differs from chronology %s (run import)" % (
                    where, row.get("Public Number") or "-", numbers.get(record) or "-"))
            local_number, public_number = row.get("Local Number", ""), row.get("Public Number", "")
            if local_number != public_number:
                if not public_number:
                    kind = "Local Number without master Public Number: cleared at sync"
                elif not local_number:
                    kind = "Public Number not yet on Local: assigned at sync"
                else:
                    kind = "Local Number differs from Public Number: renumber at sync"
                warnings.append((kind, "%s [%s -> %s]" % (where, local_number or "-", public_number or "-")))
        for where, parent in parents:
            if parent not in seen:
                errors.append("%s: Canonical / Parent Record ID %s not found in %s" % (where, parent, sheet))
        ids[sheet] = set(seen)
    for sheet in AUX:
        seen = set()
        for index, row in enumerate(workbook_rows.get(sheet, []), start=2):
            where = "%s row %d" % (sheet, index)
            if not row.get("Key"):
                errors.append("%s: empty Key" % where)
            elif row["Key"] in seen:
                errors.append("%s: duplicate Key %s" % (where, row["Key"]))
            seen.add(row.get("Key"))
            target = RECORD_TYPE_SHEET.get(row.get("Record Type"))
            if target is None:
                errors.append("%s: Record Type must be model or tool" % where)
            elif row.get("Record ID") not in ids.get(target, set()):
                errors.append("%s: Record ID %s not found in %s" % (where, row.get("Record ID"), target))
    if snapshot is not None:
        for sheet in MAIN:
            master = {r.get("Record ID"): r for r in workbook_rows.get(sheet, [])}
            missing = sorted(set(snapshot[sheet]) - set(master))
            if missing:
                errors.append("%s: %d Local records absent from master: %s" % (
                    sheet, len(missing), ", ".join(missing[:10])))
            fields = records = 0
            for record_id, (local_row, _) in snapshot[sheet].items():
                row = master.get(record_id)
                if row is None:
                    continue
                diff = sum(1 for c in PUBLIC[sheet] if row.get(c, "") != local_row.get(c, ""))
                fields += diff
                records += bool(diff)
            drift[sheet] = {"records": records, "fields": fields}
    if aux is not None:
        for sheet in AUX:
            master = {r.get("Key"): r for r in workbook_rows.get(sheet, [])}
            missing = sorted(set(aux[sheet]) - set(master))
            if missing:
                errors.append("%s: %d Local rows absent from master: %s" % (
                    sheet, len(missing), ", ".join(missing[:10])))
            fields = records = 0
            for key, values in aux[sheet].items():
                row = master.get(key)
                if row is None:
                    continue
                diff = sum(1 for c, v in values.items() if row.get(c, "") != v)
                fields += diff
                records += bool(diff)
            drift[sheet] = {"records": records, "fields": fields}
    return errors, warnings, drift


# ---------------------------------------------------------------- workbook IO

def read_workbook(path=WORKBOOK_PATH):
    """Return (rows per sheet, meta dict, extra headers per sheet); all text."""
    from openpyxl import load_workbook

    workbook = load_workbook(path)
    if "Meta" not in workbook.sheetnames:
        raise ValueError("%s is not a catalog master (no Meta sheet)" % path)
    meta = {_text(k): _text(v) for k, v in workbook["Meta"].iter_rows(min_row=2, values_only=True) if k}
    upgrading = meta.get("Schema") in UPGRADABLE_SCHEMAS
    if meta.get("Schema") != SCHEMA and not upgrading:
        raise ValueError("%s has schema %r, expected %r" % (path, meta.get("Schema"), SCHEMA))
    rows, extra = {}, {}
    for sheet, columns in [*MAIN.items(), *AUX.items(), ("Changelog", CHANGELOG)]:
        if sheet not in workbook.sheetnames:
            raise ValueError("%s lacks sheet %s" % (path, sheet))
        values = workbook[sheet].iter_rows(values_only=True)
        headers = [_text(h) for h in next(values, [])]
        absent = [c for c in columns if c not in headers]
        if upgrading and sheet in MAIN:
            absent = [c for c in absent if c not in (
                "Publication Decision", "Approx Precision", "Reason", "Canonical / Parent Record ID")]
        if absent:
            raise ValueError("%s sheet %s lacks columns: %s" % (path, sheet, ", ".join(absent)))
        extra[sheet] = [h for h in headers if h and h not in columns]
        rows[sheet] = []
        for raw in values:
            row = {h: _text(v) for h, v in zip(headers, raw) if h}
            if any(row.values()):
                if upgrading and sheet in MAIN and not row.get("Publication Decision"):
                    row["Publication Decision"] = "PUBLIC" if row.get("Status") == "PUBLISHED" else "NEEDS_REVIEW"
                rows[sheet].append(row)
    if upgrading:
        meta["Schema"] = SCHEMA
    return rows, meta, extra


RULES_RU = [
    ("Назначение", "Единая каноническая база AIpediya: все Models и Tools — опубликованные, скрытые кандидаты и новые находки. Запись сначала появляется и проверяется здесь; затем PUBLISHED-строки синхронизируются в Local, а оттуда по docs/RELEASE.md — в Production."),
    ("Status", "PUBLISHED — запись проверена и входит в публичный каталог. NEEDS_REVIEW — запись не в публичном каталоге и остаётся только в master (нерешённые вопросы или ARCHIVE)."),
    ("Publication Decision", "PUBLIC — самостоятельная публичная модель/инструмент (Status PUBLISHED после проверки даты и источников). ARCHIVE — технический snapshot/checkpoint/dated API version/alias/дубликат/закрытая или кратковременная версия: остаётся в master, без Public Number, не в публичной таблице и sitemap, данные не удаляются, решение можно пересмотреть. NEEDS_REVIEW — существование, назначение или дата не подтверждены. Решение — только по официальному описанию (release, model card, API product vs snapshot/alias), не по похожему названию."),
    ("Reason", "Почему запись не публикуется отдельно (обязательно для ARCHIVE) или что мешает решению."),
    ("Canonical / Parent Record ID", "Record ID основной записи того же листа, если это вариант, snapshot или alias."),
    ("Approx Precision", "Вычисляется из Approx Date: year / month / day."),
    ("Record ID", "Slug записи. Стабильная идентичность: после создания не меняется никогда (URL /models/<id>, /tools/<id>). Для новой записи — латиница, цифры, '-' и '_', уникально в листе."),
    ("Public Number", "Вычисляется, вручную не править. Хронологический номер по verified release date среди PUBLISHED: точная дата, иначе ≈ дата (начало периода); при равной дате — по имени, затем Record ID. Новая модель получает следующий номер; найденная позже историческая встаёт на своё место, последующие номера сдвигаются — каждое изменение пишется в Changelog."),
    ("Даты", "Exact Release Date — только подтверждённая (YYYY-MM-DD). Если точной нет, но есть надёжная дата первого публичного существования — Approx Date: ≈YYYY-MM или ≈YYYY-MM-DD. Обе сразу не заполнять. Дату git-коммита за дату выпуска не выдавать."),
    ("Проверка", "Official Source — первичный источник; Secondary Source — независимое подтверждение; Last Verified — дата проверки (YYYY-MM-DD). У PUBLISHED обязательны Name, Developer, Official Source, Last Verified. Ссылки импорта лежат в Import Sources (unverified) и ничего не подтверждают."),
    ("Missing Data", "Вычисляется: чего не хватает записи (publication_decision, name, developer, category, date, official_source, last_verified, description_en; для ARCHIVE — только reason, official_source, last_verified). Пусто = данных достаточно."),
    ("On Local / On Production", "Факт публичности записи в Local (база) и на Production (публичный sitemap, только чтение). Расхождение со Status = работа для синхронизации."),
    ("Local Number", "Номер, который сейчас стоит в Local. Отличие от Public Number = перенумерация при следующей синхронизации."),
    ("Связанные листы", "Offers, Evaluations, Access, Facts, Origins, Tool Platforms — цены, оценки, доступ, факты, страны и платформы; связь по Record Type + Record ID. Key — стабильный ключ строки; для новой строки придумать уникальный (например offer-new-<record>-1)."),
    ("Локализации", "EN и RU — редактируемые колонки. Остальные 20 локалей из записи лежат в *Other Locales (JSON) и выводятся из английского конвейером переводов."),
    ("Неизвестное", "Оставлять пустым, не нулём и не догадкой."),
    ("Changelog", "Журнал изменений master: импорт, перенумерация, ручные правки важных полей (агенту — добавить строку)."),
    ("Команды", "Импорт/обновление из Local (master не перетирается): .\\.venv\\Scripts\\python.exe manage.py catalog_master import [--production] | Проверка: … manage.py catalog_master check [--production]"),
    ("Production", "Таблица и команды не публикуют и не меняют Production; --production только читает публичный sitemap."),
]


def write_workbook(workbook_rows, meta, path=WORKBOOK_PATH, extra=None):
    """Write the whole master atomically (temp file, then replace)."""
    from openpyxl import Workbook
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    extra = extra or {}

    def fill(color):
        # Excel reads conditional-format fills from bgColor, not fgColor.
        return PatternFill("solid", fgColor=color, bgColor=color)

    header_fills = {"workflow": "1F3A5F", "verification": "7A4B00", "public": "2F5D3A", "service": "6B7280"}
    workbook = Workbook()
    workbook.remove(workbook.active)

    def write_sheet(name, columns, rows, groups=None, widths=None):
        sheet = workbook.create_sheet(name)
        headers = columns + [h for h in extra.get(name, []) if h not in columns]
        sheet.append(headers)
        for row in rows:
            values = []
            for header in headers:
                value = row.get(header, "")
                if isinstance(value, str):
                    value = ILLEGAL_CHARACTERS_RE.sub("", value)
                values.append(value or None)
            sheet.append(values)
            for cell in sheet[sheet.max_row]:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    cell.data_type = "s"
        for index, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=index)
            group = (groups or {}).get(header, "service")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor=header_fills[group])
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            letter = get_column_letter(index)
            sheet.column_dimensions[letter].width = (widths or {}).get(header, 16)
            sheet.column_dimensions[letter].number_format = "@"
        sheet.row_dimensions[1].height = 32
        sheet.auto_filter.ref = "A1:%s%d" % (get_column_letter(len(headers)), max(len(rows) + 1, 2))
        return sheet, {h: get_column_letter(i) for i, h in enumerate(headers, start=1)}

    def validation(sheet, letter, values):
        rule = DataValidation(type="list", formula1='"%s"' % ",".join(values), allow_blank=True)
        rule.error = "Allowed: " + ", ".join(values)
        rule.showErrorMessage = True
        sheet.add_data_validation(rule)
        rule.add("%s2:%s%d" % (letter, letter, MAX_VALIDATED_ROW))

    widths = {
        "Record ID": 34, "Status": 15, "Public Number": 9, "Name": 34, "Developer": 24,
        "Exact Release Date": 13, "Approx Date": 12, "Missing Data": 40,
        "Official Source": 40, "Secondary Source": 32, "Last Verified": 12,
        "On Local": 9, "On Production": 11, "Notes": 50, "Description EN": 50,
        "Description RU": 50, "Source URL": 36, "Official URL": 32,
    }
    last = MAX_VALIDATED_ROW
    for name, columns in MAIN.items():
        groups = {c: "workflow" for c in WORKFLOW}
        groups.update({c: "verification" for c in VERIFICATION})
        groups.update({c: "public" for c in (MODEL_PUBLIC if name == "Models" else TOOL_PUBLIC)})
        sheet, col = write_sheet(name, columns, workbook_rows[name], groups, widths)
        sheet.freeze_panes = "F2"
        validation(sheet, col["Status"], STATUSES)
        validation(sheet, col["Publication Decision"], DECISIONS)
        decision = col["Publication Decision"]
        for value, color in (("PUBLIC", "C6E0B4"), ("ARCHIVE", "D9D9D9"), ("NEEDS_REVIEW", "FFF4CE")):
            sheet.conditional_formatting.add(
                "%s2:%s%d" % (decision, decision, last),
                FormulaRule(formula=['$%s2="%s"' % (decision, value)], fill=fill(color)))
        validation(sheet, col["On Local"], YES_NO)
        validation(sheet, col["On Production"], YES_NO)
        validation(sheet, col["Category"], MODEL_CATEGORIES if name == "Models" else TOOL_CATEGORIES)
        validation(sheet, col["Catalog Status"], CATALOG_STATUSES)
        if name == "Models":
            validation(sheet, col["Release Stage"], STAGES)
            validation(sheet, col["Open Weights"], YES_NO)
        else:
            validation(sheet, col["Local Execution"], LOCAL_EXECUTION)
        status = col["Status"]
        for value, color in (("PUBLISHED", "C6E0B4"), ("NEEDS_REVIEW", "FFF4CE")):
            sheet.conditional_formatting.add(
                "%s2:%s%d" % (status, status, last),
                FormulaRule(formula=['$%s2="%s"' % (status, value)], fill=fill(color)))
        missing = col["Missing Data"]
        sheet.conditional_formatting.add(
            "%s2:%s%d" % (missing, missing, last),
            FormulaRule(formula=['$%s2<>""' % missing], fill=fill("F8CBAD")))
        for column in ("On Local", "On Production"):
            letter = col[column]
            sheet.conditional_formatting.add(
                "%s2:%s%d" % (letter, letter, last),
                FormulaRule(formula=['OR(AND($%s2="NEEDS_REVIEW",$%s2="YES"),AND($%s2="PUBLISHED",$%s2="NO"))'
                                     % (status, letter, status, letter)], fill=fill("F4B6B6")))
    for name, columns in AUX.items():
        sheet, col = write_sheet(name, columns, workbook_rows[name], widths={"Key": 18, "Record ID": 34})
        sheet.freeze_panes = "D2"
        validation(sheet, col["Record Type"], ["model", "tool"])
    sheet, _ = write_sheet("Changelog", CHANGELOG, workbook_rows.get("Changelog", []),
                           widths={"Timestamp (UTC)": 21, "Record ID": 34, "Reason": 60})
    sheet.freeze_panes = "A2"

    meta_sheet = workbook.create_sheet("Meta")
    meta_sheet.append(["Key", "Value"])
    for key, value in meta.items():
        meta_sheet.append([key, value])
    meta_sheet.column_dimensions["A"].width = 28
    meta_sheet.column_dimensions["B"].width = 70

    rules = workbook.create_sheet("Rules")
    rules.append(["Правило", "Описание"])
    for item in RULES_RU:
        rules.append(list(item))
    rules.column_dimensions["A"].width = 26
    rules.column_dimensions["B"].width = 130
    for (cell,) in rules.iter_rows(min_col=2, max_col=2):
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for (cell,) in rules.iter_rows(min_col=1, max_col=1):
        cell.font = Font(bold=True)

    lists = workbook.create_sheet("Lists")
    for index, (title, values) in enumerate([
            ("Status", STATUSES), ("Publication Decision", DECISIONS), ("YES/NO", YES_NO),
            ("Model Category", MODEL_CATEGORIES),
            ("Tool Category", TOOL_CATEGORIES), ("Catalog Status", CATALOG_STATUSES),
            ("Release Stage", STAGES), ("Local Execution", LOCAL_EXECUTION)], start=1):
        lists.cell(row=1, column=index, value=title).font = Font(bold=True)
        for offset, value in enumerate(values, start=2):
            lists.cell(row=offset, column=index, value=value)
        lists.column_dimensions[get_column_letter(index)].width = 20

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(suffix=".xlsx", dir=path.parent)
    os.close(handle)
    try:
        workbook.save(temp)
        os.replace(temp, path)
    except PermissionError as exc:
        raise PermissionError("%s is locked (close it in Excel and retry)" % path) from exc
    finally:
        if os.path.exists(temp):
            os.remove(temp)
