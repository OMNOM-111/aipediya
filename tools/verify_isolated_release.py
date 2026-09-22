"""Prove a code-only release on an isolated SQLite copy. Never touches Production."""
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = ROOT / ".venv" / "bin" / "python"


def run(args, env=None, cwd=ROOT):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    result = subprocess.run(args, cwd=cwd, env=merged, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stdout + "\n" + result.stderr)
    return result.stdout


def catalog_fingerprint(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        has_tool = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_tool'"
        ).fetchone()
        published_tools = (
            db.execute("SELECT COUNT(*) FROM catalog_tool WHERE published=1").fetchone()[0]
            if has_tool
            else None
        )
        tool_publication_revisions = (
            db.execute("SELECT COUNT(*) FROM catalog_toolpublicationrevision").fetchone()[0]
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_toolpublicationrevision'"
            ).fetchone()
            else None
        )
        return {
            "integrity": db.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_key_violations": len(db.execute("PRAGMA foreign_key_check").fetchall()),
            "models": db.execute("SELECT COUNT(*) FROM catalog_modelversion").fetchone()[0],
            "published_models": db.execute(
                "SELECT COUNT(*) FROM catalog_modelversion WHERE published=1 AND entry_type='model'"
            ).fetchone()[0],
            "published_tools": published_tools,
            "offers": db.execute("SELECT COUNT(*) FROM catalog_offer").fetchone()[0],
            "accesses": db.execute("SELECT COUNT(*) FROM catalog_access").fetchone()[0],
            "evaluations": db.execute("SELECT COUNT(*) FROM catalog_evaluation").fetchone()[0],
            "sources": db.execute("SELECT COUNT(*) FROM catalog_source").fetchone()[0],
            "research_records": db.execute("SELECT COUNT(*) FROM catalog_researchrecord").fetchone()[0],
            "revisions": db.execute("SELECT COUNT(*) FROM catalog_revision").fetchone()[0],
            "publication_revisions": db.execute("SELECT COUNT(*) FROM catalog_publicationrevision").fetchone()[0],
            "tool_publication_revisions": tool_publication_revisions,
        }
    finally:
        db.close()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_semantically_equal(reference_path, candidate_path):
    reference = json.loads(Path(reference_path).read_text(encoding="utf-8"))
    candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    errors = []
    for key in reference:
        if key == "source":
            continue
        if isinstance(reference[key], list):
            if Counter(map(canonical, reference[key])) != Counter(map(canonical, candidate[key])):
                errors.append(key)
        elif reference[key] != candidate[key]:
            errors.append(key)
    if errors:
        raise SystemExit("Candidate catalog differs from the Local release payload: " + ", ".join(errors))


