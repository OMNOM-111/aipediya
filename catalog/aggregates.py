"""Verifiable aggregates over published records only (GSD-09 foundation).

Every figure is a plain count over the same public projection as the datasets,
so any number can be re-derived from the published JSON/CSV. There is no
history here: counts describe the current published state only (time series
need the future public change history), and nothing is a rating.
"""
from collections import Counter

from . import datasets


def compute():
    models = datasets.records("models")
    tools = datasets.records("tools")

    def year(row):
        value = row["release_date"] or row["approximate_release_date"]
        return value[:4] if value else "unknown"

    return {
        "scope": "published records at generation time; no history",
        "dataset_versions": {
            "models": datasets.metadata("models", models)["dataset_version"],
            "tools": datasets.metadata("tools", tools)["dataset_version"],
        },
        "models": {
            "total": len(models),
            "by_release_year": dict(sorted(Counter(year(row) for row in models).items())),
            "by_date_precision": dict(Counter(row["release_date_precision"] or "unknown" for row in models)),
            "by_category": dict(Counter(row["category"] for row in models).most_common()),
            "by_origin_country": dict(Counter(code for row in models for code in row["origin_countries"]).most_common()),
            "by_status": dict(Counter(row["status"] for row in models).most_common()),
            "open_weights": sum(1 for row in models if row["open_weights"]),
            "with_api_access": sum(1 for row in models if any(a["kind"] == "api" for a in row["access"])),
            "with_listed_price": sum(1 for row in models if row["prices"]),
            "context_known": sum(1 for row in models if row["context_window_tokens"] is not None),
            "context_at_least_1m": sum(1 for row in models if (row["context_window_tokens"] or 0) >= 1_000_000),
        },
        "tools": {
            "total": len(tools),
            "by_category": dict(Counter(row["category"] for row in tools).most_common()),
            "by_local_execution": dict(Counter(row["local_execution"] or "unknown" for row in tools)),
            "by_platform": dict(Counter(code for row in tools for code in row["platforms"]).most_common()),
            "release_date_known": sum(1 for row in tools if row["release_date_precision"]),
        },
    }
