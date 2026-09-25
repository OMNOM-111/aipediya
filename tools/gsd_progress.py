"""Report or update GSD-1.0 acceptance progress in docs/timeline.json.

    python tools/gsd_progress.py                      # table
    python tools/gsd_progress.py --json               # machine-readable
    python tools/gsd_progress.py --set GSD-02.A1 --implemented --verified --evidence "..."

Verified % of an item = verified criteria / all recorded criteria x 100.
Local acceptance = sum(item verified % x item weight / 100). Criteria are never
removed to improve a percentage.
"""
import argparse
import json
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "docs" / "timeline.json"
RELEASE = "GSD-1.0"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def entry(data):
    return next(item for item in data["entries"] if item["release_id"] == RELEASE)


def summary(data):
    rows = []
    impl_total = verified_total = 0.0
    for item in entry(data)["items"]:
        criteria = item["criteria"]
        count = len(criteria)
        impl = sum(bool(c["implemented"]) for c in criteria)
        ver = sum(bool(c["verified"]) for c in criteria)
        impl_pct = round(100 * impl / count, 1)
        ver_pct = round(100 * ver / count, 1)
        impl_total += impl_pct * item["weight"] / 100
        verified_total += ver_pct * item["weight"] / 100
        rows.append({
            "id": item["id"], "title": item["title"], "weight": item["weight"],
            "criteria": count, "implemented": impl, "verified": ver,
            "implemented_pct": impl_pct, "verified_pct": ver_pct,
            "open": [c["id"] for c in criteria if not c["verified"]],
        })
    return {
        "release_id": RELEASE,
        "implementation_coverage_pct": round(impl_total, 1),
        "local_acceptance_pct": round(verified_total, 1),
        "items": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--set", action="append", default=[])
    parser.add_argument("--implemented", action="store_true")
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--evidence", default=None)
    args = parser.parse_args()
    data = load()
    if args.set:
        index = {c["id"]: c for item in entry(data)["items"] for c in item["criteria"]}
        for cid in args.set:
            if cid not in index:
                sys.exit(f"unknown criterion {cid}")
            if args.implemented or args.verified:
                index[cid]["implemented"] = True
            if args.verified:
                index[cid]["verified"] = True
            if args.evidence is not None:
                index[cid]["evidence"] = args.evidence
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = summary(data)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"{RELEASE}: implementation {result['implementation_coverage_pct']}% | Local acceptance {result['local_acceptance_pct']}%")
    for row in result["items"]:
        print(f"  {row['id']} w{row['weight']:>2}  impl {row['implemented']}/{row['criteria']} ({row['implemented_pct']}%)  verified {row['verified']}/{row['criteria']} ({row['verified_pct']}%)")


if __name__ == "__main__":
    main()
