from django.test import TestCase, override_settings, SimpleTestCase
from django.core.management import call_command
from catalog.models import ModelVersion
import os
import subprocess
import sys
from pathlib import Path


class EnvironmentNavTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_local_renders_nav_on_catalog_and_card(self):
        catalog = self.client.get("/", {"lang": "ru"}, follow=True)
        self.assertContains(catalog, 'class="env-nav"')
        self.assertContains(catalog, "env-local")
        self.assertContains(catalog, "Production")
        self.assertContains(catalog, "https://aipediya.com/ru/")
        self.assertContains(catalog, 'target="_blank"')
        english = self.client.get("/", {"lang": "en"}, follow=True)
        self.assertContains(english, 'href="https://aipediya.com/" target="_blank"')
        model = ModelVersion.objects.get(slug="qwen3-8b")
        card = self.client.get("/models/" + model.slug, {"lang": "ru"}, follow=True)
        self.assertContains(card, 'class="env-nav"')
        self.assertContains(card, "https://aipediya.com/ru/")
        self.assertEqual(self.client.get("/healthz").json()["environment"], "local")

    @override_settings(AIPEDIA_ENV="production", DEBUG=False, SECURE_SSL_REDIRECT=False,
                       SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
    def test_production_omits_nav_even_with_query_or_cookie(self):
        self.client.cookies["aipedia_env"] = "local"
        self.client.cookies["env"] = "local"
        for params in ({}, {"lang": "en"}, {"env": "local", "local": "1", "AIPEDIA_ENV": "local"}):
            response = self.client.get("/", params, secure=True, follow=True)
            self.assertNotContains(response, "env-nav")
            self.assertNotContains(response, "env-local")
            self.assertNotContains(response, "env-production")
            self.assertNotContains(response, "Production ↗")
            self.assertNotContains(response, "Production <span")
        model = ModelVersion.objects.get(slug="qwen3-8b")
        card = self.client.get("/models/" + model.slug, {"env": "local"}, secure=True)
        self.assertNotContains(card, "env-nav")
        self.assertNotContains(card, "env-production")
        health = self.client.get("/healthz", secure=True).json()
        self.assertEqual(health["environment"], "production")
        self.assertNotIn("Deploy", self.client.get("/", secure=True).content.decode())


class ProductionSettingsGuardTests(SimpleTestCase):
    def test_production_refuses_the_local_database(self):
        root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env.update({
            "AIPEDIA_ENV": "production",
            "AIPEDIA_SECRET_KEY": "production-guard-test-secret-" + "x" * 40,
            "AIPEDIA_ALLOWED_HOSTS": "aipediya.com",
            "AIPEDIA_DB": str(root / "data" / "local" / "aipedia.sqlite3"),
            "DJANGO_SETTINGS_MODULE": "aipedia.settings",
        })
        result = subprocess.run(
            [sys.executable, str(root / "manage.py"), "check"],
            cwd=root, env=env, text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Local SQLite", result.stderr + result.stdout)
