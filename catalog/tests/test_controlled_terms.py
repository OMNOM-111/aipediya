import re

from django.test import TestCase

from catalog.i18n import SUPPORTED_CODES
from catalog.public_text import PUBLIC_ENGLISH, public_text
from catalog.controlled_terms import localize_controlled

CYRILLIC = re.compile(r"[\u0400-\u04FF]")
CYRILLIC_SCRIPT = {"ru", "uk"}


class ControlledTermsTests(TestCase):
    def test_every_controlled_value_localized_on_every_supported_locale(self):
        for value in PUBLIC_ENGLISH:
            for lang in SUPPORTED_CODES:
                if lang == "ru":
                    continue
                out = localize_controlled(value, lang)
                self.assertIsNotNone(out, f"{value!r} has no {lang} translation")
                if lang not in CYRILLIC_SCRIPT:
                    self.assertFalse(
                        CYRILLIC.search(out),
                        f"{value!r} -> {out!r} still shows Cyrillic in {lang}",
                    )

    def test_ukrainian_is_translated_not_the_russian_source(self):
        self.assertEqual(localize_controlled("Самостоятельно", "uk"), "Власний хостинг")
        self.assertNotEqual(localize_controlled("песня", "uk"), "песня")

    def test_brands_plans_and_technical_ids_are_preserved(self):
        self.assertIn("Pro", localize_controlled("Pro · от", "ko"))
        self.assertIn("API", localize_controlled("Прямой API · с аудио · 1080p", "ja"))
        self.assertIn("1080p", localize_controlled("Прямой API · с аудио · 1080p", "ja"))
        self.assertIn("4K", localize_controlled("Прямой API · с аудио · 4K", "ar"))
        self.assertIn("Hugging Face", localize_controlled("Самостоятельно / Hugging Face", "de"))
        self.assertIn("Pay-as-you-go", localize_controlled(
            "Pay-as-you-go · Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки.", "th"))

    def test_public_text_prefers_localization_over_english_fallback(self):
        korean = public_text("Самостоятельно", "ko")
        self.assertEqual(korean, "자체 호스팅")
        self.assertNotIn(korean, {"Самостоятельно", "Self-hosted"})
        self.assertEqual(public_text("песня", "ja"), "曲")

    def test_russian_locale_and_unknown_values_are_unchanged(self):
        self.assertEqual(public_text("Самостоятельно", "ru"), "Самостоятельно")
        self.assertIsNone(localize_controlled("OpenAI", "ko"))
        self.assertEqual(public_text("OpenAI", "ko"), "OpenAI")
        self.assertEqual(public_text("Standard", "ko"), "Standard")
