"""Read-only Local request profile; no database writes or server restart.

Usage: python tools/profile_catalog.py --output artifacts/catalog-performance-local.json
The caller must set AIPEDIA_ENV=local and AIPEDIA_DB to the Local SQLite path.
"""

import argparse
import cProfile
import io
import json
import os
import pstats
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if os.environ.get("AIPEDIA_ENV") != "local":
    raise SystemExit("Refusing to profile a non-Local environment")
if not os.environ.get("AIPEDIA_DB"):
    raise SystemExit("Set AIPEDIA_DB to the Local SQLite file")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
os.environ.setdefault("AIPEDIA_SECRET_KEY", "local-performance-profile-only")

import django

django.setup()

from django.conf import settings
from django.db import connection
from django.db.models import Count
from django.test import Client
from catalog.models import ModelVersion, Tool

settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]


def profile(path, repeats=3):
    observations = []
    for index in range(repeats + 1):
        queries = 0
        db_seconds = 0.0

        def timing(execute, sql, params, many, context):
            nonlocal queries, db_seconds
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                queries += 1
                db_seconds += time.perf_counter() - started

        client = Client()
        cpu_started = time.process_time()
        wall_started = time.perf_counter()
        with connection.execute_wrapper(timing):
            response = client.get(path)
        observation = {
            "status": response.status_code,
            "wall_ms": round(1000 * (time.perf_counter() - wall_started), 2),
            "cpu_ms": round(1000 * (time.process_time() - cpu_started), 2),
            "db_ms": round(1000 * db_seconds, 2),
            "queries": queries,
            "response_bytes": len(response.content),
        }
        if index:
            observations.append(observation)
    return {
        "path": path,
        "samples": observations,
        "median": {key: statistics.median(item[key] for item in observations)
                   for key in ("wall_ms", "cpu_ms", "db_ms", "queries", "response_bytes")},
        "statuses": [item["status"] for item in observations],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--hotspot", help="Also show cumulative CPU hotspots for this Local path")
    parser.add_argument("--hotspot-only", action="store_true")
    parser.add_argument("--path", help="Measure one Local path instead of the standard matrix")
    args = parser.parse_args()
    if args.hotspot_only and not args.hotspot:
        parser.error("--hotspot-only requires --hotspot")
    if not args.hotspot_only and not args.output:
        parser.error("--output is required unless --hotspot-only is used")
    if args.hotspot_only:
        hotspot(args.hotspot)
        return
    if args.path:
        result = {"environment": "local", "requests": [profile(args.path)]}
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result["requests"][0], indent=2, ensure_ascii=False))
        return
    heavy = (ModelVersion.objects.filter(published=True, entry_type="model")
             .annotate(n=Count("evaluations")).order_by("-n").values_list("slug", "n").first())
    ordinary = ModelVersion.objects.filter(published=True, entry_type="model").order_by("pk").values_list("slug", flat=True).first()
    tool = Tool.objects.filter(published=True).order_by("pk").values_list("slug", flat=True).first()
    paths = [
        "/", "/es/", "/tools/", f"/models/{ordinary}",
        f"/models/{heavy[0]}", f"/tools/{tool}",
        "/?category=code", "/?sort=price_asc&price_unit=input", "/sitemap.xml",
    ]
    result = {
        "environment": "local", "database": "data/local/aipedia.sqlite3",
        "heavy_model_evaluations": heavy[1],
        "requests": [profile(path) for path in paths],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.hotspot:
        hotspot(args.hotspot)
    print(json.dumps({"output": str(output), "heavy_model_evaluations": heavy[1],
                      "medians": {item["path"]: item["median"] for item in result["requests"]}},
                     indent=2, ensure_ascii=False))


def hotspot(path):
    profiler = cProfile.Profile()
    profiler.enable()
    response = Client().get(path)
    profiler.disable()
    report = io.StringIO()
    pstats.Stats(profiler, stream=report).sort_stats("cumulative").print_stats(40)
    print(f"HOTSPOT {path} status={response.status_code}\n{report.getvalue()}")


if __name__ == "__main__":
    main()
