import copy
import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from catalog.models import ResearchRecord, ResearchRevision
from catalog.research import (
    ResearchError, openrouter_evidence, prepare_records, read_document,
    summarize, validate_document,
)
from catalog.templatetags.catalog_tags import local

COMMAND = "catalog.management.commands.import_research"
FIXTURE = Path(settings.BASE_DIR) / "data/research/aipediya_catalog_2026-09-18.json"


def row(record_id="AI-0001", **changes):
    value = {
        "record_id": record_id, "entity_type": "model", "name": "Example",
        "developer": "Example Lab", "supplier": "Example Lab",
        "access": ["API"], "plan": "Standard", "currency": "USD",
        "source_ids": ["source"], "publication_state": "review_required",
        "input_modalities": None, "output_modalities": None,
        "input_usd_per_million_tokens": None, "energy_consumption": None,
        "categories": ["text", "code"], "benchmark": {
            "value": 53, "setting": "max", "evaluation_date": None,
        },
    }
    value.update(changes)
    return value


def document(*rows):
    return {
        "project": "AIpedia", "snapshot_date": "2026-09-18",
        "sources": [{"id": "source", "url": "https://example.org/", "checked_at": "2026-09-18"}],
        "taxonomy": [{"id": "code", "label_en": "Coding"}],
        "limitations_ru": ["Unverified"], "records": list(rows or [row()]),
    }


def run_import(doc, **options):
    output = StringIO()
    with patch(f"{COMMAND}.read_document", return_value=copy.deepcopy(doc)):
        call_command("import_research", "unused.json", stdout=output, **options)
    return json.loads(output.getvalue())


def api_model(model_id="example/model", **changes):
    value = {
        "id": model_id, "hugging_face_id": "Example/Model",
        "pricing": {"prompt": "0.000000123456789", "completion": "0"},
        "per_request_limits": None,
        "architecture": {"input_modalities": ["image", "text"], "output_modalities": ["text"]},
    }
    value.update(changes)
    return value


def snapshot(*models):
    rows = list(models or [api_model()])
    return {"data": rows, "total_count": len(rows), "links": {"next": None}}


class ResearchValidationTests(SimpleTestCase):
    def test_public_russian_source_terms_have_explicit_english_labels(self):
        command = __import__(
            "catalog.management.commands.promote_research", fromlist=["Command"]
        ).Command()
        self.assertEqual(command._conditions({"plan": "В составе Pro"})["en"], "Included with Pro")
        self.assertEqual(command._conditions({"plan": "В составе Max · от"})["en"], "Included with Max · from")
        self.assertEqual(local("Самостоятельно / Hugging Face", "en"), "Self-hosted / Hugging Face")
        self.assertEqual(
            local("видео; конфигурация требует уточнения", "en"),
            "video; configuration needs verification",
        )
        self.assertEqual(
            local(
                {"ru": "Pay-as-you-go · Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки."},
                "en",
            ),
            "Pay-as-you-go · Price per video, not per second; duration and configuration need verification.",
        )

    def test_real_archive_counts_use_exact_source_keys(self):
        doc = read_document(FIXTURE)
        summary = summarize(doc)
        self.assertEqual(summary["offers"], 280)
        self.assertEqual(summary["distinct_entry_names"], 217)
        self.assertEqual(summary["distinct_model_names"], 198)
        self.assertEqual(summary["distinct_other_names"], 19)
        self.assertEqual(summary["distinct_names_by_entity_type"], {
            "model": 198, "product": 9, "runtime": 2, "service": 8,
        })
        self.assertEqual(summary["offers_by_entity_type"], {
            "model": 235, "product": 33, "runtime": 4, "service": 8,
        })
        self.assertEqual({r["publication_state"] for r in doc["records"]}, {"review_required"})

    def test_counts_do_not_merge_developers_or_count_plans_as_models(self):
        doc = document(row(), row("AI-0002", plan="Premium"),
                       row("AI-0003", developer="Other Lab"), row("AI-0004", entity_type="product"))
        summary = summarize(doc)
        self.assertEqual(summary["offers"], 4)
        self.assertEqual(summary["distinct_entry_names"], 1)
        self.assertEqual(summary["distinct_entities"], 3)

    def test_prepare_preserves_rows_metadata_and_nulls_without_normalizing(self):
        doc = document(row(custom_metadata={"price": "0.1234567890123456789"}))
        original = copy.deepcopy(doc)
        batch, items, _ = prepare_records(doc)
        self.assertEqual(batch, "AIpedia:2026-09-18")
        self.assertEqual(items[0]["external_id"], "AIpedia:2026-09-18:AI-0001")
        self.assertEqual(items[0]["payload"]["record"], original["records"][0])
        self.assertEqual(items[0]["payload"]["dataset"], {k: v for k, v in original.items() if k != "records"})
        self.assertEqual(doc, original)
        self.assertIsNone(items[0]["payload"]["record"]["input_modalities"])
        self.assertEqual(items[0]["payload"]["record"]["categories"], ["text", "code"])

    def test_rejects_malformed_duplicate_and_nonfinite_json(self):
        for raw in ('{', '{"project":"a","project":"b"}', '{"price":NaN}', '{"price":Infinity}'):
            with self.subTest(raw=raw), patch("pathlib.Path.read_text", return_value=raw):
                with self.assertRaises(ResearchError):
                    read_document("input.json")

    def test_rejects_invalid_whole_batches(self):
        bad = [
            [], {}, document(row(publication_state="accepted")),
            document(row(), row()), document(row(record_id="")),
            document(row(entity_type="unknown")), document(row(source_ids=["missing"])),
            document(row(source_ids=[{}])), document(row(name=None)),
            {**document(), "row_count": 999}, {**document(), "unique_model_names": 999},
            {**document(), "records": []}, {**document(), "snapshot_date": "yesterday"},
            {**document(), "source_count": True}, document(row(price=float("inf"))),
        ]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(ResearchError):
                validate_document(item)

    def test_namespaced_ids_fit_the_schema(self):
        for batch in ("", "x" * 201, "x" * 195):
            with self.subTest(batch=batch), self.assertRaises(ResearchError):
                prepare_records(document(), batch)


