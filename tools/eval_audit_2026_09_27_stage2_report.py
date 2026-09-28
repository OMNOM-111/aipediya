"""Stage-2 statistics of the Evaluation Evidence audit (read-only).

Compares the master backup taken before stage 2 with the current master and writes
artifacts/eval-audit-2026-09-27/stage2/STAGE2_STATS.md plus stage2_metrics.json.

Layers are counted separately and never merged into a score:
independent public (A), independent research-only incl. competitor measurements (B),
developer-reported (C), composite index. "Any verified numerical evaluation" = at least one
stored numeric row of any layer for the exact version.

  .venv\\Scripts\\python.exe tools\\eval_audit_2026_09_27_stage2_report.py \\
      --before backups\\catalog-master-eval-audit-20260927\\stage2-20260928\\AIpediya_Model_Verification_Master_before_stage2.xlsx \\
      --after AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx
"""
import argparse
import collections
import json
from pathlib import Path

from eval_audit_2026_09_27_report import CATEGORIES, family, is_ind, load

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/eval-audit-2026-09-27/stage2"


def excluded(e):
    try:
        extra = json.loads(e.get("Conditions Extra (JSON)") or "{}")
    except ValueError:
        return False
    return bool(extra.get("superseded_duplicate_of")) or str(extra.get("rating_exclusion_reason") or "").startswith("exact version differs")


def metrics(data):
    published = {m["Record ID"]: m for m in data["Models"] if m["Status"] == "PUBLISHED"}
    status = {}
    for f in data["Facts"]:
        if f.get("Fact") == "independent_evaluation_status" and f.get("Record Type") == "model":
            try:
                status[f["Record ID"]] = json.loads(f["Value (JSON)"])
            except ValueError:
                pass
    rows = collections.defaultdict(list)
    for e in data["Evaluations"]:
        if not excluded(e):
            rows[e["Record ID"]].append(e)
    per = {}
    for rid in published:
        mine = rows.get(rid, [])
        per[rid] = {"ip": {family(e) for e in mine if is_ind(e) and e.get("Public") == "YES"},
                    "np": {family(e) for e in mine if is_ind(e) and e.get("Public") != "YES"},
                    "dev": [e for e in mine if e.get("Result Kind") == "developer"],
                    "comp": [e for e in mine if e.get("Result Kind") == "composite"]}
    total = len(published)
    out = {"published_total": total}
    for n in (1, 2, 3, 4):
        out["independent_public_ge%d" % n] = sum(1 for p in per.values() if len(p["ip"]) >= n)
    classes = collections.Counter()
    for rid, p in per.items():
        if p["ip"]:
            classes["A_independent_public"] += 1
        elif p["np"]:
            classes["B_only_independent_research_only"] += 1
        elif p["dev"]:
            classes["C_only_developer"] += 1
        elif p["comp"]:
            classes["composite_only"] += 1
        else:
            st = (status.get(rid) or {}).get("status", "none")
            key = {"identity_ambiguous": "D_identity_ambiguous", "exact_version_not_found": "D_exact_version_not_found",
                   "not_applicable": "D_not_applicable", "no_published_numerical_evaluation": "D_no_published_numerical_evaluation",
                   "independent_nonpublic": "B_research_only_status_without_scores"}.get(st, "D_unresolved_" + st)
            classes[key] += 1
    out["classes"] = dict(sorted(classes.items()))
    # final mutually exclusive classes written by the stage-2 importer (present after the final Local pass)
    final = collections.Counter((status.get(rid) or {}).get("final_class") for rid in published)
    if None not in final:
        out["final_classes"] = dict(final)
        out["final_numeric"] = sum(1 for rid in published if (status.get(rid) or {}).get("has_numeric_evidence"))
        out["final_research_status_only"] = sum(1 for rid in published if (status.get(rid) or {}).get("final_class") == "independent_research_only"
                                                and not (status.get(rid) or {}).get("has_numeric_evidence"))
        out["final_independent_public_any"] = sum(1 for rid in published if "independent_public" in ((status.get(rid) or {}).get("statuses") or []))
    out["developer_and_independent"] = sum(1 for p in per.values() if p["dev"] and (p["ip"] or p["np"]))
    out["developer_and_independent_public"] = sum(1 for p in per.values() if p["dev"] and p["ip"])
    out["any_numeric"] = sum(1 for p in per.values() if p["ip"] or p["np"] or p["dev"] or p["comp"])
    out["status_counts"] = dict(collections.Counter((status.get(rid) or {}).get("status", "none") for rid in published))
    evals = data["Evaluations"]
    out["rows"] = {"total": len(evals), "independent_public": sum(1 for e in evals if is_ind(e) and e.get("Public") == "YES"),
                   "independent_nonpublic": sum(1 for e in evals if is_ind(e) and e.get("Public") != "YES"),
                   "developer": sum(1 for e in evals if e.get("Result Kind") == "developer"),
                   "developer_public": sum(1 for e in evals if e.get("Result Kind") == "developer" and e.get("Public") == "YES"),
                   "composite": sum(1 for e in evals if e.get("Result Kind") == "composite")}
    cats = {}
    for cat in CATEGORIES:
        ids = [rid for rid, m in published.items() if (m.get("Category") or "other") == cat]
        ip = sum(1 for rid in ids if per[rid]["ip"])
        anyn = sum(1 for rid in ids if per[rid]["ip"] or per[rid]["np"] or per[rid]["dev"] or per[rid]["comp"])
        cats[cat] = {"models": len(ids), "independent_public": ip, "any_numeric": anyn,
                     "independent_pct": round(100.0 * ip / len(ids), 1) if ids else 0.0, "any_pct": round(100.0 * anyn / len(ids), 1) if ids else 0.0}
    out["by_category"] = cats
    return out


