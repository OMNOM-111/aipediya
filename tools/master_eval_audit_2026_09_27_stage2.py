"""Evaluation Evidence audit, stage 2 (2026-09-27/28): developer-reported and remaining evidence.

Owner task "завершить Evaluation Evidence до конца" (Timeline card EVAL-EVIDENCE-AUDIT-2026-09-27,
stage 2). Scope is the master only: Evaluations, Facts (``independent_evaluation_status``) and
Changelog, plus the generated UI note file ``data/evaluation_gap_notes.json``. Names, Record IDs,
numbers, dates, prices, Offers/Access/Origins, Local SQLite and Production are not touched here.

Layers (never mixed; nothing here computes a rating):

* Independent Evidence — third-party runs. ``Public=YES`` only with an open results licence;
  competitor measurements (a rival developer's launch post) are ``Public=NO`` and rating-ineligible.
* Developer Evidence — results the model's developer published about its own exact version
  (model/system card, technical report, launch post, official chart). ``Result Kind=developer``,
  ``Independent=NO``, ``Public=YES`` as an attributed self-report, ``rating_eligible=false``.

Stage 2 also:

* marks existing stage-1 developer rows taken from the developer's own report as ``Public=YES``
  (same attributed-self-report policy; rows from leaderboard submissions keep the leaderboard licence);
* closes the disputed rows (GPT-5.6 Sol "promax" = GPT-5.6 Sol Pro; rounded ECI duplicates such as
  evaluation-867) with Changelog entries;
* re-derives the evidenced status fact for every model with the stage-2 vocabulary
  (independent_public, independent_nonpublic, developer_reported, no_published_numerical_evaluation,
  exact_version_not_found, identity_ambiguous, not_applicable); stage-1 ``gap`` remains only for
  NEEDS_REVIEW records outside the stage-2 scope.

Evidence rows come from tools/eval_audit_2026_09_27_stage2_data.py (hand transcription with saved
source pages/images and SHA-256). Re-running is idempotent.

  .venv\\Scripts\\python.exe tools\\master_eval_audit_2026_09_27_stage2.py --book AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx [--dry-run]
"""
import argparse
import collections
import hashlib
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402
import eval_audit_2026_09_27_stage2_data as data  # noqa: E402
from eval_audit_2026_09_27_map import CONFIGURATION_OF  # noqa: E402

RUN = "eval-audit-2026-09-27-s2"
STAGE1 = "eval-audit-2026-09-27"
CHECKED = "2026-09-28"
STAGE2 = ROOT / "artifacts/eval-audit-2026-09-27/stage2"
GAP_NOTES = ROOT / "data/evaluation_gap_notes.json"
BLOCKED = ("artificialanalysis.ai", "lmarena.ai", "arena.ai", "livebench.ai", "swebench.com")
DEVELOPER_REPORT_TYPES = ("developer technical report", "developer report")
STATUS_ORDER = ("independent_public", "independent_nonpublic", "developer_reported", "no_published_numerical_evaluation",
                "exact_version_not_found", "identity_ambiguous", "not_applicable", "gap")
