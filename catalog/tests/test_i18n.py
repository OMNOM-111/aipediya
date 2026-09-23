from django.core.management import call_command
from django.test import TestCase

from catalog.context import category_label, t
from catalog.i18n import (
    SUPPORTED_CODES, normalize_lang, parse_accept_language,
)
from catalog.models import ModelVersion


class RegistryTests(TestCase):
    def test_twenty_two_supported_languages(self):
        self.assertEqual(len(SUPPORTED_CODES), 22)
        for code in (
            "en", "ru", "zh-Hans", "es", "fr", "ar", "pt-BR", "de", "ja", "ko",
            "hi", "id", "tr", "vi", "it", "pl", "uk", "fa", "th", "nl", "bn", "zh-Hant",
        ):
            self.assertIn(code, SUPPORTED_CODES)

    def test_normalize_region_and_script_variants(self):
        self.assertEqual(normalize_lang("en-US"), "en")
        self.assertEqual(normalize_lang("ru-RU"), "ru")
        self.assertEqual(normalize_lang("zh"), "zh-Hans")
        self.assertEqual(normalize_lang("zh-CN"), "zh-Hans")
        self.assertEqual(normalize_lang("zh-TW"), "zh-Hant")
        self.assertEqual(normalize_lang("zh-Hant"), "zh-Hant")
        self.assertEqual(normalize_lang("pt"), "pt-BR")
        self.assertEqual(normalize_lang("pt-PT"), "pt-BR")
        self.assertEqual(normalize_lang("fr-CA"), "fr")
        self.assertIsNone(normalize_lang("zz"))
        self.assertIsNone(normalize_lang(""))

    def test_accept_language_respects_quality(self):
        self.assertEqual(parse_accept_language("fr-CH, fr;q=0.9, en;q=0.8"), "fr")
        self.assertEqual(parse_accept_language("de;q=0.7, es;q=0.9"), "es")
        self.assertEqual(parse_accept_language("xx, ja"), "ja")
        self.assertIsNone(parse_accept_language("xx-YY"))
        self.assertIsNone(parse_accept_language(""))

    def test_ui_resolution_and_english_fallback(self):
        self.assertEqual(t("models", "es"), "Modelos")
        self.assertEqual(t("models", "zh-Hans"), "模型")
        self.assertEqual(t("models", "ru"), "Моделей")
        self.assertEqual(t("models", "en"), "Models")
        # Acronym keys are intentionally omitted per locale and fall back to
        # English, never a raw key.
        self.assertEqual(t("github", "de"), "GitHub")
        self.assertEqual(t("api", "ja"), "API")
        self.assertEqual(t("unknown_key_xyz", "es"), "unknown_key_xyz")

    def test_category_label_resolution(self):
        labels = {"en": "Text", "ru": "Текст"}
        self.assertEqual(category_label("text", labels, "fr"), "Texte")
        self.assertEqual(category_label("text", labels, "ar"), "نص")
        self.assertEqual(category_label("text", labels, "ru"), "Текст")
        self.assertEqual(category_label("text", labels, "en"), "Text")
        # No translation yet -> English database label.
        self.assertEqual(category_label("text", labels, "de"), "Text")


class NegotiationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_url_param_selects_language(self):
        response = self.client.get("/", {"lang": "fr"})
        self.assertEqual(response.context["lang"], "fr")
        self.assertContains(response, 'lang="fr"')
        self.assertContains(response, "Modèles")

    def test_no_signal_defaults_to_english(self):
        response = self.client.get("/")
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, 'lang="en"')

    def test_accept_language_used_without_param_or_cookie(self):
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="es-ES,es;q=0.9,en;q=0.5")
        self.assertEqual(response.context["lang"], "es")

    def test_saved_cookie_outranks_accept_language(self):
        self.client.cookies["aipedia_lang"] = "de"
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="es")
        self.assertEqual(response.context["lang"], "de")

    def test_url_param_outranks_cookie(self):
        self.client.cookies["aipedia_lang"] = "de"
        response = self.client.get("/", {"lang": "ru"})
        self.assertEqual(response.context["lang"], "ru")

    def test_explicit_choice_is_remembered_in_cookie(self):
        response = self.client.get("/", {"lang": "ja"})
        self.assertEqual(response.cookies["aipedia_lang"].value, "ja")

    def test_unsupported_param_falls_back_to_english(self):
        response = self.client.get("/", {"lang": "zz"})
        self.assertEqual(response.context["lang"], "en")

    def test_country_hint_used_only_as_last_resort(self):
        response = self.client.get("/", HTTP_CF_IPCOUNTRY="BR")
        self.assertEqual(response.context["lang"], "pt-BR")
        # A stronger Accept-Language signal wins over the country hint.
        response = self.client.get("/", HTTP_CF_IPCOUNTRY="BR", HTTP_ACCEPT_LANGUAGE="ja")
        self.assertEqual(response.context["lang"], "ja")

    def test_russian_and_english_not_regressed(self):
        self.assertContains(self.client.get("/", {"lang": "ru"}), "Модели")
        self.assertContains(self.client.get("/", {"lang": "en"}), "Models")


class DirectionAndSeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_rtl_languages_set_dir_attribute(self):
        for code in ("ar", "fa"):
            response = self.client.get("/", {"lang": code})
            self.assertEqual(response.context["dir"], "rtl")
            self.assertContains(response, 'dir="rtl"')
        self.assertContains(self.client.get("/", {"lang": "en"}), 'dir="ltr"')

    def test_canonical_and_hreflang_alternates(self):
        response = self.client.get("/", {"lang": "fr"})
        self.assertContains(response, 'rel="canonical" href="https://aipediya.com/?lang=fr"')
        self.assertContains(response, 'hreflang="x-default" href="https://aipediya.com/?lang=en"')
        for code in SUPPORTED_CODES:
            self.assertContains(
                response, f'hreflang="{code}" href="https://aipediya.com/?lang={code}"'
            )

    def test_switcher_lists_every_language(self):
        response = self.client.get("/", {"lang": "en"})
        for code in SUPPORTED_CODES:
            self.assertContains(response, f'?lang={code}"')

    def test_switching_language_keeps_the_card(self):
        model = ModelVersion.objects.filter(published=True).first()
        response = self.client.get("/models/" + model.slug, {"lang": "en"})
        self.assertContains(
            response, f'hreflang="ar" href="https://aipediya.com/models/{model.slug}?lang=ar"'
        )

    def test_missing_dynamic_translation_falls_back_to_english(self):
        model = ModelVersion.objects.filter(published=True).first()
        model.description = {"en": "English only snapshot text"}
        model.save()
        response = self.client.get("/models/" + model.slug, {"lang": "de"})
        self.assertContains(response, "English only snapshot text")

    def test_sitemap_lists_localized_alternates(self):
        response = self.client.get("/sitemap.xml")
        body = response.content.decode()
        self.assertIn("xmlns:xhtml", body)
        self.assertIn('hreflang="x-default"', body)
        self.assertIn('hreflang="ar"', body)
        self.assertIn('hreflang="zh-Hant"', body)
