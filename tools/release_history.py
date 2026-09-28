"""Validate the versioned product-history contract for code releases."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"^v(?:0\.[1-9]\d*\.[0-9]+|1\.0\.0|[1-9]\d*\.[0-9]+\.[0-9]+)$")


def validate(registry, release_id=None, package_revision=None, html=None):
    errors = []
    history = registry.get("product_history", {})
    entries = {row["release_id"]: row for row in registry.get("entries", [])}
    cards = history.get("milestones", [])
    numbered = [row for row in cards if row.get("release_sequence") is not None]
    sequences = [row["release_sequence"] for row in numbered]
    if sorted(sequences) != list(range(1, len(sequences) + 1)) or len(set(sequences)) != len(sequences):
        errors.append("Release sequences must be unique and contiguous; cancelled numbers stay reserved")
    versions = [row.get("app_version") for row in numbered]
    if len(set(versions)) != len(versions):
        errors.append("App versions must be unique")
    for row in numbered:
        rid = row["release_id"]
        entry = entries.get(rid)
        if not entry or entry.get("release_sequence") != row["release_sequence"] or entry.get("app_version") != row.get("app_version"):
            errors.append(f"Entry/card version mismatch: {rid}")
        if not VERSION.fullmatch(row.get("app_version") or ""):
            errors.append(f"Invalid SemVer: {rid}")
        if row.get("production_verified") and not (row.get("production_released") and row.get("owner_approved") and row.get("local_verified") and row.get("progress") == "done"):
            errors.append(f"Invalid production state: {rid}")
        if row.get("production_released") and not row.get("production_verified"):
            errors.append(f"Release lacks Production QA: {rid}")
    for pointer in ("current_local", "current_production"):
        state = history.get(pointer)
        if not state or not any(row["release_id"] == state.get("release_id") and row.get("release_sequence") == state.get("release_sequence") and row.get("app_version") == state.get("app_version") for row in numbered):
            errors.append(f"Invalid {pointer} pointer")
    current_production = history.get("current_production", {})
    production_card = next((row for row in numbered if row["release_id"] == current_production.get("release_id")), {})
    if not production_card.get("production_verified") or production_card.get("revision") != current_production.get("revision"):
        errors.append("Current Production does not match a verified card")
    if release_id:
        card = next((row for row in numbered if row["release_id"] == release_id), None)
        if not card:
            errors.append(f"Missing release card: {release_id}")
        else:
            previous = max((row["release_sequence"] for row in numbered
                            if row["release_id"] != release_id and
                            (row.get("production_verified") or row.get("progress") in ("cancelled", "superseded"))), default=0)
            if card["release_sequence"] != previous + 1:
                errors.append("Candidate must use the next Release sequence")
            if history.get("current_local", {}).get("release_id") != release_id:
                errors.append("current_local does not identify candidate")
            for key in ("owner_approved", "local_verified"):
                if card.get(key) is not True:
                    errors.append(f"Candidate missing {key}")
            if card.get("progress") not in ("review", "done") or card.get("production_released"):
                errors.append("Candidate must be in review and not yet released")
            if not card.get("changes") or not card.get("qa", {}).get("local") or not card.get("source"):
                errors.append("Candidate needs exact changes, Local QA and source")
            if not card.get("revision"):
                errors.append("Candidate needs recorded commit/build revision")
            if package_revision and card.get("revision") != package_revision:
                errors.append("Package revision differs from release card")
            if not card.get("release_tag"):
                errors.append("Candidate needs reserved release tag")
    if html is not None:
        digest = hashlib.sha256(json.dumps(registry, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if f'name="aipediya-timeline-sha256" content="{digest}"' not in html:
            errors.append("timeline.html is stale or has not passed validation")
    return errors


def load():
    return json.loads((ROOT / "docs/timeline.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id")
    parser.add_argument("--revision")
    parser.add_argument("--html", action="store_true")
    args = parser.parse_args()
    issues = validate(load(), args.release_id, args.revision,
                      (ROOT / "timeline.html").read_text(encoding="utf-8") if args.html else None)
    if issues:
        raise SystemExit("RELEASE HISTORY FAIL: " + "; ".join(issues))
    print("RELEASE HISTORY PASS")