class ResearchImportTests(TestCase):
    def test_only_staging_is_written_and_reimport_preserves_review_decisions(self):
        call_command("seed_catalog", stdout=StringIO())
        public_models = [model for model in apps.get_app_config("catalog").get_models()
                         if model not in {ResearchRecord, ResearchRevision}]
        before = {model: list(model.objects.order_by("pk").values()) for model in public_models}
        doc = document(row(), row("AI-0002", plan="Second offer"))
        first = run_import(doc)
        self.assertEqual(first["created"], 2)
        self.assertEqual(first["published"], 0)
        records = list(ResearchRecord.objects.order_by("external_id"))
        for record, state in zip(records, ("accepted", "rejected")):
            record.state = state
            record.save(update_fields=["state"])
        timestamps = [record.imported_at for record in records]
        second = run_import(doc)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["unchanged"], 2)
        for record, state, timestamp in zip(records, ("accepted", "rejected"), timestamps):
            record.refresh_from_db()
            self.assertEqual(record.state, state)
            self.assertEqual(record.imported_at, timestamp)
        self.assertEqual(ResearchRecord.objects.count(), 2)
        self.assertEqual(before, {model: list(model.objects.order_by("pk").values()) for model in public_models})

    def test_changed_row_conflict_rolls_back_preceding_new_records(self):
        run_import(document())
        original = ResearchRecord.objects.get()
        with self.assertRaisesMessage(CommandError, "Conflicting research content"):
            run_import(document(row("AI-0002"), row(plan="Changed")))
        self.assertEqual(ResearchRecord.objects.count(), 1)
        original.refresh_from_db()
        self.assertEqual(original.payload["record"]["plan"], "Standard")

    def test_changed_root_metadata_is_a_conflict_not_silent_replacement(self):
        doc = document()
        run_import(doc)
        doc["sources"][0]["url"] = "https://example.org/changed"
        with self.assertRaises(CommandError):
            run_import(doc)
        self.assertEqual(ResearchRecord.objects.get().payload["dataset"]["sources"][0]["url"], "https://example.org/")

    def test_new_batch_does_not_duplicate_a_reviewed_record(self):
        run_import(document(), batch="research-v1")
        record = ResearchRecord.objects.get()
        record.state = "accepted"
        record.save(update_fields=["state"])
        with self.assertRaises(CommandError):
            run_import(document(row(plan="Revised")), batch="research-v2")
        self.assertEqual(ResearchRecord.objects.count(), 1)
        record.refresh_from_db()
        self.assertEqual(record.state, "accepted")

    def test_dry_run_never_accesses_database(self):
        with self.assertNumQueries(0):
            result = run_import(document(), dry_run=True)
        self.assertEqual(result["offers"], 1)
        self.assertFalse(result["database_checked"])
        self.assertNotIn("created", result)
        self.assertEqual(ResearchRecord.objects.count(), 0)

    def test_invalid_late_record_writes_nothing(self):
        with self.assertNumQueries(0), self.assertRaises(CommandError):
            run_import(document(row(), row("AI-0002", publication_state="accepted")))
        self.assertEqual(ResearchRecord.objects.count(), 0)

    def test_actual_file_imports_all_280_rows_only_to_staging(self):
        output = StringIO()
        call_command("import_research", str(FIXTURE), stdout=output)
        self.assertEqual(ResearchRecord.objects.count(), 280)
        self.assertEqual(json.loads(output.getvalue())["created"], 280)
        record = ResearchRecord.objects.get(external_id="AIpedia:2026-09-18:AI-0001")
        original = read_document(FIXTURE)
        self.assertEqual(record.payload["record"], original["records"][0])
        self.assertEqual(record.payload["dataset"]["sources"], original["sources"])
        self.assertFalse(ResearchRecord.objects.exclude(state="review_required").exists())


