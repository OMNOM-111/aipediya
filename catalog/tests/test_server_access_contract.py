"""Guard the documented, project-scoped Production entrypoint."""

import ast
import importlib.util
import runpy
import sqlite3
import sys
import tempfile
import types
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock


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

    def test_code_only_wrapper_does_not_send_a_catalog_plan(self):
        with mock.patch.dict(sys.modules, {"deploy_code_release": types.SimpleNamespace(inspect_archive=None)}):
            spec = importlib.util.spec_from_file_location("server_release_wrapper_test", ROOT / "tools/server.py")
            wrapper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wrapper)
        with mock.patch.object(wrapper, "remote_digest"), mock.patch.object(wrapper, "run") as run:
            run.return_value = types.SimpleNamespace(stdout="ok", stderr="", returncode=0)
            wrapper.deploy("/tmp/aipedia-code-abcdefabcdef-abcdefabcdef.zip", "a" * 64,
                           "b" * 40, True, None, "data/release_state.json")
        args = run.call_args.args[0]
        self.assertIn("--publication-state", args)
        self.assertIn("--dry-run", args)
        self.assertNotIn("--catalog-plan", args)

        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(wrapper, "remote_digest"), mock.patch.object(wrapper, "run") as run, \
                    mock.patch.object(wrapper, "REPORT_DIR", Path(temp)):
                run.return_value = types.SimpleNamespace(
                    stdout='{"status":"PASS","catalog_plan":null}', stderr="", returncode=0)
                wrapper.release_preflight("/tmp/aipedia-code-abcdefabcdef-abcdefabcdef.zip",
                                          "a" * 64, "b" * 40, None, "data/release_state.json")
            self.assertEqual(run.call_args.args[0][-2:], ["-", "data/release_state.json"])

    def test_code_only_preflight_scope_and_catalog_fingerprint(self):
        with mock.patch.dict(sys.modules, {"pwd": types.ModuleType("pwd")}):
            preflight = runpy.run_path(str(ROOT / "tools/server_release_preflight.py"))
        validate_scope = preflight["validate_release_scope"]
        validate_scope(14, "")
        validate_scope(13, "data/release/v013/catalog_plan.json")
        for sequence, plan in ((14, "data/release/old/catalog_plan.json"), (13, ""), (15, "")):
            with self.subTest(sequence=sequence, plan=plan), self.assertRaises(RuntimeError):
                validate_scope(sequence, plan)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.executescript("""
                    CREATE TABLE catalog_tool(slug TEXT, published INTEGER, public_number INTEGER,
                                              released TEXT, approx_released TEXT);
                    CREATE TABLE catalog_modelversion(slug TEXT, published INTEGER,
                        entry_type TEXT, public_number INTEGER);
                    CREATE TABLE catalog_offer(id INTEGER);
                    CREATE TABLE catalog_access(id INTEGER);
                    CREATE TABLE catalog_evaluation(public INTEGER);
                    CREATE TABLE catalog_source(id INTEGER);
                    CREATE TABLE catalog_benchmark(id INTEGER);
                    CREATE TABLE catalog_contenttranslation(id INTEGER, body TEXT);
                    INSERT INTO catalog_contenttranslation VALUES(1, 'before');
                """)
                db.commit()
            snapshot = preflight["snapshot"]
            before = snapshot(path)
            preflight["validate_code_only_catalog"](before, snapshot(path))
            with closing(sqlite3.connect(path)) as db:
                db.execute("UPDATE catalog_contenttranslation SET body='after' WHERE id=1")
                db.commit()
            after = snapshot(path)
            self.assertNotEqual(before["catalog_sha256"], after["catalog_sha256"])
            with self.assertRaisesRegex(RuntimeError, "Code-only trial changed catalog data"):
                preflight["validate_code_only_catalog"](before, after)
            with closing(sqlite3.connect(path)) as db:
                db.execute("ALTER TABLE catalog_contenttranslation ADD COLUMN extra TEXT")
                db.commit()
            self.assertNotEqual(after["catalog_sha256"], snapshot(path)["catalog_sha256"])
