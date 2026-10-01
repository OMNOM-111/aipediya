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
* creation of PUBLISHED master rows that Local lacks, together with their own
  master price (Offers) and access rows: a new card arrives complete, with
  Suitable/Limitations EN/RU and its release evidence. Rows are matched later
  by content (Research Key; owner + service + evidence), never duplicated.

Everything else that differs for a PUBLISHED record (names, developers,
families, sources, other texts, platforms, origin countries, new or changed
access rows and new price/evaluation rows of existing records, ...) is NOT written: it is returned as
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
    "Context": "context", "Max Output": "max_output", "License": "license", "Open Weights": "open_weights",
    "Catalog Status": "catalog_status",
}
TOOL_FIELDS = {
    "Category": "category", "Purposes": "purposes", "Local Execution": "local_execution",
    "Official URL": "official_url", "Catalog Status": "catalog_status", "Version": "version",
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
        return {"context": None, "max_output": None, "open_weights": False}.get(attr, "")
    if attr in LIST_FIELDS:
        return _split(value)
    if attr in {"context", "max_output"}:
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
                    changes.append({"sheet": sheet, "id": rid, "kind": "create", "row": row,
                                    **_linked_rows(workbook_rows, sheet, rid)})
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
    offers_by_research_key = {o.research_key: o for o in Offer.objects.all() if o.research_key}
    for sheet, manager in (("Offers", Offer.objects), ("Access", Access.objects)):
        prefix = "offer-" if sheet == "Offers" else "access-"
        current = {prefix + str(o.pk): o for o in manager.select_related("model")}
        for row in workbook_rows.get(sheet, []):
            obj = (offers_by_research_key.get(row.get("Research Key")) if sheet == "Offers"
                   and row.get("Research Key") else None) or current.get(row.get("Key"))
            if sheet == "Offers" and obj is not None and row.get("Research Key") and obj.research_key != row["Research Key"]:
                obj = None  # Local PKs are not portable across SQLite databases.
            owner_sheet = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
            if obj is None or row.get("Record ID") not in published_ids.get(owner_sheet, ()):
                continue
            wanted = "%s:%s" % (row["Record Type"], row["Record ID"])
            have = _owner_label(obj.model)
            if have != wanted and _owner_version(wanted) is not None:
                changes.append({"sheet": sheet, "id": prefix + str(obj.pk), "kind": "reassign",
                                "before": {"owner": have}, "after": {"owner": wanted},
                                "locator": _locator(obj, owner_after=_owner_version(wanted).slug)})
                reassigned.add(prefix + str(obj.pk))

    # Price rows (existing only) and evaluation visibility.
    offers = {"offer-%d" % o.pk: o for o in Offer.objects.all()}
    offers_by_research_key = {o.research_key: o for o in offers.values() if o.research_key}
    for row in workbook_rows.get("Offers", []):
        offer = (offers_by_research_key.get(row.get("Research Key")) if row.get("Research Key") else None) or offers.get(row.get("Key"))
        if offer is not None and row.get("Research Key") and offer.research_key != row["Research Key"]:
            offer = None
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
            change = {"sheet": "Offers", "id": "offer-" + str(offer.pk), "kind": "offer",
                      "before": {k: (offer.source.url if k == "source" else getattr(offer, k)) for k in wanted},
                      "after": wanted, "identity": identity, "locator": _locator(offer)}
            if "offer-" + str(offer.pk) in reassigned:
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
        exclusive = _exclusive_service(access)
        if diff and (exclusive or set(diff) == {"url"}):
            changes.append({"sheet": "Access", "id": "access-%d" % access.pk, "kind": "access_service",
                            "before": {k: getattr(access.service, k) for k in diff}, "after": diff,
                            "clone": not exclusive,
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

    created = {(c["sheet"], c["id"]) for c in changes if c["kind"] == "create"}
    changes.extend(_new_rows(workbook_rows, published_ids, created))
    changes.extend(_developer_countries(workbook_rows, published_ids))
    changes.extend(_service_providers(workbook_rows, published_ids))
    changes.extend(_benchmark_categories(workbook_rows, published_ids))
    if snapshot is not None:
        changes.extend(_unsupported(workbook_rows, snapshot, aux or {}, published_ids, changes))
    return changes


def _service_providers(workbook_rows, published_ids):
    """Change one shared service only when all its master offers agree."""
    from .models import Offer, Organization

    by_key = {offer.research_key: offer for offer in Offer.objects.select_related("service__provider")
              if offer.research_key}
    desired = {}
    for row in workbook_rows.get("Offers", []):
        owner = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
        if row.get("Record ID") not in published_ids.get(owner, ()) or not row.get("Provider"):
            continue
        offer = by_key.get(row.get("Research Key"))
        if offer is not None:
            desired.setdefault(offer.service_id, set()).add(row["Provider"])
    out = []
    for service_id, names in desired.items():
        if len(names) != 1:
            continue
        service = next(offer.service for offer in by_key.values() if offer.service_id == service_id)
        target = next(iter(names))
        if target != service.provider.name and Organization.objects.filter(name=target).count() == 1:
            out.append({"sheet": "Offers", "id": service.name, "kind": "service_provider",
                        "identity": {"name": service.name, "url": service.url},
                        "before": {"provider": service.provider.name}, "after": {"provider": target}})
    return out


def _benchmark_categories(workbook_rows, published_ids):
    """Update a shared benchmark category only with one unambiguous master value."""
    from .models import Benchmark

    desired = {}
    for row in workbook_rows.get("Evaluations", []):
        if row.get("Record ID") in published_ids.get("Models", ()) and row.get("Benchmark Category"):
            key = (row.get("Benchmark"), row.get("Protocol"))
            desired.setdefault(key, set()).add(row["Benchmark Category"])
    out = []
    for (name, protocol), values in desired.items():
        if len(values) != 1:
            continue
        benchmark = Benchmark.objects.filter(name=name, protocol=protocol).first()
        target = next(iter(values))
        if benchmark is not None and benchmark.category != target:
            out.append({"sheet": "Evaluations", "id": name, "kind": "benchmark_category",
                        "identity": {"name": name, "protocol": protocol},
                        "before": {"category": benchmark.category}, "after": {"category": target}})
    return out


def _linked_rows(workbook_rows, sheet, record_id):
    """Master price/access rows owned by a record that sync-local creates
    (a tool's rows live on its legacy product row, created with them)."""
    record_type = "model" if sheet == "Models" else "tool"
    return {key: [dict(r) for r in workbook_rows.get(aux_sheet, [])
                  if r.get("Record ID") == record_id and r.get("Record Type") == record_type]
            for aux_sheet, key in (("Offers", "offers"), ("Access", "access"))}


# Values found in Organization.country that are not a country.
NOT_A_COUNTRY = {"", "open source", "community"}


def _new_rows(workbook_rows, published_ids, created):
    """New master rows (price, access, origin country, evaluation) of existing
    PUBLISHED records. Each is identified by content so a re-run, an import
    and a release plan recognise it: offers by Research Key, evaluations by
    Observation Key, access by owner + service + evidence, origins by model +
    country. Rows without such an identity stay in the ``unsupported`` report."""
    from .models import Access, Country, Evaluation, ModelOriginCountry, ModelVersion, Offer, Tool

    changes = []
    research_keys = set(Offer.objects.exclude(research_key=None).values_list("research_key", flat=True))
    observation_keys = set(Evaluation.objects.exclude(observation_key=None).values_list("observation_key", flat=True))
    origins = set(ModelOriginCountry.objects.values_list("model__slug", "country_id"))
    countries = set(Country.objects.values_list("code", flat=True))
    models = set(ModelVersion.objects.filter(entry_type="model").values_list("slug", flat=True))
    tools = dict(Tool.objects.values_list("slug", "legacy_version__slug"))
    accesses = set(Access.objects.values_list("model__slug", "service__name", "service__url", "source__url"))
    local_keys = {"offer-%d" % pk for pk in Offer.objects.values_list("pk", flat=True)}
    local_keys |= {"access-%d" % pk for pk in Access.objects.values_list("pk", flat=True)}
    local_keys |= {"origin-%d" % pk for pk in ModelOriginCountry.objects.values_list("pk", flat=True)}
    local_keys |= {"evaluation-%d" % pk for pk in Evaluation.objects.values_list("pk", flat=True)}

    def owner(row):
        sheet = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
        rid = row.get("Record ID")
        if row.get("Key") in local_keys:
            return None  # an existing Local row (its differences are handled or reported elsewhere)
        if rid not in published_ids.get(sheet, ()) or (sheet, rid) in created:
            return None
        if sheet == "Models":
            return ("model:" + rid, rid) if rid in models else None
        return ("tool:" + rid, tools.get(rid) or "") if rid in tools else None

    for row in workbook_rows.get("Offers", []):
        found = owner(row)
        key = row.get("Research Key", "")
        if found and key and key not in research_keys:
            changes.append({"sheet": "Offers", "id": row["Key"], "kind": "offer_new", "owner": found[0], "row": dict(row)})
    for row in workbook_rows.get("Access", []):
        found = owner(row)
        if not found or not all(row.get(c) for c in ("Service", "Service Kind", "Service URL", "Source URL")):
            continue
        if (found[1], row["Service"], row["Service URL"], row["Source URL"]) in accesses:
            continue
        if found[1] and any(a[0] == found[1] and a[1] == row["Service"] and a[2] == row["Service URL"] for a in accesses):
            continue  # same service already linked (one access row per model and service)
        changes.append({"sheet": "Access", "id": row["Key"], "kind": "access_new", "owner": found[0], "row": dict(row)})
    for row in workbook_rows.get("Origins", []):
        found = owner(row)
        if (found and found[0].startswith("model:") and row.get("Country") in countries and row.get("Source URL")
                and (row["Record ID"], row["Country"]) not in origins):
            changes.append({"sheet": "Origins", "id": row["Key"], "kind": "origin_new", "owner": found[0], "row": dict(row)})
    for row in workbook_rows.get("Evaluations", []):
        found = owner(row)
        key = row.get("Observation Key", "")
        if found and found[0].startswith("model:") and key and key not in observation_keys:
            changes.append({"sheet": "Evaluations", "id": row["Key"], "kind": "evaluation_new", "owner": found[0],
                            "row": dict(row)})
    return changes


def _developer_countries(workbook_rows, published_ids):
    """Fill a developer's country from the master when Local has none (or a
    placeholder such as "Open source"). A different existing country is never
    overwritten: it stays an ``unsupported`` difference for review."""
    from .models import ModelVersion, Tool

    changes, seen = [], set()
    orgs = {m.slug: m.family.developer for m in ModelVersion.objects.filter(entry_type="model").select_related("family__developer")}
    orgs.update({"tool:" + t.slug: t.developer for t in Tool.objects.select_related("developer")})
    for sheet in cm.MAIN:
        for row in workbook_rows[sheet]:
            country = row.get("Developer Country", "")
            if row["Record ID"] not in published_ids[sheet] or country.strip().casefold() in NOT_A_COUNTRY or country == CLEAR:
                continue
            org = orgs.get(row["Record ID"] if sheet == "Models" else "tool:" + row["Record ID"])
            if org is None or org.name in seen or (org.country or "").strip().casefold() not in NOT_A_COUNTRY:
                continue
            seen.add(org.name)
            changes.append({"sheet": sheet, "id": org.name, "kind": "org_country", "record": row["Record ID"],
                            "before": {"country": org.country}, "after": {"country": country}})
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


def _same_master_value(column, master_value, database_value):
    """Compare JSON-backed master fields by value, not whitespace or key order."""
    if not column.endswith("(JSON)"):
        return master_value == database_value
    import json
    try:
        return json.loads(master_value or "{}") == json.loads(database_value or "{}")
    except (TypeError, ValueError):
        return master_value == database_value


def _unsupported(workbook_rows, snapshot, aux, published_ids, planned=()):
    """Unwritten differences, matched by content identity before local SQL key."""
    items = []
    planned_access = {c["id"] for c in planned if c["kind"] == "access_service"}
    planned_providers = {(c["identity"]["name"], c["identity"]["url"])
                         for c in planned if c["kind"] == "service_provider"}
    planned_benchmarks = {(c["identity"]["name"], c["identity"]["protocol"])
                          for c in planned if c["kind"] == "benchmark_category"}
    for sheet in cm.MAIN:
        for row in workbook_rows[sheet]:
            rid = row["Record ID"]
            if rid not in published_ids[sheet] or rid not in snapshot[sheet]:
                continue
            local_row = snapshot[sheet][rid][0]
            columns = [c for c in cm.PUBLIC[sheet]
                       if c not in SUPPORTED_COLUMNS[sheet] and c not in IGNORED_COLUMNS
                       and c not in ("Source URL",)
                       and row.get(c, "") and not _same_master_value(c, row.get(c), local_row.get(c, ""))]
            if sheet == "Tools" and "Platforms" in columns:
                extra = set(_split(local_row.get("Platforms", ""))) - set(_split(row.get("Platforms", "")))
                if not extra:
                    columns.remove("Platforms")  # only additions: supported
            if "Developer Country" in columns and local_row.get("Developer Country", "").strip().casefold() in NOT_A_COUNTRY:
                columns.remove("Developer Country")  # filled by org_country
            for column in columns:
                intentional = column in SERVICE_ONLY or (sheet == "Tools" and column == "Supported Models")
                items.append({"sheet": sheet, "id": rid,
                              "kind": "intentional_master_only" if intentional else "unsupported",
                              "columns": [column], "category": "service" if intentional else "public",
                              **({"reason": "shared source bibliography" if column in SERVICE_ONLY
                                            else "free-text model scope; no exact model Record IDs"} if intentional else {})})
    from .models import Access, Country
    exclusive = {"access-%d" % a.pk for a in Access.objects.all() if _exclusive_service(a)}
    created = {(sheet, row["Record ID"]): row for sheet in cm.MAIN for row in workbook_rows[sheet]
               if row["Record ID"] in published_ids[sheet] and row["Record ID"] not in snapshot[sheet]}
    countries = set(Country.objects.values_list("code", flat=True))
    for sheet in cm.AUX:
        local_rows = aux.get(sheet, {})
        local_natural = {}
        for local_key, local_row in local_rows.items():
            identity = cm.natural_key(sheet, local_row)
            if identity is not None:
                local_natural.setdefault(identity, (local_key, local_row))
        for row in workbook_rows.get(sheet, []):
            owner = cm.RECORD_TYPE_SHEET.get(row.get("Record Type"))
            if row.get("Record ID") not in published_ids.get(owner, ()):
                continue
            if sheet == "Facts" and row.get("Fact") not in LOCAL_FACT_KEYS:
                continue  # internal verification facts never go to the site
            identity = cm.natural_key(sheet, row)
            matched = local_natural.get(identity) if identity is not None else None
            local_key, local = matched if matched is not None else (row.get("Key"), local_rows.get(row.get("Key")))
            # Integer PKs are local to a database. A same-numbered row owned by
            # another record is never evidence of a difference in this row.
            if matched is None and local is not None and (
                    local.get("Record Type") != row.get("Record Type")
                    or local.get("Record ID") != row.get("Record ID")):
                local = None
            if local is None:
                new_record = created.get((owner, row.get("Record ID")))
                if new_record is not None and (sheet in ("Offers", "Access") or (
                        sheet == "Origins" and row.get("Country") in _split(new_record.get("Origin Countries", "")))):
                    continue  # created together with the new record
                if new_record is None and (
                        (sheet == "Offers" and row.get("Research Key"))
                        or (sheet == "Access" and all(row.get(c) for c in ("Service", "Service Kind", "Service URL", "Source URL")))
                        or (sheet == "Origins" and owner == "Models" and row.get("Country") in countries and row.get("Source URL"))
                        or (sheet == "Evaluations" and owner == "Models" and row.get("Observation Key"))):
                    continue  # new row of an existing record: offer_new / access_new / origin_new / evaluation_new
                research_pending = sheet == "Offers" and not row.get("Research Key") and (
                    '"verification_pending"' in row.get("Conditions Extra (JSON)", ""))
                items.append({"sheet": sheet, "id": row.get("Key"),
                              "kind": "intentional_master_only" if research_pending else "unsupported",
                              "record": row.get("Record ID"), "columns": ["new row"],
                              "category": "research" if research_pending else "public",
                              **({"reason": "verification_pending; missing stable Research Key"} if research_pending else {})})
                continue
            supported = set(OFFER_FIELDS) if sheet == "Offers" else ({"Public"} if sheet == "Evaluations" else set())
            if sheet == "Offers":
                supported.add("Source URL")
                if row.get("Unit") != "other":
                    supported.discard("Billing Unit")
            if sheet == "Access" and (local_key in exclusive or local_key in planned_access):
                supported |= set(SERVICE_COLUMNS)
            if sheet in ("Offers", "Access"):
                supported |= {"Record Type", "Record ID"}
            columns = [c for c, v in local.items() if c not in supported and not _same_master_value(c, row.get(c, ""), v)
                       and row.get(c, "") and c not in ("Conditions Extra (JSON)", "Checked")]
            for column in columns:
                if sheet == "Offers" and column == "Provider" and (
                        local.get("Service"), local.get("Service URL")) in planned_providers:
                    continue
                if sheet == "Evaluations" and column == "Benchmark Category" and (
                        local.get("Benchmark"), local.get("Protocol")) in planned_benchmarks:
                    continue
                intentional = ((sheet == "Offers" and column == "Billing Unit" and row.get("Unit") != "other")
                               or (sheet == "Access" and column == "Source URL")
                               or (sheet == "Tool Platforms" and column == "Source URL")
                               or (sheet == "Origins" and column == "Position"
                                   and row.get(column) == "1" and local.get(column) == "0")
                               or (sheet == "Evaluations" and column == "Score"
                                   and _same_stored_score(row.get(column), local.get(column)))
                               or (sheet == "Evaluations" and column == "Source Model"
                                   and row.get("Public") == "NO" and local.get("Public") == "NO"
                                   and '"superseded_duplicate_of"' in row.get("Conditions Extra (JSON)", "")))
                service = ((sheet == "Offers" and column == "Billing Unit")
                           or (sheet == "Access" and column == "Source URL")
                           or (sheet == "Access" and column == "Service"))
                items.append({"sheet": sheet, "id": row.get("Key"),
                              "kind": "intentional_master_only" if intentional else "unsupported",
                              "record": row.get("Record ID"), "columns": [column],
                              "category": "service" if service else "public",
                              **({"reason": ("stored score rounded to 3 decimals" if sheet == "Evaluations"
                                              else "1-based master / 0-based database position" if sheet == "Origins"
                                              else "hidden superseded duplicate" if sheet == "Evaluations"
                                              else "link evidence URL" if sheet in ("Access", "Tool Platforms")
                                              else "standard unit label")}
                                 if intentional else {})})
    return items


def _same_stored_score(master_value, database_value):
    """Evaluation.score is DecimalField(decimal_places=3)."""
    try:
        return Decimal(master_value).quantize(Decimal("0.001")) == Decimal(database_value)
    except (InvalidOperation, TypeError):
        return False


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
        texts = {attr: {} for attr, _lang in MODEL_TEXT_FIELDS.values()}
        for column, (attr, lang) in MODEL_TEXT_FIELDS.items():
            if row.get(column) and row[column] != CLEAR:
                texts[attr][lang] = row[column]
        obj = ModelVersion(family=family, entry_type="model", tasks=_split(row.get("Tasks", "")),
                           input_modalities=_split(row.get("Input Modalities", "")),
                           output_modalities=_split(row.get("Output Modalities", "")),
                           context=int(row["Context"]) if row.get("Context") else None,
                           max_output=int(row["Max Output"]) if row.get("Max Output") else None,
                           license=row.get("License", ""), open_weights=row.get("Open Weights") == "YES",
                           release_stage=row.get("Release Stage", ""), release_evidence=_evidence(row),
                           **texts, **common)
    else:
        ecosystem = {lang: row.get(column) for column, lang in
                     (("Ecosystem EN", "en"), ("Ecosystem RU", "ru")) if row.get(column)}
        obj = Tool(developer=developer, purposes=_split(row.get("Purposes", "")),
                   local_execution=row.get("Local Execution", ""), official_url=row.get("Official URL", ""),
                   ecosystem=ecosystem, **common)
    obj.save()
    if sheet == "Models":
        for position, code in enumerate(_split(row.get("Origin Countries", ""))):
            if Country.objects.filter(code=code).exists():
                ModelOriginCountry.objects.get_or_create(model=obj, country_id=code, defaults={
                    "source": source, "checked": checked, "position": position})
        for offer_row in change.get("offers", []):
            _create_offer(obj, offer_row, today)
        for access_row in change.get("access", []):
            _create_access(obj, access_row, today)
    else:
        for platform in Platform.objects.filter(code__in=_split(row.get("Platforms", ""))):
            ToolPlatform.objects.get_or_create(tool=obj, platform=platform, defaults={
                "source": source, "checked": checked})
        if change.get("offers") or change.get("access"):
            container = _legacy_container(obj, today)
            for offer_row in change.get("offers", []):
                _create_offer(container, offer_row, today)
            for access_row in change.get("access", []):
                _create_access(container, access_row, today)
    return obj


def _legacy_container(tool, today):
    """The tool's legacy product row, which holds its prices and access rows
    (as for every tool migrated from the model table); created when missing."""
    from .models import ModelFamily, ModelVersion
    if tool.legacy_version_id:
        return tool.legacy_version
    family, _ = ModelFamily.objects.get_or_create(name=tool.name, developer=tool.developer)
    base = (tool.slug[:42] + "-legacy").strip("-")
    slug, index = base, 1
    while ModelVersion.objects.filter(slug=slug).exists():
        index += 1
        slug = "%s-%d" % (base[:47], index)
    container = ModelVersion.objects.create(
        family=family, name=tool.name, slug=slug, version=tool.version or tool.name, category="other",
        entry_type={"api_platform": "api_service", "runtime": "runtime"}.get(tool.category, "product"),
        source=tool.source, checked=today, published=True, catalog_status=tool.catalog_status or "active")
    tool.legacy_version = container
    tool.save(update_fields=["legacy_version"])
    return container


def _owner_for_new_row(label, today):
    """ModelVersion that holds a new row of ``model:<slug>`` / ``tool:<slug>``."""
    from .models import ModelVersion, Tool
    kind, _sep, slug = label.partition(":")
    if kind == "model":
        return ModelVersion.objects.get(slug=slug, entry_type="model")
    return _legacy_container(Tool.objects.get(slug=slug), today)


def _create_origin(model, row, today):
    from .models import ModelOriginCountry
    position = int(row["Position"]) if str(row.get("Position", "")).isdigit() else model.origin_country_links.count()
    ModelOriginCountry.objects.get_or_create(model=model, country_id=row["Country"], defaults={
        "source": _source({"url": row["Source URL"]}), "checked": _row_date(row.get("Checked"), today),
        "position": position})


def _create_evaluation(model, row, today):
    import json
    from .models import Benchmark, Evaluation
    if Evaluation.objects.filter(observation_key=row["Observation Key"]).exists():
        raise ValueError("Evaluations %s: Observation Key already used" % row.get("Key"))
    kind = row.get("Result Kind") or "independent"
    independent = row.get("Independent") == "YES"
    if independent != (kind == "independent"):
        raise ValueError("Evaluations %s: Independent=%s contradicts Result Kind %s" % (row.get("Key"), row.get("Independent"), kind))
    benchmark, _ = Benchmark.objects.get_or_create(name=row["Benchmark"], protocol=row["Protocol"], defaults={
        "category": row.get("Benchmark Category") or "text", "unit": row.get("Unit") or "%",
        "higher_is_better": row.get("Higher Is Better") != "NO"})
    try:
        extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
    except ValueError:
        extra = {}
    conditions = {**(extra if isinstance(extra, dict) else {}),
                  **{lang: row[column] for column, lang in (("Conditions EN", "en"), ("Conditions RU", "ru"))
                     if row.get(column)}}

    def decimal(value):
        return Decimal(value) if value not in (None, "", CLEAR) else None
    Evaluation.objects.create(
        model=model, benchmark=benchmark, score=Decimal(row["Score"]), evaluator=row["Evaluator"],
        independent=independent, public=row.get("Public") == "YES", result_kind=kind,
        measured=date.fromisoformat(row["Measured"]) if row.get("Measured") else None,
        conditions=conditions, source=_source({"url": row["Source URL"], "publisher": row["Evaluator"]}),
        checked=_row_date(row.get("Checked"), today), observation_key=row["Observation Key"],
        configuration=row.get("Configuration", ""), source_model=row.get("Source Model", ""),
        source_record_id=row.get("Source Record ID", ""), snapshot=row.get("Snapshot", ""),
        source_sha256=row.get("Source SHA256", ""), confidence_low=decimal(row.get("Confidence Low")),
        confidence_high=decimal(row.get("Confidence High")))


def _evidence(row):
    import json
    try:
        value = json.loads(row.get("Release Evidence (JSON)") or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _row_date(value, today):
    try:
        return date.fromisoformat(value) if value and value != CLEAR else today
    except ValueError:
        return today


def _service_for(row, today):
    """The service named by a master row: reused when identical, else created."""
    from .models import Organization, Service
    fields = {"name": row["Service"], "kind": row["Service Kind"], "url": row["Service URL"]}
    service = Service.objects.filter(**fields).order_by("pk").first()
    if service is None:
        provider = row.get("Provider") or row["Service"]
        organization = Organization.objects.filter(name=provider).first()
        if organization is None:
            organization = Organization.objects.create(
                name=provider, source=_source({"url": row["Service URL"], "publisher": provider}), checked=today)
        service = Service.objects.create(provider=organization, compute_location=row.get("Compute Location", ""),
                                         **fields)
    return service


def _create_offer(model, row, today):
    import json
    from .models import Offer
    if not row.get("Research Key"):
        raise ValueError("Offers %s: a new price row needs a Research Key" % row.get("Key"))
    if Offer.objects.filter(research_key=row["Research Key"]).exists():
        raise ValueError("Offers %s: Research Key already used" % row.get("Key"))
    service = _service_for(row, today)
    if (row["Unit"] in {"month", "year"}) != (service.kind in {"web", "app", "cli", "ide"}) or (
            row["Unit"] not in {"month", "year"} and service.kind != "api"):
        raise ValueError("Offers %s: unit %s does not fit service kind %s" % (row.get("Key"), row["Unit"], service.kind))
    try:
        extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
    except ValueError:
        extra = {}
    conditions = {**(extra if isinstance(extra, dict) else {}),
                  **{lang: row[column] for column, lang in (("Conditions EN", "en"), ("Conditions RU", "ru"))
                     if row.get(column)}}
    if not conditions.get("ru"):
        raise ValueError("Offers %s: Conditions RU is required" % row.get("Key"))
    Offer.objects.create(
        model=model, service=service, amount=Decimal(row["Amount"]) if row.get("Amount") else None,
        unit=row["Unit"], billing_unit=row.get("Billing Unit", "") if row["Unit"] == "other" else "",
        conditions=conditions, source=_source({"url": row["Source URL"], "publisher": row.get("Provider", "")}),
        checked=_row_date(row.get("Checked"), today), active=row.get("Active") != "NO",
        primary=row.get("Primary") == "YES", research_key=row["Research Key"])


def _create_access(model, row, today):
    from .models import Access
    service = _service_for(row, today)
    source = _source({"url": row.get("Source URL") or row["Service URL"], "publisher": row.get("Provider", "")})
    Access.objects.get_or_create(model=model, service=service, defaults={
        "source": source, "checked": _row_date(row.get("Checked"), today)})


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


NEW_ROW_KINDS = ("offer_new", "access_new", "origin_new", "evaluation_new")
WRITE_KINDS = ("create", "update", "reassign", "offer", "evaluation", "number", "platforms", "access_service",
               "service_provider", "benchmark_category", "org_country", *NEW_ROW_KINDS)


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
            if kind in NEW_ROW_KINDS:
                owner = _owner_for_new_row(change["owner"], today)
                {"offer_new": _create_offer, "access_new": _create_access, "origin_new": _create_origin,
                 "evaluation_new": _create_evaluation}[kind](owner, change["row"], today)
                Revision.objects.create(model=owner, entity="%s:%s" % (change["sheet"].lower(), change["id"])[:80],
                                        action="sync_new", snapshot={"key": change["id"], "owner": change["owner"]})
                continue
            if kind == "org_country":
                from .models import Organization
                organization = Organization.objects.get(name=change["id"])
                organization.country = change["after"]["country"]
                organization.save(update_fields=["country"])
                record = ModelVersion.objects.filter(slug=change["record"], entry_type="model").first()
                if record is None:
                    tool = Tool.objects.filter(slug=change["record"]).first()
                    if tool is not None:
                        ToolPublicationRevision.objects.create(tool=tool, action=ACTION, before={"developer_country": change["before"]["country"]},
                                                               after={"developer_country": change["after"]["country"]})
                else:
                    Revision.objects.create(model=record, entity="organization:%s" % organization.pk, action="sync",
                                            snapshot={"before": change["before"], "after": change["after"]})
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
                if change.get("clone"):
                    from .models import Service
                    attributes = {"name": service.name, "provider": service.provider,
                                  "kind": service.kind, "url": service.url,
                                  "compute_location": service.compute_location}
                    attributes.update(change["after"])
                    replacement, _ = Service.objects.get_or_create(**attributes)
                    access.service = replacement
                    access.save(update_fields=["service"])
                else:
                    for attr, value in change["after"].items():
                        setattr(service, attr, value)
                    service.save(update_fields=list(change["after"]))
                Revision.objects.create(model=access.model, entity="access:%s" % access.pk, action="sync",
                                        snapshot={"before": change["before"], "after": change["after"]})
                continue
            if kind == "service_provider":
                from .models import Organization, Service
                spec = change["identity"]
                service = Service.objects.get(name=spec["name"], url=spec["url"])
                service.provider = Organization.objects.get(name=change["after"]["provider"])
                service.save(update_fields=["provider"])
                for model_id in set(service.offer_set.values_list("model_id", flat=True)) | set(
                        service.access_set.values_list("model_id", flat=True)):
                    Revision.objects.create(model_id=model_id, entity="service:%s" % service.pk,
                                            action="sync", snapshot={"before": change["before"],
                                                                     "after": change["after"]})
                continue
            if kind == "benchmark_category":
                from .models import Benchmark
                spec = change["identity"]
                benchmark = Benchmark.objects.get(name=spec["name"], protocol=spec["protocol"])
                benchmark.category = change["after"]["category"]
                benchmark.save(update_fields=["category"])
                for model_id in benchmark.evaluation_set.values_list("model_id", flat=True).distinct():
                    Revision.objects.create(model_id=model_id, entity="benchmark:%s" % benchmark.pk,
                                            action="sync", snapshot={"before": change["before"],
                                                                     "after": change["after"]})
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
    from . import freshness
    writes = [c for c in changes if c["kind"] in WRITE_KINDS]
    serial = _json.loads(_json.dumps(writes, default=lambda v: _norm("", v)))
    numbers = {sheet: {r["Record ID"]: (int(r["Public Number"]) if r.get("Public Number") and r.get("Status") == "PUBLISHED" else None)
                       for r in workbook_rows[sheet]} for sheet in cm.MAIN}
    published = {sheet: sorted(r["Record ID"] for r in workbook_rows[sheet] if r.get("Status") == "PUBLISHED")
                 for sheet in cm.MAIN}
    plan = {"schema": PLAN_SCHEMA, "release": release, "master_sha256": master_sha256,
            "changes": serial, "final_numbers": numbers, "final_published": published,
            "counts": {kind: sum(1 for c in serial if c["kind"] == kind) for kind in WRITE_KINDS}}
    plan["catalog_update"] = freshness.snapshot_from_plan(plan)
    return plan


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
    if kind == "service_provider":
        from .models import Service
        spec = change["identity"]
        found = list(Service.objects.filter(name=spec["name"], url=spec["url"]).select_related("provider")[:2])
        if len(found) != 1:
            return None, "service %s identity is absent or ambiguous" % key
        return {"provider": found[0].provider.name}, ""
    if kind == "benchmark_category":
        from .models import Benchmark
        spec = change["identity"]
        benchmark = Benchmark.objects.filter(name=spec["name"], protocol=spec["protocol"]).first()
        if benchmark is None:
            return None, "benchmark %s missing" % key
        return {"category": benchmark.category}, ""
    if kind in NEW_ROW_KINDS:
        return _new_row_state(change)
    if kind == "org_country":
        from .models import Organization
        organization = Organization.objects.filter(name=key).first()
        if organization is None:
            return None, "organization %s missing" % key
        return {"country": organization.country}, ""
    return None, "unknown kind %s" % kind


def _new_row_state(change):
    """('absent' | 'present', problem) of a new row, found by its content identity."""
    from .models import Access, Evaluation, ModelOriginCountry, ModelVersion, Offer, Tool
    row, kind = change["row"], change["kind"]
    owner_kind, _sep, slug = change["owner"].partition(":")
    if owner_kind == "model":
        holder = ModelVersion.objects.filter(slug=slug, entry_type="model").first()
        if holder is None:
            return None, "record %s missing" % slug
    else:
        tool = Tool.objects.filter(slug=slug).select_related("legacy_version").first()
        if tool is None:
            return None, "tool %s missing" % slug
        holder = tool.legacy_version
    if kind == "offer_new":
        found = Offer.objects.filter(research_key=row["Research Key"]).first()
        if found is not None and (holder is None or found.model_id != holder.pk):
            return None, "offer %s exists under another record" % row["Research Key"]
    elif kind == "evaluation_new":
        found = Evaluation.objects.filter(observation_key=row["Observation Key"]).first()
        if found is not None and found.model_id != holder.pk:
            return None, "evaluation %s exists under another record" % row["Observation Key"]
    elif kind == "origin_new":
        found = ModelOriginCountry.objects.filter(model=holder, country_id=row["Country"]).first()
    else:
        found = holder and Access.objects.filter(model=holder, service__name=row["Service"],
                                                 service__url=row["Service URL"]).first()
    return ("present" if found else "absent"), ""


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
        if kind == "create" or kind in NEW_ROW_KINDS:
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
        # a master draft that was never created (NEEDS_REVIEW) is planned
        # without a number: absent from the database is its correct state
        wrong = [slug for slug, number in plan["final_numbers"][sheet].items()
                 if numbers.get(slug, "absent" if number is not None else None) != number]
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
        if written:
            from . import freshness
            freshness.write_plan_snapshot(plan)
    return written
