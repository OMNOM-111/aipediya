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


def rows(db, table):
    found = db.execute(f"SELECT * FROM {table}").fetchall()
    if found and "id" in found[0].keys():
        return {row["id"]: dict(row) for row in found}
    return {index: tuple(row) for index, row in enumerate(sorted(found, key=lambda item: repr(tuple(item))))}


def find_catalog_plan(release):
    expected = {release.get("release_id"), release.get("release_tag")}
    expected.discard(None)
    matches = []
    for path in sorted((ROOT / "app" / "data" / "release").glob("**/catalog_plan.json")):
        try:
            plan = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if plan.get("schema") == "aipedia-catalog-plan/1" and plan.get("release") in expected:
            matches.append((path, plan))
    if len(matches) > 1:
        raise RuntimeError("Multiple catalog plans match this release: " + repr([str(path) for path, _plan in matches]))
    return matches[0] if matches else (None, None)


def expected_tables(plan):
    tables = set()
    for change in plan["changes"]:
        kind = change["kind"]
        sheet = change.get("sheet")
        if kind == "create":
            tables.update({"catalog_modelversion", "catalog_modelfamily", "catalog_organization", "catalog_source"})
            if sheet == "Tools":
                tables.update({"catalog_tool", "catalog_toolplatform"})
            if sheet == "Models" and change.get("row", {}).get("Origin Countries"):
                tables.add("catalog_modelorigincountry")
            if change.get("offers"):
                tables.update({"catalog_offer", "catalog_service", "catalog_source", "catalog_organization"})
            if change.get("access"):
                tables.update({"catalog_access", "catalog_service", "catalog_source", "catalog_organization"})
        elif kind == "update":
            tables.add("catalog_modelversion" if sheet == "Models" else "catalog_tool")
            if "source" in change.get("after", {}):
                tables.add("catalog_source")
        elif kind == "number":
            tables.add("catalog_modelversion" if sheet == "Models" else "catalog_tool")
        elif kind == "platforms":
            tables.add("catalog_toolplatform")
        elif kind == "reassign":
            tables.add("catalog_offer" if sheet == "Offers" else "catalog_access")
        elif kind == "offer":
            tables.add("catalog_offer")
            if "source" in change.get("after", {}):
                tables.add("catalog_source")
        elif kind == "evaluation":
            tables.add("catalog_evaluation")
        elif kind == "access_service":
            tables.update({"catalog_access", "catalog_service"})
        elif kind == "service_provider":
            tables.add("catalog_service")
        elif kind == "benchmark_category":
            tables.add("catalog_benchmark")
        elif kind == "org_country":
            tables.add("catalog_organization")
        elif kind == "offer_new":
            tables.update({"catalog_offer", "catalog_service", "catalog_source", "catalog_organization"})
        elif kind == "access_new":
            tables.update({"catalog_access", "catalog_service", "catalog_source", "catalog_organization"})
        elif kind == "origin_new":
            tables.add("catalog_modelorigincountry")
        elif kind == "evaluation_new":
            tables.update({"catalog_evaluation", "catalog_benchmark", "catalog_source"})
        else:
            raise RuntimeError("Unknown catalog plan kind: " + kind)
    return tables


def planned_existing_ids(plan, sheet, kinds, prefix=None):
    values = set()
    for change in plan["changes"]:
        if change.get("sheet") != sheet or change.get("kind") not in kinds:
            continue
        if prefix:
            if not change["id"].startswith(prefix + "-"):
                continue
            try:
                values.add(int(change["id"].split("-", 1)[1]))
            except ValueError:
                continue
        else:
            values.add(change["id"])
    return values


def planned_final_counts(plan):
    model_numbers = plan["final_numbers"].get("Models", {})
    tool_numbers = plan["final_numbers"].get("Tools", {})
    return {
        "models": len(plan["final_published"].get("Models", [])),
        "tools": len(plan["final_published"].get("Tools", [])),
        "models_numbered_count": sum(1 for value in model_numbers.values() if value is not None),
        "tools_numbered_count": sum(1 for value in tool_numbers.values() if value is not None),
    }


def table_existing_changes(before, after):
    if not set(before).issubset(after):
        return {"__removed__"}
    return {key for key in before if before[key] != after.get(key)}