STATUS_TEXT = {
    "independent_public": ("Publishable independent evaluations of the exact version: %s.", "Публикуемые независимые оценки точной версии: %s."),
    "independent_nonpublic": ("Independent evaluations of the exact version exist (%s) but may not be republished; shown as a status without scores.",
                              "Независимые оценки точной версии есть (%s), но их нельзя републиковать; показывается статус без баллов."),
    "developer_reported": ("Only results published by the developer (%s) were found for the exact version.",
                           "Для точной версии найдены только результаты разработчика (%s)."),
}
# bounded units -> (low, high) for an exact normalized percent; anything else is kept unnormalized
BOUNDED = {"%": (0, 100), "points (0–100)": (0, 100), "points (1–5)": (1, 5), "points (1–10)": (1, 10), "points (0–1)": (0, 1),
           "score (0–1)": (0, 1), "speaker similarity (0–1)": (0, 1), "% (accuracy = 100 − WER)": (0, 100)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fmt(value):
    text = format(value.normalize(), "f")
    return "0" if text in ("-0", "") else text


def page_path(page):
    if page.startswith("../img/"):
        return STAGE2 / "img" / page[len("../img/"):]
    return STAGE2 / "pages" / (page + ".raw")


def normalize(raw, unit):
    """(score, unit, extra) — the source value is always kept; % only when exact."""
    if unit == data.FRAC:
        return raw * 100, "%", {"source_score": str(raw), "source_unit": "fraction (0–1)", "bounded_range": [0, 1],
                                "normalized_percent": fmt(raw * 100), "normalization_method": "score × 100 (exact)"}
    extra = {"source_score": str(raw), "source_unit": unit}
    if unit in BOUNDED:
        low, high = BOUNDED[unit]
        extra.update(bounded_range=[low, high], normalized_percent=fmt((raw - low) / Decimal(high - low) * 100),
                     normalization_method="none (source is a percentage)" if unit == "%" else "(score − min)/(max − min) × 100 (exact, known scale)")
    else:
        extra.update(normalized_percent=None, normalization_method="not normalized (error rate, Elo, distance or unbounded scale)")
    return raw, unit, extra


def build_rows(models, existing):
    """Evaluation rows for the stage-2 observations (new rows and recomputed rows of this run)."""
    seen_values = {(r["Record ID"], r["Benchmark"], r["Evaluator"], r["Configuration"], r["Score"]) for r in existing if RUN not in (r.get("Key") or "")}
    out, skipped, hashes = [], collections.Counter(), {}
    for rid, key, bench, score, unit, higher, configuration, category, note in data.OBS:
        model = models[rid]
        url, page, evaluator, kind, public, title = data.SOURCES[key]
        path = page_path(page)
        if not path.exists():
            raise SystemExit("missing saved source for %s: %s" % (key, path))
        if path not in hashes:
            hashes[path] = sha(path)
        raw = Decimal(score)
        value, unit_out, extra = normalize(raw, unit)
        value_text = fmt(value)
        if (rid, bench, evaluator, configuration, value_text) in seen_values:
            skipped["already present in master (earlier run)"] += 1
            continue
        developer = kind == "developer"
        competitor = kind == "competitor"
        independent = not developer
        public_flag = True if developer else (bool(public) and not competitor)
        if developer:
            eligible, exclusion, etype = False, "developer-reported result (Developer Evidence layer, never an Independent Rating input)", "model developer (own publication)"
            licence = "developer publication; reproduced as an attributed self-reported figure"
        elif competitor:
            eligible, exclusion, etype = False, "measured by a competing model developer in its own launch material", "competitor measurement (vendor launch material)"
            licence = "vendor publication; no reuse licence for results"
        else:
            eligible = public_flag
            exclusion = None if public_flag else "not republishable (no open results licence)"
            etype, licence = "independent evaluator", ("open results licence" if public_flag else "no open results licence stated")
        extra.update({"evidence_layer": "developer" if developer else "independent", "evaluator_type": etype, "evaluator_family": evaluator,
                      "rating_eligible": eligible, "rating_exclusion_reason": exclusion, "licence": licence, "source_title": title,
                      "source_page": str(path.relative_to(ROOT)).replace("\\", "/"),
                      "exact_version_basis": "record identity checked by hand against the source's model name/checkpoint (%s)" % CHECKED,
                      "transcription_note": note or None})
        source_id = "s2:%s:%s:%s" % (key, bench, configuration)
        obs = hashlib.sha256(("%s:%s:%s" % (RUN, rid, source_id)).encode()).hexdigest()
        layer_en = "Developer-reported" if developer else ("Competitor-measured" if competitor else "Independent")
        layer_ru = "Результат разработчика" if developer else ("Замер конкурента" if competitor else "Независимый результат")
        out.append({
            "Key": "evaluation-%s-%s" % (RUN, obs[:16]), "Record Type": "model", "Record ID": rid, "Benchmark": bench[:150],
            "Protocol": ("%s; %s (%s)" % (bench, evaluator, title))[:250], "Benchmark Category": category, "Unit": unit_out[:40],
            "Higher Is Better": higher, "Score": value_text, "Evaluator": evaluator[:140],
            "Result Kind": "developer" if developer else "independent", "Independent": "YES" if independent else "NO",
            "Public": "YES" if public_flag else "NO", "Measured": "", "Configuration": configuration[:250], "Confidence Low": "", "Confidence High": "",
            "Conditions EN": "%s result for %s (%s), as published in: %s. Source value %s %s.%s" % (
                layer_en, bench, configuration, title, score, unit, (" Note: %s." % note) if note else ""),
            "Conditions RU": "%s: %s (%s), опубликовано в источнике «%s». Значение источника %s %s.%s" % (
                layer_ru, bench, configuration, title, score, unit, (" Примечание: %s." % note) if note else ""),
            "Conditions Extra (JSON)": json.dumps(extra, ensure_ascii=False, sort_keys=True), "Source URL": url, "Checked": CHECKED,
            "Observation Key": obs, "Source Model": model["Name"], "Source Record ID": source_id[:250],
            "Snapshot": "page/image saved %s" % CHECKED, "Source SHA256": hashes[path]})
    return out, skipped


def developer_rows_public(rows, log, stamp):
    """Stage-1 developer rows copied from the developer's own report become attributed public self-reports."""
    changed = 0
    for row in rows["Evaluations"]:
        if row.get("Result Kind") != "developer" or row.get("Public") == "YES":
            continue
        try:
            extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
        except ValueError:
            continue
        if extra.get("evaluator_type") not in DEVELOPER_REPORT_TYPES or any(d in (row.get("Source URL") or "") for d in BLOCKED):
            continue
        before = row["Public"]
        row["Public"] = "YES"
        extra.update(evidence_layer="developer", rating_eligible=False,
                     rating_exclusion_reason="developer-reported result (Developer Evidence layer, never an Independent Rating input)",
                     publication_basis="stage 2 policy: developer's own figures are shown as attributed self-reports")
        row["Conditions Extra (JSON)"] = json.dumps(extra, ensure_ascii=False, sort_keys=True)
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "Public (%s)" % row["Key"],
                    "Before": before, "After": "YES", "Reason": "%s: developer's own reported result shown as «Результаты разработчика» (Developer Evidence layer, rating-ineligible)" % RUN})
        changed += 1
    return changed


