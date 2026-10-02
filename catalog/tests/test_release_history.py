import copy
from django.test import SimpleTestCase

from tools.release_history import load, validate
from tools.finalize_release_history import finalize


class ReleaseHistoryTests(SimpleTestCase):
    def test_twenty_two_is_the_owner_approved_candidate(self):
        registry = load()
        self.assertEqual(validate(registry), [])
        cards = [row for row in registry["product_history"]["milestones"] if row.get("release_sequence")]
        self.assertEqual([row["release_sequence"] for row in cards], list(range(1, 23)))
        self.assertEqual(cards[-1]["app_version"], "v0.19.0")
        self.assertEqual(registry["product_history"]["current_local"]["release_sequence"], 22)
        self.assertEqual(registry["product_history"]["current_production"]["release_sequence"], 21)
        self.assertTrue(next(row for row in cards if row["release_sequence"] == 18)["production_verified"])
        self.assertFalse(next(row for row in cards if row["release_sequence"] == 17)["production_verified"])
        self.assertTrue(next(row for row in cards if row["release_sequence"] == 20)["production_verified"])
        self.assertTrue(next(row for row in cards if row["release_sequence"] == 21)["production_verified"])
        self.assertFalse(cards[-1]["production_verified"])
        self.assertEqual((cards[-1]["progress"], cards[-1]["local_verified"], cards[-1]["owner_approved"]),
               ("review", True, True))

    def test_gate_rejects_missing_review_qa_owner_and_stale_html(self):
        registry = load()
        previous = next(row for row in registry["product_history"]["milestones"]
                        if row.get("release_sequence") == 19)
        registry["product_history"]["current_production"].update(
            release_id=previous["release_id"], release_sequence=19,
            app_version=previous["app_version"], revision=previous["revision"],
            release_tag=previous["release_tag"])
        candidate = next(row for row in registry["product_history"]["milestones"]
                         if row.get("release_sequence") == 20)
        candidate.update(revision="a" * 40, production_verified=False,
                         production_released=False, owner_approved=False, local_verified=False,
                         progress="in_progress", changes=[], qa={})
        errors = validate(registry, candidate["release_id"], "a" * 40, "stale")
        self.assertTrue(any("owner_approved" in item for item in errors))
        self.assertTrue(any("Local QA" in item for item in errors))
        self.assertTrue(any("stale" in item for item in errors))

    def test_finalization_updates_same_card_after_health_and_qa(self):
        registry = load()
        card = next(row for row in registry["product_history"]["milestones"]
                    if row.get("release_sequence") == 22)
        registry["product_history"]["current_local"].update(
            release_id=card["release_id"], release_sequence=22,
            app_version=card["app_version"], release_tag=card["release_tag"])
        card.update(revision="a" * 40, local_verified=True,
                    owner_approved=True, production_verified=False,
                    production_released=False, progress="review", open=True,
                    qa={"local": "PASS"}, changes=["New version"])
        next(entry for entry in registry["entries"] if entry["release_id"] == card["release_id"]).update(
            stage="review", revision="a" * 40)
        with self.assertRaisesRegex(ValueError, "healthz"):
            finalize(copy.deepcopy(registry), card["release_id"], "b" * 40,
                     "docs/history/report.md", "backup.db", "QA PASS", "old release")
        result = finalize(registry, card["release_id"], "b" * 40,
                          "docs/history/report.md", "backup.db", "QA PASS", "b" * 40)
        self.assertEqual(result["product_history"]["current_production"]["release_sequence"], 22)
        self.assertEqual(result["product_history"]["production_evidence"], "docs/history/report.md")
        self.assertEqual(next(row for row in result["entries"]
                              if row["release_id"] == card["release_id"])["status"], "RELEASED")
        self.assertEqual(len([x for x in result["product_history"]["milestones"]
                              if x["release_id"] == card["release_id"]]), 1)
