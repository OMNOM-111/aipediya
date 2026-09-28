"""Release QA of the public catalog: blocking errors, warnings and the data-quality queue.

Run before every catalog release (``manage.py catalog_master qa``). A check is
blocking only where it applies; a verified gap recorded in the master as a
``*_status`` fact (origin_status / pricing_status / independent_evaluation_status)
moves the record to the data-quality queue instead of failing the release.

Blocking errors
* counters: tab, result counter, "Showing x / y", rendered rows and the
  database total must describe one set (EN/RU, Models/Tools);
* origin: a published record without a country/flag, unless its origin is a
  recorded ``not_established`` gap; every country must have a flag symbol;
* pricing: an active published model with a commercial API but no current
  price, unless a pricing gap is recorded; a $0 price that is not a free tier;
  a price row without source or Russian conditions;
* evaluations: a public row marked independent that is developer-reported or by
  the developer itself; a public row from a source whose terms block
  republication; a public row without source;
* provenance: a published record without a source link;
* duplicates: published names/aliases, price rows, evaluation rows;
* master <-> Local: rule violations, pending sync writes, different public sets
  or numbers; optionally master <-> Production (public sitemap).
"""
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from django.conf import settings

from . import catalog_master as cm

BLOCKED_EVALUATION_SOURCES = ("artificialanalysis.ai", "lmarena.ai", "arena.ai", "livebench.ai", "swebench.com")
FREE_WORDS = ("free", "бесплат", "gratis", "trial")
GAP = {
    "origin_status": {"not_established"},
    "pricing_status": {"no_official_hosted_price", "custom_enterprise_pricing", "superseded_in_api", "open_weights_no_hosted_api",
                       "subscription_price_not_published", "usage_based_per_model", "scheduled_price", "verification_pending"},
    # stage-2 vocabulary (D-2026-09-27-independent-evaluation-evidence-policy): every status without a
    # publishable independent result stays in the data-quality queue; "gap" remains for NEEDS_REVIEW records
    "independent_evaluation_status": {"gap", "independent_nonpublic", "developer_reported", "no_published_numerical_evaluation",
                                      "exact_version_not_found", "identity_ambiguous"},
}


def _facts(workbook_rows):
    """(record type, Record ID) -> {fact: value dict} for the *_status facts."""
    out = defaultdict(dict)
    for row in (workbook_rows or {}).get("Facts", []):
        if row.get("Fact") in GAP:
            try:
                value = json.loads(row.get("Value (JSON)") or "{}")
            except ValueError:
                value = {}
            out[(row.get("Record Type"), row.get("Record ID"))][row["Fact"]] = {**value, "source": row.get("Source URL", "")}
    return out


def _flags():
    path = Path(settings.BASE_DIR) / "static" / "flags.svg"
    return set(re.findall(r'id="flag-([A-Z]{2})"', path.read_text(encoding="utf-8"))) if path.exists() else set()


def _render_counts(client, path):
    response = client.get(path)
    html = response.content.decode("utf-8")

    def number(pattern):
        match = re.search(pattern, html)
        return int(match.group(1).replace(" ", "").replace(" ", "").replace(",", "")) if match else None
    return {
        "status": response.status_code,
        "tab_active": number(r'class="type-tab is-active"[^>]*>[^<]*<span>([\d\s, ]+)</span>'),
        "result": number(r'id="result-count">([\d\s, ]+)<'),
        "shown": number(r'id="shown-count">([\d\s, ]+)<'),
        "total": number(r'id="shown-count">[\d\s, ]+</span>\s*/\s*([\d\s, ]+)'),
        "rows": len(re.findall(r'<tr[^>]*data-slug=', html)),
        "next": bool(re.search(r'data-next-url="[^"]+"', html)),
        "numbered": number(r'data-numbered="(\d+)"'),
        "undated": number(r'data-undated="(\d+)"'),
    }