def close_disputes(rows, log, stamp):
    """Disputed rows of the stage-1 review, closed with evidence."""
    closed = []
    ev = rows["Evaluations"]
    for row in ev:
        # 1. Epoch "gpt-5.6-sol_promax" = display name "GPT-5.6 Sol (pro, max)"; external copies call it "GPT-5.6 Sol Pro".
        #    Pro is a separate parallel-compute product, not a reasoning-effort setting of GPT-5.6 Sol.
        if row["Record ID"] == "gpt-56-sol-201e54cf" and row.get("Configuration") == "promax" and row.get("Public") == "YES":
            extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
            extra.update(rating_eligible=False, rating_exclusion_reason="exact version differs: GPT-5.6 Sol Pro (pro, max), not GPT-5.6 Sol",
                         exact_version_basis="Epoch model_metadata.csv 2026-09-27: gpt-5.6-sol_promax display name 'GPT-5.6 Sol (pro, max)'; "
                                             "dtbench/lmca external rows name it 'GPT-5.6 Sol Pro'")
            closed.append((row, "Public", "NO", "exact-version rule: GPT-5.6 Sol Pro (pro, max) is a distinct parallel-compute product; kept as internal evidence"))
            row["Conditions Extra (JSON)"] = json.dumps(extra, ensure_ascii=False, sort_keys=True)
        # 2. rounded ECI rows added 2026-09-21 with Configuration «Модель» repeat the precise ECI observation of 2026-09-20
        #    (ECI is a model-group index: on a configuration card it repeats the parent's group value)
        if row.get("Benchmark") == "ECI" and row.get("Configuration") == "Модель":
            owners = {row["Record ID"]} | ({CONFIGURATION_OF[row["Record ID"]][0]} if row["Record ID"] in CONFIGURATION_OF else set())
            precise = [r for r in ev if r is not row and r["Record ID"] in owners and r["Benchmark"] == "ECI"
                       and r.get("Configuration") == "published model-group index" and r.get("Public") == "YES"]
            if precise and abs(Decimal(precise[0]["Score"]) - Decimal(row["Score"])) < 1:
                extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
                if extra.get("superseded_duplicate_of") != precise[0]["Key"]:
                    extra.update(superseded_duplicate_of=precise[0]["Key"], rating_eligible=False,
                                 rating_exclusion_reason="rounded duplicate of the precise Epoch ECI observation %s" % precise[0]["Key"])
                    closed.append((row, "Conditions Extra (JSON)", json.dumps(extra, ensure_ascii=False, sort_keys=True),
                                   "marked as a superseded duplicate (excluded from evidence counts)"))
                if row["Key"] == "evaluation-867":
                    closed.append((row, "Source Model", "DeepSeek V4 Pro 0813",
                                   "Epoch ECI model group is 'DeepSeek V4 Pro 0813' (eci_scores.csv 2026-09-27: 155.39, CI 153.70–157.31); "
                                   "'deepseek-v4-pro' is the April DeepSeek-V4-Pro group. The value 155 is correct for 0813"))
                where = "the parent card %s" % precise[0]["Record ID"] if precise[0]["Record ID"] != row["Record ID"] else "the same Epoch model group"
                closed.append((row, "Public", "NO", "rounded duplicate of the precise ECI observation %s (%s) on %s; kept as history" % (
                    precise[0]["Key"], precise[0]["Score"], where)))
    for row, field, value, reason in closed:
        if row.get(field) == value:
            continue
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "%s (%s)" % (field, row["Key"]),
                    "Before": row.get(field, ""), "After": value, "Reason": "%s: disputed row closed — %s" % (RUN, reason)})
        row[field] = value
    return [(r["Key"], f, v) for r, f, v, _ in closed]