def validate_plan_diff(plan, old, new, changed_tables, before_counts, after_counts):
    problems = []
    allowed_tables = expected_tables(plan)
    unexpected_tables = [table for table in changed_tables if table not in allowed_tables]
    if unexpected_tables:
        problems.append("unexpected changed tables: " + repr(unexpected_tables))
    final_counts = planned_final_counts(plan)
    for key, expected in final_counts.items():
        if after_counts.get(key) != expected:
            problems.append("%s=%s differs from plan %s" % (key, after_counts.get(key), expected))
    critical = {
        "catalog_modelversion": planned_existing_ids(plan, "Models", {"update", "number"}),
        "catalog_tool": planned_existing_ids(plan, "Tools", {"update", "number"}),
        "catalog_offer": planned_existing_ids(plan, "Offers", {"offer", "reassign"}, "offer"),
        "catalog_access": planned_existing_ids(plan, "Access", {"access_service", "reassign"}, "access"),
    }
    existing_table_updates = {"catalog_service", "catalog_benchmark", "catalog_organization", "catalog_evaluation"}
    if not any(change["kind"] in {"access_service", "service_provider"} for change in plan["changes"]):
        existing_table_updates.discard("catalog_service")
    if not any(change["kind"] == "benchmark_category" for change in plan["changes"]):
        existing_table_updates.discard("catalog_benchmark")
    if not any(change["kind"] == "org_country" for change in plan["changes"]):
        existing_table_updates.discard("catalog_organization")
    if not any(change["kind"] == "evaluation" for change in plan["changes"]):
        existing_table_updates.discard("catalog_evaluation")
    for table in sorted(set(old) | set(new)):
        changed_existing = table_existing_changes(old.get(table, {}), new.get(table, {}))
        if not changed_existing:
            continue
        if table in critical:
            extra = sorted(changed_existing - critical[table])
            if extra:
                problems.append("%s existing rows changed outside plan: %s" % (table, extra[:5]))
        elif table not in existing_table_updates:
            problems.append("%s existing rows changed unexpectedly" % table)
    creates = [change for change in plan["changes"] if change["kind"] == "create"]
    expected_created = {
        "catalog_modelversion": len(creates),
        "catalog_tool": sum(1 for change in creates if change["sheet"] == "Tools"),
        "catalog_offer": sum(len(change.get("offers", [])) for change in creates) + plan["counts"].get("offer_new", 0),
        "catalog_access": sum(len(change.get("access", [])) for change in creates) + plan["counts"].get("access_new", 0),
    }
    for table, expected in expected_created.items():
        actual = len(new.get(table, {})) - len(old.get(table, {}))
        if actual != expected:
            problems.append("%s created %s rows, expected %s" % (table, actual, expected))
    if not after_counts["models_numbered"] or not after_counts["tools_numbered"]:
        problems.append("published catalog numbers are not continuous")
    if (before_counts["models"], before_counts["tools"]) == (after_counts["models"], after_counts["tools"]) and plan["counts"].get("create"):
        problems.append("plan creates records but published counts did not change")
    return problems


def main():
    release = json.loads((ROOT / "app/BUILD.json").read_text())
    sequence = release.get("release_sequence")
    plan_path, plan = find_catalog_plan(release)
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
        tables = sorted({row[0] for row in old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'catalog_%'")} |
                        {row[0] for row in new.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'catalog_%'")})
        changed_tables = []
        tool_columns = Counter()
        old_rows = {}
        new_rows = {}
        for table in tables:
            if table in SKIP:
                continue
            before = rows(old, table) if old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() else {}
            after = rows(new, table) if new.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() else {}
            old_rows[table] = before
            new_rows[table] = after
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
                    "models_numbered_count": sum(number is not None for number in models),
                    "tools_numbered_count": sum(number is not None for number in tools),
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
            "catalog_plan": plan_path.relative_to(ROOT / "app").as_posix() if plan_path else None,
            "catalog_plan_counts": plan.get("counts") if plan else None,
            "integrity": new.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_keys": len(new.execute("PRAGMA foreign_key_check").fetchall()),
        }
        if plan:
            expected_tables_list = sorted(expected_tables(plan))
            problems = validate_plan_diff(plan, old_rows, new_rows, changed_tables, before_counts, after_counts)
            scoped_changes = not problems
        elif sequence >= 14:
            expected_tables_list = []
            problems = [] if not changed_tables and before_counts == after_counts and before_evidence == after_evidence else [
                "code-only release changed catalog data"]
            scoped_changes = not problems
        else:
            expected_tables_list, problems, scoped_changes = [], ["release has no catalog plan and is not code-only"], False
        report["release_sequence"] = sequence
        report["scoped_changes"] = scoped_changes
        report["expected_changed_tables"] = expected_tables_list
        report["problems"] = problems
        report["ok"] = (scoped_changes and after_counts["models_numbered"] and after_counts["tools_numbered"] and
                        report["integrity"] == "ok" and report["foreign_keys"] == 0)
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
