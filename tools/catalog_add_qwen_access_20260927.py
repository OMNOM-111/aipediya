"""Complete the Qwen3Guard download access rows in the canonical master."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from catalog import catalog_master as cm

rows, meta, extra = cm.read_workbook(cm.WORKBOOK_PATH)
stamp = cm.now_utc()
for size, suffix in (("0.6B", "0-6b"), ("4B", "4b"), ("8B", "8b")):
    record_id = f"qwen3guard-stream-{suffix}"
    key = f"access-20260927-{record_id}-weights"
    url = f"https://huggingface.co/Qwen/Qwen3Guard-Stream-{size}"
    if not any(r["Key"] == key for r in rows["Access"]):
        row = {column: "" for column in cm.AUX["Access"]}
        row.update({"Key": key, "Record Type": "model", "Record ID": record_id,
            "Service": "Qwen3Guard weights", "Service Kind": "download",
            "Service URL": url, "Provider": "Qwen / Alibaba",
            "Compute Location": "local", "Source URL": url,
            "Checked": "2026-09-27"})
        rows["Access"].append(row)
        rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Access",
            "Record ID": record_id, "Field": key, "Before": "", "After": url,
            "Reason": "Expose verified open-weight download in Local card"})
    model = next(r for r in rows["Models"] if r["Record ID"] == record_id)
    before = model["Tasks"]
    if before != "safety":
        model["Tasks"] = "safety"
        rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Models",
            "Record ID": record_id, "Field": "Tasks", "Before": before,
            "After": "safety", "Reason": "Use localized safety taxonomy; streaming detail remains in description"})

longcat = next(r for r in rows["Models"] if r["Record ID"] == "longcat-2-5-preview")
before = longcat["Tasks"]
after = "coding; agents; vision"
if before != after:
    longcat["Tasks"] = after
    rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Models",
        "Record ID": "longcat-2-5-preview", "Field": "Tasks", "Before": before,
        "After": after, "Reason": "Remove duplicate untranslated task label"})

cm.write_workbook(rows, meta, cm.WORKBOOK_PATH, extra)
print("Qwen3Guard download access recorded for 0.6B, 4B and 8B")
