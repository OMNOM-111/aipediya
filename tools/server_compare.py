"""Read-only factual database comparison for a deployed AIpediya release."""

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path


ROOT = Path("/srv/aipedia")
SKIP = {"catalog_publicationrevision", "catalog_toolpublicationrevision",
        "catalog_revision", "catalog_researchrevision", "catalog_discoveryevent",
        "catalog_auditreport", "catalog_errorreport"}
ALLOWED_TOOL_COLUMNS = {"released", "approx_released", "approx_precision", "public_number"}


def rows(db, table):
    found = db.execute(f"SELECT * FROM {table}").fetchall()
    if found and "id" in found[0].keys():
        return {row["id"]: dict(row) for row in found}
    return {index: tuple(row) for index, row in enumerate(sorted(found, key=lambda item: repr(tuple(item))))}


def main():
    name = sys.argv[1]
    if not re.fullmatch(r"aipedia-before-code-[0-9]{8}T[0-9]{6}Z\.sqlite3", name):
        raise SystemExit("Only an AIpediya pre-release backup is accepted")
    old_path = ROOT / "backups" / name
    new_path = ROOT / "data/aipedia.sqlite3"
    if not old_path.is_file():
        raise SystemExit("Pre-release backup not found")
    with sqlite3.connect(f"file:{old_path}?mode=ro", uri=True) as old, sqlite3.connect(
            f"file:{new_path}?mode=ro", uri=True) as new:
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
        report = {
            "before_database": str(old_path), "current_database": str(new_path),
            "changed_factual_tables": changed_tables,
            "tool_column_changes": dict(tool_columns),
            "integrity": new.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_keys": len(new.execute("PRAGMA foreign_key_check").fetchall()),
        }
        report["ok"] = (changed_tables == ["catalog_tool"] and
                        set(tool_columns) <= ALLOWED_TOOL_COLUMNS and
                        report["integrity"] == "ok" and report["foreign_keys"] == 0)
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
