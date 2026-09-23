import re

from django.test import TestCase

from catalog.public_text import PUBLIC_ENGLISH, public_text

CYRILLIC = re.compile(r"[\u0400-\u04FF]")


class PublicTextTests(TestCase):
    def test_controlled_russian_terms_fall_back_to_english_on_other_locales(self):
        cases = {
            "Самостоятельно": "Self-hosted",
            "Pro · от": "Pro · from",
            "видео; конфигурация требует уточнения": "video; configuration needs verification",
            "1000 страниц": "1000 pages",
            "песня": "song",
        }
        for source, english in cases.items():
            for lang in ("ko", "ja", "de", "ar", "fr", "hi", "en"):
                self.assertEqual(public_text(source, lang), english)

    def test_russian_locale_keeps_the_original_source_term(self):
        self.assertEqual(public_text("Самостоятельно", "ru"), "Самостоятельно")

    def test_unmapped_values_pass_through_unchanged(self):
        for value in ("OpenAI", "Anthropic", "Standard", "Free tier", "모델"):
            for lang in ("ko", "en", "ru"):
                self.assertEqual(public_text(value, lang), value)

    def test_english_mappings_are_free_of_cyrillic(self):
        for source, english in PUBLIC_ENGLISH.items():
            self.assertTrue(CYRILLIC.search(source), source)
            self.assertFalse(
                CYRILLIC.search(english),
                f"English mapping still contains Cyrillic: {source!r} -> {english!r}",
            )

    def test_non_string_values_are_returned_unchanged(self):
        self.assertIsNone(public_text(None, "ko"))
        self.assertEqual(public_text(42, "ko"), 42)
