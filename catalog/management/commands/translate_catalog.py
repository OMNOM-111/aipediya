import json

from django.core.management.base import BaseCommand

from catalog import translation_pipeline as pipeline
from catalog.models import ModelVersion, Tool
from catalog.translation_providers import get_provider


class Command(BaseCommand):
    help = "Translate missing/outdated dynamic catalog fields via the configured provider."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["models", "tools", "all"], default="all")
        parser.add_argument("--languages", default="", help="Comma-separated locale codes; default: all pipeline languages.")
        parser.add_argument("--states", default="missing,outdated", help="Comma-separated states to (re)translate.")
        parser.add_argument("--provider", default="", help="Override the configured provider (mock/azure/null).")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--batch-size", type=int, default=50, help="Texts per provider request during priming.")
        parser.add_argument("--status", action="store_true", help="Report state counts without translating.")
        parser.add_argument("--dry-run", action="store_true", help="Report the plan without writing translations.")

    def _objects(self, kind, limit):
        count = 0
        querysets = []
        if kind in ("models", "all"):
            querysets.append(ModelVersion.objects.filter(published=True, entry_type="model"))
        if kind in ("tools", "all"):
            querysets.append(Tool.objects.filter(published=True))
        for queryset in querysets:
            for obj in queryset.iterator():
                yield obj
                count += 1
                if limit and count >= limit:
                    return

    def handle(self, *args, **options):
        languages = [code.strip() for code in options["languages"].split(",") if code.strip()] or None
        if options["status"]:
            self.stdout.write(json.dumps(
                {"status": pipeline.pending_summary(languages)}, sort_keys=True, ensure_ascii=False
            ))
            return
        states = tuple(state.strip() for state in options["states"].split(",") if state.strip()) or ("missing", "outdated")
        provider = get_provider(options["provider"] or None)
        limit = options["limit"] or None
        result = {"provider": provider.name, "states": list(states), "dry_run": options["dry_run"]}
        if options["dry_run"]:
            # Project the real provider character spend. The pipeline reuses one
            # translation per unique (English source, language), so only the
            # first occurrence of each pair is billable; already-stored
            # translations cost nothing on a re-run.
            memory = pipeline.load_translation_memory(languages)
            seen = set()
            objects = to_translate = chars_billable = chars_naive = 0
            for obj in self._objects(options["kind"], limit):
                objects += 1
                for item in pipeline.plan(obj, languages):
                    if item["state"] not in states or not item["source"]:
                        continue
                    to_translate += 1
                    key = (item["hash"], item["language"])
                    if key in memory or key in seen:
                        continue
                    seen.add(key)
                    chars_billable += len(item["source"])
                    chars_naive += len(item["source"])
            result.update({
                "objects": objects, "to_translate": to_translate,
                "chars_billable": chars_billable,
                "unique_pairs": len(seen),
                "free_tier_chars": 2_000_000,
            })
            self.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False))
            return
        memory = pipeline.load_translation_memory(languages)
        objects = list(self._objects(options["kind"], limit))
        memory, prime_stats = pipeline.prime_translation_memory(
            objects, provider, languages=languages, states=states,
            memory=memory, batch_size=options["batch_size"],
        )
        totals = {"objects": 0, "translated": 0, "reused": 0, "skipped": 0, "failed": 0}
        for obj in objects:
            summary = pipeline.translate_object(
                obj, provider=provider, languages=languages, states=states, memory=memory
            )
            totals["objects"] += 1
            for key in ("translated", "reused", "skipped", "failed"):
                totals[key] += summary[key]
        totals["provider_requests"] = prime_stats["requests"]
        totals["provider_chars"] = prime_stats["chars"]
        totals["provider_failed"] = prime_stats["failed"]
        result.update(totals)
        self.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False))
