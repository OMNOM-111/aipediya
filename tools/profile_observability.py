"""Measure the optional request-metrics wrapper overhead on Local only.

Usage: python tools/profile_observability.py --output artifacts/observability-overhead.json
Requires AIPEDIA_ENV=local and AIPEDIA_DB pointing to Local SQLite.
"""

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if os.environ.get("AIPEDIA_ENV") != "local" or not os.environ.get("AIPEDIA_DB"):
    raise SystemExit("Set AIPEDIA_ENV=local and AIPEDIA_DB to Local SQLite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
os.environ.setdefault("AIPEDIA_SECRET_KEY", "local-observability-profile-only")

import django

django.setup()

from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory

from catalog.observability import RequestMetricCollector, RequestMetricsMiddleware


def sample(handler, request, iterations):
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    for _ in range(iterations):
        response = handler(request)
        if response.status_code != 200:
            raise RuntimeError("unexpected benchmark response")
    return ((time.perf_counter_ns() - started_wall) / iterations / 1000,
            (time.process_time_ns() - started_cpu) / iterations / 1000)


def benchmark(sql, iterations, rounds):
    def response(_request):
        if sql:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return HttpResponse("ok")

    reports = []
    collector = RequestMetricCollector(reports.append, window_seconds=3600)
    enabled = RequestMetricsMiddleware(response, collector=collector)
    request = RequestFactory().get("/healthz", HTTP_USER_AGENT="Mozilla/5.0 Chrome/120")
    request.resolver_match = SimpleNamespace(url_name="health")
    sample(response, request, 200)
    sample(enabled, request, 200)
    measurements = {"bare": [], "instrumented": []}
    for round_index in range(rounds):
        order = (("bare", response), ("instrumented", enabled))
        if round_index % 2:
            order = tuple(reversed(order))
        for label, handler in order:
            measurements[label].append(sample(handler, request, iterations))
    collector.flush()
    median = {label: {"wall_us_per_request": round(statistics.median(item[0] for item in values), 2),
                      "cpu_us_per_request": round(statistics.median(item[1] for item in values), 2)}
              for label, values in measurements.items()}
    return {"iterations_per_round": iterations, "rounds": rounds, "sql_select_one": sql,
            "median": median,
            "overhead_wall_us": round(median["instrumented"]["wall_us_per_request"] -
                                      median["bare"]["wall_us_per_request"], 2),
            "overhead_cpu_us": round(median["instrumented"]["cpu_us_per_request"] -
                                     median["bare"]["cpu_us_per_request"], 2),
            "aggregated_reports": len(reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = {"environment": "local", "benchmarks": [
        benchmark(False, 5000, 5), benchmark(True, 2000, 5),
    ]}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
