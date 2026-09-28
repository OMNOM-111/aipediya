import copy
from django.test import SimpleTestCase

from tools.release_history import load, validate
from tools.finalize_release_history import finalize


class ReleaseHistoryTests(SimpleTestCase):
    def test_baseline_has_reserved_thirteen_and_matching_pointers(self):
        registry = load()
        self.assertEqual(validate(registry), [])
        cards = [row for row in registry["product_history"]["milestones"] if row.get("release_sequence")]
        self.assertEqual([row["release_sequence"] for row in cards], list(range(1, 14)))
        self.assertEqual(cards[-1]["app_version"], "v0.13.0")
        self.assertEqual(registry["product_history"]["current_local"]["release_sequence"], 12)
        self.assertEqual(registry["product_history"]["current_production"]["release_sequence"], 12)

    def test_gate_rejects_missing_review_qa_owner_and_stale_html(self):
        registry = load()
        candidate = copy.deepcopy(registry["product_history"]["milestones"][-2])
        candidate.update(release_id="release-v014", release_sequence=14, app_version="v0.14.0",
                         revision="a" * 40, release_tag="release-v014", production_verified=False,
                         production_released=False, owner_approved=False, local_verified=False,
                         progress="in_progress", changes=[], qa={})
        registry["product_history"]["milestones"].append(candidate)
        registry["entries"].append({"release_id": "release-v014", "release_sequence": 14,
                                    "app_version": "v0.14.0"})
        registry["product_history"]["current_local"].update(
            release_id="release-v014", release_sequence=14, app_version="v0.14.0")
        errors = validate(registry, "release-v014", "a" * 40, "stale")
        self.assertTrue(any("owner_approved" in item for item in errors))
        self.assertTrue(any("Local QA" in item for item in errors))
        self.assertTrue(any("stale" in item for item in errors))

    def test_finalization_updates_same_card_after_health_and_qa(self):
        registry = load()
        prior = next(row for row in registry["product_history"]["milestones"]
                     if row.get("release_sequence") == 12)
        prior.update(production_released=True, production_verified=True, progress="done")
        registry["product_history"]["current_production"].update(
            release_id=prior["release_id"], release_sequence=12,
            app_version=prior["app_version"], revision=prior["revision"],
            release_tag=prior["release_tag"])
        card = next(row for row in registry["product_history"]["milestones"]
                    if row.get("release_sequence") == 13)
        card.update(revision="a" * 40, release_tag="release-v013", local_verified=True,
                    owner_approved=True, production_verified=False,
                    production_released=False, progress="review", open=True,
                    qa={"local": "PASS"}, changes=["New version"])
        next(entry for entry in registry["entries"] if entry["release_id"] == card["release_id"]).update(
            stage="review", revision="a" * 40)
        registry["product_history"]["current_local"].update(
            release_id=card["release_id"], release_sequence=13, app_version="v0.13.0",
            revision="a" * 40, release_tag="release-v013")
        with self.assertRaisesRegex(ValueError, "healthz"):
            finalize(copy.deepcopy(registry), card["release_id"], "b" * 40,
                     "docs/history/report.md", "backup.db", "QA PASS", "old release")
        result = finalize(registry, card["release_id"], "b" * 40,
                          "docs/history/report.md", "backup.db", "QA PASS", "b" * 40)
        self.assertEqual(result["product_history"]["current_production"]["release_sequence"], 13)
        self.assertEqual(len([x for x in result["product_history"]["milestones"]
                              if x["release_id"] == card["release_id"]]), 1)
