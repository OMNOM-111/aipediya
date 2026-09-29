"""Full-page language-switch contracts, complementing browser menu clicks."""

from urllib.parse import parse_qs, urlsplit

from django.core.management import call_command
from django.test import TestCase

from catalog.i18n import SUPPORTED_CODES, direction
from catalog.locale_urls import localize
from catalog.models import ModelVersion, Tool


class LanguageSwitchTests(TestCase):
    EXPECTED_CODES = (
        "en", "ru", "zh-Hans", "es", "fr", "ar", "pt-BR", "de", "ja", "ko", "hi",
        "id", "tr", "vi", "it", "pl", "uk", "fa", "th", "nl", "bn", "zh-Hant",
    )

    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        cls.model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        cls.tool = Tool.objects.filter(published=True).first()
        if cls.tool is None:
            from catalog.tests.test_global_search_discovery import ensure_tool
            cls.tool = ensure_tool()

    def test_every_root_and_menu_link_reaches_a_rendered_page(self):
        self.assertEqual(SUPPORTED_CODES, self.EXPECTED_CODES)
        for neutral in ("/", "/tools/"):
            for code in SUPPORTED_CODES:
                with self.subTest(page=neutral, locale=code):
                    response = self.client.get(localize(neutral, code), follow=True)
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(response.redirect_chain)
                    self.assertEqual(response.context["lang"], code)
                    self.assertContains(response, f'<html lang="{code}" dir="{direction(code)}">')
                    self.assertContains(response, 'id="model-rows"')
                    links = response.context["language_links"]
                    self.assertEqual([item[0] for item in links], list(SUPPORTED_CODES))
                    for target, _, href in links:
                        self.assertEqual(href, localize(neutral, target))

    def test_every_menu_link_preserves_entity_and_safe_query_only(self):
        self.assertIsNotNone(self.model)
        self.assertIsNotNone(self.tool)
        for neutral in (f"/models/{self.model.slug}", f"/tools/{self.tool.slug}"):
            for code in SUPPORTED_CODES:
                with self.subTest(page=neutral, locale=code):
                    response = self.client.get(localize(neutral, code) + "?q=alpha&sort=name_asc&page=2&tab=checks")
                    self.assertEqual(response.status_code, 200)
                    links = response.context["language_links"]
                    self.assertEqual(len(links), 22)
                    for target, _, href in links:
                        parsed = urlsplit(href)
                        self.assertEqual(parsed.path, localize(neutral, target))
                        self.assertEqual(parse_qs(parsed.query), {
                            "q": ["alpha"], "sort": ["name_asc"],
                            "page": ["2"], "tab": ["checks"],
                        })
                        if code == "en":
                            final = self.client.get(href, follow=True)
                            self.assertEqual(final.status_code, 200)
                            self.assertFalse(final.redirect_chain)
                            self.assertEqual(final.context["lang"], target)

    def test_switcher_drops_legacy_and_fragment_parameters(self):
        # A legacy/fragment request cannot contain a full-page menu. Check the
        # switcher builder directly with the same request state.
        from django.test import RequestFactory
        from catalog.locale_urls import switch_url
        request = RequestFactory().get("/es/?q=alpha&sort=name_asc&page=2&lang=es&kind=tool&partial=rows")
        request.aipedia_neutral_path = "/"
        for code in SUPPORTED_CODES:
            with self.subTest(locale=code):
                href = switch_url(request, code)
                self.assertEqual(urlsplit(href).path, localize("/", code))
                self.assertEqual(parse_qs(urlsplit(href).query), {
                    "q": ["alpha"], "sort": ["name_asc"], "page": ["2"],
                })
