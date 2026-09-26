"""Catalog master v4: editorial fields, drafts and the master -> Local sync."""
import shutil
import tempfile
import unittest
from datetime import date
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog import catalog_master as cm
from catalog import master_sync
from catalog.models import (
    ModelFamily, ModelVersion, Organization, PublicationRevision, Revision, Source, Tool,
)
from catalog.tests.test_catalog_master import HAS_OPENPYXL, empty_master, master_row


def archive_row(record, name, parent="", relation="", code="DUPLICATE", **extra):
    row = master_row(record, name, "2024-01-01", status="NEEDS_REVIEW", **extra)
    row.update({"Publication Decision": "ARCHIVE", "Decision Code": code, "Decision Date": "2026-09-26",
                "Reason": "fact and conclusion", "Canonical / Parent Record ID": parent, "Relation Type": relation})
    return row


class EditorialValidationTests(unittest.TestCase):
    def check(self, *models):
        rows = empty_master(models)
        cm.refresh_derived(rows, [], "test", "T")
        return cm.validate(rows)

    def test_archive_needs_code_date_reason_and_canonical_for_duplicates(self):
        bad = archive_row("dup", "Dup", code="DUPLICATE")
        bad["Decision Date"] = ""
        errors, _, _ = self.check(master_row("a", "A", "2024-01-01"), bad)
        text = "\n".join(errors)
        self.assertIn("Decision Date", text)
        self.assertIn("Canonical / Parent Record ID", text)
        errors, _, _ = self.check(master_row("a", "A", "2024-01-01"),
                                  archive_row("dup", "Dup", "a", "DUPLICATE_OF", **{"Aliases": ""}))
        self.assertEqual(errors, [])

    def test_code_must_fit_decision_and_same_entity_rows_must_be_archive(self):
        row = master_row("b", "B", "2024-01-01", **{"Decision Code": "DUPLICATE",
                                                    "Canonical / Parent Record ID": "a", "Relation Type": "ALIAS_OF"})
        errors, _, _ = self.check(master_row("a", "A", "2024-01-01"), row)
        text = "\n".join(errors)
        self.assertIn("not valid for PUBLIC", text)
        self.assertIn("must be ARCHIVE", text)

    def test_chain_to_archive_cycles_and_ambiguous_aliases_are_errors(self):
        errors, _, _ = self.check(
            archive_row("x", "X", "y", "DUPLICATE_OF"), archive_row("y", "Y", "x", "DUPLICATE_OF"),
            master_row("a", "A", "2024-01-01", Aliases="Shared"), master_row("b", "B", "2024-01-01", Aliases="shared"))
        text = "\n".join(errors)
        self.assertIn("is itself ARCHIVE", text)
        self.assertIn("cycle", text)
        self.assertIn("ambiguous", text)

    def test_alias_of_archived_duplicate_belongs_to_canonical(self):
        errors, warnings, _ = self.check(
            master_row("a", "Model A", "2024-01-01", Aliases="Old A"),
            archive_row("old", "Old A", "a", "ALIAS_OF", code="ALIAS_SNAPSHOT"))
        self.assertEqual(errors, [])
        self.assertFalse([w for w in warnings if w[0].startswith("name matches")])

    def test_rediscovered_name_is_flagged(self):
        _, warnings, _ = self.check(master_row("a", "Model A", "2024-01-01", Aliases="Alpha"),
                                    master_row("n", "alpha", "2025-01-01", status="NEEDS_REVIEW",
                                               **{"Publication Decision": "NEEDS_REVIEW", "Reason": "new find"}))
        self.assertTrue(any(k.startswith("name matches") for k, _ in warnings))

    def test_offer_units_follow_site_contract(self):
        rows = empty_master([master_row("a", "A", "2024-01-01")])
        rows["Offers"] = [
            {"Key": "o1", "Record Type": "model", "Record ID": "a", "Unit": "audio_input", "Billing Unit": "x"},
            {"Key": "o2", "Record Type": "model", "Record ID": "a", "Unit": "other", "Billing Unit": ""},
            {"Key": "o3", "Record Type": "model", "Record ID": "a", "Unit": "input", "Billing Unit": ""},
        ]
        cm.refresh_derived(rows, [], "test", "T")
        text = "\n".join(cm.validate(rows)[0])
        self.assertIn("audio_input", text)
        self.assertIn("Unit other requires Billing Unit", text)
        self.assertNotIn("o3", text)

    def test_draft_row_gets_controlled_id_and_is_never_publishable(self):
        draft = {c: "" for c in cm.MAIN["Tools"]}
        draft.update({"Name": "New Finding", "Developer": "Lab", "Official Source": "https://example.com/n"})
        rows = empty_master()
        rows["Tools"] = [draft]
        log = []
        cm.refresh_derived(rows, log, "test", "2026-09-26T00:00:00Z")
        row = rows["Tools"][0]
        self.assertRegex(row["Record ID"], r"^new-finding-[0-9a-f]{8}$")
        self.assertEqual((row["Status"], row["Publication Decision"]), ("NEEDS_REVIEW", "NEEDS_REVIEW"))
        self.assertIn("date (exact or ≈)", row["Missing Data"])
        self.assertEqual(cm.validate(rows)[0], [])
        record = row["Record ID"]
        cm.refresh_derived(rows, log, "test", "2026-09-27T00:00:00Z")
        self.assertEqual(rows["Tools"][0]["Record ID"], record)

    def test_coverage_counts_unique_records_not_events(self):
        rows = empty_master([master_row("a", "A", "2024-01-01"), master_row("b", "B", "2024-01-01")])
        rows["Changelog"] = [{"Sheet": "Models", "Record ID": "a", "Field": "Verification result"}] * 3
        meta = cm.refresh_meta({"Охват, не полнота проверки": '=TEXT(B13/B10,"0.00%")', "Проверено ранее": "=B13-B24"},
                               rows, "T")
        self.assertEqual(meta["Охват, не полнота проверки"], "50.00%")
        self.assertNotIn("Проверено ранее", meta)

    def test_clear_token_counts_as_empty_in_checks(self):
        errors, _, _ = self.check(master_row("a", "A", "2024-01-01", **{"License": cm.CLEAR}))
        self.assertEqual(errors, [])