RENDER = r"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.test_settings")
django.setup()
from django.test import Client
from catalog.models import ModelVersion
import json
client = Client()
secure = os.environ["AIPEDIA_ENV"] == "production"
catalog = client.get("/", {"lang": "ru"}, secure=secure)
english = client.get("/", {"lang": "en", "env": "local", "local": "1"}, secure=secure)
slug = ModelVersion.objects.filter(published=True).values_list("slug", flat=True).first()
card = client.get("/models/" + slug, {"env": "local"}, secure=secure)
health = client.get("/healthz", secure=secure).json()
html = (catalog.content + english.content + card.content).decode()
print(json.dumps({"environment": health["environment"], "nav": "env-nav" in html, "production_link": "env-production" in html, "status": catalog.status_code}))
"""


if __name__ == "__main__":
    source = ROOT / "backups" / "chronology-production-after.sqlite3"
    desired = ROOT / "data" / "local" / "aipedia.sqlite3"
    payload = ROOT / "catalog" / "migrations" / "data" / "global_catalog_20260922.json"
    if not source.is_file() or not desired.is_file() or not payload.is_file():
        raise SystemExit("Release verification requires the exact Production baseline, Local DB, and catalog payload")
    built = json.loads(run([str(PYTHON), str(ROOT / "tools" / "build_code_release.py")]))
    archive = Path(built["archive"])
    dry = json.loads(run([str(PYTHON), str(ROOT / "tools" / "deploy_code_release.py"), str(archive), "--sha256", built["sha256"], "--dry-run"]))
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if any(name.endswith(".sqlite3") or name.endswith(".env") or "secret.key" in name for name in names):
            raise SystemExit("Archive contains a forbidden file")
    with tempfile.TemporaryDirectory(prefix="aipedia-isolated-", ignore_cleanup_errors=True) as raw:
        isolated = Path(raw) / "aipedia.sqlite3"
        with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(isolated) as dst:
            src.backup(dst)
        before = catalog_fingerprint(isolated)
        secret = "isolated-verify-secret-not-for-production-" + "x" * 24
        prod_env = {
            "AIPEDIA_ENV": "production",
            "AIPEDIA_SECRET_KEY": secret,
            "AIPEDIA_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
            "AIPEDIA_DB": str(isolated),
            "AIPEDIA_PUBLIC_ORIGIN": "https://aipediya.com",
            "DJANGO_SETTINGS_MODULE": "aipedia.settings",
        }
        run(
            [
                str(PYTHON),
                str(ROOT / "manage.py"),
                "migrate",
                "catalog",
                "0013_normalize_generic_platforms",
                "--noinput",
            ],
            env=prod_env,
        )
        migrated_baseline = Path(raw) / "production-after-0013.sqlite3"
        with sqlite3.connect(isolated.resolve().as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(migrated_baseline) as dst:
            src.backup(dst)
        run([str(PYTHON), str(ROOT / "manage.py"), "migrate", "--noinput"], env=prod_env)
        after = catalog_fingerprint(isolated)
        expected = json.loads(payload.read_text(encoding="utf-8"))["expected"]
        expected_fingerprint = {
            "integrity": "ok",
            "foreign_key_violations": 0,
            "models": expected["model_versions_total"],
            "published_models": expected["models_published"],
            "published_tools": expected["tools_published"],
            "offers": expected["offers"],
            "accesses": expected["accesses"],
            "evaluations": expected["evaluations"],
            "sources": expected["sources"],
            "research_records": expected["research_records"],
            "revisions": expected["revisions"],
            "publication_revisions": expected["publication_revisions"],
            "tool_publication_revisions": expected["tool_publication_revisions"],
        }
        if after != expected_fingerprint:
            raise SystemExit({"expected": expected_fingerprint, "actual": after})
        candidate_payload = Path(raw) / "candidate-catalog.json"
        run(
            [
                str(PYTHON),
                str(ROOT / "tools" / "export_catalog_release.py"),
                "--baseline",
                str(migrated_baseline),
                "--desired",
                str(isolated),
                "--output",
                str(candidate_payload),
            ]
        )
        assert_semantically_equal(payload, candidate_payload)
        render_prod = {**prod_env, "DJANGO_SETTINGS_MODULE": "aipedia.test_settings"}
        production = run([str(PYTHON), "-c", RENDER], env=render_prod)
        production_state = json.loads(production)
        local_env = {
            "AIPEDIA_ENV": "local",
            "AIPEDIA_SECRET_KEY": "local-preview-only-not-for-production",
            "AIPEDIA_DB": str(isolated),
            "AIPEDIA_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
            "DJANGO_SETTINGS_MODULE": "aipedia.test_settings",
        }
        local = json.loads(run([str(PYTHON), "-c", RENDER], env=local_env))
        if production_state["nav"] or production_state["production_link"] or production_state["environment"] != "production":
            raise SystemExit("Production isolated render leaked Local navigation")
        if not local["nav"] or not local["production_link"] or local["environment"] != "local":
            raise SystemExit("Local isolated render is missing environment navigation")
        print(json.dumps({
            "status": "PASS",
            "archive": built,
            "dry_run": {"commit": dry["commit"], "copies_sqlite": dry["copies_sqlite"]},
            "baseline_fingerprint": before,
            "release_fingerprint": after,
            "semantic_catalog_match": True,
            "production_html_has_nav": production_state["nav"],
            "local_html_has_nav": local["nav"],
        }, indent=2))
