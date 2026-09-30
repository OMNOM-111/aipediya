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
