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
SKIP_FACTUAL_TABLES = {"catalog_publicationrevision", "catalog_toolpublicationrevision",
                       "catalog_revision", "catalog_researchrevision", "catalog_discoveryevent",
                       "catalog_auditreport", "catalog_errorreport"}


def checked(command, *, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed: {result.stdout[-1500:]} {result.stderr[-1500:]}")
    return result.stdout.strip()


def validate_release_scope(sequence, plan):
    if plan and (sequence in (12, 13) or sequence >= 16):
        return
    if not plan and sequence >= 14 and sequence != 16:
        return
    raise RuntimeError("Catalog plan does not match release scope")


def validate_code_only_catalog(copied, after):
    if copied["catalog_sha256"] != after["catalog_sha256"]:
        raise RuntimeError("Code-only trial changed catalog data")


def rows(db, table):
    found = db.execute(f"SELECT * FROM {table}").fetchall()
    if found and "id" in found[0].keys():
        return {row["id"]: dict(row) for row in found}
    return {index: tuple(row) for index, row in enumerate(sorted(found, key=lambda item: repr(tuple(item))))}


def changed_factual_tables(before, after):
    names = sorted(set(before["factual_tables"]) | set(after["factual_tables"]))
    return [name for name in names if before["factual_tables"].get(name, {}) != after["factual_tables"].get(name, {})]


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


def changed_existing(before, after, label):
    if not set(before[label]).issubset(after[label]):
        removed = sorted(set(before[label]) - set(after[label]))[:5]
        raise RuntimeError("Trial removed existing %s rows: %s" % (label, removed))
    return {key for key in before[label] if before[label][key] != after[label].get(key)}


def planned_final_counts(plan):
    model_numbers = plan["final_numbers"].get("Models", {})
    tool_numbers = plan["final_numbers"].get("Tools", {})
    return {
        "published_models": len(plan["final_published"].get("Models", [])),
        "published_tools": len(plan["final_published"].get("Tools", [])),
        "numbered_models": sum(1 for value in model_numbers.values() if value is not None),
        "numbered_tools": sum(1 for value in tool_numbers.values() if value is not None),
    }


def validate_catalog_plan_trial(plan, before, after, *, already_applied=False):
    expected = expected_tables(plan)
    changed = changed_factual_tables(before, after)
    unexpected = [table for table in changed if table not in expected]
    if unexpected:
        raise RuntimeError("Trial changed catalog tables outside the plan: " + repr(unexpected))
    final_counts = planned_final_counts(plan)
    for key, expected_value in final_counts.items():
        if after[key] != expected_value:
            raise RuntimeError("Trial %s=%s differs from plan %s" % (key, after[key], expected_value))
    if after["integrity"] != "ok" or after["foreign_keys"]:
        raise RuntimeError("Trial SQLite integrity failed")
    if not after["numbers_continuous"] or not after["model_numbers_continuous"]:
        raise RuntimeError("Trial catalog numbering is not continuous")
    allowed_models = planned_existing_ids(plan, "Models", {"update", "number"})
    allowed_tools = planned_existing_ids(plan, "Tools", {"update", "number"})
    allowed_offers = planned_existing_ids(plan, "Offers", {"offer", "reassign"}, "offer")
    allowed_accesses = planned_existing_ids(plan, "Access", {"access_service", "reassign"}, "access")
    for label, allowed in (("model_rows", allowed_models), ("tools", allowed_tools),
                           ("offers", allowed_offers), ("accesses", allowed_accesses)):
        extra = sorted(changed_existing(before, after, label) - allowed)
        if extra:
            raise RuntimeError("Trial changed existing %s rows outside the plan: %s" % (label, extra[:5]))
    if already_applied:
        return
    creates = [change for change in plan["changes"] if change["kind"] == "create"]
    legacy_tool_rows = {
        change["id"] for change in creates
        if change["sheet"] == "Tools" and (change.get("offers") or change.get("access"))
    }
    for change in plan["changes"]:
        if change.get("kind") not in {"offer_new", "access_new", "evaluation_new"}:
            continue
        owner_kind, _sep, owner_slug = change.get("owner", "").partition(":")
        if owner_kind != "tool":
            continue
        current_tool = before["tools"].get(owner_slug)
        if current_tool is None or not current_tool.get("legacy_version_id"):
            legacy_tool_rows.add(owner_slug)
    expected_created = {
        # Model creates always add ModelVersion. A Tool adds the legacy
        # ModelVersion holder only when prices/access/evaluations need it.
        "model_rows": sum(1 for change in creates if change["sheet"] == "Models")
                      + len(legacy_tool_rows),
        "tools": sum(1 for change in creates if change["sheet"] == "Tools"),
        "offers": sum(len(change.get("offers", [])) for change in creates) + plan["counts"].get("offer_new", 0),
        "accesses": sum(len(change.get("access", [])) for change in creates) + plan["counts"].get("access_new", 0),
    }
    for label, expected_count in expected_created.items():
        actual = len(after[label]) - len(before[label])
        if actual != expected_count:
            raise RuntimeError("Trial created %s %s rows, expected %s from plan" % (actual, label, expected_count))


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
        tables = list(db.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name LIKE 'catalog_%' ORDER BY name"))
        factual_tables = {}
        for table, schema in tables:
            catalog_digest.update(repr((table, schema)).encode("utf-8"))
            catalog_digest.update(b"\n")
            quoted = '"' + table.replace('"', '""') + '"'
            for row in db.execute(f"SELECT * FROM {quoted} ORDER BY rowid"):
                catalog_digest.update(repr(tuple(row)).encode("utf-8"))
                catalog_digest.update(b"\n")
            if table not in SKIP_FACTUAL_TABLES:
                factual_tables[table] = rows(db, quoted)
        return {
            "integrity": integrity, "foreign_keys": fk, "tools": tools, "model_rows": model_rows,
            "offers": offers, "accesses": accesses, "factual_tables": factual_tables,
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
    if plan_data:
        validate_catalog_plan_trial(plan_data, before, after, already_applied="already applied" in dry_plan.lower())
    else:
        validate_code_only_catalog(copied, after)
    if after["integrity"] != "ok" or after["foreign_keys"] or not after["numbers_continuous"] or not after["model_numbers_continuous"]:
        raise RuntimeError("Trial SQLite integrity or numbering failed")
    if "models changed=0" not in dry_state or "tools changed=0" not in dry_state:
        raise RuntimeError("Publication-state dry-run differs from the approved catalog plan")
    report = {
        "status": "PASS", "commit": commit, "sha256": digest, "backup": str(backup),
        "catalog_plan": plan or None, "publication_state": publication,
        "production_database_untouched": True,
        "changed_factual_tables": changed_factual_tables(before, after),
        "before": {k: v for k, v in before.items() if k not in ("tools", "model_rows", "offers", "accesses", "factual_tables")},
        "trial": {k: v for k, v in after.items() if k not in ("tools", "model_rows", "offers", "accesses", "factual_tables")},
        "created_models": len(after["model_rows"]) - len(before["model_rows"]),
        "created_tools": len(after["tools"]) - len(before["tools"]),
        "plan_dry_run": dry_plan[-600:], "plan_apply": applied[-600:],
        "publication_dry_run": dry_state[-600:],
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
