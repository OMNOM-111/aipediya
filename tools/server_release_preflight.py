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
from pathlib import Path


ROOT = Path("/srv/aipedia")
DB = ROOT / "data/aipedia.sqlite3"
BACKUPS = ROOT / "backups"
ALLOWED_TOOL_COLUMNS = {"released", "approx_released", "approx_precision", "public_number"}


def checked(command, *, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed: {result.stdout[-1500:]} {result.stderr[-1500:]}")
    return result.stdout.strip()


def snapshot(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(db.execute("PRAGMA foreign_key_check").fetchall())
        tools = {row["slug"]: dict(row) for row in db.execute("SELECT * FROM catalog_tool")}
        published = [row for row in tools.values() if row["published"]]
        numbers = sorted(row["public_number"] for row in published if row["public_number"] is not None)
        model_rows = {row["slug"]: dict(row) for row in db.execute("SELECT * FROM catalog_modelversion")}
        models = db.execute("SELECT COUNT(*) FROM catalog_modelversion WHERE published=1 AND entry_type='model'").fetchone()[0]
        return {
            "integrity": integrity, "foreign_keys": fk, "tools": tools, "model_rows": model_rows,
            "published_tools": len(published), "numbered_tools": len(numbers),
            "numbers_continuous": numbers == list(range(1, len(published) + 1)),
            "exact_dates": sum(bool(row["released"]) for row in published),
            "approximate_dates": sum(bool(row["approx_released"]) for row in published),
            "without_date": sum(not row["released"] and not row["approx_released"] for row in published),
            "published_models": models,
        }


def main():
    archive, digest, commit, plan, publication = sys.argv[1:]
    if not re.fullmatch(r"/tmp/aipedia-code-[0-9a-f]{12}-[0-9a-f]{12}\.zip", archive):
        raise RuntimeError("Archive must be inside the AIpediya temporary namespace")
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("Invalid release identity")
    if not Path(archive).is_file() or hashlib.sha256(Path(archive).read_bytes()).hexdigest() != digest:
        raise RuntimeError("Uploaded archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("MANIFEST.json"))
        if manifest["commit"] != commit or manifest.get("kind") != "code":
            raise RuntimeError("Archive manifest does not match approved release")
        for name, expected in manifest["files"].items():
            if name.startswith("/") or ".." in Path(name).parts or name.lower().endswith((".sqlite3", ".env")):
                raise RuntimeError("Unsafe release entry: " + name)
            if hashlib.sha256(z.read(name)).hexdigest() != expected:
                raise RuntimeError("Release entry digest mismatch: " + name)
        if "app/" + plan not in manifest["files"] or "app/" + publication not in manifest["files"]:
            raise RuntimeError("Approved catalog plan/publication manifest absent")
    before = snapshot(DB)
    if before["integrity"] != "ok" or before["foreign_keys"]:
        raise RuntimeError("Production SQLite baseline failed integrity checks")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = BACKUPS / f"aipedia-preflight-tools-csp-{stamp}.sqlite3"
    if backup.exists():
        raise RuntimeError("Preflight backup path exists")
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    os.chmod(backup, 0o600)
    account = pwd.getpwnam("aipedia")
    os.chown(backup, account.pw_uid, account.pw_gid)
    copied = snapshot(backup)
    if any(before[k] != copied[k] for k in ("tools", "model_rows", "published_models", "published_tools")):
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
        dry_plan = checked(prefix + ["catalog_master", "apply-plan", "--plan-out", plan], cwd=app)
        applied = checked(prefix + ["catalog_master", "apply-plan", "--plan-out", plan, "--apply"], cwd=app)
        dry_state = checked(prefix + ["sync_publication_state", "apply", publication], cwd=app)
    after = snapshot(backup)
    changed = Counter()
    for slug, row in before["tools"].items():
        if slug not in after["tools"]:
            raise RuntimeError("A Tool disappeared from trial database")
        for column, old in row.items():
            if after["tools"][slug][column] != old:
                changed[column] += 1
    if set(changed) - ALLOWED_TOOL_COLUMNS or set(after["tools"]) != set(before["tools"]):
        raise RuntimeError("Trial changed Tool fields outside the approved scope")
    expected_changes = {"public_number": 140, "released": 4, "approx_released": 23, "approx_precision": 23}
    if dict(changed) != expected_changes:
        raise RuntimeError(f"Trial Tool diff differs from approved Local: {dict(changed)}")
    if (after["published_tools"], after["numbered_tools"], after["exact_dates"],
            after["approximate_dates"], after["without_date"], after["published_models"]) != (143, 143, 60, 83, 0, 321):
        raise RuntimeError("Trial catalog counts differ from approved Local: " +
                           repr({k: after[k] for k in ("published_tools", "numbered_tools",
                               "exact_dates", "approximate_dates", "without_date", "published_models")}))
    if after["integrity"] != "ok" or after["foreign_keys"] or not after["numbers_continuous"]:
        raise RuntimeError("Trial SQLite integrity or numbering failed")
    if before["published_models"] != after["published_models"]:
        raise RuntimeError("Model publication count changed")
    if before["model_rows"] != after["model_rows"]:
        raise RuntimeError("Trial changed Model rows")
    if not dry_state:
        raise RuntimeError("Publication-state dry-run returned no result")
    report = {
        "status": "PASS", "commit": commit, "sha256": digest, "backup": str(backup),
        "catalog_plan": plan, "publication_state": publication,
        "production_database_untouched": True,
        "before": {k: v for k, v in before.items() if k not in ("tools", "model_rows")},
        "trial": {k: v for k, v in after.items() if k not in ("tools", "model_rows")},
        "tool_column_changes": dict(changed), "plan_dry_run": dry_plan[-600:],
        "plan_apply": applied[-600:], "publication_dry_run": dry_state[-600:],
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
