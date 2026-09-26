"""Minimal, safe synchronisation Catalog Master -> Local database.

What is transferred (see docs/CATALOG_MASTER.md, "Контракт sync-local"):

* publication: ``published`` follows master ``Status`` (PUBLISHED = shown);
* identity: ``aliases``; ``redirect_to`` (the canonical card) for hidden rows
  whose Relation Type is DUPLICATE_OF / ALIAS_OF / FORMAT_OF / MODE_OF;
* numbering: ``public_number`` = master ``Public Number`` (chronological plan of
  public, dated records); hidden and undated records get no number;
* fields of PUBLISHED rows: dates, release stage, lifecycle status, category,
  tasks/modalities, context, license, open weights, Description EN/RU; for
  tools also purposes, local execution, official URL;
* existing price rows (Offers, by Key): amount, unit, billing unit (only for
  Unit=other), conditions EN/RU, active, primary, checked date;
* existing evaluation rows (by Key): the ``Public`` flag only;
* the "Source" link of PUBLISHED records and of their existing price rows
  (switch to the master Source URL; an existing Source row keeps its title);
* platforms of PUBLISHED tools: missing ones are added, none removed;
* existing access rows: service kind / URL / compute location / name, only when
  that service belongs to this one access row (shared services are reported);
* creation of PUBLISHED master rows that Local lacks.

Everything else that differs for a PUBLISHED record (names, developers,
families, sources, other texts, platforms, origin countries, new or changed
access rows, new price/evaluation rows, ...) is NOT written: it is returned as
``unsupported`` items and reported as a warning by the command, never hidden
behind a general "synchronised" message. Drafts and deferred/archived records
are not created and their fields are not synced (they are not public).

An empty master cell never erases a Local value; ``<CLEAR>`` does. Record
changes go through ``save()`` with a revision row; only the renumbering step
writes ``public_number`` with a targeted update (``save()`` deliberately
refuses to change numbers) and logs every old/new number as a revision.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from . import catalog_master as cm

CLEAR = cm.CLEAR
ACTION = "catalog_master_sync"
RENUMBER = "catalog_master_renumber"

MODEL_FIELDS = {
    "Release Stage": "release_stage", "Category": "category", "Tasks": "tasks",
    "Input Modalities": "input_modalities", "Output Modalities": "output_modalities",
    "Context": "context", "License": "license", "Open Weights": "open_weights",
    "Catalog Status": "catalog_status",
}
TOOL_FIELDS = {
    "Category": "category", "Purposes": "purposes", "Local Execution": "local_execution",
    "Official URL": "official_url", "Catalog Status": "catalog_status",
}
TEXT_FIELDS = {"Description EN": ("description", "en"), "Description RU": ("description", "ru")}
MODEL_TEXT_FIELDS = {"Suitable EN": ("suitable", "en"), "Suitable RU": ("suitable", "ru"),
                     "Limitations EN": ("limitations", "en"), "Limitations RU": ("limitations", "ru")}
LIST_FIELDS = {"tasks", "input_modalities", "output_modalities", "purposes"}
SUPPORTED_COLUMNS = {
    "Models": set(MODEL_FIELDS) | set(TEXT_FIELDS) | set(MODEL_TEXT_FIELDS) | {"Exact Release Date", "Approx Date"},
    "Tools": set(TOOL_FIELDS) | set(TEXT_FIELDS) | {"Exact Release Date", "Approx Date"},
}
# Master columns that are internal/derived and never compared.
IGNORED_COLUMNS = {"Checked (DB)", "Release Evidence (JSON)", "Approx Evidence (JSON)",
                   "Description Other Locales (JSON)", "Suitable Other Locales (JSON)",
                   "Limitations Other Locales (JSON)", "Ecosystem Other Locales (JSON)",
                   "Research Entity ID", "Legacy Record ID"}
OFFER_FIELDS = ["Amount", "Unit", "Billing Unit", "Conditions EN", "Conditions RU", "Active", "Primary", "Checked"]
LOCAL_FACT_KEYS = {"modalities", "languages", "speed", "memory", "energy", "training", "ownership", "service_price"}


def _split(value):
    return [part.strip() for part in value.replace(",", ";").split(";") if part.strip()]


def _convert(attr, value):
    if value == CLEAR:
        if attr in LIST_FIELDS:
            return []
        return {"context": None, "open_weights": False}.get(attr, "")
    if attr in LIST_FIELDS:
        return _split(value)
    if attr == "context":
        return int(value)
    if attr == "open_weights":
        return value == "YES"
    return value


def _dates(row):
    """(released, approx_released, approx_precision), or "silent" when the master says nothing."""
    exact, approx = row.get("Exact Release Date", ""), row.get("Approx Date", "")
    if exact == CLEAR and approx in ("", CLEAR):
        return None, None, ""
    if exact and exact != CLEAR:
        return date.fromisoformat(exact), None, ""
    if approx and approx != CLEAR:
        value = approx.lstrip("≈").strip()
        precision = cm.approx_precision(value)
        parts = [int(p) for p in value.split("-")] + [1, 1]
        return None, date(parts[0], parts[1], parts[2]), "day" if precision == "day" else "month"
    return "silent"


def _redirects(sheet_rows, workbook_rows=None):
    by_id = {r["Record ID"]: r for r in sheet_rows}
    out = {}
    for row in sheet_rows:
        if row.get("Publication Decision") == "ARCHIVE" and row.get("Relation Type") in cm.SAME_ENTITY:
            cross = cm.cross_parent(row.get("Canonical / Parent Record ID", ""))
            if cross and workbook_rows is not None:
                other = {r["Record ID"]: r for r in workbook_rows.get(cross[0], [])}
                if other.get(cross[1], {}).get("Status") == "PUBLISHED":
                    out[row["Record ID"]] = cross[1]  # the view resolves it on the other catalog
                continue
            target = cm.canonical_target(row, by_id)
            if target and by_id[target].get("Status") == "PUBLISHED":
                out[row["Record ID"]] = target
    return out


def _value(obj, attr):
    if attr == "source":
        return obj.source.url
    value = getattr(obj, attr)
    return list(value) if isinstance(value, list) else value


def target_numbers(workbook_rows):
    """(sheet, Record ID) -> planned public number (int) or None."""
    out = {}
    for sheet in cm.MAIN:
        for row in workbook_rows[sheet]:
            number = row.get("Public Number", "")
            out[(sheet, row["Record ID"])] = int(number) if number and row.get("Status") == "PUBLISHED" else None
    return out


def _offer_values(row):
    values = {}
    if row.get("Amount"):
        try:
            values["amount"] = None if row["Amount"] == CLEAR else Decimal(row["Amount"])
        except InvalidOperation:
            pass
    if row.get("Unit") and row["Unit"] != CLEAR:
        values["unit"] = row["Unit"]
    # The site shows a Billing Unit instead of its localized standard unit label
    # and leaves such prices out of comparisons, so it is written only for
    # Unit=other (contract); for standard units it stays an informational note.
    if row.get("Billing Unit") and (row.get("Unit") == "other" or row["Billing Unit"] == CLEAR):
        values["billing_unit"] = "" if row["Billing Unit"] == CLEAR else row["Billing Unit"]
    for column, flag in (("Active", "active"), ("Primary", "primary")):
        if row.get(column) in ("YES", "NO"):
            values[flag] = row[column] == "YES"
    if row.get("Checked") and row["Checked"] != CLEAR:
        try:
            values["checked"] = date.fromisoformat(row["Checked"])
        except ValueError:
            pass
    return values


def plan(workbook_rows, snapshot=None, aux=None):
    """Return a list of change dicts; nothing is written.

    ``snapshot``/``aux`` (from ``catalog_master.local_snapshot``) enable the
    ``unsupported`` report; without them only supported changes are planned.
    """
    from .models import Access, Evaluation, ModelVersion, Offer, Platform, Tool

    changes = []
    platform_codes = set(Platform.objects.values_list("code", flat=True))
    numbers = target_numbers(workbook_rows)
    published_ids = {sheet: {r["Record ID"] for r in workbook_rows[sheet] if r.get("Status") == "PUBLISHED"}
                     for sheet in cm.MAIN}
    for sheet, manager, fields in (
            ("Models", ModelVersion.objects.filter(entry_type="model"), MODEL_FIELDS),
            ("Tools", Tool.objects.all(), TOOL_FIELDS)):
        rows = workbook_rows[sheet]
        redirects = _redirects(rows, workbook_rows)
        local = {obj.slug: obj for obj in manager}
        for row in rows:
            rid = row["Record ID"]
            obj = local.get(rid)
            publish = row.get("Status") == "PUBLISHED"
            if obj is None:
                if publish:
                    changes.append({"sheet": sheet, "id": rid, "kind": "create", "row": row})
                continue
            wanted = {}
            if obj.published != publish:
                wanted["published"] = publish
            aliases = [a for a in cm.split_aliases(row.get("Aliases")) if a != CLEAR]
            if row.get("Aliases") and aliases != list(obj.aliases or []):
                wanted["aliases"] = aliases
            if redirects.get(rid, "") != obj.redirect_to:
                wanted["redirect_to"] = redirects.get(rid, "")
            if publish:
                for column, attr in fields.items():
                    raw = row.get(column, "")
                    if not raw:
                        continue  # silent master cell: keep the Local value
                    try:
                        value = _convert(attr, raw)
                    except ValueError:
                        continue
                    if value != _value(obj, attr):
                        wanted[attr] = value
                texts = {}
                for column, (attr, lang) in {**TEXT_FIELDS, **(MODEL_TEXT_FIELDS if sheet == "Models" else {})}.items():
                    value = texts.setdefault(attr, dict(getattr(obj, attr) or {}))
                    raw = row.get(column, "")
                    if raw and (raw if raw != CLEAR else "") != value.get(lang, ""):
                        if raw == CLEAR:
                            value.pop(lang, None)
                        else:
                            value[lang] = raw
                        wanted[attr] = value
                source_url = row.get("Source URL", "")
                if source_url and source_url != CLEAR and source_url != obj.source.url:
                    wanted["source"] = {"url": source_url, "title": row.get("Source Title") or row["Name"],
                                        "publisher": row.get("Source Publisher") or row.get("Developer", "")}
                dates = _dates(row)
                if dates != "silent":
                    released, approx, precision = dates
                    if (obj.released, obj.approx_released, obj.approx_precision) != (released, approx, precision):
                        wanted.update({"released": released, "approx_released": approx, "approx_precision": precision})
            if wanted:
                before = {k: _value(obj, k) for k in wanted}
                changes.append({"sheet": sheet, "id": rid, "kind": "update", "before": before, "after": wanted})
            if publish and sheet == "Tools":
                have = {link.platform.code for link in obj.platform_links.all()}
                missing = [code for code in _split(row.get("Platforms", "")) if code not in have and code in platform_codes]
                if missing:
                    changes.append({"sheet": sheet, "id": rid, "kind": "platforms", "before": sorted(have), "after": missing})
            if obj.public_number != numbers.get((sheet, rid)):
                changes.append({"sheet": sheet, "id": rid, "kind": "number",
                                "before": obj.public_number, "after": numbers.get((sheet, rid))})

    # Existing price/access rows whose owner changed in the master (e.g. the
    # prices of a model wrongly listed as a tool) move to the new owner.
    reassigned = set()
    for sheet, manager in (("Offers", Offer.objects), ("Access", Access.objects)):
        prefix = "offer-" if sheet == "Offers" else "access-"
        current = {prefix + str(o.pk): o for o in manager.select_related("model")}
        for row in workbook_rows.get(sheet, []):
            obj = current.get(row.get("Key"))
            owner_sheet = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
            if obj is None or row.get("Record ID") not in published_ids.get(owner_sheet, ()):
                continue
            wanted = "%s:%s" % (row["Record Type"], row["Record ID"])
            have = _owner_label(obj.model)
            if have != wanted and _owner_version(wanted) is not None:
                changes.append({"sheet": sheet, "id": row["Key"], "kind": "reassign",
                                "before": {"owner": have}, "after": {"owner": wanted},
                                "locator": _locator(obj, owner_after=_owner_version(wanted).slug)})
                reassigned.add(row["Key"])

    # Price rows (existing only) and evaluation visibility.
    offers = {"offer-%d" % o.pk: o for o in Offer.objects.all()}
    for row in workbook_rows.get("Offers", []):
        offer = offers.get(row.get("Key"))
        owner = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
        if offer is None or row.get("Record ID") not in published_ids.get(owner, ()):
            continue
        values = _offer_values(row)
        conditions = dict(offer.conditions or {})
        for column, lang in (("Conditions EN", "en"), ("Conditions RU", "ru")):
            if row.get(column) and row[column] != conditions.get(lang, ""):
                conditions[lang] = row[column]
                values["conditions"] = conditions
        wanted = {k: v for k, v in values.items() if getattr(offer, k) != v}
        source_url = row.get("Source URL", "")
        if source_url and source_url != CLEAR and source_url != offer.source.url:
            wanted["source"] = {"url": source_url, "title": source_url[:200], "publisher": row.get("Provider", "")[:120]}
        if wanted:
            identity = _offer_identity(offer)
            change = {"sheet": "Offers", "id": row["Key"], "kind": "offer",
                      "before": {k: (offer.source.url if k == "source" else getattr(offer, k)) for k in wanted},
                      "after": wanted, "identity": identity, "locator": _locator(offer)}
            if row.get("Key") in reassigned:
                # the owner changes first (reassign is planned earlier), so the
                # row may be found under either owner
                target = _owner_version("%s:%s" % (row["Record Type"], row["Record ID"]))
                change["identity_after"] = {**identity, "model": target.slug}
            changes.append(change)
    accesses = {"access-%d" % a.pk: a for a in Access.objects.select_related("service", "model")}
    for row in workbook_rows.get("Access", []):
        access = accesses.get(row.get("Key"))
        owner = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
        if access is None or row.get("Record ID") not in published_ids.get(owner, ()):
            continue
        diff = _service_diff(access, row)
        if diff and _exclusive_service(access):
            changes.append({"sheet": "Access", "id": row["Key"], "kind": "access_service",
                            "before": {k: getattr(access.service, k) for k in diff}, "after": diff,
                            "identity": {"model": access.model.slug, "service": access.service.name},
                            "locator": _locator(access, service_after=diff)})
    evaluations = {"evaluation-%d" % e.pk: e for e in Evaluation.objects.select_related("model")}
    for row in workbook_rows.get("Evaluations", []):
        evaluation = evaluations.get(row.get("Key"))
        if evaluation is None or row.get("Public") not in ("YES", "NO"):
            continue
        public = row["Public"] == "YES"
        if evaluation.public != public:
            changes.append({"sheet": "Evaluations", "id": row["Key"], "kind": "evaluation",
                            "before": {"public": evaluation.public}, "after": {"public": public},
                            "identity": {"model": evaluation.model.slug}, "locator": _locator(evaluation)})

    if snapshot is not None:
        changes.extend(_unsupported(workbook_rows, snapshot, aux or {}, published_ids))
    return changes


def _locator(obj, owner_after=None, service_after=None):
    """Stable, database-independent address of a price/evaluation/access row.

    Primary keys differ between Local and Production (found by the v014 server
    preflight), so plans locate rows by content: offers by their unique
    research_key, evaluations by their unique observation_key, access rows by
    (model, service name, service URL, evidence URL). Values after the change
    are included so an already applied plan is recognised.
    """
    from .models import Access, Evaluation, Offer
    if isinstance(obj, Offer) and obj.research_key:
        return {"research_key": obj.research_key}
    if isinstance(obj, Evaluation) and obj.observation_key:
        return {"observation_key": obj.observation_key}
    if isinstance(obj, Access):
        before = {"model": obj.model.slug, "service": obj.service.name, "service_url": obj.service.url,
                  "source_url": obj.source.url}
        after = dict(before)
        if owner_after:
            after["model"] = owner_after
        if service_after:
            after.update({"service": service_after.get("name", before["service"]),
                          "service_url": service_after.get("url", before["service_url"])})
        return {"access": before, "access_after": after}
    return {}


def _find_access(spec):
    from .models import Access
    found = list(Access.objects.filter(model__slug=spec["model"], service__name=spec["service"],
                                       service__url=spec["service_url"], source__url=spec["source_url"])[:2])
    return found[0] if len(found) == 1 else None


def resolve_row(change):
    """The target row of an aux change: by stable locator, else by the Local pk."""
    from .models import Access, Evaluation, Offer
    locator = change.get("locator") or {}
    cls = {"Offers": Offer, "Evaluations": Evaluation, "Access": Access}[change["sheet"]]
    if "research_key" in locator:
        return Offer.objects.filter(research_key=locator["research_key"]).select_related("model").first()
    if "observation_key" in locator:
        return Evaluation.objects.filter(observation_key=locator["observation_key"]).select_related("model").first()
    if "access" in locator:
        return _find_access(locator["access"]) or _find_access(locator["access_after"])
    return cls.objects.filter(pk=int(change["id"].split("-")[-1])).select_related("model").first()


def _owner_label(model_version):
    """'tool:<slug>' for a tool's legacy row, else 'model:<slug>'."""
    from .models import Tool
    tool = Tool.objects.filter(legacy_version=model_version).only("slug").first()
    return "tool:%s" % tool.slug if tool else "model:%s" % model_version.slug


