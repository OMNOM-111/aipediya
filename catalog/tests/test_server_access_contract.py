"""Guard the documented, project-scoped Production entrypoint."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ServerAccessContractTests(unittest.TestCase):
    def test_canonical_wrapper_and_scope(self):
        wrapper = ROOT / "tools/server.py"
        self.assertTrue(wrapper.is_file())
        tree = ast.parse(wrapper.read_text(encoding="utf-8"))
        assignments = {
            target.id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
            and target.id in {"ALIAS", "REMOTE_ROOT", "SERVICE"}
        }
        self.assertEqual(assignments, {
            "ALIAS": "aipediya-prod", "REMOTE_ROOT": "/srv/aipedia", "SERVICE": "aipedia"
        })
        source = wrapper.read_text(encoding="utf-8")
        self.assertIn('"ssh", ALIAS', source)
        self.assertIn('"scp", "-B"', source)
        self.assertIn("remote_digest(remote, digest)", source)
        self.assertIn("release-preflight", source)

    def test_documents_prevent_credential_rediscovery(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        release = (ROOT / "docs/RELEASE.md").read_text(encoding="utf-8")
        for required in ("python tools/server.py preflight", "aipediya-prod", "не искать"):
            self.assertIn(required, agents + release)
        self.assertIn("Manual/Ask and rerun the same server command", agents)
        self.assertIn("/srv/aipedia", release)
        self.assertIn("`aipedia`", release)

    def test_alias_template_contains_no_secret_material(self):
        config = (ROOT / "deploy/aipediya-prod.ssh_config.example").read_text(encoding="utf-8")
        self.assertIn("Host aipediya-prod", config)
        self.assertIn("StrictHostKeyChecking yes", config)
        self.assertIn("UserKnownHostsFile ~/.ssh/known_hosts", config)
        self.assertIn("IdentityFile ~/.ssh/codex_stratforge_stage9", config)
        for forbidden in ("BEGIN OPENSSH PRIVATE KEY", "BEGIN RSA PRIVATE KEY",
                          "StrictHostKeyChecking no", "UserKnownHostsFile /dev/null",
                          "AIPEDIA_SECRET_KEY=", "CLOUDFLARE_TOKEN=", ".env="):
            self.assertNotIn(forbidden, config)
