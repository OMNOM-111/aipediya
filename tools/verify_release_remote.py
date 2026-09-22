"""Read-only Production verification for the 2026-09-22 AIpedia release."""

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path("/srv/aipedia")
DB = ROOT / "data" / "aipedia.sqlite3"
PAYLOAD = ROOT / "app" / "catalog" / "migrations" / "data" / "global_catalog_20260922.json"
EXPECTED_PAYLOAD_SHA256 = "5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2"
EXPECTED = {
    "models_published": 763,
    "tools_published": 138,
    "model_versions_total": 901,
    "offers": 555,
    "accesses": 1205,
    "evaluations": 881,
    "sources": 343,
    "research_records": 2900,
    "research_revisions": 3590,
    "revisions": 4354,
    "publication_revisions": 3049,
    "tool_publication_revisions": 158,
}


def one(db, query, parameters=()):
    return db.execute(query, parameters).fetchone()[0]


def sample(db, table, slug):
    row = db.execute(
        f"SELECT slug, name, catalog_status, public_number, published FROM {table} WHERE slug=?",
        (slug,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing sample: {slug}")
    return dict(row)


def assert_contiguous(db, table, where):
    numbers = [
        row[0]
        for row in db.execute(
            f"SELECT public_number FROM {table} WHERE {where} AND public_number IS NOT NULL ORDER BY public_number"
        )
    ]
    if numbers != list(range(1, len(numbers) + 1)):
        raise RuntimeError(f"non-contiguous public numbers in {table}")
    return {"numbered": len(numbers), "first": numbers[:18], "last": numbers[-1:]}


def main():
    db = sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        counts = {
            "models_published": one(
                db,
                "SELECT COUNT(*) FROM catalog_modelversion WHERE published=1 AND entry_type='model'",
            ),
            "tools_published": one(db, "SELECT COUNT(*) FROM catalog_tool WHERE published=1"),
            "model_versions_total": one(db, "SELECT COUNT(*) FROM catalog_modelversion"),
            "offers": one(db, "SELECT COUNT(*) FROM catalog_offer"),
            "accesses": one(db, "SELECT COUNT(*) FROM catalog_access"),
            "evaluations": one(db, "SELECT COUNT(*) FROM catalog_evaluation"),
            "sources": one(db, "SELECT COUNT(*) FROM catalog_source"),
            "research_records": one(db, "SELECT COUNT(*) FROM catalog_researchrecord"),
            "research_revisions": one(db, "SELECT COUNT(*) FROM catalog_researchrevision"),
            "revisions": one(db, "SELECT COUNT(*) FROM catalog_revision"),
            "publication_revisions": one(db, "SELECT COUNT(*) FROM catalog_publicationrevision"),
            "tool_publication_revisions": one(db, "SELECT COUNT(*) FROM catalog_toolpublicationrevision"),
        }
        payload_sha256 = hashlib.sha256(PAYLOAD.read_bytes()).hexdigest()
        report = {
            "status": "PASS",
            "build": json.loads((ROOT / "app" / "BUILD.json").read_text()),
            "integrity": one(db, "PRAGMA integrity_check"),
            "foreign_key_violations": len(db.execute("PRAGMA foreign_key_check").fetchall()),
            "payload_sha256": payload_sha256,
            "counts": counts,
            "model_numbers": assert_contiguous(
                db, "catalog_modelversion", "published=1 AND entry_type='model'"
            ),
            "tool_numbers": assert_contiguous(db, "catalog_tool", "published=1"),
            "samples": {
                "retired": sample(db, "catalog_modelversion", "jurassic-1-jumbo-3bcc324f"),
                "current_api": sample(db, "catalog_modelversion", "gpt-6-astra-d05a172f"),
                "open_weight": sample(db, "catalog_modelversion", "llama-3-70b-instruct-a953989a"),
                "tts": sample(db, "catalog_modelversion", "eleven-v3-42cde628"),
                "tool": sample(db, "catalog_tool", "chatgpt-46cd5277"),
                "api_tool": sample(db, "catalog_tool", "grok-voice-api-e5ae4c9e"),
            },
            "catalog_migrations": [
                row[0]
                for row in db.execute(
                    "SELECT name FROM django_migrations WHERE app='catalog' ORDER BY id"
                )
            ],
        }
        if counts != EXPECTED:
            raise RuntimeError(f"count mismatch: {counts}")
        if report["integrity"] != "ok" or report["foreign_key_violations"]:
            raise RuntimeError("database integrity check failed")
        if payload_sha256 != EXPECTED_PAYLOAD_SHA256:
            raise RuntimeError("installed payload digest mismatch")
        if report["catalog_migrations"][-1] != "0014_global_catalog_20260922":
            raise RuntimeError("release migration is not current")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
