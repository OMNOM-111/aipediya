import hashlib
import json
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "catalog" / "migrations" / "data" / "global_catalog_20260922.json"
EXPECTED_SHA256 = "5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2"


class GlobalCatalogReleasePayloadTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.raw = PAYLOAD.read_bytes()
        cls.payload = json.loads(cls.raw)

    def test_payload_is_exact_audited_artifact(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(self.payload["format"], "aipedia-natural-catalog-v1")
        self.assertEqual(
            self.payload["expected"],
            {
                "models_published": 763,
                "tools_published": 138,
                "model_versions_total": 901,
                "offers": 555,
                "accesses": 1205,
                "evaluations": 881,
                "sources": 343,
                "research_records": 2900,
                "research_revisions": 3590,
                "revisions": 4354,
                "publication_revisions": 3049,
                "tool_publication_revisions": 158,
            },
        )

    def test_natural_identifiers_are_unique(self):
        checks = {
            "model slug": [row["slug"] for row in self.payload["models"]],
            "tool slug": [row["slug"] for row in self.payload["tools"]],
            "source URL": [row["url"] for row in self.payload["sources"]],
            "research external ID": [
                row["external_id"] for row in self.payload["new_research_records"]
            ],
        }
        for label, values in checks.items():
            self.assertEqual(len(values), len(set(values)), label)

    def test_payload_contains_no_local_paths_or_secret_markers(self):
        lowered = self.raw.decode("utf-8").lower()
        for forbidden in (
            "c:\\\\users\\\\",
            "/users/",
            "secret_key",
            "private_key",
            "-----begin private key-----",
            "data/local/aipedia.sqlite3",
        ):
            self.assertNotIn(forbidden, lowered)
