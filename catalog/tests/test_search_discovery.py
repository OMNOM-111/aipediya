from django.core.management import call_command
from django.test import TestCase

from catalog.models import ModelVersion


class SearchDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_catalog_has_canonical_alternates_and_parameter_pages_are_noindex(self):
        response = self.client.get("/?lang=en")
        self.assertContains(response, 'rel="canonical" href="https://aipediya.com/?lang=en"')
        self.assertContains(response, 'hreflang="ru" href="https://aipediya.com/?lang=ru"')
        self.assertNotContains(response, 'name="robots" content="noindex,follow"')
        filtered = self.client.get("/?lang=en&q=gemini")
        self.assertContains(filtered, 'name="robots" content="noindex,follow"')

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
        page = self.client.get("/?lang=en&page=2")
        self.assertEqual(page.context["page"].number, 2)
        self.assertContains(page, 'rel="canonical" href="https://aipediya.com/?lang=en&amp;page=2"')
        self.assertNotContains(page, 'name="robots" content="noindex,follow"')
        duplicate = self.client.get("/?lang=en&page=1")
        self.assertContains(duplicate, 'name="robots" content="noindex,follow"')

    def test_published_cards_are_in_sitemap_and_render_in_server_html(self):
        model = ModelVersion.objects.filter(published=True).first()
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, f"/models/{model.slug}?lang=ru")
        detail = self.client.get(f"/models/{model.slug}?lang=en")
        self.assertContains(detail, model.name)
        self.assertContains(detail, f"{model.name}")
        self.assertContains(detail, 'hreflang="en"')

    def test_robots_ads_and_indexnow_key_are_safe_while_unconfigured(self):
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Sitemap: https://aipediya.com/sitemap.xml")
        page = self.client.get("/?lang=ru")
        self.assertNotContains(page, "adsbygoogle")
        self.assertEqual(self.client.get("/indexnow/not-configured.txt").status_code, 404)
