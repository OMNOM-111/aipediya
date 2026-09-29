"""Optional, bounded request-cost aggregates for the AIpediya process.

No URL, slug, query value, IP address, cookie, or raw User-Agent is persisted.
The 10-second windows can be joined to PID CPU samples without an access log.
"""

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from django.conf import settings
from django.db import connection


_ROUTES = {
    "catalog": "models_root", "tool_catalog": "tools_root",
    "detail": "model_panel", "tool_detail": "tool_panel",
    "sitemap": "sitemap_index", "sitemap_locale": "sitemap_locale",
    "health": "health", "robots": "robots", "indexnow_key": "indexnow_key",
    "indexnow_root_key": "indexnow_key", "collections": "collections",
    "collection": "collection", "datasets": "datasets",
    "datasets_index": "datasets", "dataset_page": "datasets",
    "dataset_manifest": "datasets", "dataset_download": "datasets",
}
_SEARCH_BOTS = ("googlebot", "bingbot", "yandexbot", "baiduspider", "duckduckbot")
_AI_BOTS = ("gptbot", "oai-searchbot", "chatgpt-user", "claudebot", "perplexitybot",
            "bytespider", "ccbot")
_SEO_BOTS = ("semrushbot", "ahrefsbot", "mj12bot", "dotbot")
_QA_AGENTS = ("aipediya-gsd", "aipediya-performance-audit", "aipediya-search-qa")
_FILTER_KEYS = frozenset({"category", "developer", "status", "access", "country", "purpose",
                          "pricing", "price_unit", "price_mode", "evaluated_only", "benchmark"})
_LATENCY_CEILINGS_MS = (50, 200, 500, 1000, 2500)
_MAX_GROUPS = 512


def ua_bucket(raw):
    """Only retain a declared agent family, never the client-supplied string."""
    ua = raw[:512].lower()
    for token in _QA_AGENTS:
        if token in ua:
            return "own_qa", token
    for token in _SEARCH_BOTS:
        if token in ua:
            return "search_crawler", token
    for token in _AI_BOTS:
        if token in ua:
            return "ai_crawler", token
    for token in _SEO_BOTS:
        if token in ua:
            return "seo_crawler", token
    if re.search(r"bot|spider|crawl|slurp", ua):
        return "other_declared_crawler", "other"
    if "edg/" in ua:
        return "browser", "edge"
    if "chrome/" in ua:
        return "browser", "chrome"
    if "firefox/" in ua:
        return "browser", "firefox"
    if "safari/" in ua:
        return "browser", "safari"
    return "unknown", "unknown"


def route_bucket(request):
    match = getattr(request, "resolver_match", None)
    name = getattr(match, "url_name", None)
    if name in _ROUTES:
        return _ROUTES[name]
    if name:
        return "other_matched"
    # Redirects and middleware 404s may not have a resolver match. Only a
    # fixed first-component class is retained; the path itself is discarded.
    path = getattr(request, "aipedia_neutral_path", request.path_info)
    if path.startswith("/static/"):
        return "static"
    if path.startswith("/models/"):
        return "unmatched_model"
    if path.startswith("/tools/"):
        return "unmatched_tool"
    return "unmatched_other"


def action_bucket(request):
    params = request.GET
    actions = []
    if "q" in params:
        actions.append("search")
    if any(key in params for key in _FILTER_KEYS):
        actions.append("filter")
    if "sort" in params:
        sort = params.get("sort", "")
        if sort.startswith("price_"):
            actions.append("sort_price")
        elif sort.startswith("number_") or sort.startswith("release_"):
            actions.append("sort_chronology")
        else:
            actions.append("sort_other")
    if "page" in params:
        actions.append("page")
    if "partial" in params:
        actions.append("partial")
    return "+".join(actions) if actions else "default"


def _rss_bytes():
    try:
        fields = Path("/proc/self/statm").read_text(encoding="ascii").split()
        return int(fields[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError, AttributeError):
        return None


def _io_counters():
    try:
        lines = Path("/proc/self/io").read_text(encoding="ascii").splitlines()
        pairs = (line.split(":", 1) for line in lines if ":" in line)
        return {key: int(value.strip()) for key, value in pairs
                if key in {"read_bytes", "write_bytes", "rchar", "wchar"}}
    except (OSError, ValueError):
        return None


class RotatingJsonlWriter:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024,
                                           backupCount=2, encoding="utf-8", delay=True)
        self.handler.setFormatter(logging.Formatter("%(message)s"))

    def __call__(self, report):
        record = logging.LogRecord("aipedia.request_metrics", logging.INFO, "", 0,
                                   json.dumps(report, ensure_ascii=False, separators=(",", ":")),
                                   (), None)
        self.handler.handle(record)