def _owner_version(label):
    from .models import ModelVersion, Tool
    kind, _sep, slug = label.partition(":")
    if kind == "model":
        return ModelVersion.objects.filter(slug=slug, entry_type="model").first()
    tool = Tool.objects.filter(slug=slug).select_related("legacy_version").first()
    return tool.legacy_version if tool else None


SERVICE_COLUMNS = {"Service": "name", "Service Kind": "kind", "Service URL": "url", "Compute Location": "compute_location"}


def _service_diff(access, row):
    return {attr: row[column] for column, attr in SERVICE_COLUMNS.items()
            if row.get(column) and row[column] != CLEAR and row[column] != getattr(access.service, attr)}


def _exclusive_service(access):
    from .models import Access, Offer
    return (Access.objects.filter(service_id=access.service_id).count() == 1
            and not Offer.objects.filter(service_id=access.service_id).exists())


def _offer_identity(offer):
    return {"model": offer.model.slug, "unit": offer.unit, "research_key": offer.research_key or ""}


# Category of each unsupported difference, for the report.
SERVICE_ONLY = {"Source Title", "Source Publisher"}


def _unsupported(workbook_rows, snapshot, aux, published_ids):
    """Differences of PUBLISHED records that sync-local does not write."""
    items = []
    for sheet in cm.MAIN:
        for row in workbook_rows[sheet]:
            rid = row["Record ID"]
            if rid not in published_ids[sheet] or rid not in snapshot[sheet]:
                continue
            local_row = snapshot[sheet][rid][0]
            columns = [c for c in cm.PUBLIC[sheet]
                       if c not in SUPPORTED_COLUMNS[sheet] and c not in IGNORED_COLUMNS
                       and c not in ("Source URL",)
                       and row.get(c, "") and row.get(c) != local_row.get(c, "")]
            if sheet == "Tools" and "Platforms" in columns:
                extra = set(_split(local_row.get("Platforms", ""))) - set(_split(row.get("Platforms", "")))
                if not extra:
                    columns.remove("Platforms")  # only additions: supported
            for column in columns:
                items.append({"sheet": sheet, "id": rid, "kind": "unsupported", "columns": [column],
                              "category": "service" if column in SERVICE_ONLY else "public"})
    local_platforms = {(v.get("Record ID"), v.get("Platform")) for v in aux.get("Tool Platforms", {}).values()}
    local_origins = {(v.get("Record ID"), v.get("Country")) for v in aux.get("Origins", {}).values()}
    from .models import Access
    exclusive = {"access-%d" % a.pk for a in Access.objects.all() if _exclusive_service(a)}
    for sheet in cm.AUX:
        local_rows = aux.get(sheet, {})
        for row in workbook_rows.get(sheet, []):
            owner = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
            if row.get("Record ID") not in published_ids.get(owner, ()):
                continue
            if sheet == "Facts" and row.get("Fact") not in LOCAL_FACT_KEYS:
                continue  # internal verification facts never go to the site
            local = local_rows.get(row.get("Key"))
            if local is None:
                if sheet == "Tool Platforms" and (row.get("Record ID"), row.get("Platform")) in local_platforms:
                    continue  # same link already in Local under its own key
                if sheet == "Origins" and (row.get("Record ID"), row.get("Country")) in local_origins:
                    continue
                items.append({"sheet": sheet, "id": row.get("Key"), "kind": "unsupported",
                              "record": row.get("Record ID"), "columns": ["new row"], "category": "public"})
                continue
            supported = set(OFFER_FIELDS) if sheet == "Offers" else ({"Public"} if sheet == "Evaluations" else set())
            if sheet == "Offers":
                supported.add("Source URL")
                if row.get("Unit") != "other":
                    supported.discard("Billing Unit")
            if sheet == "Access" and row.get("Key") in exclusive:
                supported |= set(SERVICE_COLUMNS)
            if sheet in ("Offers", "Access"):
                supported |= {"Record Type", "Record ID"}
            columns = [c for c, v in local.items() if c not in supported and row.get(c, "") != v
                       and row.get(c, "") and c not in ("Conditions Extra (JSON)", "Checked")]
            for column in columns:
                service = ((sheet == "Offers" and column == "Billing Unit")
                           or (sheet == "Access" and column == "Source URL")
                           or (sheet == "Access" and column == "Service"))
                items.append({"sheet": sheet, "id": row.get("Key"), "kind": "unsupported",
                              "record": row.get("Record ID"), "columns": [column],
                              "category": "service" if service else "public"})
    return items


