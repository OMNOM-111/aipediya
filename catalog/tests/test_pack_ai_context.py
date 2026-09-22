from django.test import SimpleTestCase
from pathlib import Path
import hashlib
import importlib.util
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def load_pack():
    path = ROOT / "tools" / "pack_ai_context.py"
    spec = importlib.util.spec_from_file_location("pack_ai_context", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackAiContextTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pack = load_pack()

    def test_deny_secrets_and_local_sqlite(self):
        deny = self.pack.deny
        self.assertTrue(deny("data/local/aipedia.sqlite3"))
        self.assertTrue(deny("data/local/secret.key"))
        self.assertTrue(deny(".env"))
        self.assertTrue(deny("deploy/.env.production"))
        self.assertTrue(deny("logs/local-launcher.log"))
        self.assertTrue(deny("secret.key"))
        self.assertFalse(deny("AGENTS.md"))
        self.assertFalse(deny("docs/EXECUTION_STATE.md"))
        self.assertFalse(deny("tools/pack_ai_context.py"))
        self.assertIsNotNone(self.pack.copy_allowed("tools/pack_ai_context.py"))

    def test_parse_production_commit_and_state_stamp(self):
        release = (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
        commit = self.pack.parse_production_commit(release)
        self.assertTrue(commit)
        self.assertGreaterEqual(len(commit), 7)
        state = (ROOT / "docs" / "EXECUTION_STATE.md").read_text(encoding="utf-8")
        self.assertTrue(self.pack.parse_state_updated(state))
        evidence = self.pack.parse_evidence_paths(state)
        self.assertIn("tools/pack_ai_context.py", evidence)

    def test_pack_writes_three_layers_and_excludes_secrets(self):
        manifest = self.pack.pack()
        md_path = ROOT / "AI_CONTEXT" / "AI_CONTEXT.md"
        zip_path = ROOT / "AI_CONTEXT" / "AI_CONTEXT.zip"
        self.assertTrue(md_path.is_file())
        self.assertTrue(zip_path.is_file())
        text = md_path.read_text(encoding="utf-8")
        self.assertIn("Три слоя: Local / GitHub / Production", text)
        self.assertIn("Незакоммиченные изменения", text)
        self.assertIn("Следующий шаг", text)
        self.assertIn("docs/EXECUTION_STATE.md", text)
        self.assertFalse(manifest["production_live_checked"])
        self.assertEqual(manifest["sha256_zip"], hashlib.sha256(zip_path.read_bytes()).hexdigest())
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        self.assertIn("AI_CONTEXT.md", names)
        self.assertIn("sources/AGENTS.md", names)
        self.assertIn("sources/tools/pack_ai_context.py", names)
        self.assertTrue(any(name.endswith("install-shortcuts.ps1") for name in names))
        for name in names:
            self.assertFalse(self.pack.deny(name), name)
            self.assertFalse(name.endswith(".sqlite3"), name)
            self.assertFalse(name.endswith(".env"), name)
            self.assertNotIn("secret.key", name)
        self.assertFalse(any("data/research/" in name for name in names))
