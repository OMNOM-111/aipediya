"""Maintain the AIpediya Catalog Master workbook (Models + Tools).

import - create the master or merge Local into it: new Local records/rows are
         added, Local-owned columns refreshed, Missing Data and chronological
         Public Numbers recomputed (changes logged). Master data is never
         overwritten by Local.
check  - validate rules, completeness against Local and report drift.
--production reads the public sitemap only. Nothing is published or written
to any database.
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog import catalog_master as cm


class Command(BaseCommand):
    help = "Import Local into, or check, the AIpediya Catalog Master workbook."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["import", "check"])
        parser.add_argument("--path", default=str(cm.WORKBOOK_PATH))
        parser.add_argument("--production", action="store_true",
                            help="Read the public sitemap to fill On Production (read-only).")
        parser.add_argument("--rebuild", action="store_true",
                            help="Replace a workbook that is not a catalog master (old registry).")
        parser.add_argument("--max-lines", type=int, default=15)

    def handle(self, action, path, production, rebuild, max_lines, **opts):
        path = Path(path)
        live = None
        if production:
            try:
                live = cm.fetch_production()
            except OSError as exc:
                raise CommandError("Production sitemap unavailable: %s" % exc)
        if action == "import":
            self.run_import(path, live, rebuild)
        else:
            self.run_check(path, live, max_lines)

    def _load(self, path, rebuild=False):
        if not path.exists():
            return {}, {}, {}
        try:
            return cm.read_workbook(path)
        except ValueError as exc:
            if rebuild:
                self.stdout.write("rebuild: %s" % exc)
                return {}, {}, {}
            raise CommandError("%s (pass --rebuild to replace it)" % exc)

    def run_import(self, path, live, rebuild):
        rows, meta, extra = self._load(path, rebuild)
        snapshot, aux = cm.local_snapshot()
        stamp = cm.now_utc()
        summary = cm.import_from_local(rows, snapshot, aux, production=live, stamp=stamp)
        meta = dict(meta)
        meta.update({
            "Schema": cm.SCHEMA,
            "Last Import (UTC)": stamp,
            "Local Models (public/total)": "%d/%d" % (
                sum(1 for r, _ in snapshot["Models"].values() if r["On Local"] == "YES"),
                len(snapshot["Models"])),
            "Local Tools (public/total)": "%d/%d" % (
                sum(1 for r, _ in snapshot["Tools"].values() if r["On Local"] == "YES"),
                len(snapshot["Tools"])),
        })
        if live is not None:
            meta.update({
                "Production Checked (UTC)": stamp,
                "Production Release": live[1],
                "Production Sitemap (models/tools)": "%d/%d" % (len(live[0]["Models"]), len(live[0]["Tools"])),
            })
        cm.write_workbook(rows, meta, path, extra)
        self.stdout.write("import: %s" % path)
        for sheet, info in summary.items():
            self.stdout.write("  %s: %s" % (sheet, info))

    def run_check(self, path, live, max_lines):
        if not path.exists():
            raise CommandError("%s does not exist; run: manage.py catalog_master import" % path)
        rows, meta, _ = self._load(path)
        if live is not None:
            for sheet in cm.MAIN:
                for row in rows[sheet]:
                    actual = "YES" if row["Record ID"] in live[0][sheet] else "NO"
                    if row.get("On Production") != actual:
                        row["On Production"] = actual
        snapshot, aux = cm.local_snapshot()
        errors, warnings, drift = cm.validate(rows, snapshot, aux)
        for sheet in cm.MAIN:
            counts = {}
            for row in rows[sheet]:
                counts[row.get("Status", "")] = counts.get(row.get("Status", ""), 0) + 1
            self.stdout.write("check %s: rows=%d %s" % (
                sheet, len(rows[sheet]), " ".join("%s=%d" % (k or "(empty)", v) for k, v in sorted(counts.items()))))
        for sheet in cm.AUX:
            self.stdout.write("check %s: rows=%d" % (sheet, len(rows[sheet])))
        self.stdout.write("drift vs Local (master changes pending sync): %s" % drift)
        if warnings:
            kinds = {}
            for kind, where in warnings:
                kinds.setdefault(kind, []).append(where)
            self.stdout.write("warnings: %d" % len(warnings))
            for kind, places in sorted(kinds.items(), key=lambda item: -len(item[1]))[:max_lines]:
                self.stdout.write("  %5d x %s (e.g. %s)" % (len(places), kind, places[0]))
        for error in errors[:max_lines]:
            self.stdout.write("  ERROR " + error)
        if errors:
            raise CommandError("%d rule violation(s)" % len(errors))
        self.stdout.write("check: OK")
