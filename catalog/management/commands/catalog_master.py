"""Maintain the AIpediya Catalog Master workbook (Models + Tools).

import - create the master or merge Local into it: new Local records/rows are
         added, Local-owned columns refreshed, Missing Data and chronological
         Public Numbers recomputed (changes logged). Master data is never
         overwritten by Local.
refresh - recompute derived columns (Missing Data, counts, chronological
         Public Numbers, Meta counters) without reading Local.
check  - validate rules, completeness against Local and report drift.
sync-local - plan (default) or --apply the minimal master -> Local sync
         (publication flags, aliases/redirects, structured fields of
         PUBLISHED rows, creation of new PUBLISHED rows). Point AIPEDIA_DB at
         a copy first; empty cells never erase Local values, <CLEAR> does.
release-plan - write the sync plan of the master against THIS database (a
         copy of the release baseline) as a portable JSON release plan
         (--plan-out), with expected old values and final numbers.
apply-plan - on the target database (e.g. Production after migrate): check
         the plan (--plan-out path) against expected old values; with --apply
         write it atomically. Already applied -> no writes; mismatch -> abort.
--production reads the public sitemap only. Nothing is published or written
to any database.
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog import catalog_master as cm


class Command(BaseCommand):
    help = "Import Local into, or check, the AIpediya Catalog Master workbook."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["import", "refresh", "check", "sync-local", "release-plan", "apply-plan"])
        parser.add_argument("--path", default=str(cm.WORKBOOK_PATH))
        parser.add_argument("--production", action="store_true",
                            help="Read the public sitemap to fill On Production (read-only).")
        parser.add_argument("--rebuild", action="store_true",
                            help="Replace a workbook that is not a catalog master (old registry).")
        parser.add_argument("--max-lines", type=int, default=15)
        parser.add_argument("--apply", action="store_true", help="sync-local: write the plan (default: dry run).")
        parser.add_argument("--max-changes", type=int, default=200,
                            help="sync-local: refuse to write more create/update changes than this.")
        parser.add_argument("--plan-out", default="", help="sync-local/release-plan: write the plan as JSON; apply-plan: read it.")
        parser.add_argument("--release", default="", help="release-plan: release name recorded in the plan.")

    def handle(self, action, path, production, rebuild, max_lines, **opts):
        if action == "sync-local":
            return self.run_sync(Path(path), opts["apply"], opts["max_changes"], opts["plan_out"])
        if action == "release-plan":
            return self.run_release_plan(Path(path), opts["plan_out"], opts["release"])
        if action == "apply-plan":
            return self.run_apply_plan(opts["plan_out"], opts["apply"])
        path = Path(path)
        live = None
        if production:
            try:
                live = cm.fetch_production()
            except OSError as exc:
                raise CommandError("Production sitemap unavailable: %s" % exc)
        if action == "import":
            self.run_import(path, live, rebuild)
        elif action == "refresh":
            self.run_refresh(path)
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
        meta = cm.refresh_meta(meta, rows, stamp)
        cm.write_workbook(rows, meta, path, extra)
        self.stdout.write("import: %s" % path)
        for sheet, info in summary.items():
            self.stdout.write("  %s: %s" % (sheet, info))

    def run_sync(self, path, apply, max_changes, plan_out):
        import json
        from django.conf import settings
        from catalog import master_sync

        if not path.exists():
            raise CommandError("%s does not exist" % path)
        rows, _meta, _extra = self._load(path)
        snapshot, aux = cm.local_snapshot()
        errors, _warnings, _drift = cm.validate(rows, snapshot, aux)
        if errors:
            raise CommandError("master check fails (%d errors); run check first" % len(errors))
        changes = master_sync.plan(rows, snapshot, aux)
        kinds = {}
        for change in changes:
            key = change["kind"]
            if key == "update":
                key += ":" + ",".join(sorted(change["after"]))
            elif key == "unsupported":
                key += ":%s:%s:%s" % (change.get("category", "public"), change["sheet"], ",".join(change["columns"]))
            kinds[key] = kinds.get(key, 0) + 1
        self.stdout.write("database: %s" % settings.DATABASES["default"]["NAME"])
        for key, count in sorted(kinds.items()):
            self.stdout.write("  %5d %s" % (count, key))
        unsupported = [c for c in changes if c["kind"] == "unsupported"]
        hidden_drift = sum(1 for sheet in cm.MAIN for r in rows[sheet]
                           if r.get("Status") != "PUBLISHED" and r["Record ID"] in snapshot[sheet]
                           and any(r.get(c, "") != snapshot[sheet][r["Record ID"]][0].get(c, "")
                                   for c in cm.PUBLIC[sheet]))
        if plan_out:
            serial = []
            for change in changes:
                item = {k: v for k, v in change.items() if k != "row"}
                if "row" in change:
                    item["name"] = change["row"]["Name"]
                serial.append(item)
            Path(plan_out).write_text(json.dumps(serial, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        if hidden_drift:
            self.stdout.write("note: %d non-public records differ from Local; their fields are not synced "
                              "(not public; see docs/CATALOG_MASTER.md)" % hidden_drift)
        if unsupported:
            public = sum(1 for c in unsupported if c.get("category", "public") == "public")
            self.stdout.write(self.style.WARNING(
                "WARNING: %d differences of PUBLISHED records are NOT transferred by sync-local "
                "(%d affect public data, %d are service/representation differences; listed above as "
                "'unsupported:<category>'); review them separately" % (len(unsupported), public, len(unsupported) - public)))
        if not apply:
            self.stdout.write("dry run: nothing written (pass --apply)")
            return
        try:
            written = master_sync.apply(changes, rows, max_changes=max_changes)
        except ValueError as exc:
            raise CommandError(str(exc))
        self.stdout.write("applied: %d changes" % written)

    def run_release_plan(self, path, plan_out, release):
        import hashlib
        import json
        from catalog import master_sync

        if not plan_out:
            raise CommandError("--plan-out is required")
        rows, _meta, _extra = self._load(path)
        errors, _w, _d = cm.validate(rows)
        if errors:
            raise CommandError("master check fails (%d errors)" % len(errors))
        changes = master_sync.plan(rows)
        plan = master_sync.build_release_plan(rows, changes, hashlib.sha256(path.read_bytes()).hexdigest(), release)
        Path(plan_out).write_text(json.dumps(plan, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        self.stdout.write("release plan: %s %s sha256=%s" % (plan_out, plan["counts"],
                                                            hashlib.sha256(Path(plan_out).read_bytes()).hexdigest()))

    def run_apply_plan(self, plan_path, apply):
        import json
        from django.conf import settings
        from catalog import master_sync

        if not plan_path:
            raise CommandError("--plan-out <plan.json> is required")
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        state, problems = master_sync.check_plan(plan)
        self.stdout.write("database: %s | plan %s | state: %s | counts %s" % (
            settings.DATABASES["default"]["NAME"], plan.get("release") or plan_path, state, plan.get("counts")))
        for problem in problems[:20]:
            self.stdout.write("  PROBLEM " + problem)
        if state == "mismatch":
            raise CommandError("plan does not match this database (%d problems); nothing written" % len(problems))
        if state == "applied":
            leftover = master_sync.final_state_problems(plan)
            if leftover:
                raise CommandError("changes applied but final state differs: %s" % leftover)
            self.stdout.write("already applied: nothing to write")
            return
        if not apply:
            self.stdout.write("dry run: plan is pending and applicable (pass --apply)")
            return
        try:
            written = master_sync.apply_plan(plan)
        except ValueError as exc:
            raise CommandError(str(exc))
        self.stdout.write("applied: %d writes; final state matches the plan" % written)

    def run_refresh(self, path):
        if not path.exists():
            raise CommandError("%s does not exist" % path)
        rows, meta, extra = self._load(path)
        stamp = cm.now_utc()
        renumbered = cm.refresh_derived(rows, rows.setdefault("Changelog", []), "chronology recomputed on refresh", stamp)
        meta = dict(meta)
        meta["Schema"] = cm.SCHEMA
        meta = cm.refresh_meta(meta, rows, stamp)
        cm.write_workbook(rows, meta, path, extra)
        self.stdout.write("refresh: %s renumbered=%d" % (path, renumbered))

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
