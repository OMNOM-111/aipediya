import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Benchmark, Evaluation, ModelVersion, Offer, PublicationRevision



def write_package():
    source = {
        "id": "official", "title": "Official documentation", "url": "https://example.org/docs",
    }
    entities = [
        {"entity_id": "minimax-turbo", "entity_type": "model", "name": "speech-2.8-turbo", "developer": "MiniMax", "categories": ["speech"], "description_ru": "Речь", "description_en": "Speech"},
        {"entity_id": "minimax-hd", "entity_type": "model", "name": "speech-2.8-hd", "developer": "MiniMax", "categories": ["speech"], "description_ru": "Речь", "description_en": "Speech"},
        {"entity_id": "gpt-oss", "entity_type": "model", "name": "gpt-oss-20b", "developer": "OpenAI", "categories": ["code"], "description_ru": "Код", "description_en": "Code"},
        {"entity_id": "video", "entity_type": "model", "name": "Example Video", "developer": "Example", "categories": ["video_generation"], "description_ru": "Видео", "description_en": "Video"},
        {"entity_id": "api", "entity_type": "model", "name": "Example API", "developer": "Example", "categories": ["code"], "description_ru": "Код", "description_en": "Code"},
    ]

    def record(record_id, entity_id, **values):
        entity = next(item for item in entities if item["entity_id"] == entity_id)
        row = {
            "record_id": record_id, "entity_id": entity_id, "entity_type": entity["entity_type"],
            "name": entity["name"], "developer": entity["developer"], "source_ids": ["official"],
            "checked_at": "2026-09-19", "access_entry_url": "https://example.org/docs",
            "interface_types": ["API"], "execution_location": "cloud", "billing_kind": "usage",
            "price_verification": "not_verified", "publication_state": "review_required",
        }
        row.update(values)
        return row

    document = {
        "project": "AIpedia test", "snapshot_date": "2026-09-19", "sources": [source], "entities": entities,
        "taxonomy": [
            {"id": "speech", "label_ru": "Речь", "label_en": "Speech"},
            {"id": "code", "label_ru": "Программирование", "label_en": "Coding"},
            {"id": "video_generation", "label_ru": "Генерация видео", "label_en": "Video generation"},
        ],
        "records": [
            record("AI-0098", "minimax-turbo", price_verification="published_rates_checked", price_usd_per_unit=60, billing_unit="1M символов"),
            record("AI-0097", "minimax-hd", price_verification="published_rates_checked", price_usd_per_unit=100, billing_unit="1M символов"),
            record("AI-0350", "gpt-oss", interface_types=["local_runtime"], execution_location="local", billing_kind="local"),
            record("AI-video", "video"),
            record("AI-api", "api", price_verification="published_rates_checked", input_usd_per_million_tokens=1),
        ],
        "evaluations": [{
            "entity_id": "gpt-oss", "evidence_type": "independent_benchmark", "verification": "source_result_checked",
            "source_url": "https://example.org/evaluation", "metric": "GPQA Diamond", "setting": "test protocol",
            "value": 75, "evaluator": "Example evaluator", "checked_at": "2026-09-19",
        }],
    }
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
    with handle:
        json.dump(document, handle)
    return Path(handle.name)


class PublicCatalogFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.package = write_package()
        call_command("import_research", str(cls.package))
        call_command("promote_research", str(cls.package))
        Evaluation.objects.filter(benchmark__protocol="test protocol").update(public=True)

    @classmethod
    def tearDownClass(cls):
        cls.package.unlink(missing_ok=True)
        super().tearDownClass()

    def test_minimax_unit_survives_import_publication_and_both_languages(self):
        turbo = Offer.objects.get(research_key="AI-0098:unit")
        hd = Offer.objects.get(research_key="AI-0097:unit")
        self.assertEqual((turbo.amount, turbo.unit), (60, "million_characters"))
        self.assertEqual((hd.amount, hd.unit), (100, "million_characters"))
        for lang, expected in (("ru", "1M символов"), ("en", "1M characters")):
            response = self.client.get(f"/?lang={lang}&q=speech-2.8-turbo")
            self.assertContains(response, "60</strong>", html=False)
            self.assertContains(response, expected)

    def test_local_cli_never_becomes_cloud_access(self):
        model = ModelVersion.objects.get(research_entity_id="gpt-oss")
        self.assertTrue(all(access.service.compute_location == "local" for access in model.accesses.all()))
        response = self.client.get(f"/models/{model.slug}?lang=ru")
        self.assertContains(response, "Локально")
        self.assertNotContains(response, "Вычисления: Облако")

    def test_taxonomy_labels_and_checked_evaluations_render_without_internal_ids(self):
        response = self.client.get("/?lang=en&category=video_generation")
        self.assertContains(response, "Video generation")
        self.assertNotContains(response, ">video_generation<", html=False)
        checked = Evaluation.objects.filter(independent=True, source__url__startswith="https://").count()
        self.assertGreater(checked, 0)

    def test_numeric_sorts_require_an_explicit_comparison_scope(self):
        price_response = self.client.get("/?lang=en&price_unit=input&sort=price_asc")
        self.assertEqual(price_response.context["price_unit"], "input")
        self.assertContains(price_response, "Price unit")

        benchmark = Benchmark.objects.get(protocol="test protocol")
        response = self.client.get(f"/?lang=en&benchmark={benchmark.pk}&sort=check_best&evaluated_only=1")
        models = list(response.context["page"])
        self.assertTrue(models)
        self.assertTrue(all(
            Evaluation.objects.filter(model=model, independent=True, benchmark=benchmark).exists()
            for model in models
        ))
        self.assertContains(response, "Selected test: best result")

    def test_localization_refresh_is_audited_and_never_changes_prices(self):
        offer = Offer.objects.get(research_key="AI-0098:unit")
        offer.conditions = {"ru": "В составе Pro", "en": "В составе Pro"}
        offer.save(update_fields=["conditions"])
        amount = offer.amount
        call_command("refresh_public_localizations")
        offer.refresh_from_db()
        self.assertEqual(offer.amount, amount)
        self.assertEqual(offer.conditions["en"], "Included with Pro")
        self.assertTrue(PublicationRevision.objects.filter(action="localize_offer", model=offer.model).exists())
