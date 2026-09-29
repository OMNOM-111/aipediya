"""The optional #015 telemetry must be useful without retaining user input."""

import json
from types import SimpleNamespace

from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from catalog.observability import (RequestMetricCollector, RequestMetricsMiddleware,
                                   action_bucket, route_bucket, ua_bucket)


class RequestMetricClassificationTests(SimpleTestCase):
    def test_ua_families_are_declared_classes_not_raw_values(self):
        self.assertEqual(ua_bucket("Mozilla/5.0 (compatible; Googlebot/2.1)"),
                         ("search_crawler", "googlebot"))
        self.assertEqual(ua_bucket("GPTBot/1.0 secret-marker"), ("ai_crawler", "gptbot"))
        self.assertEqual(ua_bucket("Mozilla/5.0 Chrome/120"), ("browser", "chrome"))
        self.assertEqual(ua_bucket("odd-private-agent secret-marker"), ("unknown", "unknown"))

    def test_routes_and_actions_discard_slugs_and_query_values(self):
        request = RequestFactory().get(
            "/models/private-record?q=sensitive-term&sort=price_asc&category=medical"
        )
        request.resolver_match = SimpleNamespace(url_name="detail")
        self.assertEqual(route_bucket(request), "model_panel")
        self.assertEqual(action_bucket(request), "search+filter+sort_price")
        request.resolver_match = None
        self.assertEqual(route_bucket(request), "unmatched_model")

    def test_disabled_by_default_even_if_test_host_has_a_flag(self):
        self.assertFalse(settings.AIPEDIA_REQUEST_METRICS_ENABLED)
        self.assertNotIn("catalog.observability.RequestMetricsMiddleware", settings.MIDDLEWARE)

    def test_group_cardinality_is_bounded(self):
        reports = []
        collector = RequestMetricCollector(reports.append, window_seconds=3600)
        collector.start()
        for index in range(600):
            collector.observe("route", "default", "browser", "chrome", index,
                              1_000_000, 100_000, 0, 0, None)
        report = collector.flush()
        self.assertLessEqual(len(report["groups"]), 512)
        self.assertEqual(sum(group["count"] for group in report["groups"]), 600)
        self.assertEqual(len(reports), 1)


class RequestMetricMiddlewareTests(TestCase):
    def test_measures_sql_and_response_without_private_request_content(self):
        reports = []
        collector = RequestMetricCollector(reports.append, window_seconds=3600)

        def get_response(request):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            response = HttpResponse("ok")
            response["Content-Length"] = "2"
            return response

        middleware = RequestMetricsMiddleware(get_response, collector=collector)
        request = RequestFactory().get(
            "/models/private-record?q=sensitive-term&sort=price_asc",
            HTTP_USER_AGENT="GPTBot/1.0 secret-marker",
            HTTP_COOKIE="session=do-not-log",
            REMOTE_ADDR="192.0.2.44",
        )
        request.resolver_match = SimpleNamespace(url_name="detail")
        self.assertEqual(middleware(request).status_code, 200)
        report = collector.flush()
        self.assertEqual(len(reports), 1)
        self.assertEqual(report["pid"] > 0, True)
        self.assertIn("process_cpu_pct_one_core", report)
        self.assertIn("rss_bytes", report)
        self.assertIn("io_delta", report)
        group = report["groups"][0]
        self.assertEqual((group["route"], group["action"], group["ua_class"],
                          group["ua_family"], group["status"]),
                         ("model_panel", "search+sort_price", "ai_crawler", "gptbot", 200))
        self.assertEqual((group["count"], group["sql_count_sum"], group["response_bytes_sum"]),
                         (1, 1, 2))
        self.assertGreaterEqual(group["sql_ms_sum"], 0)
        self.assertGreaterEqual(group["thread_cpu_ms_sum"], 0)
        serialized = json.dumps(report)
        for secret in ("private-record", "sensitive-term", "medical", "secret-marker",
                       "do-not-log", "192.0.2.44", "GPTBot/1.0"):
            self.assertNotIn(secret, serialized)

    def test_sink_failure_never_changes_response(self):
        def broken_writer(_report):
            raise OSError("metrics disk unavailable")

        collector = RequestMetricCollector(broken_writer, window_seconds=0)
        middleware = RequestMetricsMiddleware(lambda request: HttpResponse("alive"),
                                              collector=collector)
        request = RequestFactory().get("/healthz")
        request.resolver_match = SimpleNamespace(url_name="health")
        response = middleware(request)
        self.assertEqual((response.status_code, response.content), (200, b"alive"))
