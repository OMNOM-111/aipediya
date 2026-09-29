"""Run by tools/server.py on the AIpediya host; trial the approved release on a DB backup."""

import hashlib
import json
import os
import pwd
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter
from contextlib import closing
from pathlib import Path


ROOT = Path("/srv/aipedia")
DB = ROOT / "data/aipedia.sqlite3"
BACKUPS = ROOT / "backups"


def checked(command, *, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed: {result.stdout[-1500:]} {result.stderr[-1500:]}")
    return result.stdout.strip()


def validate_release_scope(sequence, plan):
    if sequence in (12, 13) and plan:
        return
    if sequence == 14 and not plan:
        return
    raise RuntimeError("Catalog plan does not match release scope")


def validate_code_only_catalog(copied, after):
    if copied["catalog_sha256"] != after["catalog_sha256"]:
        raise RuntimeError("Code-only trial changed catalog data")


def snapshot(path):
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(db.execute("PRAGMA foreign_key_check").fetchall())
        tools = {row["slug"]: dict(row) for row in db.execute("SELECT * FROM catalog_tool")}
        published = [row for row in tools.values() if row["published"]]
        numbers = sorted(row["public_number"] for row in published if row["public_number"] is not None)
        model_rows = {row["slug"]: dict(row) for row in db.execute("SELECT * FROM catalog_modelversion")}
        models = [row for row in model_rows.values() if row["published"] and row["entry_type"] == "model"]
        model_numbers = sorted(row["public_number"] for row in models if row["public_number"] is not None)
        offers = {row["id"]: dict(row) for row in db.execute("SELECT * FROM catalog_offer")}
        accesses = {row["id"]: dict(row) for row in db.execute("SELECT * FROM catalog_access")}
        evaluations = db.execute("SELECT COUNT(*), COALESCE(SUM(public), 0) FROM catalog_evaluation").fetchone()
        sources = db.execute("SELECT COUNT(*) FROM catalog_source").fetchone()[0]
        benchmarks = db.execute("SELECT COUNT(*) FROM catalog_benchmark").fetchone()[0]
        catalog_digest = hashlib.sha256()
        tables = db.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name LIKE 'catalog_%' ORDER BY name")
        for table, schema in tables:
            catalog_digest.update(repr((table, schema)).encode("utf-8"))
            catalog_digest.update(b"\n")
            quoted = '"' + table.replace('"', '""') + '"'
            for row in db.execute(f"SELECT * FROM {quoted} ORDER BY rowid"):
                catalog_digest.update(repr(tuple(row)).encode("utf-8"))
                catalog_digest.update(b"\n")
        return {
            "integrity": integrity, "foreign_keys": fk, "tools": tools, "model_rows": model_rows,
            "offers": offers, "accesses": accesses,
            "catalog_sha256": catalog_digest.hexdigest(),
            "evaluation_rows": evaluations[0], "evaluation_public": evaluations[1],
            "source_rows": sources, "benchmark_rows": benchmarks,
            "published_tools": len(published), "numbered_tools": len(numbers),
            "numbers_continuous": numbers == list(range(1, len(published) + 1)),
            "exact_dates": sum(bool(row["released"]) for row in published),
            "approximate_dates": sum(bool(row["approx_released"]) for row in published),
            "without_date": sum(not row["released"] and not row["approx_released"] for row in published),
            "published_models": len(models), "numbered_models": len(model_numbers),
            "model_numbers_continuous": model_numbers == list(range(1, len(models) + 1)),
        }


def main():
    archive, digest, commit, plan, publication = sys.argv[1:]
    plan = "" if plan == "-" else plan
    if not re.fullmatch(r"/tmp/aipedia-code-[0-9a-f]{12}-[0-9a-f]{12}\.zip", archive):
        raise RuntimeError("Archive must be inside the AIpediya temporary namespace")
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("Invalid release identity")
    if not Path(archive).is_file() or hashlib.sha256(Path(archive).read_bytes()).hexdigest() != digest:
        raise RuntimeError("Uploaded archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("MANIFEST.json"))
        if manifest["commit"] != commit or manifest.get("kind") not in {"code", "code-candidate"}:
            raise RuntimeError("Archive manifest does not match approved release")
        for name, expected in manifest["files"].items():
            if name.startswith("/") or ".." in Path(name).parts or name.lower().endswith((".sqlite3", ".env")):
                raise RuntimeError("Unsafe release entry: " + name)
            if hashlib.sha256(z.read(name)).hexdigest() != expected:
                raise RuntimeError("Release entry digest mismatch: " + name)
        sequence = manifest["release_sequence"]
        validate_release_scope(sequence, plan)
        if (plan and "app/" + plan not in manifest["files"]) or "app/" + publication not in manifest["files"]:
            raise RuntimeError("Approved catalog plan/publication manifest absent")
        plan_data = json.loads(z.read("app/" + plan)) if plan else None
    before = snapshot(DB)
    if before["integrity"] != "ok" or before["foreign_keys"]:
        raise RuntimeError("Production SQLite baseline failed integrity checks")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = BACKUPS / f"aipedia-preflight-{manifest['release_sequence']:03d}-{stamp}.sqlite3"
    if backup.exists():
        raise RuntimeError("Preflight backup path exists")
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    os.chmod(backup, 0o600)
    account = pwd.getpwnam("aipedia")
    os.chown(backup, account.pw_uid, account.pw_gid)
    copied = snapshot(backup)
    if any(before[k] != copied[k] for k in ("tools", "model_rows", "offers", "accesses",
                                              "published_models", "published_tools", "evaluation_rows", "evaluation_public",
                                              "source_rows", "benchmark_rows")):
        raise RuntimeError("Online backup does not match Production baseline")
    with tempfile.TemporaryDirectory(prefix="aipedia-preflight-", dir="/tmp") as temp:
        stage = Path(temp)
        with zipfile.ZipFile(archive) as z:
            for name in manifest["files"]:
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))
        for path in [stage, *stage.rglob("*")]:
            os.chown(path, account.pw_uid, account.pw_gid)
            os.chmod(path, 0o750 if path.is_dir() else 0o640)
        app = stage / "app"
        prefix = ["runuser", "-u", "aipedia", "--", "env", "AIPEDIA_ENV=local",
                  f"AIPEDIA_DB={backup}", str(ROOT / "venv/bin/python"), str(app / "manage.py")]
        checked(prefix + ["check"], cwd=app)
        checked(prefix + ["migrate", "--noinput"], cwd=app)
        dry_plan = checked(prefix + ["catalog_master", "apply-plan", "--plan-out", plan], cwd=app) if plan else ""
        applied = checked(prefix + ["catalog_master", "apply-plan", "--plan-out", plan, "--apply"], cwd=app) if plan else ""
        dry_state = checked(prefix + ["sync_publication_state", "apply", publication], cwd=app)
    after = snapshot(backup)
    if not set(before["tools"]).issubset(after["tools"]) or not set(before["model_rows"]).issubset(after["model_rows"]):
        raise RuntimeError("Trial removed an existing catalog record")
    if sequence == 13 and {kind: plan_data["counts"].get(kind, 0) for kind in
                           ("access_service", "service_provider", "benchmark_category")} != {
                               "access_service": 11, "service_provider": 1, "benchmark_category": 1}:
        raise RuntimeError("Release #013 plan counts differ from the approved scope")
    unchanged = ("tools", "model_rows", "offers") if sequence == 13 else (
        "tools", "model_rows", "offers", "accesses")
    if any(before[k] != after[k] for k in unchanged):
        raise RuntimeError("Trial changed model/tool identity, publication or price outside the approved plan")
    if sequence == 13:
        expected_access_ids = {int(change["id"].split("-", 1)[1]) for change in
                               plan_data["changes"]
                               if change["kind"] == "access_service"}
        changed_access_ids = {key for key in before["accesses"] if before["accesses"][key] != after["accesses"].get(key)}
        if before["accesses"].keys() != after["accesses"].keys() or changed_access_ids != expected_access_ids:
            raise RuntimeError("Trial Access changes differ from the approved plan")
        for key in changed_access_ids:
            if {k: v for k, v in before["accesses"][key].items() if k != "service_id"} != {
                    k: v for k, v in after["accesses"][key].items() if k != "service_id"}:
                raise RuntimeError("Trial changed an Access field other than service_id")
    if sequence == 14:
        validate_code_only_catalog(copied, after)
    if (before["published_models"], before["published_tools"]) != (325, 147):
        raise RuntimeError("Production baseline differs from the approved release predecessor")
    if (after["published_models"], after["numbered_models"],
            after["published_tools"], after["numbered_tools"]) != (325, 325, 147, 147):
        raise RuntimeError("Trial catalog counts differ from approved Local: " +
                           repr({k: after[k] for k in ("published_tools", "numbered_tools",
                               "published_models", "numbered_models")}))
    expected_evaluations = (906, 851, 5010, 2741) if sequence == 12 else (5010, 2741, 5010, 2741)
    expected_dependencies = (436, 35, 999, 982) if sequence == 12 else (999, 982, 999, 982)
    if (before["evaluation_rows"], before["evaluation_public"],
            after["evaluation_rows"], after["evaluation_public"]) != expected_evaluations:
        raise RuntimeError("Trial evaluation totals differ from the approved Production delta")
    if (before["source_rows"], before["benchmark_rows"],
            after["source_rows"], after["benchmark_rows"]) != expected_dependencies:
        raise RuntimeError("Trial evidence dependencies differ from the approved Production delta")
    if after["integrity"] != "ok" or after["foreign_keys"] or not after["numbers_continuous"] or not after["model_numbers_continuous"]:
        raise RuntimeError("Trial SQLite integrity or numbering failed")
    if "models changed=0" not in dry_state or "tools changed=0" not in dry_state:
        raise RuntimeError("Publication-state dry-run differs from the approved catalog plan")
    report = {
        "status": "PASS", "commit": commit, "sha256": digest, "backup": str(backup),
        "catalog_plan": plan or None, "publication_state": publication,
        "production_database_untouched": True,
        "before": {k: v for k, v in before.items() if k not in ("tools", "model_rows", "offers", "accesses")},
        "trial": {k: v for k, v in after.items() if k not in ("tools", "model_rows", "offers", "accesses")},
        "created_models": len(after["model_rows"]) - len(before["model_rows"]),
        "created_tools": len(after["tools"]) - len(before["tools"]),
        "plan_dry_run": dry_plan[-600:], "plan_apply": applied[-600:],
        "publication_dry_run": dry_state[-600:],
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
