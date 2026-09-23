from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from catalog.models import ModelVersion, Offer, Evaluation, Benchmark, Revision, Organization


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        # Synthetic release dates for ordering fixtures, never production data.
        ModelVersion.objects.update(released=date(2020, 1, 1))
        from catalog.chronology import renumber_chronologically
        renumber_chronologically()

    def names(self, params):
        return [m.slug for m in self.client.get("/", params).context["page"]]

    def test_pages_and_missing(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        for model in ModelVersion.objects.all():
            response = self.client.get("/models/" + model.slug, {"lang": "ru"})
            self.assertContains(response, model.version)
            self.assertContains(response, "Платформа и оценка")
            self.assertContains(response, f"#{model.public_number}")
        self.assertEqual(self.client.get("/models/not-real").status_code, 404)
        self.assertEqual(self.client.get("/healthz").json()["service"], "aipedia")

    def test_search_category_task_access(self):
        self.assertEqual(self.names({"q": "qWeN"}), ["qwen3-8b"])
        self.assertEqual(self.names({"category": "image"}), ["flux-1-schnell"])
        self.assertIn("qwen3-8b", self.names({"q": "ПРОГРАММИРОВАНИЕ"}))
        self.assertEqual(self.names({"category": "audio", "task": "translation"}), ["voxtral-mini-3b-2507"])
        self.assertEqual(len(self.names({"access": "download"})), 3)
        self.assertEqual(self.names({"q": "not-a-model"}), [])
        google = Organization.objects.get(name="Google")
        self.assertEqual(len(self.names({"developer": google.pk})), 4)

    def test_price_sort_is_numeric_same_unit_unknown_last(self):
        response = self.client.get("/", {"price_unit": "input", "price_scope": "standard", "sort": "price_asc"})
        offers = [model.comparison_offer.amount if model.comparison_offer else None for model in response.context["page"]]
        priced = [amount for amount in offers if amount is not None]
        self.assertEqual(priced, sorted(priced))
        self.assertTrue(all(amount is None for amount in offers[len(priced):]))
        self.assertNotIn("flux-1-schnell", [model.slug for model in response.context["page"][:len(priced)]])
        offer = Offer.objects.get(model__slug="gemini-2-5-flash-lite", unit="input", primary=True)
        Offer.objects.filter(model=offer.model, unit="input").update(conditions={"ru": "Batch", "en": "Batch"})
        standard = self.client.get("/", {"price_unit": "input", "price_scope": "standard", "sort": "price_asc"})
        all_prices = self.client.get("/", {"price_unit": "input", "price_scope": "all", "sort": "price_asc"})
        self.assertIsNone(next(model for model in standard.context["page"] if model.slug == offer.model.slug).comparison_offer)
        self.assertIsNotNone(next(model for model in all_prices.context["page"] if model.slug == offer.model.slug).comparison_offer)

    def test_benchmark_sort_respects_direction_and_missing(self):
        bench = Benchmark.objects.get(name="AIME 2025")
        response = self.client.get("/", {"benchmark": bench.pk, "sort": "check_best"})
        models = list(response.context["page"])
        results = [m.comparison_evaluation.score for m in models if m.comparison_evaluation]
        self.assertEqual(results, sorted(results, reverse=True))
        self.assertTrue(all(m.comparison_evaluation is None for m in models[len(results):]))
        self.assertTrue(all(m.comparison_evaluation.benchmark_id == bench.pk for m in models if m.comparison_evaluation))
        bench.higher_is_better = False
        bench.save()
        response = self.client.get("/", {"benchmark": bench.pk, "sort": "check_best"})
        self.assertEqual([m.comparison_evaluation.score for m in response.context["page"] if m.comparison_evaluation], sorted(results))
        self.assertIn("flux-1-schnell", self.names({"benchmark": bench.pk}))
        self.assertNotIn("flux-1-schnell", self.names({"benchmark": bench.pk, "evaluated_only": "1"}))

    def test_filters_and_catalogue_state_survive_links(self):
        bench = Benchmark.objects.get(name="AIME 2025")
        response = self.client.get("/", {"q": "Gemini", "category": "code", "access": "api", "lang": "en", "benchmark": bench.pk, "sort": "check_best"})
        self.assertContains(response, 'lang="en"')
        self.assertContains(response, "data-filter-control=\"category\"")
        self.assertContains(response, "data-filter-control=\"access\"")
        self.assertContains(response, "data-filter-control=\"benchmark\"")
        first = response.context["page"][0]
        detail = self.client.get(f"/models/{first.slug}", response.wsgi_request.GET)
        self.assertContains(detail, "category=code")
        self.assertContains(detail, "benchmark=")

    def test_pagination_and_invalid_values(self):
        from catalog.views import INITIAL_PAGE_SIZE, CHUNK_SIZE
        source = ModelVersion.objects.first()
        need = INITIAL_PAGE_SIZE + 5 - ModelVersion.objects.count()
        for i in range(max(0, need)):
            ModelVersion.objects.create(
                family=source.family, name=f"Test version {i}", slug=f"test-version-{i}",
                version="test", category=source.category, tasks=source.tasks, description=source.description,
                source=source.source, checked=source.checked,
            )
        first = self.client.get("/")
        self.assertEqual(len(first.context["page"]), INITIAL_PAGE_SIZE)
        self.assertTrue(first.context["page"].has_next)
        response = self.client.get("/", {"page": 2})
        page = response.context["page"]
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page), min(CHUNK_SIZE, page.paginator.count - INITIAL_PAGE_SIZE))
        for params in ({"page": "nonsense"}, {"sort": "DROP TABLE"}, {"benchmark": "invalid"}, {"developer": "-1"}):
            self.assertEqual(self.client.get("/", params).status_code, 200)

    def test_editorial_history_and_seed_preservation(self):
        offer = Offer.objects.first()
        old = str(offer.amount)
        offer.amount = Decimal("17.50")
        offer.save()
        changes = Revision.objects.filter(model=offer.model, entity="Offer")
        self.assertTrue(any(Decimal(r.snapshot["amount"]) == Decimal(old) for r in changes))
        self.assertEqual(changes.first().snapshot["amount"], "17.50")
        call_command("seed_catalog", verbosity=0)
        offer.refresh_from_db()
        self.assertEqual(offer.amount, Decimal("17.50"))
        self.assertEqual(ModelVersion.objects.count(), 7)

    def test_validation_and_stale(self):
        offer = Offer.objects.first()
        offer.amount = -1
        with self.assertRaises(ValidationError):
            offer.full_clean()
        offer.amount = 1
        offer.unit = "month"
        with self.assertRaises(ValidationError):
            offer.full_clean()
        offer.checked = timezone.localdate() - timedelta(days=31)
        self.assertTrue(offer.stale)

    def test_public_editing_endpoint_is_not_exposed(self):
        self.assertEqual(self.client.post("/report", {"message": "A real correction"}).status_code, 404)

    def test_archiving_keeps_chronology_and_newer_release_gets_later_number(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        assigned = model.public_number
        model.catalog_status = "archived"
        model.save(update_fields=["catalog_status"])
        self.assertEqual(ModelVersion.objects.get(pk=model.pk).public_number, assigned)
        self.assertIn(model.slug, self.names({}))
        self.assertNotIn(model.slug, self.names({"status": "active"}))
        self.assertIn(model.slug, self.names({"status": "archived"}))
        new = ModelVersion.objects.create(
            family=model.family, name="New permanent number", slug="new-permanent-number",
            version="1", category=model.category, tasks=model.tasks, description=model.description,
            source=model.source, checked=model.checked, released=date(2021, 1, 1),
        )
        self.assertGreater(new.public_number, assigned)
        self.assertEqual(self.names({"q": f"#{new.public_number}"}), [new.slug])

    def test_hidden_models_and_html_escaping(self):
        model = ModelVersion.objects.get(slug="qwen3-8b")
        model.published = False
        model.save()
        self.assertNotIn(model.slug, self.names({}))
        self.assertEqual(self.client.get("/models/" + model.slug).status_code, 404)
        response = self.client.get("/", {"q": '<script>alert(1)</script>'})
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertEqual(self.client.get("/admin/").status_code, 302)
