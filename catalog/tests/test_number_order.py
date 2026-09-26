"""Full-order regression checks of catalog numbers (owner report 2026-09-26:
200 -> 197 -> 198 -> 196 in the default newest-first listing).

The rendered table rows (first page plus every scroll chunk) must follow the
chosen direction strictly: number_asc / release_asc increase, number_desc /
release_desc (the default) decrease, entries without a number stay last in
both directions, filters only leave gaps.
"""
import re
from datetime import date
from unittest import mock

from django.test import TestCase

from catalog.models import ModelFamily, ModelVersion, Organization, Source, Tool

ROW = re.compile(r'<tr data-slug="([^"]+)" data-kind="(?:model|tool)" data-released="[^"]*" data-number="([^"]*)"')


class NumberOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(title="S", publisher="S", url="https://example.com/s")
        cls.lab_a = Organization.objects.create(name="Lab A", source=cls.source, checked=date(2026, 1, 1))
        cls.lab_b = Organization.objects.create(name="Lab B", source=cls.source, checked=date(2026, 1, 1))
        fam_a = ModelFamily.objects.create(name="A", developer=cls.lab_a)
        fam_b = ModelFamily.objects.create(name="B", developer=cls.lab_b)
        # (name, family, exact, approx, precision): same exact dates, an
        # approximate month starting on the same day as an exact date, and names
        # whose alphabetical order differs from the number order.
        spec = [
            ("Zeta", fam_a, date(2024, 3, 1), None, ""),
            ("Alpha", fam_b, date(2024, 3, 1), None, ""),
            ("Month", fam_a, None, date(2024, 3, 1), "month"),
            ("Mid", fam_b, date(2024, 6, 15), None, ""),
            ("Beta", fam_a, date(2024, 6, 15), None, ""),
            ("Day", fam_b, None, date(2024, 6, 15), "day"),
            ("Late", fam_a, date(2025, 1, 1), None, ""),
            ("Old", fam_b, date(2020, 1, 1), None, ""),
        ]
        rows = []
        for name, family, exact, approx, precision in spec:
            rows.append(ModelVersion.objects.create(
                name=name, slug=name.lower(), family=family, version="1", category="text", tasks=["text"],
                released=exact, approx_released=approx, approx_precision=precision,
                source=cls.source, checked=date(2026, 1, 1), published=True))
        # Numbers as the master assigns them: (date, name, Record ID).
        ordered = sorted(rows, key=lambda m: (m.released or m.approx_released, m.name.casefold(), m.slug))
        ModelVersion.objects.update(public_number=None)
        for number, model in enumerate(ordered, 1):
            ModelVersion.objects.filter(pk=model.pk).update(public_number=number)
        tools = [("Tool Z", date(2023, 5, 1)), ("Tool A", date(2023, 5, 1)), ("Tool M", None),
                 ("Tool Q", date(2022, 1, 1)), ("Tool N", None)]
        for name, released in tools:
            Tool.objects.create(name=name, slug=name.lower().replace(" ", "-"), developer=cls.lab_a,
                                category="ai_app", released=released, source=cls.source,
                                checked=date(2026, 1, 1), published=True)
        Tool.objects.update(public_number=None)
        dated = sorted(Tool.objects.exclude(released=None), key=lambda t: (t.released, t.name.casefold(), t.slug))
        for number, tool in enumerate(dated, 1):
            Tool.objects.filter(pk=tool.pk).update(public_number=number)

    def listing(self, path, **params):
        """All rows of a listing, first page plus every scroll chunk."""
        first = self.client.get(path, params)
        rows = ROW.findall(first.content.decode())
        page = 2
        while True:
            chunk = self.client.get(path, {**params, "page": page, "partial": "rows"},
                                    HTTP_X_REQUESTED_WITH="AIpedia")
            found = ROW.findall(chunk.content.decode()) if chunk.status_code == 200 else []
            if not found:
                return rows
            rows.extend(found)
            page += 1

    @staticmethod
    def numbers(rows):
        return [int(n) if n not in ("", "None") else None for _slug, n in rows]

    def assert_direction(self, numbers, descending):
        numbered = [n for n in numbers if n is not None]
        self.assertEqual(numbered, sorted(numbered, reverse=descending), numbers)
        self.assertEqual(len(set(numbered)), len(numbered))
        tail = numbers[len(numbered):]
        self.assertTrue(all(n is None for n in tail) and None not in numbers[:len(numbered)],
                        "entries without a number must stay last: %s" % numbers)

    def test_models_every_chronological_and_number_sort_is_strict(self):
        for sort, descending in (("number_asc", False), ("number_desc", True),
                                 ("release_asc", False), ("release_desc", True)):
            with self.subTest(sort=sort):
                numbers = self.numbers(self.listing("/", sort=sort))
                self.assertEqual(sorted(numbers), list(range(1, 9)))
                self.assert_direction(numbers, descending)
        default = self.numbers(self.listing("/"))
        self.assertEqual(default, list(range(8, 0, -1)))  # newest first, strictly decreasing

    def test_same_date_and_approximate_entries_follow_master_numbers(self):
        rows = self.listing("/", sort="release_asc")
        self.assertEqual([slug for slug, _n in rows],
                         ["old", "alpha", "month", "zeta", "beta", "day", "mid", "late"])
        self.assertEqual([slug for slug, _n in self.listing("/", sort="release_desc")],
                         ["late", "mid", "day", "beta", "zeta", "month", "alpha", "old"])
        self.assertEqual(ModelVersion.objects.get(slug="month").approx_precision, "month")

    def test_chunk_boundaries_continue_the_same_order(self):
        with mock.patch("catalog.views.INITIAL_PAGE_SIZE", 3), mock.patch("catalog.views.CHUNK_SIZE", 2):
            for sort, descending in (("release_desc", True), ("release_asc", False),
                                     ("number_desc", True), ("number_asc", False)):
                with self.subTest(sort=sort):
                    numbers = self.numbers(self.listing("/", sort=sort))
                    self.assertEqual(len(numbers), 8)
                    self.assert_direction(numbers, descending)
            tools = self.numbers(self.listing("/tools/", sort="release_desc"))
            self.assertEqual(tools, [3, 2, 1, None, None])

    def test_filter_leaves_gaps_but_keeps_direction(self):
        numbers = self.numbers(self.listing("/", developer=str(self.lab_a.pk)))
        self.assertTrue(0 < len(numbers) < 8)
        self.assert_direction(numbers, True)
        numbers = self.numbers(self.listing("/", developer=str(self.lab_b.pk), sort="release_asc"))
        self.assert_direction(numbers, False)

    def test_tools_both_directions_with_undated_last(self):
        for sort, expected in (("number_asc", [1, 2, 3, None, None]), ("number_desc", [3, 2, 1, None, None]),
                               ("release_asc", [1, 2, 3, None, None]), ("release_desc", [3, 2, 1, None, None])):
            with self.subTest(sort=sort):
                self.assertEqual(self.numbers(self.listing("/tools/", sort=sort)), expected)
        self.assertEqual(self.numbers(self.listing("/tools/")), [3, 2, 1, None, None])

    def test_sorting_never_changes_stored_numbers(self):
        before = sorted(ModelVersion.objects.values_list("slug", "public_number"))
        for sort in ("release_desc", "number_asc", "name_asc", "developer_desc"):
            self.listing("/", sort=sort)
        self.assertEqual(before, sorted(ModelVersion.objects.values_list("slug", "public_number")))

    def test_stale_chunk_reply_is_ignored_by_the_client(self):
        from pathlib import Path
        script = (Path(__file__).resolve().parents[2] / "static" / "site.js").read_text(encoding="utf-8")
        loader = script[script.index("const loadNext = async"):script.index("const observerOptions")]
        self.assertLess(loader.index("await fetch(nextUrl"), loader.index("dataset.nextUrl !== nextUrl) return"))
        self.assertLess(loader.index("dataset.nextUrl !== nextUrl) return"), loader.index("modelRows.append"))
