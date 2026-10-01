"""Apply the canonical master correction found during Release #021 owner review."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog import catalog_master as cm


RECORD_ID = "gemini-4-argon-bcdaec0e"
SOURCE = "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/"
VALUE = "1000000"
REASON = "Release #021 owner review: official Gemini 4 Argon maximum output"


def apply(path: Path) -> dict:
    rows, meta, extra = cm.read_workbook(path)
    row = next(item for item in rows["Models"] if item.get("Record ID") == RECORD_ID)
    if row.get("Official Source") != SOURCE:
        raise ValueError("Gemini 4 Argon official source does not match the reviewed source")
    if row.get("Context"):
        raise ValueError("Gemini 4 Argon input context must remain unknown")
    before = row.get("Max Output", "")
    changed = before != VALUE
    if changed:
        row["Max Output"] = VALUE
        stamp = cm.now_utc()
        rows["Changelog"].append({
            "Timestamp (UTC)": stamp,
            "Sheet": "Models",
            "Record ID": RECORD_ID,
            "Field": "Max Output",
            "Before": before,
            "After": VALUE,
            "Reason": REASON,
        })
        meta = cm.refresh_meta(dict(meta), rows, stamp)
        cm.write_workbook(rows, meta, path, extra)
    return {"record_id": RECORD_ID, "before": before, "after": VALUE, "changed": changed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=cm.WORKBOOK_PATH)
    args = parser.parse_args()
    print(json.dumps(apply(args.path), ensure_ascii=False, indent=2))
