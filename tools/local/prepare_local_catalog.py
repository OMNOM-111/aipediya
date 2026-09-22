"""Copy a secret-free published catalog snapshot into the Local SQLite once."""
import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE = ROOT / "backups" / "chronology-production-after.sqlite3"
DEFAULT_DESTINATION = ROOT / "data" / "local" / "aipedia.sqlite3"
SANITIZE = (
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_session",
    "django_admin_log",
    "catalog_errorreport",
)
EXPECTED = {
    "catalog_modelversion": 255,
    "catalog_offer": 503,
    "catalog_evaluation": 854,
    "catalog_access": 280,
}


def backup_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Integrity check failed for " + str(destination))


def sanitize(path):
    with sqlite3.connect(path) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in SANITIZE:
            if table in names:
                db.execute(f"DELETE FROM [{table}]")
        db.commit()
        db.execute("VACUUM")


def counts(path):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        data = {table: db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0] for table in EXPECTED}
        data.update({
            "published": db.execute("SELECT COUNT(*) FROM catalog_modelversion WHERE published=1").fetchone()[0],
            "numbered": db.execute("SELECT COUNT(*) FROM catalog_modelversion WHERE public_number IS NOT NULL").fetchone()[0],
            "users": db.execute("SELECT COUNT(*) FROM auth_user").fetchone()[0],
            "sessions": db.execute("SELECT COUNT(*) FROM django_session").fetchone()[0],
            "first": db.execute(
                "SELECT public_number, slug, name FROM catalog_modelversion WHERE public_number=1"
            ).fetchone(),
            "integrity": db.execute("PRAGMA integrity_check").fetchone()[0],
        })
        if "catalog_tool" in names:
            data.update({
                "split_catalogs": True,
                "published_models": db.execute(
                    "SELECT COUNT(*) FROM catalog_modelversion WHERE published=1 AND entry_type='model'"
                ).fetchone()[0],
                "active_models": db.execute(
                    "SELECT COUNT(*) FROM catalog_modelversion "
                    "WHERE published=1 AND entry_type='model' AND catalog_status='active'"
                ).fetchone()[0],
                "numbered_models": db.execute(
                    "SELECT COUNT(*) FROM catalog_modelversion "
                    "WHERE entry_type='model' AND public_number IS NOT NULL"
                ).fetchone()[0],
                "published_tools": db.execute(
                    "SELECT COUNT(*) FROM catalog_tool WHERE published=1"
                ).fetchone()[0],
                "active_tools": db.execute(
                    "SELECT COUNT(*) FROM catalog_tool WHERE published=1 AND catalog_status='active'"
                ).fetchone()[0],
                "numbered_tools": db.execute(
                    "SELECT COUNT(*) FROM catalog_tool WHERE public_number IS NOT NULL"
                ).fetchone()[0],
                "first_model": db.execute(
                    "SELECT public_number, slug, name FROM catalog_modelversion "
                    "WHERE entry_type='model' AND public_number=1"
                ).fetchone(),
                "first_tool": db.execute(
                    "SELECT public_number, slug, name FROM catalog_tool WHERE public_number=1"
                ).fetchone(),
            })
        else:
            data["split_catalogs"] = False
    return data


def verify(path, exact_snapshot=False):
    data = counts(path)
    if data["integrity"] != "ok":
        raise SystemExit("Local catalog failed integrity_check")
    if exact_snapshot:
        for table, expected in EXPECTED.items():
            if data[table] != expected:
                raise SystemExit(f"{table} count {data[table]} != {expected}")
    if exact_snapshot and data["split_catalogs"]:
        expected_split = {
            "published": 255,
            "published_models": 234,
            "active_models": 233,
            "numbered_models": 198,
            "published_tools": 21,
            "active_tools": 21,
            "numbered_tools": 14,
        }
        if any(data[key] != value for key, value in expected_split.items()):
            raise SystemExit("Split catalog counts do not match the Local snapshot")
        if not data["first_model"] or data["first_model"][1] != "eleven-multilingual-v2-833c0947":
            raise SystemExit("Model chronology #1 does not match the Local catalog")
        if not data["first_tool"] or data["first_tool"][1] != "github-copilot-179ab1d0":
            raise SystemExit("Tool chronology #1 does not match the Local catalog")
    elif exact_snapshot and (data["published"] != 255 or data["numbered"] != 212):
        raise SystemExit("Published chronology counts do not match the public catalog")
    if data["users"] or data["sessions"]:
        raise SystemExit("Refusing a local catalog that still contains users or sessions")
    if exact_snapshot and not data["split_catalogs"] and (not data["first"] or data["first"][1] != "github-copilot-179ab1d0"):
        raise SystemExit("Chronology #1 does not match the published catalog")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    destination = args.destination.resolve()
    source = args.source.resolve()
    if destination.exists() and not args.replace:
        print(json.dumps({"status": "kept", "database": str(destination), **verify(destination)}, ensure_ascii=False))
        raise SystemExit(0)
    legacy = ROOT / "data" / "aipedia.sqlite3"
    archived_legacy = ROOT / "backups" / "local-pre-environments.sqlite3"
    if legacy.is_file() and not archived_legacy.is_file():
        backup_file(legacy, archived_legacy)
    if not source.is_file():
        raise SystemExit("Published catalog snapshot is missing: " + str(source))
    if destination.exists() and args.replace:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        previous = ROOT / "backups" / f"local-before-replace-{stamp}.sqlite3"
        backup_file(destination, previous)
        os.remove(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup_file(source, destination)
    sanitize(destination)
    report = {
        "status": "prepared",
        "source": str(source),
        "database": str(destination),
        "copied_at": datetime.now(timezone.utc).isoformat(),
        **verify(destination, exact_snapshot=True),
    }
    (destination.parent / "catalog-source.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