class ProductionSitemapTests(unittest.TestCase):
    def test_sitemap_index_is_followed_to_the_english_sitemap(self):
        pages = {
            "/sitemap.xml": '<sitemapindex><sitemap><loc>https://x/sitemaps/en.xml</loc></sitemap>'
                            '<sitemap><loc>https://x/sitemaps/ru.xml</loc></sitemap></sitemapindex>',
            "/sitemaps/en.xml": "<urlset><url><loc>https://x/models/a</loc></url></urlset>",
        }
        self.assertEqual(cm.production_sitemaps(pages.__getitem__), [pages["/sitemaps/en.xml"]])
        self.assertEqual(cm.production_sitemaps({"/sitemap.xml": "<urlset/>"}.__getitem__), ["<urlset/>"])


@unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
class MasterSyncTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(title="Fixture", publisher="Fixture", url="https://example.com/src")
        cls.org = Organization.objects.create(name="Lab", source=cls.source, checked=date(2026, 1, 1))
        cls.family = ModelFamily.objects.create(name="Fixture", developer=cls.org)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "master.xlsx"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def model(self, slug, published=True, **extra):
        return ModelVersion.objects.create(
            name=slug.title(), slug=slug, family=self.family, version="1", published=published,
            entry_type="model", source=self.source, checked=date(2026, 1, 1), released=date(2024, 1, 1),
            license="MIT", description={"en": slug.title() + " model"},
            release_evidence={"source_url": "https://example.com/" + slug, "checked": "2026-09-01"}, **extra)

    def command(self, action, **options):
        out = StringIO()
        call_command("catalog_master", action, path=str(self.path), stdout=out, **options)
        return out.getvalue()

    def edit(self, change):
        rows, meta, extra = cm.read_workbook(self.path)
        change(rows)
        cm.refresh_derived(rows, rows["Changelog"], "test edit", cm.now_utc())
        cm.write_workbook(rows, meta, self.path, extra)

    def test_add_fix_alias_draft_and_rerun_without_duplicates(self):
        self.model("canon")
        self.model("dupe")
        self.command("import")

        def change(rows):
            by = {r["Record ID"]: r for r in rows["Models"]}
            by["canon"].update({"License": "Apache-2.0", "Aliases": "Dupe | Canon Old", "Release Stage": "released"})
            by["dupe"].update({"Publication Decision": "ARCHIVE", "Status": "NEEDS_REVIEW", "Decision Code": "DUPLICATE",
                               "Decision Date": "2026-09-26", "Reason": "same weights",
                               "Canonical / Parent Record ID": "canon", "Relation Type": "DUPLICATE_OF"})
            new = master_row("", "Brand New", "2025-05-05", Developer="New Lab", Family="New",
                             **{"Record ID": "", "Description RU": "новая"})
            draft = {c: "" for c in cm.MAIN["Models"]}
            draft.update({"Name": "Half Known", "Developer": "Somebody"})
            rows["Models"] += [new, draft]
        self.edit(change)
        self.assertIn("check: OK", self.command("check"))
        rows, _, _ = cm.read_workbook(self.path)
        new_id = [r["Record ID"] for r in rows["Models"] if r["Name"] == "Brand New"][0]
        draft_id = [r["Record ID"] for r in rows["Models"] if r["Name"] == "Half Known"][0]

        dry = self.command("sync-local")
        self.assertIn("dry run", dry)
        self.assertFalse(ModelVersion.objects.filter(slug=new_id).exists())
        self.command("sync-local", apply=True)
        canon, dupe = ModelVersion.objects.get(slug="canon"), ModelVersion.objects.get(slug="dupe")
        self.assertEqual((canon.license, canon.aliases), ("Apache-2.0", ["Dupe", "Canon Old"]))
        self.assertEqual((dupe.published, dupe.redirect_to), (False, "canon"))
        created = ModelVersion.objects.get(slug=new_id)
        self.assertTrue(created.published)
        self.assertIsNotNone(created.public_number)
        self.assertFalse(ModelVersion.objects.filter(slug=draft_id).exists())
        self.assertTrue(PublicationRevision.objects.filter(model=dupe, action=master_sync.ACTION).exists())
        self.assertTrue(Revision.objects.filter(model=canon, entity="catalog_master").exists())

        response = self.client.get("/models/dupe")
        self.assertEqual((response.status_code, response["Location"]), (301, "/models/canon"))
        self.assertEqual(self.client.get("/models/" + draft_id).status_code, 404)
        listing = self.client.get("/", {"q": "Canon Old"}).content.decode()
        self.assertIn('data-slug="canon"', listing)
        self.assertNotIn('data-slug="dupe"', self.client.get("/", {"q": "Dupe"}).content.decode())

        counts = (ModelVersion.objects.count(), PublicationRevision.objects.count(), Revision.objects.count())
        self.command("import")
        self.assertIn("dry run", self.command("sync-local", apply=False))
        self.command("sync-local", apply=True)
        self.assertEqual(counts, (ModelVersion.objects.count(), PublicationRevision.objects.count(),
                                  Revision.objects.count()))
        rows, _, _ = cm.read_workbook(self.path)
        self.assertEqual(sum(1 for r in rows["Models"] if r["Name"] == "Brand New"), 1)

    def test_empty_cell_keeps_value_and_clear_token_erases_it(self):
        self.model("keep")
        self.command("import")
        self.edit(lambda rows: rows["Models"][0].update({"License": ""}))
        self.command("sync-local", apply=True)
        self.assertEqual(ModelVersion.objects.get(slug="keep").license, "MIT")
        self.edit(lambda rows: rows["Models"][0].update({"License": cm.CLEAR}))
        self.command("sync-local", apply=True)
        self.assertEqual(ModelVersion.objects.get(slug="keep").license, "")

    def test_mass_change_guard_and_failing_master_write_nothing(self):
        for index in range(3):
            self.model("m%d" % index, published=False)
        self.command("import")
        self.edit(lambda rows: [r.update({"Status": "PUBLISHED", "Publication Decision": "PUBLIC",
                                          "Official Source": "https://example.com/x", "Last Verified": "2026-09-26",
                                          "Decision Code": "CURRENT_RELEASE"}) for r in rows["Models"]])
        with self.assertRaises(CommandError):
            self.command("sync-local", apply=True, max_changes=2)
        self.assertEqual(ModelVersion.objects.filter(published=True).count(), 0)
        self.edit(lambda rows: rows["Models"][0].update({"Exact Release Date": "2024-99-99"}))
        with self.assertRaises(CommandError):
            self.command("sync-local", apply=True)
        self.assertFalse(Tool.objects.exists())


@unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
class MasterSyncNumbersAndRelationsTests(MasterSyncTests):
    """Chronological numbers, evaluation visibility, price units, warnings."""

    def test_add_fix_alias_draft_and_rerun_without_duplicates(self):  # covered by the parent class
        pass

    def test_empty_cell_keeps_value_and_clear_token_erases_it(self):
        pass

    def test_mass_change_guard_and_failing_master_write_nothing(self):
        pass

    def test_numbers_follow_master_chronology_and_hidden_or_undated_get_none(self):
        from catalog.models import Benchmark, Evaluation, Offer, Service
        self.model("late")
        ModelVersion.objects.filter(slug="late").update(released=date(2025, 1, 1))
        early = self.model("early")
        hidden = self.model("hidden", published=False)
        undated_tool = Tool.objects.create(name="Undated", slug="undated", developer=self.org, category="ai_app",
                                           source=self.source, checked=date(2026, 1, 1))
        service = Service.objects.create(name="API", provider=self.org, kind="api", url="https://example.com/api")
        offer = Offer.objects.create(model=early, service=service, amount="1.00", unit="input",
                                     conditions={"ru": "да", "en": "yes"}, source=self.source, checked=date(2026, 1, 1))
        bench = Benchmark.objects.create(name="Bench", protocol="p", category="text")
        evaluation = Evaluation.objects.create(model=early, benchmark=bench, score="1", evaluator="AA", public=True,
                                               source=self.source, checked=date(2026, 1, 1))
        self.command("import")

        def change(rows):
            for offer_row in rows["Offers"]:
                offer_row.update({"Billing Unit": "USD / 1M tokens", "Amount": "2"})
            for ev in rows["Evaluations"]:
                ev["Public"] = "NO"
            by = {r["Record ID"]: r for r in rows["Models"]}
            by["early"]["Source Title"] = "Renamed source"
        self.edit(change)
        out = self.command("sync-local", apply=True, max_changes=50)
        self.assertIn("NOT transferred", out)
        numbers = {m.slug: m.public_number for m in ModelVersion.objects.all()}
        self.assertEqual((numbers["early"], numbers["late"], numbers["hidden"]), (1, 2, None))
        self.assertIsNone(Tool.objects.get(pk=undated_tool.pk).public_number)
        offer.refresh_from_db()
        evaluation.refresh_from_db()
        self.assertEqual((offer.amount, offer.billing_unit, evaluation.public), (2, "", False))
        self.assertTrue(PublicationRevision.objects.filter(action=master_sync.RENUMBER).exists())
        self.assertIsNone(ModelVersion.objects.get(pk=hidden.pk).public_number)
        self.assertEqual(len([c for c in master_sync.plan(cm.read_workbook(self.path)[0])
                              if c["kind"] in ("create", "update", "number", "offer", "evaluation")]), 0)


@unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
class ReleasePlanTests(MasterSyncTests):
    """Platforms, sources, exclusive access services and release plans."""

    def test_add_fix_alias_draft_and_rerun_without_duplicates(self):
        pass

    def test_empty_cell_keeps_value_and_clear_token_erases_it(self):
        pass

    def test_mass_change_guard_and_failing_master_write_nothing(self):
        pass

    def setUp(self):
        super().setUp()
        from catalog.models import Access, Platform, Service
        self.web, _ = Platform.objects.get_or_create(code="web", defaults={"labels": {"en": "Web"}})
        Platform.objects.get_or_create(code="api", defaults={"labels": {"en": "API"}})
        self.tool = Tool.objects.create(name="Kit", slug="kit", developer=self.org, category="runtime",
                                        source=self.source, checked=date(2026, 1, 1), released=date(2024, 2, 2))
        self.canon = self.model("canon")
        self.dupe = self.model("dupe")
        self.service = Service.objects.create(name="Kit WEB", provider=self.org, kind="web",
                                              url="https://example.com/kit", compute_location="cloud")
        self.access = Access.objects.create(model=self.canon, service=self.service, source=self.source,
                                            checked=date(2026, 1, 1))
        self.command("import")

        def change(rows):
            tools = {r["Record ID"]: r for r in rows["Tools"]}
            tools["kit"].update({"Platforms": "web; api", "Source URL": "https://example.com/kit-launch",
                                 "Source Title": "Kit launch"})
            models = {r["Record ID"]: r for r in rows["Models"]}
            models["dupe"].update({"Publication Decision": "ARCHIVE", "Status": "NEEDS_REVIEW", "Decision Code": "DUPLICATE",
                                   "Decision Date": "2026-09-26", "Reason": "same", "Relation Type": "DUPLICATE_OF",
                                   "Canonical / Parent Record ID": "canon"})
            models["canon"]["Aliases"] = "Dupe"
            for access in rows["Access"]:
                access.update({"Service Kind": "download", "Compute Location": "local"})
        self.edit(change)

    def test_platforms_sources_and_exclusive_access_service(self):
        from catalog.models import Access, Platform, ToolPlatform
        self.command("sync-local", apply=True)
        self.tool.refresh_from_db()
        self.assertEqual(sorted(l.platform.code for l in self.tool.platform_links.all()), ["api", "web"])
        self.assertEqual(self.tool.source.url, "https://example.com/kit-launch")
        service = Access.objects.get(pk=self.access.pk).service
        self.assertEqual((service.kind, service.compute_location), ("download", "local"))
        # re-import does not duplicate platform links known under master keys
        self.command("import")
        self.assertIn("check: OK", self.command("check"))
        rows = cm.read_workbook(self.path)[0]
        self.assertEqual(sum(1 for r in rows["Tool Platforms"] if r["Record ID"] == "kit"), 2)

    def plan_file(self):
        import json
        out = self.tmp / "plan.json"
        self.command("release-plan", plan_out=str(out), release="test")
        return out, json.loads(out.read_text(encoding="utf-8"))

    def test_release_plan_apply_rerun_mismatch_and_rollback(self):
        import json
        from unittest import mock
        out, plan = self.plan_file()
        self.assertGreater(plan["counts"]["update"], 0)
        baseline = sorted(ModelVersion.objects.values_list("slug", "published", "public_number"))

        tampered = self.tmp / "tampered.json"
        bad = json.loads(out.read_text(encoding="utf-8"))
        for change in bad["changes"]:
            if change["kind"] == "update" and "published" in change["before"]:
                change["before"]["published"] = not change["before"]["published"]
                change["after"]["published"] = change["before"]["published"]
        tampered.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(CommandError):
            self.command("apply-plan", plan_out=str(tampered), apply=True)
        self.assertEqual(baseline, sorted(ModelVersion.objects.values_list("slug", "published", "public_number")))

        with mock.patch.object(master_sync, "final_state_problems", return_value=["forced failure"]):
            with self.assertRaises(CommandError):
                self.command("apply-plan", plan_out=str(out), apply=True)
        self.assertEqual(baseline, sorted(ModelVersion.objects.values_list("slug", "published", "public_number")))

        self.assertIn("pending", self.command("apply-plan", plan_out=str(out)))
        self.assertIn("final state matches", self.command("apply-plan", plan_out=str(out), apply=True))
        self.assertEqual((ModelVersion.objects.get(slug="dupe").published, ModelVersion.objects.get(slug="dupe").redirect_to),
                         (False, "canon"))
        revisions = PublicationRevision.objects.count()
        self.assertIn("already applied", self.command("apply-plan", plan_out=str(out), apply=True))
        self.assertEqual(revisions, PublicationRevision.objects.count())


@unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
class CrossCatalogReclassificationTests(MasterSyncTests):
    """A model wrongly listed as a tool: archive the tool, move its rows, 301."""

    def test_add_fix_alias_draft_and_rerun_without_duplicates(self):
        pass

    def test_empty_cell_keeps_value_and_clear_token_erases_it(self):
        pass

    def test_mass_change_guard_and_failing_master_write_nothing(self):
        pass

    def test_tool_archived_to_model_rows_move_and_old_url_redirects(self):
        import json
        from catalog.models import Access, Offer, Service
        voice = self.model("voice", published=False)
        legacy = self.model("voice-tool")
        ModelVersion.objects.filter(pk=legacy.pk).update(entry_type="product")
        tool = Tool.objects.create(name="Voice", slug="voice-tool", developer=self.org, category="api_service",
                                   legacy_version=legacy, source=self.source, checked=date(2026, 1, 1),
                                   released=date(2026, 9, 10))
        service = Service.objects.create(name="API", provider=self.org, kind="api", url="https://example.com/api")
        offer = Offer.objects.create(model=legacy, service=service, amount="0.05", unit="minute",
                                     conditions={"ru": "сессия", "en": "session"}, source=self.source,
                                     checked=date(2026, 1, 1), research_key="voice:minute")
        access = Access.objects.create(model=legacy, service=service, source=self.source, checked=date(2026, 1, 1))
        self.command("import")

        def change(rows):
            models = {r["Record ID"]: r for r in rows["Models"]}
            models["voice"].update({"Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Official Source": "https://example.com/m",
                                    "Last Verified": "2026-09-26", "Decision Code": "CURRENT_RELEASE",
                                    "Suitable EN": "Realtime voice agents", "Limitations EN": "Backend billed separately"})
            tools = {r["Record ID"]: r for r in rows["Tools"]}
            tools["voice-tool"].update({"Status": "NEEDS_REVIEW", "Publication Decision": "ARCHIVE", "Decision Code": "MODEL_APP_SPLIT",
                                        "Relation Type": "DUPLICATE_OF", "Canonical / Parent Record ID": "Models:voice",
                                        "Reason": "wrong classification", "Decision Date": "2026-09-26"})
            for sheet in ("Offers", "Access"):
                for row in rows[sheet]:
                    if row["Record ID"] == "voice-tool":
                        row.update({"Record Type": "model", "Record ID": "voice"})
        self.edit(change)
        self.assertIn("check: OK", self.command("check"))
        out = self.tmp / "plan.json"
        self.command("release-plan", plan_out=str(out))
        plan = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(plan["counts"]["reassign"], 2)
        # The target database numbers these rows differently (as Production
        # did in the v014 preflight): the plan must find them by content.
        Offer.objects.filter(pk=offer.pk).delete()
        Access.objects.filter(pk=access.pk).delete()
        filler = Offer.objects.create(model=legacy, service=service, amount="9", unit="month",
                                      conditions={"ru": "другое"}, source=self.source, checked=date(2026, 1, 1),
                                      research_key="other:month")
        offer = Offer.objects.create(model=legacy, service=service, amount="0.05", unit="minute",
                                     conditions={"ru": "сессия", "en": "session"}, source=self.source,
                                     checked=date(2026, 1, 1), research_key="voice:minute")
        access = Access.objects.create(model=legacy, service=service, source=self.source, checked=date(2026, 1, 1))
        self.assertNotIn(offer.pk, [int(c["id"].split("-")[-1]) for c in plan["changes"] if c["sheet"] == "Offers"])
        self.assertIn("final state matches", self.command("apply-plan", plan_out=str(out), apply=True))
        filler.refresh_from_db()
        self.assertEqual(filler.model_id, legacy.pk)  # an unrelated row that took the old pk is untouched
        offer.refresh_from_db(); access.refresh_from_db(); voice.refresh_from_db()
        self.assertEqual((offer.model_id, access.model_id), (voice.pk, voice.pk))
        self.assertEqual((voice.published, voice.suitable.get("en")), (True, "Realtime voice agents"))
        tool.refresh_from_db()
        self.assertEqual((tool.published, tool.redirect_to), (False, "voice"))
        response = self.client.get("/tools/voice-tool")
        self.assertEqual((response.status_code, response["Location"]), (301, "/models/voice"))
        self.assertEqual(self.client.get("/models/voice").status_code, 200)
        self.assertIn("already applied", self.command("apply-plan", plan_out=str(out), apply=True))
        self.command("import")
        self.assertIn("check: OK", self.command("check"))
        self.assertFalse([c for c in master_sync.plan(cm.read_workbook(self.path)[0]) if c["kind"] in master_sync.WRITE_KINDS])

    def test_cross_sheet_link_rules(self):
        rows = empty_master([master_row("m", "M", "2024-01-01")])
        tool = {c: "" for c in cm.MAIN["Tools"]}
        tool.update({"Record ID": "t", "Name": "T", "Status": "PUBLISHED", "Publication Decision": "PUBLIC",
                     "Canonical / Parent Record ID": "Models:m", "Relation Type": "DUPLICATE_OF",
                     "Official Source": "https://example.com/t", "Last Verified": "2026-09-26"})
        rows["Tools"] = [tool]
        cm.refresh_derived(rows, [], "t", "T")
        text = "\n".join(cm.validate(rows)[0])
        self.assertIn("must be ARCHIVE", text)
        tool.update({"Canonical / Parent Record ID": "Models:ghost"})
        self.assertIn("not found", "\n".join(cm.validate(rows)[0]))