def superseded(row):
    """Rows kept only as history: another product/version, or a rounded duplicate of a kept observation."""
    try:
        extra = json.loads(row.get("Conditions Extra (JSON)") or "{}")
    except ValueError:
        return False
    return bool(extra.get("superseded_duplicate_of")) or str(extra.get("rating_exclusion_reason") or "").startswith("exact version differs")


FINAL_CLASSES = ("independent_public", "independent_and_developer", "independent_research_only", "developer_reported",
                 "no_published_numerical_evaluation", "exact_version_not_found", "identity_ambiguous", "not_applicable")


def final_class(ind_public, research_numeric, research_status, dev, statuses):
    """Mutually exclusive class of a card (owner's list, 2026-09-28)."""
    independent_any = ind_public or research_numeric or research_status
    if dev and independent_any:
        return "independent_and_developer"
    if ind_public:
        return "independent_public"
    if research_numeric or research_status:
        return "independent_research_only"
    if dev:
        return "developer_reported"
    for name in ("not_applicable", "identity_ambiguous", "exact_version_not_found", "no_published_numerical_evaluation"):
        if name in statuses:
            return name
    return "gap"


def derive_status(rows, models, stage1):
    evals = collections.defaultdict(list)
    for row in rows["Evaluations"]:
        if not superseded(row):
            evals[row["Record ID"]].append(row)
    out = {}
    for rid, model in models.items():
        mine = evals.get(rid, [])
        ind = [e for e in mine if e.get("Result Kind") == "independent" and e.get("Independent") == "YES"]
        ind_pub = [e for e in ind if e.get("Public") == "YES"]
        ind_np = [e for e in ind if e.get("Public") != "YES"]
        research, competitor = set(), set()
        for e in ind_np:
            try:
                extra = json.loads(e.get("Conditions Extra (JSON)") or "{}")
            except ValueError:
                extra = {}
            if str(extra.get("rating_exclusion_reason") or "").startswith("exact version differs"):
                continue  # another product/version kept only as history (e.g. GPT-5.6 Sol Pro rows)
            (competitor if "competitor" in str(extra.get("evaluator_type") or "") else research).add(e["Evaluator"])
        dev = [e for e in mine if e.get("Result Kind") == "developer"]
        comp = [e for e in mine if e.get("Result Kind") == "composite"]
        comp_pub = [e for e in comp if e.get("Public") == "YES"]
        comp_np = [e for e in comp if e.get("Public") != "YES"]
        research |= {e["Evaluator"] for e in comp_np}  # e.g. Artificial Analysis index: independent, not republishable
        explicit = data.STATUS.get(rid)
        statuses = []
        if ind_pub or comp_pub:
            statuses.append("independent_public")
        if ind_np or comp_np or (explicit and explicit["status"] == "independent_nonpublic"):
            statuses.append("independent_nonpublic")
        if dev:
            statuses.append("developer_reported")
        if explicit and explicit["status"] not in statuses:
            statuses.append(explicit["status"])
        if rid in CONFIGURATION_OF and "not_applicable" not in statuses:
            statuses.append("not_applicable")
        previous = (stage1.get(rid) or {}).get("status")
        if not statuses:
            statuses.append({"exact_version_not_found": "exact_version_not_found", "identity_ambiguous": "identity_ambiguous",
                             "not_applicable": "not_applicable"}.get(previous, "gap"))
        statuses.sort(key=STATUS_ORDER.index)
        primary = statuses[0]
        evidence = {k: v for k, v in (stage1.get(rid) or {}).items()
                    if k in ("searched_names", "checked_sources", "rejected_source_names", "next_step")}
        evidence.update({"record_id": rid, "checked": CHECKED, "status": primary, "statuses": statuses,
                         "independent_public_evaluators": sorted({e["Evaluator"] for e in ind_pub}),
                         "independent_nonpublic_evaluators": sorted(research | competitor),
                         "research_only_evaluators": sorted(research), "competitor_evaluators": sorted(competitor),
                         "developer_evaluators": sorted({e["Evaluator"] for e in dev}),
                         "counts": {"independent_public": len(ind_pub), "independent_nonpublic": len(ind_np), "developer": len(dev), "composite": len(comp)},
                         "stage": "stage 2 (%s)" % RUN, "previous_status": previous})
        if primary == "independent_nonpublic" and not (research or competitor) and explicit:
            evidence["reason_en"], evidence["reason_ru"] = explicit["found_en"], explicit["found_ru"]
        elif primary == "independent_nonpublic":
            en, ru = [], []
            if research:
                en.append("independent studies of the exact version exist (%s) but their results may not be republished" % ", ".join(sorted(research)))
                ru.append("есть независимые исследования точной версии (%s), но их результаты нельзя републиковать" % ", ".join(sorted(research)))
            if competitor:
                en.append("competing developers published their own measurements (%s); these are not independent and are not shown" % ", ".join(sorted(competitor)))
                ru.append("конкуренты опубликовали собственные замеры (%s); это не независимая проверка, баллы не показываются" % ", ".join(sorted(competitor)))
            evidence["reason_en"] = "; ".join(en)[:1].upper() + "; ".join(en)[1:] + "."
            evidence["reason_ru"] = "; ".join(ru)[:1].upper() + "; ".join(ru)[1:] + "."
        elif primary in STATUS_TEXT:
            names = ", ".join(evidence["independent_public_evaluators"] if primary == "independent_public" else evidence["developer_evaluators"])
            evidence["reason_en"], evidence["reason_ru"] = STATUS_TEXT[primary][0] % names, STATUS_TEXT[primary][1] % names
        elif explicit:
            evidence["reason_en"], evidence["reason_ru"] = explicit["found_en"], explicit["found_ru"]
        if explicit:
            evidence["stage2_finding_en"], evidence["stage2_finding_ru"] = explicit["found_en"], explicit["found_ru"]
            evidence["stage2_checked_sources"] = explicit["checked"]
        dev_sources = sorted({e["Source URL"] for e in dev})
        if dev_sources:
            evidence["developer_sources"] = dev_sources[:12]
        numeric = bool(ind_pub or comp_pub or ind_np or comp_np or dev)
        evidence["final_class"] = final_class(bool(ind_pub or comp_pub), bool(ind_np or comp_np),
                                              bool(explicit and explicit["status"] == "independent_nonpublic"), bool(dev), statuses)
        evidence["has_numeric_evidence"] = numeric
        if model.get("Status") == "PUBLISHED" and (primary == "gap" or evidence["final_class"] == "gap"):
            raise SystemExit("PUBLISHED model %s still has status gap" % rid)
        out[rid] = evidence
    return out


