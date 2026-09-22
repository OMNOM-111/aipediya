"""Compare two AIpedia SQLite catalog databases without modifying either."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def catalog_tables(connection):
    return [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name LIKE 'catalog_%' ORDER BY name"
        )
    ]


def columns(connection, table):
    return [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]


def row_digest(connection, table, names):
    order = "id" if "id" in names else names[0]
    digest = hashlib.sha256()
    for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY "{order}"'):
        digest.update(json.dumps(row, ensure_ascii=False, default=str).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args()
    left_path = Path(args.left).resolve()
    right_path = Path(args.right).resolve()
    left = sqlite3.connect(left_path.as_uri() + "?mode=ro", uri=True)
    right = sqlite3.connect(right_path.as_uri() + "?mode=ro", uri=True)
    try:
        tables = sorted(set(catalog_tables(left)) | set(catalog_tables(right)))
        report = {}
        for table in tables:
            left_names = columns(left, table)
            right_names = columns(right, table)
            left_count = left.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] if left_names else None
            right_count = right.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] if right_names else None
            report[table] = {
                "left": left_count,
                "right": right_count,
                "delta": None if left_count is None or right_count is None else left_count - right_count,
                "same_columns": left_names == right_names,
                "same_rows": (
                    left_names == right_names
                    and left_count == right_count
                    and row_digest(left, table, left_names) == row_digest(right, table, right_names)
                ),
            }
        output = {
            "left": str(left_path),
            "right": str(right_path),
            "left_integrity": left.execute("PRAGMA integrity_check").fetchone()[0],
            "right_integrity": right.execute("PRAGMA integrity_check").fetchone()[0],
            "tables": report,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    finally:
        left.close()
        right.close()


if __name__ == "__main__":
    main()
