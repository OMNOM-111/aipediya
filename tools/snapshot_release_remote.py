"""Create a private online backup and report AIpedia Production state.

Run on the existing AIpedia host with sudo. The script never reads secrets and
never writes to the live database; it creates a new SQLite online backup and a
temporary transfer copy with restrictive permissions.
"""

import argparse
import hashlib
import json
import os
import pwd
import re
import shutil
import sqlite3
from pathlib import Path


ROOT = Path("/srv/aipedia")
DB = ROOT / "data/aipedia.sqlite3"


def table_count(connection, table, where=""):
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not exists:
        return None
    return connection.execute(f"SELECT COUNT(*) FROM {table} {where}").fetchone()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", args.label):
        raise SystemExit("label must be UTC YYYYMMDDTHHMMSSZ")

    name = f"aipedia-before-global-catalog-{args.label}.sqlite3"
    destination = ROOT / "backups" / name
    transfer = Path("/tmp") / name
    if destination.exists() or transfer.exists():
        raise SystemExit("Refusing to overwrite an existing release backup")

    source = sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)
    try:
        with sqlite3.connect(destination) as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("backup integrity_check failed")
        os.chmod(destination, 0o600)
        app_account = pwd.getpwnam("aipedia")
        os.chown(destination, app_account.pw_uid, app_account.pw_gid)

        shutil.copyfile(destination, transfer)
        transfer_account = pwd.getpwnam("stratforge")
        os.chmod(transfer, 0o600)
        os.chown(transfer, transfer_account.pw_uid, transfer_account.pw_gid)

        counts = {
            "models_published": table_count(
                source, "catalog_modelversion", "WHERE published=1"
            ),
            "tools_published": table_count(
                source, "catalog_tool", "WHERE published=1"
            ),
            "offers": table_count(source, "catalog_offer"),
            "accesses": table_count(source, "catalog_access"),
            "evaluations": table_count(source, "catalog_evaluation"),
            "sources": table_count(source, "catalog_source"),
            "research_records": table_count(source, "catalog_researchrecord"),
            "revisions": table_count(source, "catalog_revision"),
            "publication_revisions": table_count(
                source, "catalog_publicationrevision"
            ),
        }
        migrations = source.execute(
            "SELECT name FROM django_migrations WHERE app='catalog' ORDER BY id"
        ).fetchall()
        build_path = ROOT / "app" / "BUILD.json"
        build = json.loads(build_path.read_text()) if build_path.exists() else {}
        report = {
            "backup": str(destination),
            "transfer": str(transfer),
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "integrity": source.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_key_violations": len(
                source.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "counts": counts,
            "migrations": [row[0] for row in migrations],
            "build": build,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        source.close()


if __name__ == "__main__":
    main()