def pct(n, d):
    return "%.1f%%" % (100.0 * n / d) if d else "—"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()
    before, after = metrics(load(args.before)), metrics(load(args.after))
    (OUT / "stage2_metrics.json").write_text(json.dumps({"before": before, "after": after}, ensure_ascii=False, indent=1), encoding="utf-8")
    p = after["published_total"]
    lines = ["# Evaluation Evidence stage 2 — BEFORE → AFTER (PUBLISHED = %d)" % p, "",
             "BEFORE = master backup taken before stage 2 (after stage 1). Layers are counted separately; no rating is computed.", "",
             "## Independent evidence", "", "| Metric | Before | After |", "|---|---|---|"]
    for n in (1, 2, 3, 4):
        k = "independent_public_ge%d" % n
        lines.append("| ≥%d public independent evaluator(s) | %d (%s) | %d (%s) |" % (n, before[k], pct(before[k], p), after[k], pct(after[k], p)))
    lines += ["", "**Any verified numerical evaluation coverage: %d / %d = %s** (before %d / %d = %s)" % (
                  after["any_numeric"], p, pct(after["any_numeric"], p), before["any_numeric"], p, pct(before["any_numeric"], p)), "",
              "## By category", "", "| Category | Models | Independent coverage (before → after) | Any evaluation coverage (before → after) |", "|---|---|---|---|"]
    for cat in CATEGORIES:
        b, a = before["by_category"][cat], after["by_category"][cat]
        lines.append("| %s | %d | %d (%.1f%%) → %d (%.1f%%) | %d (%.1f%%) → %d (%.1f%%) |" % (
            cat, a["models"], b["independent_public"], b["independent_pct"], a["independent_public"], a["independent_pct"],
            b["any_numeric"], b["any_pct"], a["any_numeric"], a["any_pct"]))
    if "final_classes" in after:
        fc = after["final_classes"]
        lines += ["", "## Final classification (mutually exclusive, 325 PUBLISHED)", "", "| Class | Models |", "|---|---|"]
        for key in ("independent_public", "independent_and_developer", "independent_research_only", "developer_reported",
                    "no_published_numerical_evaluation", "exact_version_not_found", "identity_ambiguous", "not_applicable"):
            lines.append("| %s | %d |" % (key, fc.get(key, 0)))
        lines += ["| **total** | %d |" % sum(fc.values()), "",
                  "Public independent (any, overlaps with independent_and_developer): %d / %d" % (after["final_independent_public_any"], p),
                  "", "Numeric evidence: %d = independent_public + independent_and_developer + developer_reported + independent_research_only with numbers "
                  "(%d research-only cards carry only a status, no numbers)." % (after["final_numeric"], after["final_research_status_only"])]
    lines += ["", "## Evaluation rows", "", "| Rows | Before | After |", "|---|---|---|"]
    for key in ("total", "independent_public", "independent_nonpublic", "developer", "developer_public", "composite"):
        lines.append("| %s | %d | %d |" % (key, before["rows"][key], after["rows"][key]))
    lines += ["", "## Status facts of PUBLISHED models", "", "Before: `%s`" % json.dumps(before["status_counts"]), "", "After: `%s`" % json.dumps(after["status_counts"])]
    (OUT / "STAGE2_STATS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
