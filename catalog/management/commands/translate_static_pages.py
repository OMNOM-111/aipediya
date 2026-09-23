"""Machine-translate public static-page prose into all pipeline languages.

Fills ``data/static_page_translations.json`` (a ``source_hash -> {lang: text}``
overlay) for the pages in :data:`catalog.static_pages.STATIC_PAGES`. Idempotent
and deduplicated: an unchanged block is never re-sent to the provider.
"""
import json

from django.core.management.base import BaseCommand

from catalog import static_pages
from catalog.translation_pipeline import target_languages
from catalog.translation_providers import TranslationError, get_provider


class Command(BaseCommand):
    help = "Translate public static-page prose (privacy, …) into all pipeline languages."

    def add_arguments(self, parser):
        parser.add_argument("--provider", default="", help="Override the configured provider (mock/azure/null).")
        parser.add_argument("--languages", default="", help="Comma-separated locale codes; default: all pipeline languages.")
        parser.add_argument("--dry-run", action="store_true", help="Report the plan without writing.")

    def handle(self, *args, **options):
        provider = get_provider(options["provider"] or None)
        languages = [c.strip() for c in options["languages"].split(",") if c.strip()] or None
        langs = target_languages(languages)
        overlay = {}
        if static_pages._OVERLAY_PATH.exists():
            overlay = json.loads(static_pages._OVERLAY_PATH.read_text(encoding="utf-8"))

        sources = []
        for blocks in static_pages.STATIC_PAGES.values():
            for _tag, english, _russian in blocks:
                if english:
                    sources.append(english)
        sources += [english for english, _ru in static_pages.STATIC_LABELS.values() if english]
        # Unique (source, language) pairs still needing a translation.
        pending = {}
        for english in sources:
            digest = static_pages.source_hash(english)
            for lang in langs:
                if overlay.get(digest, {}).get(lang):
                    continue
                pending.setdefault(lang, []).append((digest, english))

        result = {"provider": provider.name, "blocks": len(set(sources)), "languages": langs,
                  "to_translate": sum(len(v) for v in pending.values()), "dry_run": options["dry_run"]}
        if options["dry_run"] or not pending:
            self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return

        requests = chars = 0
        for lang, entries in pending.items():
            try:
                texts = provider.translate_batch([src for _d, src in entries], lang, static_pages.SOURCE_LANGUAGE)
                requests += 1
            except TranslationError:
                continue
            for (digest, src), text in zip(entries, texts):
                if text:
                    overlay.setdefault(digest, {})[lang] = text
                    chars += len(src)
        static_pages._OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
        static_pages._OVERLAY_PATH.write_text(
            json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        static_pages.clear_overlay_cache()
        result.update({"provider_requests": requests, "provider_chars": chars})
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))