def _json_ready(values):
    out = {}
    for key, value in values.items():
        if isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value)
        out[key] = value
    return out


def _create(change, today):
    from .models import (
        Country, ModelFamily, ModelOriginCountry, ModelVersion, Organization, Platform, Source, Tool, ToolPlatform,
    )

    row, sheet = change["row"], change["sheet"]
    source_url = row.get("Official Source") or row.get("Source URL")
    source, _ = Source.objects.get_or_create(url=source_url, defaults={
        "title": (row.get("Source Title") or row["Name"])[:200],
        "publisher": (row.get("Source Publisher") or row["Developer"])[:120]})
    developer, _ = Organization.objects.get_or_create(name=row["Developer"], defaults={
        "country": row.get("Developer Country", ""), "source": source, "checked": today})
    checked = date.fromisoformat(row["Last Verified"]) if row.get("Last Verified") else today
    dates = _dates(row)
    released, approx, precision = (None, None, "") if dates == "silent" else dates
    common = {
        "name": row["Name"], "slug": row["Record ID"], "version": row.get("Version") or row["Name"],
        "category": row.get("Category", ""), "released": released, "approx_released": approx,
        "approx_precision": precision, "source": source, "checked": checked, "published": True,
        "catalog_status": row.get("Catalog Status") or "active",
        "description": {k: v for k, v in (("en", row.get("Description EN")), ("ru", row.get("Description RU"))) if v},
        "aliases": cm.split_aliases(row.get("Aliases")),
    }
    if sheet == "Models":
        family, _ = ModelFamily.objects.get_or_create(name=row.get("Family") or row["Name"], developer=developer)
        obj = ModelVersion(family=family, entry_type="model", tasks=_split(row.get("Tasks", "")),
                           input_modalities=_split(row.get("Input Modalities", "")),
                           output_modalities=_split(row.get("Output Modalities", "")),
                           context=int(row["Context"]) if row.get("Context") else None,
                           license=row.get("License", ""), open_weights=row.get("Open Weights") == "YES",
                           release_stage=row.get("Release Stage", ""), **common)
    else:
        obj = Tool(developer=developer, purposes=_split(row.get("Purposes", "")),
                   local_execution=row.get("Local Execution", ""), official_url=row.get("Official URL", ""), **common)
    obj.save()
    if sheet == "Models":
        for position, code in enumerate(_split(row.get("Origin Countries", ""))):
            if Country.objects.filter(code=code).exists():
                ModelOriginCountry.objects.get_or_create(model=obj, country_id=code, defaults={
                    "source": source, "checked": checked, "position": position})
    else:
        for platform in Platform.objects.filter(code__in=_split(row.get("Platforms", ""))):
            ToolPlatform.objects.get_or_create(tool=obj, platform=platform, defaults={
                "source": source, "checked": checked})
    return obj


