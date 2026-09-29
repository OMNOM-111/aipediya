from django.test import TestCase


class ContentSecurityPolicyTests(TestCase):
    def test_local_standalone_history_uses_no_network_csp(self):
        response = self.client.get("/ru/history/")
        self.assertEqual(response.status_code, 200)
        policy = response["Content-Security-Policy"]
        self.assertIn("default-src 'none'", policy)
        self.assertIn("connect-src 'none'", policy)
        self.assertIn("script-src 'unsafe-inline'", policy)
        self.assertIn("style-src 'unsafe-inline'", policy)
        self.assertNotIn("static.cloudflareinsights.com", policy)

    def test_cloudflare_beacon_has_narrow_script_and_same_origin_connect_sources(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        directives = dict(
            part.strip().split(" ", 1)
            for part in response["Content-Security-Policy"].split(";")
        )
        self.assertEqual(
            directives["script-src"],
            "'self' https://static.cloudflareinsights.com/beacon.min.js "
            "https://static.cloudflareinsights.com/beacon.min.js/",
        )
        self.assertEqual(directives["connect-src"], "'self'")
        self.assertEqual(directives["default-src"], "'self'")
        self.assertEqual(directives["style-src"], "'self'")
        self.assertEqual(directives["frame-ancestors"], "'none'")
        self.assertNotIn("'unsafe-inline'", response["Content-Security-Policy"])
        self.assertNotIn("'unsafe-eval'", response["Content-Security-Policy"])
        self.assertNotIn("*", response["Content-Security-Policy"])
