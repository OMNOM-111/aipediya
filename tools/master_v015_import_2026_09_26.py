"""Master v015 (catch-up 2026-09-26) -> import-ready: Record IDs and vocabulary.

The v015 workbook was assembled outside this repository; `catalog_master check`
rejects two NEW Record IDs containing '.' (only letters, digits, '-' and '_'
are allowed). Neither record has ever been on Local or Production, so the
stable-ID rule is not violated by normalizing them before their first sync.
Every reference in the linked sheets (Offers, Access, Facts, Origins, Tool
Platforms, Evaluations) moves with the record; each move goes to the
Changelog. Older Changelog rows keep the ID they were written with.

Tasks and modalities of the new records were written as free text
("speech synthesis", "robot state"); the site uses a closed vocabulary for
filters and localized labels (modalities text/image/audio/video/other; task
keys already used by published records). The precise wording stays in the
descriptions; each replacement goes to the Changelog. Re-running is a no-op.

  .venv\\Scripts\\python.exe tools\\master_v015_import_2026_09_26.py --book AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402

RUN = "v015 import 2026-09-26"
RENAMES = {
    "gemini-3.8-flash-tts": "gemini-3-8-flash-tts",
    "gemini-3.8-flash-lite-tts": "gemini-3-8-flash-lite-tts",
}
AS_RECEIVED_SHA256 = "cc431f94468d3eebf2e58398888407fa0517aea685939944b91b2043849ff158"
LINKED = ("Offers", "Evaluations", "Access", "Facts", "Origins", "Tool Platforms")
VOCABULARY = {
    "gemini-3-8-flash-tts": {"Tasks": "speech"},
    "gemini-3-8-flash-lite-tts": {"Tasks": "speech"},
    "yandex-speech-tts-live": {"Tasks": "speech"},
    "nemotron-3-diarization": {"Tasks": "speech; audio_processing", "Output Modalities": "text"},
    "sarvam-vision-2-1": {"Tasks": "ocr; vision; text", "Output Modalities": "text"},
    "gliner-2-5-decide": {"Tasks": "text", "Input Modalities": "text", "Output Modalities": "text"},
    "flux-3-action-droid": {"Tasks": "robotics; vision", "Input Modalities": "image; text; other",
                            "Output Modalities": "video; other"},
    "flux-3-action-so101": {"Tasks": "robotics; vision", "Input Modalities": "image; text; other",
                            "Output Modalities": "video; other"},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    args = parser.parse_args()
    book = Path(args.book)
    before_sha = hashlib.sha256(book.read_bytes()).hexdigest()
    rows, meta, extra = cm.read_workbook(book)
    stamp = cm.now_utc()
    log = rows["Changelog"]
    reason = ("%s: Record ID contained '.', rejected by catalog_master check; normalized before the first sync "
              "(record never on Local/Production)" % RUN)
    moved = changed = 0
    for old, new in RENAMES.items():
        record = next((r for r in rows["Models"] if r["Record ID"] == old), None)
        if record is None:
            assert any(r["Record ID"] == new for r in rows["Models"]), new
            continue  # already renamed
        assert not any(r["Record ID"] == new for sheet in cm.MAIN for r in rows[sheet]), new
        assert record.get("On Local") != "YES" and record.get("On Production") != "YES", record["Record ID"]
        record["Record ID"] = new
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Models", "Record ID": new, "Field": "Record ID",
                    "Before": old, "After": new, "Reason": reason})
        for sheet in LINKED:
            for row in rows.get(sheet, []):
                if row.get("Record ID") == old and row.get("Record Type", "model") == "model":
                    row["Record ID"] = new
                    moved += 1
                    log.append({"Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": new,
                                "Field": "Record ID (%s)" % row.get("Key", ""), "Before": old, "After": new,
                                "Reason": reason})
    models = {r["Record ID"]: r for r in rows["Models"]}
    for record_id, fields in VOCABULARY.items():
        row = models[record_id]
        for field, value in fields.items():
            if row.get(field, "") != value:
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Models", "Record ID": record_id, "Field": field,
                            "Before": row.get(field, ""), "After": value,
                            "Reason": "%s: free text -> site vocabulary (filters, localized labels); "
                                      "details remain in Description EN/RU" % RUN})
                row[field] = value
                changed += 1
    renumbered = cm.refresh_derived(rows, log, "%s: chronology recomputed" % RUN, stamp)
    meta = dict(meta)
    meta.update({"Version": "v015", "Built From": "v015 catch-up as received sha256 %s + %s" % (AS_RECEIVED_SHA256, RUN)})
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, book, extra)
    print(json.dumps({"book": str(book), "before_sha256": before_sha,
                      "after_sha256": hashlib.sha256(book.read_bytes()).hexdigest(),
                      "renamed": RENAMES, "linked_rows_moved": moved, "vocabulary_fields": changed,
                      "renumbered_events": renumbered,
                      "published": {s: sum(1 for r in rows[s] if r["Status"] == "PUBLISHED") for s in cm.MAIN}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