def write_gap_notes(status, models):
    """UI note file: every PUBLISHED model without a publishable independent result gets an explained status."""
    by_slug = {}
    for rid, ev in sorted(status.items()):
        if models[rid].get("Status") != "PUBLISHED" or ev["status"] == "independent_public":
            continue
        links = [{"url": u, "label_ru": "Проверенный источник", "label_en": "Checked source", "kind": "checked_source"}
                 for u in (ev.get("stage2_checked_sources") or ev.get("developer_sources") or [])[:6]]
        by_slug[rid] = {"reason_code": ev["status"], "statuses": ev["statuses"], "final_class": ev["final_class"],
                        "reason": {"ru": ev.get("reason_ru", ""), "en": ev.get("reason_en", "")}, "checked": CHECKED,
                        "independent_nonpublic_evaluators": ev["independent_nonpublic_evaluators"],
                        "developer_evaluators": ev["developer_evaluators"], "links": links,
                        "checked_sources": [link["url"] for link in links]}
    # research-only / competitor evaluator names for every PUBLISHED card (names only, never scores)
    evidence = {rid: {"research_only": ev["research_only_evaluators"], "competitor": ev["competitor_evaluators"]}
                for rid, ev in sorted(status.items()) if models[rid].get("Status") == "PUBLISHED"
                and (ev["research_only_evaluators"] or ev["competitor_evaluators"])}
    GAP_NOTES.write_text(json.dumps({"checked": CHECKED, "by_slug": by_slug, "nonpublic_evidence_by_slug": evidence},
                                    ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(by_slug)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--notes-only", action="store_true", help="recompute and write data/evaluation_gap_notes.json only; the workbook is not written")
    parser.add_argument("--report", default=str(STAGE2 / "stage2_data.json"))
    args = parser.parse_args()
    book = Path(args.book)
    before_sha = sha(book)
    rows, meta, extra = cm.read_workbook(book)
    stamp = cm.now_utc()
    log = rows["Changelog"]
    models = {r["Record ID"]: r for r in rows["Models"]}
    for rid in {o[0] for o in data.OBS} | set(data.STATUS):
        assert rid in models, rid
    columns = list(rows["Evaluations"][0].keys())
    run_rows = {r["Key"]: r for r in rows["Evaluations"] if RUN in (r.get("Key") or "")}
    new_rows, skipped = build_rows(models, rows["Evaluations"])
    added = corrected = 0
    for new in new_rows:
        existing = run_rows.pop(new["Key"], None)
        if existing is None:
            row = {c: "" for c in columns}
            row.update(new)
            rows["Evaluations"].append(row)
            log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "row added (%s)" % row["Key"], "Before": "",
                        "After": ("%s | %s %s | %s | %s | Independent=%s Public=%s" % (row["Benchmark"], row["Score"], row["Unit"], row["Evaluator"],
                                                                                  row["Result Kind"], row["Independent"], row["Public"]))[:500],
                        "Reason": "%s: evaluation evidence of the exact version transcribed from the saved source" % RUN})
            added += 1
            continue
        for field, value in new.items():
            if field in columns and existing.get(field, "") != value:
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": existing["Record ID"], "Field": "%s (%s)" % (field, existing["Key"]),
                            "Before": str(existing.get(field, ""))[:1500], "After": value[:1500], "Reason": "%s: correction of this run's row" % RUN})
                existing[field] = value
                corrected += 1
    if run_rows:  # observations removed from the data file since an earlier pass of this run
        drop = set(run_rows)
        for key in sorted(drop):
            row = run_rows[key]
            log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "row removed (%s)" % key,
                        "Before": ("%s | %s | %s" % (row["Benchmark"], row["Score"], row["Evaluator"]))[:500], "After": "",
                        "Reason": "%s: observation withdrawn from this run's evidence file" % RUN})
        rows["Evaluations"][:] = [r for r in rows["Evaluations"] if r["Key"] not in drop]
    flipped = developer_rows_public(rows, log, stamp)
    disputes = close_disputes(rows, log, stamp)
    # stage-1 facts keep their search evidence (searched names, checked sources, rejected names); the status
    # wording is re-derived. On a re-run the stage-1 status is read back from "previous_status".
    stage1 = {}
    for fact in rows["Facts"]:
        if fact.get("Fact") == "independent_evaluation_status" and fact.get("Record Type") == "model":
            try:
                value = json.loads(fact.get("Value (JSON)") or "{}")
            except ValueError:
                value = {}
            if RUN in (value.get("stage") or ""):
                value["status"] = value.get("previous_status")
            stage1[fact["Record ID"]] = value
    status = derive_status(rows, models, stage1)
    facts = {(f["Record Type"], f["Record ID"], f["Fact"]): f for f in rows["Facts"] if f.get("Fact") == "independent_evaluation_status"}
    fact_columns = list(rows["Facts"][0].keys())
    changed_facts = added_facts = 0
    for rid, evidence in status.items():
        value = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
        existing = facts.get(("model", rid, "independent_evaluation_status"))
        if existing is None:
            row = {c: "" for c in fact_columns}
            row.update({"Key": ("fact-%s-independent_evaluation_status-%s" % (RUN, rid))[:120], "Record Type": "model", "Record ID": rid,
                        "Fact": "independent_evaluation_status", "Value (JSON)": value, "Source URL": "https://epoch.ai/benchmarks/use-this-data", "Checked": CHECKED})
            rows["Facts"].append(row)
            added_facts += 1
            continue
        if existing["Value (JSON)"] != value:
            log.append({"Timestamp (UTC)": stamp, "Sheet": "Facts", "Record ID": rid, "Field": "Value (JSON) (%s)" % existing["Key"],
                        "Before": existing["Value (JSON)"][:1500], "After": value[:1500], "Reason": "%s: status re-derived with the stage-2 vocabulary and evidence" % RUN})
            existing["Value (JSON)"] = value
            existing["Checked"] = CHECKED
            changed_facts += 1
    published = {rid for rid, m in models.items() if m.get("Status") == "PUBLISHED"}
    report = {"before_sha256": before_sha, "added_evaluations": added, "corrected_fields": corrected, "skipped": dict(skipped),
              "developer_rows_made_public": flipped, "disputes_closed": disputes, "facts_added": added_facts, "facts_changed": changed_facts,
              "status_counts_published": dict(collections.Counter(status[r]["status"] for r in published)),
              "final_class_published": dict(collections.Counter(status[r]["final_class"] for r in published)),
              "numeric_evidence_published": sum(1 for r in published if status[r]["has_numeric_evidence"]),
              "status_counts_all": dict(collections.Counter(v["status"] for v in status.values()))}
    if not args.dry_run or args.notes_only:
        report["gap_notes_written"] = write_gap_notes(status, models)
    if args.notes_only:
        print(json.dumps({"gap_notes_written": report["gap_notes_written"]}))
        return
    Path(args.report).write_text(json.dumps({**report, "status": status}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    if args.dry_run:
        print("dry run: workbook not written")
        return
    meta = dict(meta)
    meta.update({"Verification run": "%s — evaluation evidence stage 2 (Evaluations, Facts)" % RUN})
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, book, extra)
    print(json.dumps({"after_sha256": sha(book)}, indent=1))


if __name__ == "__main__":
    main()