def _renumber(targets):
    """Bring public_number in line with the master plan; log old/new numbers."""
    from .models import ModelVersion, PublicationRevision, Tool, ToolPublicationRevision

    changed = 0
    # All ModelVersion rows take part: public_number is unique across the table
    # and a tool's legacy row (entry_type != model) must never hold a number.
    for sheet, manager in (("Models", ModelVersion.objects.all()), ("Tools", Tool.objects.all())):
        moves = [(obj, obj.public_number,
                  targets.get((sheet, obj.slug)) if getattr(obj, "entry_type", "model") == "model" else None)
                 for obj in manager]
        moves = [m for m in moves if m[1] != m[2]]
        if not moves:
            continue
        cls = ModelVersion if sheet == "Models" else Tool
        cls.objects.filter(pk__in=[obj.pk for obj, _old, _new in moves]).update(public_number=None)
        for obj, old, new in moves:
            if new is not None:
                cls.objects.filter(pk=obj.pk).update(public_number=new)
            payload = {"action": RENUMBER, "before": {"public_number": old},
                       "after": {"public_number": new, "identity": obj.slug,
                                 "rule": "chronological position of public dated records (owner 2026-09-26)"}}
            if sheet == "Models":
                PublicationRevision.objects.create(model=obj, entity_id=obj.research_entity_id or obj.slug, **payload)
            else:
                ToolPublicationRevision.objects.create(tool=obj, **payload)
            changed += 1
    return changed


