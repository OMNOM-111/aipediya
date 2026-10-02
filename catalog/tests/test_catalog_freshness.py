import json
import tempfile
from pathlib import Path
from django.test import SimpleTestCase

from catalog import freshness
from tools import deploy_code_release


class CatalogFreshnessSnapshotTests(SimpleTestCase):
    def test_snapshot_is_derived_from_catalog_plan(self):
        plan = {
            "schema": "aipedia-catalog-plan/1",
            "release": "release-test-daily",
            "changes": [
                {"kind": "create", "sheet": "Models", "id": "model-new", "row": {"Name": "Model New"}},
                {"kind": "create", "sheet": "Tools", "id": "tool-new", "row": {"Name": "Tool New"}},
                {"kind": "update", "sheet": "Models", "id": "model-old", "row": {"Name": "Model Old"}},
                {"kind": "update", "sheet": "Tools", "id": "tool-old", "row": {"Name": "Tool Old"}},
                {"kind": "offer_new", "sheet": "Offers", "id": "offer", "row": {"Name": "Not a card"}},
            ],
        }
        snapshot = freshness.snapshot_from_plan(plan, "2026-09-29T21:39:59Z")
        self.assertEqual(snapshot["release"], "release-test-daily")
        self.assertEqual(snapshot["updated_at_utc"], "2026-09-29T21:39:59Z")
        self.assertEqual(snapshot["counts"], {
            "added_models": 1, "added_tools": 1, "updated_models": 1,
            "updated_tools": 1, "updated_records": 2,
        })
        self.assertEqual(
            [(item["record_type"], item["action"], item["record_id"], item["name"]) for item in snapshot["entries"]],
            [("model", "added", "model-new", "Model New"), ("tool", "added", "tool-new", "Tool New"),
             ("model", "updated", "model-old", "Model Old"), ("tool", "updated", "tool-old", "Tool Old")],
        )

    def test_related_row_changes_update_the_existing_card_but_renumbering_does_not(self):
        plan = {"changes": [
            {"kind": "create", "sheet": "Models", "id": "kev", "row": {"Name": "Kev", "Exact Release Date": "2026-09-24"}},
            {"kind": "number", "sheet": "Models", "id": "old-model", "before": 3, "after": 4},
            {"kind": "number", "sheet": "Models", "id": "kev", "before": None, "after": 3},
            {"kind": "platforms", "sheet": "Tools", "id": "copilot", "before": ["web"], "after": ["macos"]},
            {"kind": "offer_new", "sheet": "Offers", "id": "o1", "owner": "tool:copilot"},
            {"kind": "access_new", "sheet": "Access", "id": "a1", "owner": "model:glm"},
            {"kind": "evaluation", "sheet": "Evaluations", "id": "e1", "identity": {"model": "gpt"}},
            {"kind": "service_provider", "sheet": "Offers", "id": "Shared API", "identity": {"name": "Shared API"}},
            {"kind": "benchmark_category", "sheet": "Evaluations", "id": "Bench", "identity": {"name": "Bench"}},
        ]}
        rows = {"Models": [{"Record ID": "glm", "Name": "GLM"}, {"Record ID": "gpt", "Name": "GPT"}],
                "Tools": [{"Record ID": "copilot", "Name": "GitHub Copilot"}]}
        snapshot = freshness.snapshot_from_plan(plan, "2026-10-02T00:00:00Z", rows=rows)
        self.assertEqual(
            [(item["record_type"], item["action"], item["record_id"], item["name"]) for item in snapshot["entries"]],
            [("model", "added", "kev", "Kev"), ("tool", "updated", "copilot", "GitHub Copilot"),
             ("model", "updated", "glm", "GLM"), ("model", "updated", "gpt", "GPT")],
        )
        self.assertEqual(snapshot["counts"]["updated_records"], 3)

    def test_recent_release_predicate_uses_confirmed_dates_only(self):
        from datetime import date
        today = date(2026, 10, 2)
        self.assertTrue(freshness.is_recent_release(date(2026, 10, 2), today))
        self.assertTrue(freshness.is_recent_release(date(2026, 10, 1), today))
        self.assertFalse(freshness.is_recent_release(date(2026, 9, 30), today))
        self.assertFalse(freshness.is_recent_release(date(2026, 10, 3), today))
        self.assertFalse(freshness.is_recent_release(None, today))

    def test_code_only_release_does_not_change_freshness_snapshot(self):
        snapshot = {
            "schema": freshness.SCHEMA,
            "release": "release-before",
            "updated_at_utc": "2026-09-29T21:39:59Z",
            "counts": {"added_models": 1, "added_tools": 0, "updated_models": 0, "updated_tools": 0, "updated_records": 0},
            "entries": [{"record_type": "model", "action": "added", "record_id": "m", "name": "Model"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "freshness.json"
            freshness.write_snapshot(snapshot, path)
            steps = deploy_code_release.planned_steps("a" * 40, publication_state="data/release_state.json")
            self.assertFalse(any("catalog_master apply-plan" in step for step in steps))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), snapshot)

    def test_snapshot_normalizes_approximate_date_prefix(self):
        plan = {"changes": [{
            "kind": "create", "sheet": "Tools", "id": "preview",
            "row": {"Name": "Preview", "Approx Date": "≈2026-03", "Approx Precision": "month"},
        }]}
        item = freshness.snapshot_from_plan(plan, "2026-09-30T00:00:00Z")["entries"][0]
        self.assertEqual(item["release_date"], "2026-03")
        self.assertTrue(item["release_date_approx"])