class RequestMetricCollector:
    def __init__(self, writer, window_seconds=10):
        self.writer = writer
        self.window_ns = max(1, int(window_seconds * 1_000_000_000))
        self.lock = threading.Lock()
        self.started_ns = None
        self.started_utc = None
        self.cpu_start_ns = None
        self.io_start = None
        self.groups = {}

    def start(self):
        with self.lock:
            if self.started_ns is None:
                self.started_ns = time.monotonic_ns()
                self.started_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
                self.cpu_start_ns = time.process_time_ns()
                self.io_start = _io_counters()

    def observe(self, route, action, ua_class, ua_family, status, wall_ns,
                thread_ns, sql_count, sql_ns, response_bytes):
        now = time.monotonic_ns()
        key = (route, action, ua_class, ua_family, int(status))
        with self.lock:
            # Reserve one slot for all combinations beyond the bounded set.
            if key not in self.groups and len(self.groups) >= _MAX_GROUPS - 1:
                key = ("overflow", "other", "other", "other", 0)
            stats = self.groups.setdefault(key, {
                "count": 0, "wall_ms_sum": 0.0, "wall_ms_max": 0.0,
                "thread_cpu_ms_sum": 0.0, "sql_count_sum": 0,
                "sql_count_max": 0, "sql_ms_sum": 0.0, "sql_ms_max": 0.0,
                "response_bytes_sum": 0, "response_bytes_known": 0,
                "latency_bins": [0] * (len(_LATENCY_CEILINGS_MS) + 1),
            })
            wall_ms = wall_ns / 1_000_000
            sql_ms = sql_ns / 1_000_000
            stats["count"] += 1
            stats["wall_ms_sum"] += wall_ms
            stats["wall_ms_max"] = max(stats["wall_ms_max"], wall_ms)
            stats["thread_cpu_ms_sum"] += thread_ns / 1_000_000
            stats["sql_count_sum"] += sql_count
            stats["sql_count_max"] = max(stats["sql_count_max"], sql_count)
            stats["sql_ms_sum"] += sql_ms
            stats["sql_ms_max"] = max(stats["sql_ms_max"], sql_ms)
            if response_bytes is not None:
                stats["response_bytes_sum"] += response_bytes
                stats["response_bytes_known"] += 1
            bin_index = next((i for i, ceiling in enumerate(_LATENCY_CEILINGS_MS)
                              if wall_ms <= ceiling), len(_LATENCY_CEILINGS_MS))
            stats["latency_bins"][bin_index] += 1
            report = self._snapshot_locked(now) if now - self.started_ns >= self.window_ns else None
        if report is not None:
            self.writer(report)

    def flush(self):
        with self.lock:
            report = self._snapshot_locked(time.monotonic_ns()) if self.groups else None
        if report is not None:
            self.writer(report)
        return report

    def _snapshot_locked(self, now):
        io_end = _io_counters()
        io_delta = ({key: io_end[key] - self.io_start[key] for key in io_end.keys() & self.io_start.keys()}
                    if io_end is not None and self.io_start is not None else None)
        elapsed_ns = max(1, now - self.started_ns)
        cpu_ns = time.process_time_ns() - self.cpu_start_ns
        report = {
            "schema": 1, "pid": os.getpid(), "start_utc": self.started_utc,
            "end_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "window_ms": round(elapsed_ns / 1_000_000, 2),
            "process_cpu_ms": round(cpu_ns / 1_000_000, 2),
            "process_cpu_pct_one_core": round(100 * cpu_ns / elapsed_ns, 2),
            "rss_bytes": _rss_bytes(), "io_delta": io_delta,
            "latency_bin_ceilings_ms": _LATENCY_CEILINGS_MS,
            "groups": [dict(route=key[0], action=key[1], ua_class=key[2],
                            ua_family=key[3], status=key[4], **value)
                       for key, value in sorted(self.groups.items())],
        }
        self.started_ns = now
        self.started_utc = report["end_utc"]
        self.cpu_start_ns = time.process_time_ns()
        self.io_start = io_end
        self.groups = {}
        return report


class RequestMetricsMiddleware:
    """Synchronous WSGI instrumentation; enabled only by an explicit setting."""

    def __init__(self, get_response, collector=None):
        self.get_response = get_response
        self._reported_failure = False
        self.collector = collector or RequestMetricCollector(
            RotatingJsonlWriter(settings.AIPEDIA_REQUEST_METRICS_PATH),
            settings.AIPEDIA_REQUEST_METRICS_WINDOW_SECONDS,
        )

    def __call__(self, request):
        try:
            self.collector.start()
        except Exception:
            self._warn_once()
            return self.get_response(request)
        started = time.perf_counter_ns()
        thread_started = time.thread_time_ns()
        sql_count = 0
        sql_ns = 0
        response = None

        def count_sql(execute, sql, params, many, context):
            nonlocal sql_count, sql_ns
            sql_started = time.perf_counter_ns()
            try:
                return execute(sql, params, many, context)
            finally:
                sql_count += 1
                sql_ns += time.perf_counter_ns() - sql_started

        try:
            with connection.execute_wrapper(count_sql):
                response = self.get_response(request)
            return response
        finally:
            wall_ns = time.perf_counter_ns() - started
            thread_ns = time.thread_time_ns() - thread_started
            length = response.get("Content-Length") if response is not None else None
            content_bytes = int(length) if length and length.isdecimal() else None
            ua_class, ua_family = ua_bucket(request.META.get("HTTP_USER_AGENT", ""))
            try:
                self.collector.observe(route_bucket(request), action_bucket(request),
                                       ua_class, ua_family,
                                       response.status_code if response is not None else 500,
                                       wall_ns, thread_ns, sql_count, sql_ns, content_bytes)
            except Exception:
                self._warn_once()

    def _warn_once(self):
        if not self._reported_failure:
            self._reported_failure = True
            logging.getLogger(__name__).warning("Request metrics unavailable; application response unaffected")