WRITE_KINDS = ("create", "update", "reassign", "offer", "evaluation", "number", "platforms", "access_service")


def _source(value):
    from .models import Source
    source, _ = Source.objects.get_or_create(url=value["url"], defaults={
        "title": (value.get("title") or value["url"])[:200], "publisher": (value.get("publisher") or "")[:120]})
    return source


def apply(changes, workbook_rows, max_changes=200, today=None, targets=None):
    """Write the plan through save() with revisions, then renumber.

    ``targets`` ((sheet, slug) -> number) replaces the numbers of
    ``workbook_rows`` when a release plan is applied without the workbook."""
    from .models import (
        Access, Evaluation, ModelVersion, Offer, Platform, PublicationRevision, Revision, Tool, ToolPlatform,
        ToolPublicationRevision,
    )
    from .translation_pipeline import suppress_auto_translation

    writes = [c for c in changes if c["kind"] in WRITE_KINDS]
    if len(writes) > max_changes:
        raise ValueError("%d changes exceed --max-changes %d; nothing written" % (len(writes), max_changes))
    today = today or date.today()
    with transaction.atomic(), suppress_auto_translation():
        for change in writes:
            kind = change["kind"]
            if kind == "number":
                continue
            if kind == "create":
                obj = _create(change, today)
                after = {"created": True, "published": True}
                if change["sheet"] == "Models":
                    PublicationRevision.objects.create(model=obj, entity_id=obj.slug, action=ACTION,
                                                       before={}, after=after)
                else:
                    ToolPublicationRevision.objects.create(tool=obj, action=ACTION, before={}, after=after)
                continue
            if kind == "platforms":
                tool = Tool.objects.get(slug=change["id"])
                for platform in Platform.objects.filter(code__in=change["after"]):
                    ToolPlatform.objects.get_or_create(tool=tool, platform=platform,
                                                       defaults={"source": tool.source, "checked": today})
                ToolPublicationRevision.objects.create(tool=tool, action=ACTION, before={"platforms": change["before"]},
                                                       after={"platforms_added": change["after"]})
                continue
            if kind == "reassign":
                obj = resolve_row(change)
                previous = obj.model
                obj.model = _owner_version(change["after"]["owner"])
                obj.save(update_fields=["model"])
                for owner in (previous, obj.model):
                    Revision.objects.create(model=owner, entity="%s:%s" % (change["sheet"].lower(), obj.pk),
                                            action="reassign", snapshot={"before": change["before"], "after": change["after"]})
                continue
            if kind == "access_service":
                access = resolve_row(change)
                service = access.service
                for attr, value in change["after"].items():
                    setattr(service, attr, value)
                service.save(update_fields=list(change["after"]))
                Revision.objects.create(model=access.model, entity="access:%s" % access.pk, action="sync",
                                        snapshot={"before": change["before"], "after": change["after"]})
                continue
            if kind in ("offer", "evaluation"):
                obj = resolve_row(change)
                for attr, value in change["after"].items():
                    setattr(obj, attr, _source(value) if attr == "source" else value)
                obj.save(update_fields=list(change["after"]))
                Revision.objects.create(model=obj.model, entity="%s:%s" % (kind, obj.pk), action="sync",
                                        snapshot={"before": _json_ready(change["before"]),
                                                  "after": _json_ready(change["after"])})
                continue
            if change["sheet"] == "Models":
                obj = ModelVersion.objects.get(slug=change["id"], entry_type="model")
            else:
                obj = Tool.objects.get(slug=change["id"])
            for attr, value in change["after"].items():
                setattr(obj, attr, _source(value) if attr == "source" else value)
            obj.save(update_fields=list(change["after"]))
            before, after = _json_ready(change["before"]), _json_ready(change["after"])
            if change["sheet"] == "Models":
                if "published" in after:
                    PublicationRevision.objects.create(
                        model=obj, entity_id=obj.research_entity_id or obj.slug, action=ACTION,
                        before={"published": before["published"], "public_number": obj.public_number},
                        after={"published": after["published"], "public_number": obj.public_number})
                Revision.objects.create(model=obj, entity="catalog_master", action="sync",
                                        snapshot={"before": before, "after": after})
            else:
                ToolPublicationRevision.objects.create(tool=obj, action=ACTION, before=before, after=after)
        renumbered = _renumber(targets if targets is not None else target_numbers(workbook_rows))
    return len([c for c in writes if c["kind"] != "number"]) + renumbered


