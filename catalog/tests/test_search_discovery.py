from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import ModelVersion


@override_settings(AIPEDIA_INDEXING_ALLOWED=True)
class SearchDiscoveryTests(TestCase):
    """Production-mode search signals, isolated from the Local protection."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_catalog_has_canonical_alternates_and_parameter_pages_are_noindex(self):
        response = self.client.get("/")
        self.assertContains(response, 'rel="canonical" href="https://aipediya.com/"')
        self.assertContains(response, 'hreflang="ru" href="https://aipediya.com/ru/"')
        self.assertNotContains(response, 'name="robots" content="noindex,follow"')
        filtered = self.client.get("/?q=gemini")
        self.assertContains(filtered, 'name="robots" content="noindex,follow"')
        # A unique filtered selection is never declared a copy of the root.
        self.assertNotContains(filtered, 'rel="canonical"')

    def test_plain_pagination_is_indexable_and_self_canonical(self):
        from catalog.views import INITIAL_PAGE_SIZE
        template = ModelVersion.objects.filter(published=True).first()
        need = INITIAL_PAGE_SIZE + 5 - ModelVersion.objects.filter(published=True).count()
        ModelVersion.objects.bulk_create([
            ModelVersion(
                family=template.family, name=f"Pagination model {number}", slug=f"pagination-model-{number}",
                version=f"Pagination model {number}", category=template.category, tasks=template.tasks,
                description=template.description, source=template.source, checked=template.checked,
            )
            for number in range(max(0, need))
        ])
        page = self.client.get("/ru/?page=2")
        self.assertEqual(page.context["page"].number, 2)
        self.assertContains(page, 'rel="canonical" href="https://aipediya.com/ru/?page=2"')
        self.assertContains(page, 'hreflang="en" href="https://aipediya.com/?page=2"')
        self.assertNotContains(page, 'name="robots" content="noindex,follow"')
        self.assertEqual(self.client.get("/ru/?page=1")["Location"], "/ru/")

    def test_published_cards_are_in_sitemap_and_render_in_server_html(self):
        model = ModelVersion.objects.filter(published=True, entry_type="model").first()
        sitemap = self.client.get("/sitemaps/ru.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, f"<loc>https://aipediya.com/ru/models/{model.slug}</loc>")
        detail = self.client.get(f"/models/{model.slug}")
        self.assertContains(detail, model.name)
        self.assertContains(detail, 'hreflang="en"')

    def test_robots_ads_and_indexnow_key_are_safe_while_unconfigured(self):
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Sitemap: https://aipediya.com/sitemap.xml")
        page = self.client.get("/ru/")
        self.assertNotContains(page, "adsbygoogle")
        self.assertEqual(self.client.get("/indexnow/not-configured.txt").status_code, 404)
