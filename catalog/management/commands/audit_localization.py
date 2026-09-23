"""Audit localization completeness across all supported languages.

Reports, per language, any gaps in the static interface strings, the category
and country reference tables, and the machine-translated dynamic catalog
fields. Read-only: it never calls a translation provider and never writes.

Usage::

    python manage.py audit_localization
    python manage.py audit_localization --languages fr,de --fail-on-gap
"""
import json

from django.core.management.base import BaseCommand

from catalog import translation_pipeline as pipeline
from catalog.context import TEXT
from catalog.countries import COUNTRY_TRANSLATIONS
from catalog.i18n import SUPPORTED_CODES
from catalog.models import Country
from catalog.ui_translations import CATEGORY_TRANSLATIONS, TRANSLATIONS


class Command(BaseCommand):
    help = "Report per-language localization gaps for UI strings and catalog data."

    # Interface keys that intentionally stay identical in every language:
    # acronyms and brand terms (API, CLI, IDE, GitHub, OCR, 3D) plus one key
    # whose value is deliberately empty. They resolve via the English fallback
    # and are never real localization gaps.
    UNIVERSAL_UI_KEYS = frozenset({"api", "cli", "ide", "github", "3d", "ocr", "no_rating_yet"})

    def add_arguments(self, parser):
        parser.add_argument("--languages", default="", help="Comma-separated locale codes; default: all non-base languages.")
        parser.add_argument("--fail-on-gap", action="store_true", help="Exit non-zero when any gap is found.")

    def handle(self, *args, **options):
        selected = [code.strip() for code in options["languages"].split(",") if code.strip()]
        languages = [c for c in SUPPORTED_CODES if c not in ("ru", "en") and (not selected or c in selected)]
        ui_keys = set(TEXT) - self.UNIVERSAL_UI_KEYS
        category_codes = set(next(iter(CATEGORY_TRANSLATIONS.values()), {}))
        country_codes = {c.code.upper() for c in Country.objects.all()}
        dynamic = pipeline.pending_summary(languages)
        # Split the raw "missing" into a real content gap (English source exists
        # but is untranslated) versus empty-source slots (nothing to translate),
        # so an empty optional field is never mistaken for a localization gap.
        from catalog.models import ModelVersion, Tool
        translated = outdated = untranslated = no_source = 0
        objs = list(ModelVersion.objects.filter(published=True, entry_type="model")) + list(Tool.objects.filter(published=True))
        for obj in objs:
            for item in pipeline.plan(obj, languages):
                if not item["source"]:
                    no_source += 1
                elif item["state"] in ("current", "reviewed"):
                    translated += 1
                elif item["state"] == "outdated":
                    outdated += 1
                else:
                    untranslated += 1
        dynamic_detail = {
            "translated": translated, "outdated": outdated,
            "untranslated_with_source": untranslated, "empty_source": no_source,
        }

        report = {}
        total_gaps = 0
        for lang in languages:
            ui_missing = sorted(k for k in ui_keys if k not in TRANSLATIONS.get(lang, {}))
            cat_missing = sorted(c for c in category_codes if c not in CATEGORY_TRANSLATIONS.get(lang, {}))
            country_missing = sorted(
                code for code in country_codes
                if lang not in COUNTRY_TRANSLATIONS.get(code, {})
            )
            gaps = len(ui_missing) + len(cat_missing) + len(country_missing)
            total_gaps += gaps
            report[lang] = {
                "ui_missing": ui_missing,
                "category_missing": cat_missing,
                "country_missing": country_missing,
            }

        result = {
            "languages": languages,
            "ui_keys": len(ui_keys),
            "category_codes": len(category_codes),
            "country_codes": len(country_codes),
            "static_gaps": total_gaps,
            "dynamic": dynamic,
            "dynamic_detail": dynamic_detail,
            "per_language": report,
        }
        self.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
        if options["fail_on_gap"] and (total_gaps or untranslated or outdated):
            self.stderr.write("Localization gaps detected.")
            raise SystemExit(1)