# ------------------------------------------------------------ release plans
#
# A release plan carries the verified Local package to another database (e.g.
# Production after migrate) without copying SQLite: every change names its
# record by Record ID (slug) plus identity fields, the value expected *before*
# and the value to write; the final number of every record is included.
# ``check_plan`` classifies the target as pending (all "before" values match),
# applied (all "after" values match) or mismatch (anything else: nothing is
# written). ``apply_plan`` writes inside one transaction and verifies the
# final state, so a failure leaves the database unchanged.

PLAN_SCHEMA = "aipedia-catalog-plan/1"
_DATE_ATTRS = {"released", "approx_released", "checked"}


def _norm(attr, value):
    if attr in ("description", "suitable", "limitations") and isinstance(value, dict):
        # sync owns EN/RU; other locales belong to the translation pipeline
        return {k: v for k, v in value.items() if k in ("en", "ru")}
    if attr == "source":
        return value["url"] if isinstance(value, dict) else value
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if attr == "amount" and value is not None:
        return format(Decimal(str(value)).normalize(), "f")
    return value


def _restore(attr, value):
    if attr in _DATE_ATTRS and isinstance(value, str):
        return date.fromisoformat(value)
    if attr == "amount" and value is not None and not isinstance(value, Decimal):
        return Decimal(str(value))
    return value