class OpenRouterEvidenceTests(SimpleTestCase):
    def evidence(self, doc, api=None):
        return openrouter_evidence(doc, api if api is not None else snapshot(), "2026-09-19T00:00:00+00:00")

    def test_exact_id_prices_use_decimal_and_never_approve_the_row(self):
        doc = document(row(openrouter_id="example/model", supplier="OpenRouter",
                           input_usd_per_million_tokens="0.123456789",
                           output_usd_per_million_tokens=0))
        result = self.evidence(doc)
        fields = result["records"][0]["fields"]
        self.assertEqual(fields["input_usd_per_million_tokens"]["openrouter_usd_per_million"], "0.123456789000000")
        self.assertEqual(fields["input_usd_per_million_tokens"]["status"], "numeric_match_only")
        self.assertEqual(fields["output_usd_per_million_tokens"]["status"], "numeric_match_only")
        self.assertEqual(result["records"][0]["publication_state"], "review_required")
        self.assertEqual(result["observed_openrouter_models"][0]["raw_pricing"]["prompt"], "0.000000123456789")

    def test_repository_matches_retain_every_variant_without_comparing_other_provider_prices(self):
        api = snapshot(api_model(), api_model("example/model:free", pricing={"prompt": "0", "completion": "0"}))
        result = self.evidence(document(row(repository_id="Example/Model")), api)
        fields = result["records"][0]["fields"]
        self.assertEqual(fields["repository_id"]["openrouter_ids"], ["example/model", "example/model:free"])
        self.assertEqual(fields["input_usd_per_million_tokens"]["status"], "not_comparable_provider_or_id")
        self.assertEqual(len(result["observed_openrouter_models"]), 2)
        self.assertIsNone(result["observed_openrouter_models"][0]["per_request_limits"])

    def test_name_similarity_never_establishes_model_identity(self):
        result = self.evidence(document(row(name="example/model")))
        self.assertEqual(result["observed_openrouter_models"], [])
        self.assertEqual(result["records"][0]["fields"]["openrouter_id"]["status"], "not_verifiable_missing_exact_id")

    def test_price_differences_and_null_are_distinct_from_free(self):
        doc = document(row(openrouter_id="example/model", supplier="OpenRouter",
                           input_usd_per_million_tokens=1))
        fields = self.evidence(doc)["records"][0]["fields"]
        self.assertEqual(fields["input_usd_per_million_tokens"]["status"], "numeric_difference")
        self.assertEqual(fields["output_usd_per_million_tokens"]["status"], "unknown")

    def test_negative_sentinel_and_conditional_pricing_are_preserved(self):
        pricing = {"prompt": "-1", "completion": None, "overrides": [{"min_prompt_tokens": 200000, "prompt": "0.000005"}]}
        result = self.evidence(document(row(openrouter_id="example/model")), snapshot(api_model(pricing=pricing)))
        observed = result["observed_openrouter_models"][0]
        self.assertIsNone(observed["usd_per_million_tokens"]["prompt"])
        self.assertEqual(observed["raw_pricing"], pricing)

    def test_invalid_empty_duplicate_or_partial_snapshots_are_rejected(self):
        for value in (
            {}, {"data": []}, {**snapshot(), "error": {"message": "failed"}},
            {**snapshot(), "total_count": 2}, {**snapshot(), "links": {"next": "?offset=1"}},
            snapshot(api_model(), api_model()), snapshot(api_model(pricing=None)),
            snapshot(api_model(id=None)), {**snapshot(), "links": []},
        ):
            with self.subTest(value=value), self.assertRaises(ResearchError):
                self.evidence(document(), value)
