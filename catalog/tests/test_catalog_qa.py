"""Release QA rules (catalog_qa) and currency-aware prices (v015 final)."""
import json
from datetime import date
from decimal import Decimal

from django.test import TestCase

from catalog import catalog_qa
from catalog.comparison import price_matches
from catalog.models import (
    Access, Benchmark, Country, Evaluation, ModelFamily, ModelOriginCountry, ModelVersion, Offer, Organization,
    Service, Source,
)
from catalog.templatetags.catalog_tags import currencies, price


class CatalogQaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(title="S", publisher="P", url="https://example.com/s")
        cls.org = Organization.objects.create(name="Lab", country="USA", source=cls.source, checked=date(2026, 1, 1))
        cls.family = ModelFamily.objects.create(name="F", developer=cls.org)
        cls.us, _ = Country.objects.get_or_create(code="US", defaults={"name_ru": "США", "name_en": "United States"})
        cls.api = Service.objects.create(name="Lab API", provider=cls.org, kind="api", url="https://example.com/api")

    def model(self, slug, origin=True, **extra):
        model = ModelVersion.objects.create(
            name=slug.title(), slug=slug, family=self.family, version="1", published=True, entry_type="model",
            category="text", source=self.source, checked=date(2026, 1, 1), released=date(2025, 1, 1),
            release_evidence={"source_url": "https://example.com/r"}, description={"en": "d"}, **extra)
        if origin:
            ModelOriginCountry.objects.create(model=model, country=self.us, source=self.source, checked=date(2026, 1, 1))
        return model

    def facts(self, *items):
        return {"Facts": [{"Record Type": rt, "Record ID": rid, "Fact": fact, "Value (JSON)": json.dumps(value),
                           "Source URL": "https://example.com/f"} for rt, rid, fact, value in items]}

    def errors(self, rows=None):
        result = catalog_qa.run(rows)
        return result["errors"], result["queue"]

    def test_clean_catalog_passes_and_counters_agree(self):
        self.model("a")
        self.model("b")
        errors, queue = self.errors()
        self.assertEqual(errors, [])
        self.assertEqual(queue, [])

    def test_missing_country_is_blocking_unless_a_gap_is_recorded(self):
        self.model("nocountry", origin=False)
        errors, _ = self.errors()
        self.assertTrue(any("nocountry has no country/flag" in e for e in errors))
        errors, queue = self.errors(self.facts(("model", "nocountry", "origin_status",
                                                {"status": "not_established", "reason": "community project"})))
        self.assertFalse(any("nocountry" in e for e in errors))
        self.assertTrue(any("community project" in q for q in queue))

    def test_commercial_api_without_price_needs_offer_or_gap(self):
        model = self.model("api-model")
        Access.objects.create(model=model, service=self.api, source=self.source, checked=date(2026, 1, 1))
        errors, _ = self.errors()
        self.assertTrue(any("api-model has a commercial API" in e for e in errors))
        errors, queue = self.errors(self.facts(("model", "api-model", "pricing_status", {"status": "custom_enterprise_pricing"})))
        self.assertFalse(any("api-model" in e for e in errors))
        self.assertTrue(queue)
        Offer.objects.create(model=model, service=self.api, amount=Decimal("0"), unit="input", conditions={"ru": "Стандарт", "en": "Standard"},
                             source=self.source, checked=date(2026, 1, 1))
        errors, _ = self.errors()
        self.assertTrue(any("$0 without a stated free tier" in e for e in errors))

    def test_vendor_result_cannot_be_independent_and_blocked_sources_stay_hidden(self):
        model = self.model("evald")
        bench = Benchmark.objects.create(name="B", protocol="p", category="text")
        Evaluation.objects.create(model=model, benchmark=bench, score=1, evaluator="Lab", independent=True, public=True,
                                  result_kind="independent", source=self.source, checked=date(2026, 1, 1))
        blocked = Source.objects.create(title="AA", publisher="AA", url="https://artificialanalysis.ai/models")
        Evaluation.objects.create(model=model, benchmark=bench, score=2, evaluator="Artificial Analysis", independent=True,
                                  public=True, result_kind="independent", source=blocked, checked=date(2026, 1, 1))
        errors, _ = self.errors()
        self.assertTrue(any("marked independent but independent by Lab" in e for e in errors))
        self.assertTrue(any("block republication" in e for e in errors))

    def test_duplicate_names_are_blocking(self):
        self.model("one", aliases=["Shared Name"])
        self.model("two", aliases=["shared name"])
        errors, _ = self.errors()
        self.assertTrue(any("duplicates" in e and "shared name" in e for e in errors))


class CurrencyTests(TestCase):
    def test_price_uses_the_row_currency_and_comparison_stays_in_usd(self):
        class Row:
            def __init__(self, amount, conditions):
                self.amount, self.conditions, self.active, self.billing_unit, self.unit = Decimal(amount), conditions, True, "", "input"
                self.service = type("S", (), {"kind": "api"})()
        self.assertEqual(price(Row("0.5", {"currency": "INR"})), "₹0.5")
        self.assertEqual(price(Row("0.25", {"currency": "RUB"})), "0.25 ₽")
        self.assertEqual(price(Row("2", {})), "$2")
        self.assertEqual(currencies([Row("1", {}), Row("1", {"currency": "INR"})]), "USD, INR")
        self.assertTrue(price_matches(Row("2", {"ru": "Стандарт", "en": "Standard"}), "input"))
        self.assertFalse(price_matches(Row("2", {"ru": "Стандарт", "en": "Standard", "currency": "INR"}), "input"))