def build_release_plan(workbook_rows, changes, master_sha256="", release=""):
    import json as _json
    writes = [c for c in changes if c["kind"] in WRITE_KINDS]
    serial = _json.loads(_json.dumps(writes, default=lambda v: _norm("", v)))
    numbers = {sheet: {r["Record ID"]: (int(r["Public Number"]) if r.get("Public Number") and r.get("Status") == "PUBLISHED" else None)
                       for r in workbook_rows[sheet]} for sheet in cm.MAIN}
    published = {sheet: sorted(r["Record ID"] for r in workbook_rows[sheet] if r.get("Status") == "PUBLISHED")
                 for sheet in cm.MAIN}
    return {"schema": PLAN_SCHEMA, "release": release, "master_sha256": master_sha256,
            "changes": serial, "final_numbers": numbers, "final_published": published,
            "counts": {kind: sum(1 for c in serial if c["kind"] == kind) for kind in WRITE_KINDS}}


def _current(change):
    """(current comparable value, identity problem or '')."""
    from .models import Access, Evaluation, ModelVersion, Offer, Tool
    kind, key = change["kind"], change["id"]
    if kind in ("create", "update", "number", "platforms"):
        manager = ModelVersion.objects.filter(entry_type="model") if change["sheet"] == "Models" else Tool.objects
        obj = manager.filter(slug=key).first()
        if kind == "create":
            return ("absent" if obj is None else ("present" if obj.published else "hidden")), ""
        if obj is None:
            return None, "record %s missing" % key
        if kind == "number":
            return obj.public_number, ""
        if kind == "platforms":
            return sorted(link.platform.code for link in obj.platform_links.all()), ""
        return {k: _norm(k, _value(obj, k)) for k in change["after"]}, ""
    if kind == "reassign":
        obj = resolve_row(change)
        if obj is None:
            return None, "%s not found by its stable locator" % key
        return {"owner": _owner_label(obj.model)}, ""
    if kind == "offer":
        obj = resolve_row(change)
        if obj is None or _offer_identity(obj) not in (change.get("identity"), change.get("identity_after")):
            return None, "offer %s identity differs" % key
        return {k: _norm(k, obj.source.url if k == "source" else getattr(obj, k)) for k in change["after"]}, ""
    if kind == "evaluation":
        obj = resolve_row(change)
        if obj is None or (change.get("identity") and obj.model.slug != change["identity"].get("model")):
            return None, "evaluation %s identity differs" % key
        return {"public": obj.public}, ""
    if kind == "access_service":
        obj = resolve_row(change)
        if obj is None or obj.model.slug != change["identity"]["model"]:
            return None, "access %s identity differs" % key
        return {k: getattr(obj.service, k) for k in change["after"]}, ""
    return None, "unknown kind %s" % kind


