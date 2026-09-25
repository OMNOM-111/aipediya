from datetime import date

from django.test import TestCase

from catalog.models import (
    ModelFamily, ModelVersion, Organization, Source, Tool,
)


class PermanentNumberAndDateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(
            title="Fixture", publisher="Fixture", url="https://example.com/releases"
        )
        cls.org = Organization.objects.create(
            name="Fixture", source=cls.source, checked=date(2026, 1, 1)
        )
        cls.family = ModelFamily.objects.create(name="Fixture", developer=cls.org)

    def model(self, name, released=None, approx=None, precision=""):
        return ModelVersion.objects.create(
            name=name, slug=name.lower(), family=self.family, version="1",
            released=released, approx_released=approx, approx_precision=precision,
            source=self.source, checked=date(2026, 1, 1),
        )

    def test_new_published_model_takes_the_next_free_number(self):
        first = self.model("Alpha", date(2024, 1, 1))
        second = self.model("Bravo", date(2023, 1, 1))
        first.refresh_from_db(); second.refresh_from_db()
        self.assertEqual((first.public_number, second.public_number), (1, 2))
        third = self.model("Charlie")
        third.refresh_from_db()
        self.assertEqual(third.public_number, 3)

    def test_approximate_date_renders_with_prefix_and_class(self):
        self.model("Aprx", approx=date(2024, 9, 1), precision="month")
        response = self.client.get("/", {"lang": "en"}, follow=True)
        html = response.content.decode()
        self.assertIn("release-date approx", html)
        self.assertIn("\u2248 Sep 2024", html)

    def test_approximate_day_precision_shows_full_date(self):
        self.model("Aprx", approx=date(2024, 9, 21), precision="day")
        response = self.client.get("/", {"lang": "en"}, follow=True)
        self.assertIn("\u2248 Sep 21, 2024", response.content.decode())

    def test_rows_expose_slug_and_name_link_for_whole_row_click(self):
        self.model("Alpha", date(2024, 1, 1))
        html = self.client.get("/").content.decode()
        row = html.split('data-slug="alpha"', 1)[1].split("</tr>", 1)[0]
        self.assertIn("model-name", row)

    def test_tools_default_sort_is_newest_first(self):
        Tool.objects.create(
            name="Newer Tool", slug="newer-tool", version="1", developer=self.org,
            category="coding_agent", purposes=["coding"], released=date(2025, 1, 1),
            source=self.source, checked=date(2026, 1, 1),
        )
        Tool.objects.create(
            name="Older Tool", slug="older-tool", version="1", developer=self.org,
            category="coding_agent", purposes=["coding"], released=date(2020, 1, 1),
            source=self.source, checked=date(2026, 1, 1),
        )
        response = self.client.get("/", {"kind": "tool"}, follow=True)
        self.assertEqual(response.context["sort"], "release_desc")
        self.assertEqual(
            [tool.slug for tool in response.context["page"]],
            ["newer-tool", "older-tool"],
        )
