"""BEFORE → AFTER report of the 2026-09-27 independent-evaluation audit (read-only).

Compares two master workbooks (the pre-audit backup and the current book) and writes
artifacts/eval-audit-2026-09-27/REPORT.md plus metrics.json. Nothing is modified.

  .venv\\Scripts\\python.exe tools\\eval_audit_2026_09_27_report.py \\
      --before backups\\catalog-master-eval-audit-20260927\\AIpediya_Model_Verification_Master_before_eval_audit.xlsx \\
      --after AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx
"""
import argparse
import collections
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/eval-audit-2026-09-27"
CATEGORIES = ("text", "image", "video", "audio", "other")


def load(path):
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for name in ("Models", "Evaluations", "Facts"):
        rows = book[name].iter_rows(values_only=True)
        head = next(rows)
        out[name] = [dict(zip(head, ["" if v is None else str(v) for v in r])) for r in rows if any(v is not None for v in r)]
    return out


def family(evaluation):
    try:
        extra = json.loads(evaluation.get("Conditions Extra (JSON)") or "{}")
    except ValueError:
        extra = {}
    fam = (extra.get("evaluator_family") if isinstance(extra, dict) else None) or evaluation.get("Evaluator") or ""
    kind = (extra.get("evaluator_type") or "") if isinstance(extra, dict) else ""
    if "report" in kind and " (" in fam:  # paper/report rows: the organization, not the paper title
        fam = fam.split(" (", 1)[0]
    return fam


def benchmark_family(name):
    if name.startswith("MTEB"):
        return "MTEB"
    if name.startswith("FrontierMath"):
        return "FrontierMath"
    if name.startswith("Aider"):
        return name
    return re.sub(r"\s*\(.*\)$", "", name)


def is_ind(e):
    return e.get("Independent") == "YES" and e.get("Result Kind") == "independent"


def metrics(data):
    models = {m["Record ID"]: m for m in data["Models"]}
    published = {k: m for k, m in models.items() if m["Status"] == "PUBLISHED"}
    status = {}
    for f in data["Facts"]:
        if f.get("Fact") == "independent_evaluation_status" and f.get("Record Type") == "model":
            try:
                status[f["Record ID"]] = json.loads(f["Value (JSON)"])
            except ValueError:
                pass
    by_model = collections.defaultdict(list)
    for e in data["Evaluations"]:
        by_model[e["Record ID"]].append(e)

    def per_model(rid):
        rows = by_model.get(rid, [])
        pub = [e for e in rows if is_ind(e) and e.get("Public") == "YES"]
        ind = [e for e in rows if is_ind(e)]
        dev = [e for e in rows if e.get("Result Kind") == "developer"]
        return {"public_evaluators": {family(e) for e in pub}, "all_evaluators": {family(e) for e in ind},
                "public_rows": len(pub), "independent_rows": len(ind), "not_public_rows": len(ind) - len(pub), "developer_rows": len(dev),
                "public_benchmarks": {e["Benchmark"] for e in pub}, "public_families": {benchmark_family(e["Benchmark"]) for e in pub},
                "public_categories": {e.get("Benchmark Category") for e in pub}}

    stats = {rid: per_model(rid) for rid in models}
    total_pub = len(published)
    out = {"models_total": len(models), "published_total": total_pub,
           "published_researched": sum(1 for rid in published if rid in status),
           "status_counts_published": dict(collections.Counter(status.get(rid, {}).get("status", "none") for rid in published)),
           "status_counts_all": dict(collections.Counter(status.get(rid, {}).get("status", "none") for rid in models))}
    for n in (1, 2, 3, 4):
        out["published_ge%d_public_evaluators" % n] = sum(1 for rid in published if len(stats[rid]["public_evaluators"]) >= n)
        out["published_ge%d_any_independent_evaluators" % n] = sum(1 for rid in published if len(stats[rid]["all_evaluators"]) >= n)
    evals = data["Evaluations"]
    out["unique_public_independent_evaluators"] = sorted({family(e) for e in evals if is_ind(e) and e.get("Public") == "YES"})
    out["unique_independent_evaluators_any"] = sorted({family(e) for e in evals if is_ind(e)})
    out["unique_public_benchmark_families"] = sorted({benchmark_family(e["Benchmark"]) for e in evals if is_ind(e) and e.get("Public") == "YES"})
    out["public_independent_observations"] = sum(1 for e in evals if is_ind(e) and e.get("Public") == "YES")
    out["independent_not_public_observations"] = sum(1 for e in evals if is_ind(e) and e.get("Public") != "YES")
    out["developer_observations"] = sum(1 for e in evals if e.get("Result Kind") == "developer")
    out["composite_observations"] = sum(1 for e in evals if e.get("Result Kind") == "composite")
    out["evaluations_total"] = len(evals)
    out["published_developer_only"] = sum(1 for rid in published if not stats[rid]["independent_rows"] and stats[rid]["developer_rows"])
    out["published_exact_version_gaps"] = sum(1 for rid in published if status.get(rid, {}).get("status") in ("exact_version_not_found", "identity_ambiguous"))
    cats = {}
    for cat in CATEGORIES:
        ids = [rid for rid, m in published.items() if (m.get("Category") or "other") == cat]
        cats[cat] = {"models": len(ids), "researched": sum(1 for rid in ids if rid in status),
                     "ge1_public_independent": sum(1 for rid in ids if stats[rid]["public_evaluators"]),
                     "ge2_public_evaluators": sum(1 for rid in ids if len(stats[rid]["public_evaluators"]) >= 2),
                     "ge1_any_independent": sum(1 for rid in ids if stats[rid]["all_evaluators"]),
                     "gaps": sum(1 for rid in ids if not stats[rid]["public_evaluators"])}
        cats[cat]["coverage_pct"] = round(100 * cats[cat]["ge1_public_independent"] / cats[cat]["models"], 1) if ids else 0.0
    out["by_category"] = cats
    return out, published, stats, status


