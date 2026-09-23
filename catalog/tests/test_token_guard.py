"""Regression tests for technical-token protection (the "1M -> metre" defect)."""
import json
from unittest import mock

from django.test import TestCase

from catalog import token_guard
from catalog.translation_providers import AzureTranslationProvider


class TokenGuardTests(TestCase):
    def test_detects_technical_tokens_but_not_plain_words(self):
        tokens = token_guard.find_tokens(
            "Context: 1M; GPT-5.2 uses gpt-5-pro via API at https://x.co/a with 128K and 7B; Text"
        )
        for expected in ["1M", "GPT-5.2", "gpt-5-pro", "API", "https://x.co/a", "128K", "7B"]:
            self.assertIn(expected, tokens)
        self.assertNotIn("Text", tokens)
        self.assertNotIn("Context", tokens)

    def test_html_roundtrip_is_lossless(self):
        source = "Context: 1M; Input: Text; Open weights: No. See https://x.co/a and GPT-5.2."
        self.assertEqual(token_guard.from_protected_html(token_guard.to_protected_html(source)), source)

    def test_tokens_survive_translation_of_surrounding_text(self):
        protected = token_guard.to_protected_html("Context: 1M; open weights: No")
        # Simulate a provider translating only the non-protected text.
        translated = protected.replace("Context", "Contexte").replace("open weights", "poids").replace("No", "Non")
        restored = token_guard.from_protected_html(translated)
        self.assertIn("1M", restored)
        self.assertIn("Contexte", restored)

    def test_missing_tokens_detects_a_dropped_unit(self):
        self.assertEqual(token_guard.missing_tokens("Context: 1M", "زمینه: ۱ متر"), ["1M"])
        self.assertEqual(token_guard.missing_tokens("Context: 1M", "Contexte : 1M"), [])


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class AzureProtectionTests(TestCase):
    def test_request_marks_tokens_notranslate_and_restores_them(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            body = json.loads(req.data.decode("utf-8"))
            captured["sent"] = body[0]["text"]
            captured["url"] = req.full_url
            # Simulate Azure: translate the non-protected text, keep spans verbatim.
            out = body[0]["text"].replace("Context", "Contexte")
            return FakeResponse(json.dumps([{"translations": [{"text": out}]}]).encode("utf-8"))

        provider = AzureTranslationProvider(key="dummy", region="eastus2")
        with mock.patch("catalog.translation_providers.urllib_request.urlopen", fake_urlopen):
            result = provider.translate_batch(["Context: 1M"], "fa")
        self.assertIn("textType=html", captured["url"])
        self.assertIn('translate="no"', captured["sent"])
        self.assertIn("1M", captured["sent"])
        self.assertEqual(result, ["Contexte: 1M"])
