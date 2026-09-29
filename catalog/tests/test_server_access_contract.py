"""Guard the documented, project-scoped Production entrypoint."""

import ast
import copy
import importlib.util
import io
import json
import runpy
import sqlite3
import sys
import tempfile
import types
import unittest
from contextlib import closing, redirect_stdout
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
        validate_scope(15, "")
        validate_scope(13, "data/release/v013/catalog_plan.json")
        validate_scope(16, "data/release/daily-catalog-20260929/catalog_plan.json")
        validate_scope(17, "")
        validate_scope(18, "data/release/daily-catalog-20260930/catalog_plan.json")
        for sequence, plan in ((14, "data/release/old/catalog_plan.json"),
                               (15, "data/release/old/catalog_plan.json"), (13, ""), (16, "")):
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

    def test_catalog_plan_trial_validation_is_plan_derived(self):
        with mock.patch.dict(sys.modules, {"pwd": types.ModuleType("pwd")}):
            preflight = runpy.run_path(str(ROOT / "tools/server_release_preflight.py"))
        validate = preflight["validate_catalog_plan_trial"]
        base_counts = {
            "integrity": "ok", "foreign_keys": 0,
            "numbers_continuous": True, "model_numbers_continuous": True,
            "published_models": 1, "numbered_models": 1,
            "published_tools": 0, "numbered_tools": 0,
            "evaluation_rows": 0, "evaluation_public": 0,
            "source_rows": 1, "benchmark_rows": 0,
        }
        before = {
            **base_counts,
            "model_rows": {"m1": {"slug": "m1", "public_number": 1, "name": "M1"}},
            "tools": {}, "offers": {1: {"id": 1, "model_id": 1}},
            "accesses": {1: {"id": 1, "model_id": 1, "service_id": 1}},
            "factual_tables": {
                "catalog_modelversion": {1: {"id": 1, "slug": "m1", "public_number": 1}},
                "catalog_tool": {}, "catalog_offer": {1: {"id": 1}}, "catalog_access": {1: {"id": 1}},
                "catalog_source": {1: {"id": 1}}, "catalog_organization": {1: {"id": 1}},
                "catalog_modelfamily": {1: {"id": 1}}, "catalog_service": {1: {"id": 1}},
            },
        }
        create_plan = {
            "schema": "aipedia-catalog-plan/1", "release": "future", "counts": {"create": 2},
            "final_published": {"Models": ["m1", "m2"], "Tools": ["tool1"]},
            "final_numbers": {"Models": {"m1": 1, "m2": 2}, "Tools": {"tool1": 1}},
            "changes": [
                {"kind": "create", "sheet": "Models", "id": "m2", "row": {"Origin Countries": "US"},
                 "offers": [], "access": []},
                {"kind": "create", "sheet": "Tools", "id": "tool1", "row": {},
                 "offers": [{"Key": "offer-new"}], "access": [{"Key": "access-new"}]},
            ],
        }
        after = copy.deepcopy(before)
        after.update({"published_models": 2, "numbered_models": 2, "published_tools": 1, "numbered_tools": 1,
                      "source_rows": 2})
        after["model_rows"] = {**before["model_rows"], "m2": {"slug": "m2"}, "tool1": {"slug": "tool1"}}
        after["tools"] = {"tool1": {"slug": "tool1"}}
        after["offers"] = {**before["offers"], 2: {"id": 2}}
        after["accesses"] = {**before["accesses"], 2: {"id": 2}}
        after["factual_tables"] = copy.deepcopy(before["factual_tables"])
        after["factual_tables"]["catalog_modelversion"][2] = {"id": 2, "slug": "m2", "public_number": 2}
        after["factual_tables"]["catalog_modelversion"][3] = {"id": 3, "slug": "tool1", "public_number": None}
        after["factual_tables"]["catalog_tool"][1] = {"id": 1, "slug": "tool1", "public_number": 1}
        after["factual_tables"]["catalog_offer"][2] = {"id": 2}
        after["factual_tables"]["catalog_access"][2] = {"id": 2}
        after["factual_tables"]["catalog_source"][2] = {"id": 2}
        after["factual_tables"]["catalog_organization"][2] = {"id": 2}
        after["factual_tables"]["catalog_modelfamily"][2] = {"id": 2}
        after["factual_tables"]["catalog_service"][2] = {"id": 2}
        after["factual_tables"]["catalog_modelorigincountry"] = {1: {"id": 1}}
        validate(create_plan, before, after)

        foreign = copy.deepcopy(after)
        foreign["model_rows"]["m1"] = {"slug": "m1", "public_number": 99, "name": "M1"}
        with self.assertRaisesRegex(RuntimeError, "outside the plan"):
            validate(create_plan, before, foreign)
        wrong_count = copy.deepcopy(after)
        wrong_count["published_tools"] = 2
        with self.assertRaisesRegex(RuntimeError, "differs from plan"):
            validate(create_plan, before, wrong_count)
        unexpected_table = copy.deepcopy(after)
        unexpected_table["factual_tables"]["catalog_evaluation"] = {1: {"id": 1}}
        with self.assertRaisesRegex(RuntimeError, "outside the plan"):
            validate(create_plan, before, unexpected_table)

        already = copy.deepcopy(after)
        validate(create_plan, already, already, already_applied=True)

    def test_catalog_plan_trial_allows_updates_and_related_changes(self):
        with mock.patch.dict(sys.modules, {"pwd": types.ModuleType("pwd")}):
            preflight = runpy.run_path(str(ROOT / "tools/server_release_preflight.py"))
        validate = preflight["validate_catalog_plan_trial"]
        base = {
            "integrity": "ok", "foreign_keys": 0,
            "numbers_continuous": True, "model_numbers_continuous": True,
            "published_models": 1, "numbered_models": 1,
            "published_tools": 1, "numbered_tools": 1,
            "evaluation_rows": 1, "evaluation_public": 1,
            "source_rows": 1, "benchmark_rows": 1,
            "model_rows": {"m1": {"slug": "m1", "name": "old", "public_number": 1}},
            "tools": {"t1": {"slug": "t1", "public_number": 1}},
            "offers": {1: {"id": 1, "service_id": 1}},
            "accesses": {1: {"id": 1, "service_id": 1}},
            "factual_tables": {
                "catalog_modelversion": {1: {"id": 1, "slug": "m1", "name": "old"}},
                "catalog_tool": {1: {"id": 1, "slug": "t1"}},
                "catalog_offer": {1: {"id": 1, "service_id": 1}},
                "catalog_access": {1: {"id": 1, "service_id": 1}},
                "catalog_service": {1: {"id": 1, "provider_id": 1, "url": "old"}},
                "catalog_benchmark": {1: {"id": 1, "category": "old"}},
                "catalog_organization": {1: {"id": 1, "country": ""}},
            },
        }
        plan = {
            "schema": "aipedia-catalog-plan/1", "release": "future",
            "counts": {"update": 1, "access_service": 1, "service_provider": 1,
                       "benchmark_category": 1, "org_country": 1},
            "final_published": {"Models": ["m1"], "Tools": ["t1"]},
            "final_numbers": {"Models": {"m1": 1}, "Tools": {"t1": 1}},
            "changes": [
                {"kind": "update", "sheet": "Models", "id": "m1", "before": {"name": "old"}, "after": {"name": "new"}},
                {"kind": "access_service", "sheet": "Access", "id": "access-1", "before": {"url": "old"},
                 "after": {"url": "new"}, "identity": {"model": "m1", "service": "API"}},
                {"kind": "service_provider", "sheet": "Offers", "id": "API", "identity": {"name": "API", "url": "new"},
                 "before": {"provider": "Old"}, "after": {"provider": "New"}},
                {"kind": "benchmark_category", "sheet": "Evaluations", "id": "Bench", "identity": {"name": "Bench", "protocol": "main"},
                 "before": {"category": "old"}, "after": {"category": "text"}},
                {"kind": "org_country", "sheet": "Models", "id": "Org", "record": "m1",
                 "before": {"country": ""}, "after": {"country": "US"}},
            ],
        }
        after = copy.deepcopy(base)
        after["model_rows"]["m1"] = {"slug": "m1", "name": "new", "public_number": 1}
        after["accesses"][1] = {"id": 1, "service_id": 2}
        after["factual_tables"]["catalog_modelversion"][1]["name"] = "new"
        after["factual_tables"]["catalog_access"][1]["service_id"] = 2
        after["factual_tables"]["catalog_service"][1].update({"provider_id": 2, "url": "new"})
        after["factual_tables"]["catalog_benchmark"][1]["category"] = "text"
        after["factual_tables"]["catalog_organization"][1]["country"] = "US"
        validate(plan, base, after)

    def test_code_only_release_comparison_requires_unchanged_factual_tables(self):
        spec = importlib.util.spec_from_file_location("server_compare_test", ROOT / "tools/server_compare.py")
        compare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compare)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app").mkdir()
            (root / "backups").mkdir()
            (root / "data").mkdir()
            (root / "app/BUILD.json").write_text('{"release_sequence":14}', encoding="utf-8")
            backup = root / "backups/aipedia-before-code-20260929T000000Z.sqlite3"
            current = root / "data/aipedia.sqlite3"
            with closing(sqlite3.connect(backup)) as db:
                db.executescript("""
                    CREATE TABLE catalog_modelversion(id INTEGER PRIMARY KEY, public_number INTEGER,
                        published INTEGER, entry_type TEXT);
                    CREATE TABLE catalog_tool(id INTEGER PRIMARY KEY, public_number INTEGER,
                        published INTEGER);
                    CREATE TABLE catalog_source(id INTEGER PRIMARY KEY);
                    CREATE TABLE catalog_benchmark(id INTEGER PRIMARY KEY);
                    CREATE TABLE catalog_evaluation(id INTEGER PRIMARY KEY, public INTEGER);
                """)
                db.executemany("INSERT INTO catalog_modelversion VALUES (?, ?, 1, 'model')",
                               ((n, n) for n in range(1, 326)))
                db.executemany("INSERT INTO catalog_tool VALUES (?, ?, 1)",
                               ((n, n) for n in range(1, 148)))
                db.executemany("INSERT INTO catalog_source VALUES (?)", ((n,) for n in range(1, 1000)))
                db.executemany("INSERT INTO catalog_benchmark VALUES (?)", ((n,) for n in range(1, 983)))
                db.executemany("INSERT INTO catalog_evaluation VALUES (?, ?)",
                               ((n, int(n <= 2741)) for n in range(1, 5011)))
                db.commit()
            current.write_bytes(backup.read_bytes())
            def report():
                output = io.StringIO()
                with mock.patch.object(compare, "ROOT", root), \
                        mock.patch.object(sys, "argv", ["server_compare", backup.name]), \
                        redirect_stdout(output):
                    compare.main()
                return json.loads(output.getvalue())
            self.assertTrue(report()["ok"])
            (root / "app/BUILD.json").write_text('{"release_sequence":15}', encoding="utf-8")
            self.assertTrue(report()["ok"])
            with closing(sqlite3.connect(current)) as db:
                db.execute("UPDATE catalog_tool SET public_number=999 WHERE id=1")
                db.commit()
            changed = report()
            self.assertFalse(changed["ok"])
            self.assertEqual(changed["changed_factual_tables"], ["catalog_tool"])

    def test_catalog_release_comparison_uses_deployed_plan_not_release_allowlist(self):
        spec = importlib.util.spec_from_file_location("server_compare_plan_test", ROOT / "tools/server_compare.py")
        compare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compare)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app/data/release/future-daily").mkdir(parents=True)
            (root / "backups").mkdir()
            (root / "data").mkdir()
            (root / "app/BUILD.json").write_text(json.dumps({
                "release_sequence": 18,
                "release_id": "DAILY-CATALOG-UPDATE-2026-09-30",
                "release_tag": "release-2026-09-30-daily-catalog-update",
            }), encoding="utf-8")
            plan = {
                "schema": "aipedia-catalog-plan/1",
                "release": "release-2026-09-30-daily-catalog-update",
                "counts": {"create": 1},
                "final_published": {"Models": ["m1", "m2"], "Tools": []},
                "final_numbers": {"Models": {"m1": 1, "m2": 2}, "Tools": {}},
                "changes": [{"kind": "create", "sheet": "Models", "id": "m2", "row": {}, "offers": [], "access": []}],
            }
            (root / "app/data/release/future-daily/catalog_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            backup = root / "backups/aipedia-before-code-20260930T000000Z.sqlite3"
            current = root / "data/aipedia.sqlite3"
            schema = """
                CREATE TABLE catalog_modelversion(id INTEGER PRIMARY KEY, slug TEXT, public_number INTEGER,
                    published INTEGER, entry_type TEXT, name TEXT);
                CREATE TABLE catalog_tool(id INTEGER PRIMARY KEY, slug TEXT, public_number INTEGER, published INTEGER);
                CREATE TABLE catalog_source(id INTEGER PRIMARY KEY, title TEXT);
                CREATE TABLE catalog_benchmark(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_evaluation(id INTEGER PRIMARY KEY, public INTEGER);
                CREATE TABLE catalog_modelfamily(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_organization(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_service(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_offer(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_access(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_modelorigincountry(id INTEGER PRIMARY KEY);
                CREATE TABLE catalog_toolplatform(id INTEGER PRIMARY KEY);
            """
            with closing(sqlite3.connect(backup)) as db:
                db.executescript(schema)
                db.execute("INSERT INTO catalog_modelversion VALUES (1, 'm1', 1, 1, 'model', 'M1')")
                db.execute("INSERT INTO catalog_source VALUES (1, 'source')")
                db.commit()
            current.write_bytes(backup.read_bytes())
            with closing(sqlite3.connect(current)) as db:
                db.execute("INSERT INTO catalog_modelversion VALUES (2, 'm2', 2, 1, 'model', 'M2')")
                db.commit()

            def report():
                output = io.StringIO()
                with mock.patch.object(compare, "ROOT", root), \
                        mock.patch.object(sys, "argv", ["server_compare", backup.name]), \
                        redirect_stdout(output):
                    compare.main()
                return json.loads(output.getvalue())

            passed = report()
            self.assertTrue(passed["ok"], passed)
            self.assertEqual(passed["catalog_plan"], "data/release/future-daily/catalog_plan.json")
            self.assertEqual((passed["before"]["models"], passed["after"]["models"]), (1, 2))

            with closing(sqlite3.connect(current)) as db:
                db.execute("UPDATE catalog_source SET title='unexpected' WHERE id=1")
                db.commit()
            failed = report()
            self.assertFalse(failed["ok"])
            self.assertTrue(any("catalog_source existing rows" in problem for problem in failed["problems"]))
