"""Read-only factual database comparison for a deployed AIpediya release."""

import json
import re
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path


ROOT = Path("/srv/aipedia")
SKIP = {"catalog_publicationrevision", "catalog_toolpublicationrevision",
        "catalog_revision", "catalog_researchrevision", "catalog_discoveryevent",
        "catalog_auditreport", "catalog_errorreport"}
EXPECTED_TABLES_012 = ["catalog_benchmark", "catalog_evaluation", "catalog_source"]
EXPECTED_TABLES_013 = ["catalog_access", "catalog_benchmark", "catalog_service"]


def rows(db, table):
    found = db.execute(f"SELECT * FROM {table}").fetchall()
    if found and "id" in found[0].keys():
        return {row["id"]: dict(row) for row in found}
    return {index: tuple(row) for index, row in enumerate(sorted(found, key=lambda item: repr(tuple(item))))}


def main():
    release = json.loads((ROOT / "app/BUILD.json").read_text())
    sequence = release.get("release_sequence")
    name = sys.argv[1]
    if not re.fullmatch(r"aipedia-before-code-[0-9]{8}T[0-9]{6}Z\.sqlite3", name):
        raise SystemExit("Only an AIpediya pre-release backup is accepted")
    old_path = ROOT / "backups" / name
    new_path = ROOT / "data/aipedia.sqlite3"
    if not old_path.is_file():
        raise SystemExit("Pre-release backup not found")
    with closing(sqlite3.connect(f"file:{old_path}?mode=ro", uri=True)) as old, closing(sqlite3.connect(
            f"file:{new_path}?mode=ro", uri=True)) as new:
        old.row_factory = new.row_factory = sqlite3.Row
        tables = [row[0] for row in old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'catalog_%' ORDER BY name")]
        changed_tables = []
        tool_columns = Counter()
        for table in tables:
            if table in SKIP:
                continue
            before, after = rows(old, table), rows(new, table)
            if before == after:
                continue
            changed_tables.append(table)
            if table == "catalog_tool" and before.keys() == after.keys():
                for key, old_row in before.items():
                    for column, old_value in old_row.items():
                        if after[key][column] != old_value:
                            tool_columns[column] += 1
        def published_counts(db):
            models = [row[0] for row in db.execute(
                "SELECT public_number FROM catalog_modelversion WHERE published=1 AND entry_type='model'")]
            tools = [row[0] for row in db.execute(
                "SELECT public_number FROM catalog_tool WHERE published=1")]
            return {"models": len(models), "tools": len(tools),
                    "models_numbered": None not in models and sorted(models) == list(range(1, len(models) + 1)),
                    "tools_numbered": None not in tools and sorted(tools) == list(range(1, len(tools) + 1))}

        before_counts, after_counts = published_counts(old), published_counts(new)
        def evidence_counts(db):
            return {
                "sources": db.execute("SELECT COUNT(*) FROM catalog_source").fetchone()[0],
                "benchmarks": db.execute("SELECT COUNT(*) FROM catalog_benchmark").fetchone()[0],
                "evaluations": db.execute("SELECT COUNT(*) FROM catalog_evaluation").fetchone()[0],
                "public_evaluations": db.execute("SELECT COALESCE(SUM(public), 0) FROM catalog_evaluation").fetchone()[0],
            }
        before_evidence, after_evidence = evidence_counts(old), evidence_counts(new)
        report = {
            "before_database": str(old_path), "current_database": str(new_path),
            "changed_factual_tables": changed_tables,
            "tool_column_changes": dict(tool_columns),
            "before": before_counts, "after": after_counts,
            "before_evidence": before_evidence, "after_evidence": after_evidence,
            "integrity": new.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_keys": len(new.execute("PRAGMA foreign_key_check").fetchall()),
        }
        if sequence == 12:
            expected_tables = EXPECTED_TABLES_012
            expected_before = {"sources": 436, "benchmarks": 35,
                               "evaluations": 906, "public_evaluations": 851}
            expected_after = {"sources": 999, "benchmarks": 982,
                              "evaluations": 5010, "public_evaluations": 2741}
            scoped_changes = True
        elif sequence == 13:
            expected_tables = EXPECTED_TABLES_013
            expected_before = expected_after = {"sources": 999, "benchmarks": 982,
                                                 "evaluations": 5010, "public_evaluations": 2741}
            plan = json.loads((ROOT / "app/data/release/reconciliation-20260928/catalog_plan.json").read_text())
            before_access, after_access = rows(old, "catalog_access"), rows(new, "catalog_access")
            expected_ids = {int(item["id"].split("-", 1)[1]) for item in plan["changes"]
                            if item["kind"] == "access_service"}
            changed_ids = {key for key in before_access if before_access[key] != after_access.get(key)}
            scoped_changes = (before_access.keys() == after_access.keys() and changed_ids == expected_ids and
                              all({k: v for k, v in before_access[key].items() if k != "service_id"} ==
                                  {k: v for k, v in after_access[key].items() if k != "service_id"}
                                  for key in changed_ids))
        elif sequence == 16:
            expected_tables = ["catalog_access", "catalog_modelfamily", "catalog_modelorigincountry", "catalog_modelversion",
                               "catalog_offer", "catalog_organization", "catalog_service", "catalog_source",
                               "catalog_tool", "catalog_toolplatform"]
            expected_before = {"sources": 999, "benchmarks": 982,
                               "evaluations": 5010, "public_evaluations": 2741}
            expected_after = {"sources": 1003, "benchmarks": 982,
                              "evaluations": 5010, "public_evaluations": 2741}
            before_tools, after_tools = rows(old, "catalog_tool"), rows(new, "catalog_tool")
            before_models, after_models = rows(old, "catalog_modelversion"), rows(new, "catalog_modelversion")
            before_offers, after_offers = rows(old, "catalog_offer"), rows(new, "catalog_offer")
            before_access, after_access = rows(old, "catalog_access"), rows(new, "catalog_access")
            scoped_changes = (
                set(before_tools).issubset(after_tools) and set(before_models).issubset(after_models)
                and set(before_offers).issubset(after_offers) and set(before_access).issubset(after_access)
                and all(before_tools[key] == after_tools[key] for key in before_tools)
                and all(before_models[key] == after_models[key] for key in before_models)
                and all(before_offers[key] == after_offers[key] for key in before_offers)
                and all(before_access[key] == after_access[key] for key in before_access)
            )
        elif sequence >= 14:
            expected_tables = []
            expected_before = expected_after = {"sources": 999, "benchmarks": 982,
                                                 "evaluations": 5010, "public_evaluations": 2741}
            scoped_changes = True
        else:
            expected_tables, expected_before, expected_after, scoped_changes = [], {}, {}, False
        report["release_sequence"] = sequence
        report["scoped_changes"] = scoped_changes
        report["ok"] = (changed_tables == expected_tables and scoped_changes and
                        (before_counts["models"], before_counts["tools"]) == ((325, 147) if sequence == 16 else (325, 147)) and
                        (after_counts["models"], after_counts["tools"]) == ((331, 149) if sequence == 16 else (325, 147)) and
                        before_evidence == expected_before and after_evidence == expected_after and
                        after_counts["models_numbered"] and after_counts["tools_numbered"] and
                        report["integrity"] == "ok" and report["foreign_keys"] == 0)
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