def check_plan(plan):
    """Return (state, problems): state is 'pending', 'applied' or 'mismatch'."""
    if plan.get("schema") != PLAN_SCHEMA:
        return "mismatch", ["unknown plan schema %r" % plan.get("schema")]
    pending = applied = 0
    problems = []
    for change in plan["changes"]:
        current, problem = _current(change)
        if problem:
            problems.append(problem)
            continue
        kind = change["kind"]
        if kind == "create":
            before_ok, after_ok = current == "absent", current == "present"
        elif kind == "number":
            before_ok, after_ok = current == change["before"], current == change["after"]
        elif kind == "platforms":
            before_ok = current == sorted(change["before"])
            after_ok = set(change["after"]) <= set(current)
        else:
            norm_before = {k: _norm(k, v) for k, v in change["before"].items()}
            norm_after = {k: _norm(k, v) for k, v in change["after"].items()}
            before_ok, after_ok = current == norm_before, current == norm_after
        if after_ok:
            applied += 1
        elif before_ok:
            pending += 1
        else:
            problems.append("%s %s %s: target %r is neither the expected old value nor the new value"
                            % (change["sheet"], change["id"], kind, current))
    if problems:
        return "mismatch", problems
    if pending and applied:
        return "mismatch", ["partially applied: %d pending, %d applied" % (pending, applied)]
    return ("applied" if not pending else "pending"), []


def final_state_problems(plan):
    from .models import ModelVersion, Tool
    problems = []
    for sheet, manager in (("Models", ModelVersion.objects.filter(entry_type="model")), ("Tools", Tool.objects.all())):
        published = sorted(manager.filter(published=True).values_list("slug", flat=True))
        if published != plan["final_published"][sheet]:
            problems.append("%s published set differs from the plan" % sheet)
        numbers = dict(manager.values_list("slug", "public_number"))
        wrong = [slug for slug, number in plan["final_numbers"][sheet].items() if numbers.get(slug, "absent") != number]
        if wrong:
            problems.append("%s numbers differ from the plan: %s" % (sheet, wrong[:5]))
    return problems


def apply_plan(plan):
    """Apply a pending plan atomically; returns the number of writes."""
    state, problems = check_plan(plan)
    if state == "applied":
        return 0
    if state != "pending":
        raise ValueError("plan does not match the target: %s" % problems[:10])
    changes = []
    for change in plan["changes"]:
        change = dict(change)
        if change["kind"] in ("update", "offer"):
            change["after"] = {k: _restore(k, v) for k, v in change["after"].items()}
        changes.append(change)
    targets = {(sheet, slug): number for sheet, mapping in plan["final_numbers"].items()
               for slug, number in mapping.items()}
    with transaction.atomic():
        written = apply(changes, None, max_changes=len(changes) + 1, targets=targets)
        problems = final_state_problems(plan)
        if problems:
            raise ValueError("final state differs from the plan, rolled back: %s" % problems)
    return written
