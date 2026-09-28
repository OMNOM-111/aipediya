"""Idempotently correct the three Furniture Assembly taxonomy cells in master.

Epoch AI describes this benchmark as reasoning over photographs and manuals.
The other 22 observations in the same benchmark already use ``image``.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")

import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402


KEYS = {
    "evaluation-v015-final-2026-09-27-5f3603ee12862b65",
    "evaluation-v015-final-2026-09-27-aa44324b423b2993",
    "evaluation-v015-final-2026-09-27-06a3e913a6a23e0f",
}
SOURCE = "https://epoch.ai/benchmarks/furniture-assembly"
KIMI_ACCESS_KEYS = {"access-95", "access-96", "access-97"}
KIMI_SOURCE = "https://www.moonshot.ai/"


def main():
    rows, meta, extra = cm.read_workbook()
    changed = 0
    for row in rows["Evaluations"]:
        if row["Key"] not in KEYS:
            continue
        assert row["Benchmark"] == "Furniture Assembly"
        assert row["Benchmark Category"] in ("text", "image")
        if row["Benchmark Category"] == "image":
            continue
        before = row["Benchmark Category"]
        row["Benchmark Category"] = "image"
        rows["Changelog"].append({
            "Timestamp (UTC)": cm.now_utc(), "Sheet": "Evaluations",
            "Record ID": row["Key"], "Field": "Benchmark Category",
            "Before": before, "After": "image",
            "Reason": "reconciliation #013: Epoch Furniture Assembly uses photographs; " + SOURCE,
        })
        changed += 1
    assert sum(row["Key"] in KEYS for row in rows["Evaluations"]) == 3
    for row in rows["Access"]:
        if row["Key"] not in KIMI_ACCESS_KEYS:
            continue
        assert row["Provider"] in ("Kimi API", "Moonshot AI")
        if row["Provider"] == "Moonshot AI":
            continue
        row["Provider"] = "Moonshot AI"
        rows["Changelog"].append({
            "Timestamp (UTC)": cm.now_utc(), "Sheet": "Access",
            "Record ID": row["Key"], "Field": "Provider",
            "Before": "Kimi API", "After": "Moonshot AI",
            "Reason": "reconciliation #013: Kimi API is operated by Moonshot AI; " + KIMI_SOURCE,
        })
        changed += 1
    assert sum(row["Key"] in KIMI_ACCESS_KEYS for row in rows["Access"]) == 3
    if changed:
        cm.write_workbook(rows, meta, extra=extra)
    print("Reconciliation master rows changed:", changed)


if __name__ == "__main__":
    main()
