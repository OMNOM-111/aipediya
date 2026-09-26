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
from catalog.models import (
    Access, ModelFamily, ModelVersion, Offer, Organization, Service, Source, Tool,
)

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def master_row(record, name, released="", status="PUBLISHED", **extra):
    row = {c: "" for c in cm.MAIN["Models"]}
    decision = "PUBLIC" if status == "PUBLISHED" else "NEEDS_REVIEW"
    if decision == "NEEDS_REVIEW":
        extra.setdefault("Reason", "open question")
    row.update({
        "Record ID": record, "Name": name, "Developer": "Lab", "Status": status,
        "Publication Decision": decision,
        "Exact Release Date": released, "Category": "text", "Description EN": "d",
        "Official Source": "https://example.com/" + record, "Last Verified": "2026-09-24",
    })
    row.update(extra)
    return row


def empty_master(models=()):
    rows = {sheet: [] for sheet in [*cm.MAIN, *cm.AUX, "Changelog"]}
    rows["Models"] = list(models)
    return rows


class ChronologyTests(unittest.TestCase):
    def test_new_release_takes_next_number(self):
        rows = empty_master([master_row("a", "A", "2024-01-01"), master_row("b", "B", "2025-01-01")])
        cm.refresh_derived(rows, rows["Changelog"], "test", "T")
        rows["Changelog"].clear()
        rows["Models"].append(master_row("c", "C", "2026-09-24"))
        cm.refresh_derived(rows, rows["Changelog"], "new release", "T")
        numbers = {r["Record ID"]: r["Public Number"] for r in rows["Models"]}
        self.assertEqual(numbers, {"a": "1", "b": "2", "c": "3"})
        self.assertEqual([(e["Record ID"], e["Before"], e["After"]) for e in rows["Changelog"]], [("c", "", "3")])

    def test_historical_model_is_inserted_and_later_numbers_shift_with_changelog(self):
        rows = empty_master([master_row("a", "A", "2024-01-01"), master_row("b", "B", "2025-01-01")])
        cm.refresh_derived(rows, rows["Changelog"], "test", "T")
        rows["Changelog"].clear()
        rows["Models"].append(master_row("old", "Old", "2020-05-01"))
        cm.refresh_derived(rows, rows["Changelog"], "historical insert", "T")
        numbers = {r["Record ID"]: r["Public Number"] for r in rows["Models"]}
        self.assertEqual(numbers, {"old": "1", "a": "2", "b": "3"})
        log = {(e["Record ID"], e["Before"], e["After"]) for e in rows["Changelog"]}
        self.assertEqual(log, {("old", "", "1"), ("a", "1", "2"), ("b", "2", "3")})
        self.assertTrue(all(e["Reason"] == "historical insert" for e in rows["Changelog"]))

    def test_only_published_dated_rows_are_numbered(self):
        rows = empty_master([
            master_row("a", "A", "2024-01-01"),
            master_row("r", "R", "2023-01-01", status="NEEDS_REVIEW"),
            master_row("u", "U", ""),
            master_row("x", "X", "", **{"Approx Date": "≈2023-06"}),
        ])
        cm.refresh_derived(rows, rows["Changelog"], "test", "T")
        numbers = {r["Record ID"]: r["Public Number"] for r in rows["Models"]}
        self.assertEqual(numbers, {"x": "1", "a": "2", "r": "", "u": ""})
        self.assertIn("date (exact or ≈)", rows["Models"][2]["Missing Data"])

    def test_same_date_orders_by_name_then_record_id(self):
        rows = empty_master([master_row("z", "Beta", "2024-01-01"), master_row("y", "alpha", "2024-01-01")])
        self.assertEqual(cm.chronology_numbers(rows["Models"]), {"y": "1", "z": "2"})


class ValidationTests(unittest.TestCase):
    def numbered(self, *models):
        rows = empty_master(models)
        cm.refresh_derived(rows, [], "test", "T")
        return rows

    def test_valid_master_has_no_errors(self):
        errors, _, _ = cm.validate(self.numbered(master_row("a", "A", "2024-01-01")))
        self.assertEqual(errors, [])

    def test_rule_violations_are_reported(self):
        rows = self.numbered(
            master_row("a", "A", "2024-01-01", **{"Approx Date": "≈2024-01"}),
            master_row("b", "B", "2024-02-01", **{"Official Source": ""}),
            master_row("c", "C", status="DONE"),
            master_row("bad id", "D"),
        )
        rows["Models"][0]["Public Number"] = "7"
        rows["Offers"].append({"Key": "offer-1", "Record Type": "model", "Record ID": "ghost"})
        errors, _, _ = cm.validate(rows)
        text = "\n".join(errors)
        for fragment in ("not both", "PUBLISHED requires Official Source", "PUBLISHED or NEEDS_REVIEW",
                         "Record ID may contain", "differs from chronology", "ghost not found"):
            self.assertIn(fragment, text)

    def test_needs_review_public_somewhere_is_a_warning(self):
        rows = self.numbered(master_row("r", "R", status="NEEDS_REVIEW", **{"On Production": "YES"}))
        errors, warnings, _ = cm.validate(rows)
        self.assertEqual(errors, [])
        self.assertIn("not PUBLISHED (NEEDS_REVIEW) but public on Production: hide at next sync",
                      [k for k, _ in warnings])


@unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
class CatalogMasterCommandTests(TestCase):
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

    def model(self, name, published=True, released=None, entry_type="model"):
        return ModelVersion.objects.create(
            name=name, slug=name.lower(), family=self.family, version="1", published=published,
            released=released, entry_type=entry_type, source=self.source, checked=date(2026, 1, 1),
            description={"en": name + " model", "ru": "модель", "de": "Modell"},
            release_evidence={"source_url": "https://example.com/" + name.lower(), "checked": "2026-09-01"},
        )

    def command(self, action, **options):
        out = StringIO()
        call_command("catalog_master", action, path=str(self.path), stdout=out, **options)
        return out.getvalue()

    def test_import_covers_models_tools_relations_and_preserves_master_edits(self):
        public = self.model("Public", released=date(2024, 1, 1))
        self.model("Hidden", published=False)
        legacy = self.model("Toolish", entry_type="product")
        tool = Tool.objects.create(name="Tool", slug="tool", developer=self.org, category="ai_app",
                                   legacy_version=legacy, source=self.source, checked=date(2026, 1, 1),
                                   released=date(2023, 5, 1))
        service = Service.objects.create(name="API", provider=self.org, kind="api", url="https://example.com/api")
        Offer.objects.create(model=public, service=service, amount="1.50", unit="input",
                             conditions={"ru": "да", "en": "yes"}, source=self.source, checked=date(2026, 1, 1))
        Access.objects.create(model=legacy, service=service, source=self.source, checked=date(2026, 1, 1))

        self.command("import")
        rows, meta, _ = cm.read_workbook(self.path)
        models = {r["Record ID"]: r for r in rows["Models"]}
        self.assertEqual(set(models), {"public", "hidden"})
        self.assertEqual(models["public"]["Status"], "PUBLISHED")
        self.assertEqual(models["public"]["Public Number"], "1")
        self.assertEqual(models["public"]["Official Source"], "https://example.com/public")
        self.assertEqual(models["public"]["Offers"], "1")
        self.assertEqual(models["public"]["Description Other Locales (JSON)"], '{"de": "Modell"}')
        self.assertEqual(models["hidden"]["Status"], "NEEDS_REVIEW")
        self.assertEqual(models["hidden"]["Official Source"], "")
        self.assertEqual(rows["Tools"][0]["Record ID"], tool.slug)
        self.assertEqual(rows["Tools"][0]["Access"], "1")
        self.assertEqual(rows["Offers"][0]["Amount"], "1.5")
        self.assertEqual(meta["Schema"], cm.SCHEMA)
        self.assertIn("check: OK", self.command("check"))

        models["public"]["Description EN"] = "edited in master"
        rows["Models"].append(master_row("older", "Older", "2020-01-01"))
        cm.write_workbook(rows, meta, self.path)
        self.command("import")
        rows, _, _ = cm.read_workbook(self.path)
        models = {r["Record ID"]: r for r in rows["Models"]}
        self.assertEqual(models["public"]["Description EN"], "edited in master")
        self.assertEqual((models["older"]["Public Number"], models["public"]["Public Number"]), ("1", "2"))
        self.assertEqual(models["older"]["On Local"], "NO")
        self.assertTrue(any(e["Record ID"] == "public" and e["Before"] == "1" and e["After"] == "2"
                            for e in rows["Changelog"]))
        out = self.command("check")
        self.assertIn("'Models': {'records': 1, 'fields': 1}", out)
        public.refresh_from_db()
        self.assertEqual(public.description["en"], "Public model")

    def test_check_fails_when_a_local_record_is_missing(self):
        self.model("Public", released=date(2024, 1, 1))
        self.command("import")
        self.model("Later", released=date(2025, 1, 1))
        with self.assertRaises(CommandError):
            self.command("check")

    def test_import_refuses_foreign_workbook_without_rebuild(self):
        from openpyxl import Workbook
        Workbook().save(self.path)
        with self.assertRaises(CommandError):
            self.command("import")
        self.command("import", rebuild=True)
        self.assertEqual(cm.read_workbook(self.path)[1]["Schema"], cm.SCHEMA)