def run(workbook_rows=None, production=None):
    """Return {"errors": [...], "warnings": [...], "queue": [...], "stats": {...}}."""
    from django.test import Client

    from .comparison import developer_countries
    from .models import Evaluation, ModelVersion, Offer, Tool

    errors, warnings, queue = [], [], []
    facts = _facts(workbook_rows)
    flags = _flags()

    def gap(record_type, rid, fact):
        value = facts.get((record_type, rid), {}).get(fact)
        return value if value and value.get("status") in GAP[fact] else None

    models = list(ModelVersion.objects.filter(entry_type="model", published=True)
                  .select_related("family__developer", "source")
                  .prefetch_related("origin_country_links__country", "origin_country_links__source",
                                    "offers__service", "offers__source", "accesses__service", "evaluations__source"))
    tools = list(Tool.objects.filter(published=True).select_related("developer", "source", "legacy_version")
                 .prefetch_related("legacy_version__offers__service", "legacy_version__accesses__service"))

    # ---- counters (server render, EN/RU)
    hosts = [h for h in settings.ALLOWED_HOSTS if h not in ("*",) and not h.startswith(".")]
    client = Client(HTTP_HOST=hosts[0] if hosts else "testserver")
    expected = {"models": len(models), "tools": len(tools)}
    numbered = {"models": sum(1 for m in models if m.public_number), "tools": sum(1 for t in tools if t.public_number)}
    rendered = {}
    for kind, paths in (("models", ("/", "/ru/")), ("tools", ("/tools/", "/ru/tools/"))):
        for path in paths:
            counts = _render_counts(client, path)
            rendered[path] = counts
            values = {"tab": counts["tab_active"], "result": counts["result"], "total": counts["total"]}
            if counts["status"] != 200 or any(v != expected[kind] for v in values.values()):
                errors.append("counters %s: %s != database %d" % (path, values, expected[kind]))
            if counts["shown"] != counts["rows"] or (not counts["next"] and counts["rows"] != expected[kind]):
                errors.append("counters %s: shown %s, rendered rows %s, database %d" % (path, counts["shown"], counts["rows"], expected[kind]))
            undated = expected[kind] - numbered[kind]
            if undated and (counts["numbered"], counts["undated"]) != (numbered[kind], undated):
                errors.append("counters %s: № note %s/%s != database %d numbered / %d undated"
                              % (path, counts["numbered"], counts["undated"], numbered[kind], undated))

    # ---- origin and flags
    for model in models:
        codes = [link.country_id for link in model.origin_country_links.all()]
        if not codes:
            reason = gap("model", model.slug, "origin_status")
            (queue if reason else errors).append("origin: model %s has no country/flag%s" % (
                model.slug, " (" + reason.get("reason", "") + ")" if reason else ""))
        for link in model.origin_country_links.all():
            if link.country_id not in flags:
                errors.append("origin: no SVG flag for %s (model %s)" % (link.country_id, model.slug))
            if not link.source_id or not link.source.url:
                errors.append("provenance: origin %s of %s has no source" % (link.country_id, model.slug))
    for tool in tools:
        codes = [c.code for c in developer_countries(tool.developer.country)]
        if not codes:
            reason = gap("tool", tool.slug, "origin_status")
            (queue if reason else errors).append("origin: tool %s (developer %r, country %r) has no country/flag%s" % (
                tool.slug, tool.developer.name, tool.developer.country, " (" + reason.get("reason", "") + ")" if reason else ""))
        for code in codes:
            if code not in flags:
                errors.append("origin: no SVG flag for %s (tool %s)" % (code, tool.slug))

    # ---- pricing
    def priced(offers):
        return [o for o in offers if o.active and o.amount is not None]
    for model in models:
        offers = list(model.offers.all())
        apis = [a for a in model.accesses.all() if a.service.kind == "api"]
        reason = gap("model", model.slug, "pricing_status")
        if model.catalog_status == "active" and apis and not priced(offers):
            (queue if reason else errors).append("pricing: active model %s has a commercial API (%s) but no current price%s" % (
                model.slug, apis[0].service.name, " — " + reason["status"] if reason else ""))
        elif model.catalog_status == "active" and not apis and not priced(offers) and model.open_weights:
            pass  # open weights without a hosted API: price not applicable
        _offer_rows(model.slug, offers, errors)
    for tool in tools:
        offers = list(tool.legacy_version.offers.all()) if tool.legacy_version else []
        reason = gap("tool", tool.slug, "pricing_status")
        if reason:
            queue.append("pricing: tool %s — %s" % (tool.slug, reason["status"]))
        _offer_rows(tool.slug, offers, errors)

    # ---- evaluations
    for model in models:
        public = [e for e in model.evaluations.all() if e.public]
        developer = (model.family.developer.name or "").casefold()
        for evaluation in public:
            where = "evaluation %s/%s" % (model.slug, evaluation.observation_key or evaluation.pk)
            if evaluation.independent and (evaluation.result_kind != "independent" or evaluation.evaluator.casefold() == developer):
                errors.append("%s: marked independent but %s by %s" % (where, evaluation.result_kind, evaluation.evaluator))
            if evaluation.result_kind == "developer" and evaluation.independent:
                errors.append("%s: developer-reported result counted as independent" % where)
            if not evaluation.source_id or not evaluation.source.url:
                errors.append("provenance: %s has no source" % where)
            elif any(domain in evaluation.source.url for domain in BLOCKED_EVALUATION_SOURCES):
                errors.append("%s: public result from a source whose terms block republication (%s)" % (where, evaluation.source.url))
        independent = [e for e in public if e.independent and e.result_kind == "independent"]
        reason = gap("model", model.slug, "independent_evaluation_status")
        if reason and independent:
            errors.append("evaluations: %s has independent results but an evaluation gap is recorded" % model.slug)
        elif reason:
            queue.append("evaluations: %s — no publishable independent evaluation (%s)" % (model.slug, reason.get("reason_en", "")[:120]))

    # ---- provenance and duplicates
    for model in models:
        if not model.source_id or not model.source.url:
            errors.append("provenance: model %s has no source" % model.slug)
        if model.released and not (model.release_evidence or {}).get("source_url"):
            warnings.append("provenance: model %s has a release date without release evidence URL" % model.slug)
    for tool in tools:
        if not tool.source_id or not tool.source.url:
            errors.append("provenance: tool %s has no source" % tool.slug)
    for label, records in (("model", models), ("tool", tools)):
        names = defaultdict(set)
        for record in records:
            for name in [record.name, *(record.aliases or [])]:
                names[re.sub(r"\s+", " ", name.casefold()).strip()].add(record.slug)
        for name, slugs in names.items():
            if len(slugs) > 1:
                errors.append("duplicates: %s name/alias %r used by %s" % (label, name, sorted(slugs)))
    offer_keys = Counter((o.model_id, o.service_id, o.unit, str(o.amount), (o.conditions or {}).get("en", ""), o.billing_unit, o.active)
                         for o in Offer.objects.filter(model__published=True))
    errors.extend("duplicates: price row repeated %d× %s" % (n, key[:5]) for key, n in offer_keys.items() if n > 1)
    evaluation_keys = Counter((e.model_id, e.benchmark_id, e.configuration, e.source_record_id)
                              for e in Evaluation.objects.filter(public=True).exclude(source_record_id=""))
    errors.extend("duplicates: evaluation repeated %d× %s" % (n, key) for key, n in evaluation_keys.items() if n > 1)

    # ---- master <-> Local <-> Production
    if workbook_rows is not None and "Models" in workbook_rows:
        from . import master_sync
        snapshot, aux = cm.local_snapshot()
        master_errors, _w, _d = cm.validate(workbook_rows, snapshot, aux)
        errors.extend("master: " + e for e in master_errors[:20])
        pending = [c for c in master_sync.plan(workbook_rows) if c["kind"] in master_sync.WRITE_KINDS]
        if pending:
            errors.append("master -> Local: %d changes not synced (%s)" % (
                len(pending), ", ".join(sorted(Counter(c["kind"] for c in pending)))))
        for sheet, records in (("Models", models), ("Tools", tools)):
            master = {r["Record ID"] for r in workbook_rows[sheet] if r.get("Status") == "PUBLISHED"}
            local = {r.slug for r in records}
            if master != local:
                errors.append("master <-> Local %s: public sets differ (+%s / -%s)" % (
                    sheet, sorted(local - master)[:5], sorted(master - local)[:5]))
            if production is not None:
                live = production[0][sheet]
                if live != master:
                    errors.append("master <-> Production %s: public sets differ (+%s / -%s)" % (
                        sheet, sorted(live - master)[:5], sorted(master - live)[:5]))

    return {"checked": date.today().isoformat(), "errors": errors, "warnings": warnings, "queue": sorted(queue),
            "stats": {"models": len(models), "tools": len(tools), "numbered": numbered, "rendered": rendered,
                      "production_release": production[1] if production else None}}


def _offer_rows(owner, offers, errors):
    for offer in offers:
        where = "price %s/%s" % (owner, offer.research_key or offer.pk)
        if not offer.source_id or not offer.source.url:
            errors.append("provenance: %s has no source" % where)
        if not (offer.conditions or {}).get("ru"):
            errors.append("pricing: %s has no Russian conditions" % where)
        if offer.active and offer.amount is not None and offer.amount == 0:
            text = " ".join(str(v) for v in (offer.conditions or {}).values()).casefold()
            if not any(word in text for word in FREE_WORDS):
                errors.append("pricing: %s is $0 without a stated free tier" % where)
