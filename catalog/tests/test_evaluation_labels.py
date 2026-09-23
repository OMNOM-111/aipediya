import re

from django.test import TestCase

from catalog.context import t
from catalog.evaluation_labels import evaluation_label

CYRILLIC = re.compile(r"[\u0400-\u04FF]")


class EvaluationLabelTests(TestCase):
    def test_model_configuration_reuses_the_localized_model_label(self):
        self.assertEqual(evaluation_label("Модель", "en"), "Model")
        self.assertEqual(evaluation_label("Модель", "ru"), "Модель")
        # Reuses the existing 22-language "model" label (Ukrainian is also
        # "Модель", which is correct — the Cyrillic-leak check below covers the
        # locales that must never show Cyrillic).
        for lang in ("ko", "ja", "de", "ar", "uk"):
            self.assertEqual(evaluation_label("Модель", lang), t("model", lang))

    def test_controlled_russian_values_never_leak_to_other_locales(self):
        russian_values = ("Модель", "Точная версия / API snapshot", "как указано на leaderboard")
        for value in russian_values:
            for lang in ("en", "ko", "ja", "zh-Hans", "fr", "ar", "hi"):
                resolved = evaluation_label(value, lang)
                self.assertFalse(
                    CYRILLIC.search(resolved),
                    f"{value!r} in {lang} still shows Cyrillic: {resolved!r}",
                )

    def test_technical_values_pass_through_unchanged(self):
        for value in ("Standard", "Free tier", "Paid · Standard", "Off-peak", "long context"):
            for lang in ("ko", "en", "ru"):
                self.assertEqual(evaluation_label(value, lang), value)

    def test_api_token_is_preserved_in_translation(self):
        self.assertIn("API", evaluation_label("Точная версия / API snapshot", "ko"))

    def test_empty_values_are_returned_unchanged(self):
        self.assertEqual(evaluation_label("", "ko"), "")
        self.assertIsNone(evaluation_label(None, "ko"))
