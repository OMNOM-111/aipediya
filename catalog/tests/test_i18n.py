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

    # ADR D-2026-09-25-locale-paths: the address alone decides the language.
    # Cookies, Accept-Language and country headers never change an explicit
    # URL; old ?lang= links answer one permanent redirect.

    def test_locale_path_selects_language(self):
        response = self.client.get("/fr/")
        self.assertEqual(response.context["lang"], "fr")
        self.assertContains(response, 'lang="fr"')
        self.assertContains(response, "Modèles")

    def test_legacy_lang_param_redirects_permanently_once(self):
        response = self.client.get("/", {"lang": "fr"})
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/fr/")
        final = self.client.get("/", {"lang": "fr"}, follow=True)
        self.assertEqual(len(final.redirect_chain), 1)
        self.assertEqual(final.context["lang"], "fr")

    def test_no_signal_defaults_to_english(self):
        response = self.client.get("/")
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, 'lang="en"')

    def test_accept_language_cookie_and_country_never_change_explicit_url(self):
        self.client.cookies["aipedia_lang"] = "de"
        for path, lang in (("/", "en"), ("/ru/", "ru"), ("/ja/", "ja")):
            response = self.client.get(path, HTTP_ACCEPT_LANGUAGE="es", HTTP_CF_IPCOUNTRY="BR")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["lang"], lang)
            self.assertNotIn("Cookie", response.get("Vary", ""))
            self.assertNotIn("Accept-Language", response.get("Vary", ""))

    def test_server_never_sets_a_language_cookie(self):
        response = self.client.get("/ja/")
        self.assertNotIn("aipedia_lang", response.cookies)

    def test_unsupported_param_falls_back_to_english(self):
        response = self.client.get("/", {"lang": "zz"}, follow=True)
        self.assertEqual(response.context["lang"], "en")

    def test_russian_and_english_not_regressed(self):
        self.assertContains(self.client.get("/ru/"), "Модели")
        self.assertContains(self.client.get("/"), "Models")


class DirectionAndSeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_rtl_languages_set_dir_attribute(self):
        for code in ("ar", "fa"):
            response = self.client.get("/", {"lang": code}, follow=True)
            self.assertEqual(response.context["dir"], "rtl")
            self.assertContains(response, 'dir="rtl"')
        self.assertContains(self.client.get("/", {"lang": "en"}, follow=True), 'dir="ltr"')

    def test_canonical_and_hreflang_alternates(self):
        from catalog.readiness import ready_locales
        model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        ready = ready_locales(model)
        self.assertIn("en", ready)
        with self.settings(AIPEDIA_INDEXING_ALLOWED=True):
            response = self.client.get("/models/" + model.slug)
        self.assertContains(response, f'rel="canonical" href="https://aipediya.com/models/{model.slug}"')
        self.assertContains(response, f'hreflang="x-default" href="https://aipediya.com/models/{model.slug}"')
        for code in ready:
            prefix = "" if code == "en" else "/" + code.lower()
            self.assertContains(response, f'hreflang="{code}" href="https://aipediya.com{prefix}/models/{model.slug}"')

    def test_switcher_lists_every_language(self):
        response = self.client.get("/")
        for code in SUPPORTED_CODES:
            prefix = "/" if code == "en" else f"/{code.lower()}/"
            self.assertContains(response, f'href="{prefix}" hreflang="{code}"')

    def test_switching_language_keeps_the_card(self):
        model = ModelVersion.objects.filter(published=True).first()
        response = self.client.get("/models/" + model.slug)
        self.assertContains(response, f'href="/ar/models/{model.slug}" hreflang="ar"')

    def test_missing_dynamic_translation_falls_back_to_english(self):
        model = ModelVersion.objects.filter(published=True).first()
        model.description = {"en": "English only snapshot text"}
        model.save()
        response = self.client.get("/models/" + model.slug, {"lang": "de"}, follow=True)
        self.assertContains(response, "English only snapshot text")

    def test_sitemap_lists_localized_alternates(self):
        index = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("<sitemapindex", index)
        self.assertIn("https://aipediya.com/sitemaps/en.xml", index)
        body = self.client.get("/sitemaps/en.xml").content.decode()
        self.assertIn("xmlns:xhtml", body)
        self.assertIn('hreflang="x-default"', body)
        self.assertIn('hreflang="ar"', body)
        self.assertIn('hreflang="zh-Hant"', body)
