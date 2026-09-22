from django.test import SimpleTestCase, TestCase
from django.core.management import call_command

from catalog.marks import ALIASES, MARK_DIR, PUBLISHED_DEVELOPERS, mark_for


class MarkFileTests(SimpleTestCase):
    def test_every_alias_resolves_to_a_file(self):
        self.assertGreaterEqual(len(ALIASES), 34)
        for name, stem in ALIASES.items():
            self.assertTrue(list(MARK_DIR.glob(stem + ".*")), name)
            mark = mark_for(name)
            self.assertIsNotNone(mark, name)
            self.assertTrue(mark["svg"] or mark["file"], name)

    def test_published_developers_all_have_marks(self):
        self.assertEqual(len(PUBLISHED_DEVELOPERS), 34)
        for name in PUBLISHED_DEVELOPERS:
            mark = mark_for(name)
            self.assertIsNotNone(mark, name)
            self.assertTrue(mark["svg"] or mark["file"], name)

    def test_xai_and_zai_name_variants(self):
        self.assertIsNotNone(mark_for("xAI"))
        self.assertIsNotNone(mark_for("SpaceXAI / xAI (extra note)"))
        self.assertIsNotNone(mark_for("Z.ai"))
        self.assertEqual(mark_for("xAI")["svg"] or mark_for("xAI")["file"],
                         mark_for("SpaceXAI / xAI (бренд документации)")["svg"]
                         or mark_for("SpaceXAI / xAI (бренд документации)")["file"])

    def test_unknown_developer_keeps_the_letter_fallback(self):
        self.assertIsNone(mark_for("No Such Lab"))
        self.assertIsNone(mark_for(""))


class MarkPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_catalog_and_panel_show_developer_marks(self):
        page = self.client.get("/")
        self.assertContains(page, "model-mark has-logo")
        self.assertContains(page, "#1976D2")
        self.assertContains(page, "#FA520F")
        panel = self.client.get("/models/gemini-2-5-pro")
        self.assertContains(panel, "panel-mark")
        self.assertContains(panel, "#1976D2")
        self.assertNotContains(panel, ">G</span>")
