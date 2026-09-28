"""Close the same release card after observed Production health and QA."""
import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from .release_history import ROOT, validate
except ImportError:  # direct script invocation
    from release_history import ROOT, validate


def finalize(registry, release_id, commit, release_report, backup, qa_evidence, health_body):
    errors = validate(registry, release_id)
    if errors:
        raise ValueError("; ".join(errors))
    if commit not in health_body:
        raise ValueError("/healthz does not confirm the deployed commit")
    if not all((release_report, backup, qa_evidence)):
        raise ValueError("Release report, backup and Production QA evidence are required")
    card = next(row for row in registry["product_history"]["milestones"] if row["release_id"] == release_id)
    if not card.get("owner_approved") or not card.get("local_verified"):
        raise ValueError("The owner and Local gates must pass before closure")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    card.update(production_released=True, production_verified=True, progress="done",
                revision=commit, production_verified_at=timestamp,
                release_report=release_report, backup=backup)
    card.setdefault("qa", {})["production"] = qa_evidence
    card["open"] = False
    entry = next(row for row in registry["entries"] if row["release_id"] == release_id)
    entry.update(environment="production", stage="released", revision=commit,
                 production_verified_at=timestamp, release_tag=card["release_tag"])
    registry["product_history"]["current_production"] = {
        "release_id": release_id, "release_sequence": card["release_sequence"],
        "app_version": card["app_version"], "release_tag": card["release_tag"],
        "revision": commit, "confirmed_at": timestamp,
        "evidence": qa_evidence, "source": release_report,
    }
    errors = validate(registry)
    if errors:
        raise ValueError("; ".join(errors))
    return registry


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--production-qa", required=True, help="Path to passing gsd_production_qa JSON report")
    args = parser.parse_args()
    source = ROOT / "docs/timeline.json"
    report = ROOT / args.release_report
    if not report.is_file() or not str(report.resolve()).startswith(str((ROOT / "docs/history").resolve())):
        raise SystemExit("Release report must exist under docs/history")
    if not re.fullmatch(r"aipedia-before-code-\d{8}T\d{6}Z\.sqlite3", args.backup):
        raise SystemExit("A verified AIpediya pre-deploy backup filename is required")
    qa_report = json.loads(Path(args.production_qa).read_text(encoding="utf-8"))
    if not (qa_report.get("passed", 0) > 0 and qa_report.get("passed") == qa_report.get("total")
            and not qa_report.get("failures") and args.commit in json.dumps(qa_report.get("health", {}))):
        raise SystemExit("Production QA report must pass fully for the deployed commit")
    with urllib.request.urlopen("https://aipediya.com/healthz", timeout=15) as response:
        health = response.read().decode("utf-8")
    registry = json.loads(source.read_text(encoding="utf-8"))
    finalized = finalize(registry, args.release_id, args.commit, args.release_report,
                         args.backup, f"{qa_report['passed']}/{qa_report['total']} PASS; {args.production_qa}", health)
    source.write_text(json.dumps(finalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from build_product_history import build
    build()
    print("POST-PRODUCTION HISTORY PASS: card, current_production and timeline.html updated")
