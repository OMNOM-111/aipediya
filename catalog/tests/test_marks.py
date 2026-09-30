from django.test import SimpleTestCase, TestCase
from django.core.management import call_command

from catalog.marks import ALIASES, MARK_DIR, PUBLISHED_DEVELOPERS, RECORD_ALIASES, mark_for


class MarkFileTests(SimpleTestCase):
    def test_every_alias_resolves_to_a_file(self):
        self.assertGreaterEqual(len(ALIASES), 34)
        for name, stem in ALIASES.items():
            self.assertTrue(list(MARK_DIR.glob(stem + ".*")), name)
            mark = mark_for(name)
            self.assertIsNotNone(mark, name)
            self.assertTrue(mark["svg"] or mark["file"], name)

    def test_published_developers_all_have_marks(self):
        self.assertEqual(len(PUBLISHED_DEVELOPERS), 36)
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

    def test_release_019_uses_only_the_official_target_marks(self):
        self.assertEqual(mark_for("Anthropic")["svg"], mark_for("Anthropic", "claude-sonnet-5-5-899c1979")["svg"])
        self.assertEqual(mark_for("ElevenLabs")["svg"], mark_for("ElevenLabs", "eleven-v4-1cc3a926")["svg"])
        self.assertEqual(mark_for("ElevenLabs")["svg"], mark_for("ElevenLabs", "eleven-v4-turbo-6a02a110")["svg"])
        for slug in ("holo4-27b-62d1091f", "holo4-35b-a3b-b9f93a3e", "holotron4-30b-a3b-c0c87f8d"):
            self.assertEqual(mark_for("H Company", slug)["file"], "marks/hcompany.png")
        self.assertEqual(RECORD_ALIASES, {"cue-77457549": "cue"})
        self.assertIn("<title>Cue</title>", str(mark_for("Manus", "cue-77457549")["svg"]))
        self.assertEqual(mark_for("Manus", "manus-0214c7c8")["file"], "marks/manus.png")
        self.assertNotEqual(
            mark_for("Manus", "cue-77457549")["svg"],
            mark_for("Manus", "manus-0214c7c8")["svg"],
        )


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