def pct(n, d):
    return "%.1f%%" % (100.0 * n / d) if d else "—"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()
    before, _, _, _ = metrics(load(args.before))
    after, published, stats, status = metrics(load(args.after))
    (OUT / "metrics.json").write_text(json.dumps({"before": before, "after": after}, ensure_ascii=False, indent=1), encoding="utf-8")
    p = after["published_total"]
    lines = ["# Independent-evaluation audit — BEFORE → AFTER (2026-09-27)", "",
             "Master only (Evaluations, Facts, Changelog). Local SQLite, site and Production unchanged.", "",
             "## Coverage (PUBLISHED = %d)" % p, "", "| Metric | Before | After |", "|---|---|---|"]
    row = lambda label, b, a: lines.append("| %s | %s | %s |" % (label, b, a))  # noqa: E731
    row("Models total", before["models_total"], after["models_total"])
    row("PUBLISHED researched (has independent_evaluation_status)", "%d (%s)" % (before["published_researched"], pct(before["published_researched"], p)),
        "%d (%s)" % (after["published_researched"], pct(after["published_researched"], p)))
    for n in (1, 2, 3, 4):
        row("PUBLISHED with ≥%d public independent evaluator(s)" % n, "%d (%s)" % (before["published_ge%d_public_evaluators" % n], pct(before["published_ge%d_public_evaluators" % n], p)),
            "%d (%s)" % (after["published_ge%d_public_evaluators" % n], pct(after["published_ge%d_public_evaluators" % n], p)))
    for n in (1, 2, 3):
        row("PUBLISHED with ≥%d independent evaluator(s), incl. Public=NO" % n, before["published_ge%d_any_independent_evaluators" % n], after["published_ge%d_any_independent_evaluators" % n])
    lines += ["", "## Diversity", "", "| Metric | Before | After |", "|---|---|---|"]
    row("Unique public independent evaluator organizations", len(before["unique_public_independent_evaluators"]), len(after["unique_public_independent_evaluators"]))
    row("Unique independent evaluator organizations (incl. Public=NO)", len(before["unique_independent_evaluators_any"]), len(after["unique_independent_evaluators_any"]))
    row("Unique public benchmark families", len(before["unique_public_benchmark_families"]), len(after["unique_public_benchmark_families"]))
    row("Public independent observations", before["public_independent_observations"], after["public_independent_observations"])
    row("Independent but Public=NO observations", before["independent_not_public_observations"], after["independent_not_public_observations"])
    row("Developer-reported observations", before["developer_observations"], after["developer_observations"])
    row("Composite index observations", before["composite_observations"], after["composite_observations"])
    row("PUBLISHED developer-only", before["published_developer_only"], after["published_developer_only"])
    row("PUBLISHED exact-version / identity gaps", before["published_exact_version_gaps"], after["published_exact_version_gaps"])
    lines += ["", "Public independent evaluators after: " + ", ".join(after["unique_public_independent_evaluators"]), "",
              "## By category (PUBLISHED)", "", "| Category | Models | Researched | ≥1 public independent | ≥2 public evaluators | ≥1 independent incl. Public=NO | Gaps (no public) | Coverage |", "|---|---|---|---|---|---|---|---|"]
    for cat in CATEGORIES:
        b, a = before["by_category"][cat], after["by_category"][cat]
        lines.append("| %s | %d | %d | %d → %d | %d → %d | %d | %d | %.1f%% → %.1f%% |" % (cat, a["models"], a["researched"], b["ge1_public_independent"], a["ge1_public_independent"],
                                                                                   b["ge2_public_evaluators"], a["ge2_public_evaluators"], a["ge1_any_independent"], a["gaps"], b["coverage_pct"], a["coverage_pct"]))
    lines += ["", "## Status of PUBLISHED models", "", "Before: %s" % json.dumps(before["status_counts_published"]), "", "After: %s" % json.dumps(after["status_counts_published"]), "",
              "## Remaining PUBLISHED models without a public independent evaluation (%d)" % sum(1 for rid in published if not stats[rid]["public_evaluators"]), "",
              "| Record ID | Name | Developer | Category | Status | Reason | Developer-only rows | Independent (Public=NO) | Next step |", "|---|---|---|---|---|---|---|---|---|"]
    for rid, m in sorted(published.items(), key=lambda kv: ((kv[1].get("Category") or ""), kv[1]["Name"].lower())):
        if stats[rid]["public_evaluators"]:
            continue
        st = status.get(rid, {})
        lines.append("| %s | %s | %s | %s | %s | %s | %d | %s | %s |" % (
            rid, m["Name"], m["Developer"], m.get("Category"), st.get("status", "—"), (st.get("reason_en") or "").replace("|", "/"),
            stats[rid]["developer_rows"], ", ".join(sorted(stats[rid]["all_evaluators"] - stats[rid]["public_evaluators"])).replace("|", "/") or "—",
            (st.get("next_step") or "").replace("|", "/")))
    lines += ["", "Checked sources for every model (evidence in Facts.independent_evaluation_status → checked_sources): Epoch AI hub snapshot 2026-09-27 "
              "(own runs + external leaderboards), lmarena-ai/leaderboard-dataset, Aider leaderboards, Hugging Face Open ASR Leaderboard, MTEB results."]
    (OUT / "BEFORE_AFTER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: after[k] for k in after if not k.startswith("unique") and k != "by_category"}, indent=1))
    print("before public coverage %d/%d; after %d/%d" % (before["published_ge1_public_evaluators"], p, after["published_ge1_public_evaluators"], p))


if __name__ == "__main__":
    main()
