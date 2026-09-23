"""Offline quality audit of stored machine translations.

Compares every stored translation against its English source without calling any
provider. Flags mechanical quality problems that do not need a native speaker:
dropped numbers, dropped brand/model/API/URL identifiers, untranslated
passthrough (no target script / identical to English), encoding artifacts, and
extreme length ratios (possible omission or addition).
"""
import json
import re
import unicodedata

from django.core.management.base import BaseCommand

from catalog.models import ModelVersion, Tool
from catalog.translation_pipeline import MODEL_FIELDS, TOOL_FIELDS, english_source, target_languages

URL_RE = re.compile(r"https?://\S+")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
# Identifiers that must survive translation: URLs, versioned/hyphenated model
# names (GPT-4, claude-3-haiku, Veo 3.1), and all-caps acronyms (API, OCR, ECI).
IDENT_RE = re.compile(r"https?://\S+|\b[A-Za-z][\w.]*[-/][\w.\-/]*\d[\w.\-/]*|\b[A-Za-z]*\d[\w.]*\b|\b[A-Z]{2,}\b")

# Eastern-Arabic / Persian digits normalize to ASCII so localized numerals
# (۱۲۳ / ١٢٣) are recognized as the same number.
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(s):
    return s.translate(_DIGITS)


def number_present(num, text):
    normalized = normalize_digits(text)
    # A locale may swap the decimal/thousands separator (1.05 -> 1,05).
    variants = {num, num.replace(",", "."), num.replace(".", ","), num.replace(",", "").replace(".", "")}
    return any(v in normalized for v in variants)

# Minimum fraction of characters that must be in the language's own script for a
# non-Latin locale (CJK/Arabic/etc. mix in Latin brand names, so this is loose).
SCRIPT_RANGES = {
    "ru": ("CYRILLIC",), "uk": ("CYRILLIC",),
    "ar": ("ARABIC",), "fa": ("ARABIC",),
    "hi": ("DEVANAGARI",), "bn": ("BENGALI",), "th": ("THAI",),
    "ja": ("CJK", "HIRAGANA", "KATAKANA"), "ko": ("HANGUL",),
    "zh-Hans": ("CJK",), "zh-Hant": ("CJK",),
}
LATIN_LANGS = {"es", "fr", "de", "it", "pl", "nl", "id", "vi", "tr", "pt-BR"}


def has_script(text, families):
    for ch in text:
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if any(fam in name for fam in families):
            return True
    return False


class Command(BaseCommand):
    help = "Offline mechanical quality audit of stored translations (no provider calls)."

    def add_arguments(self, parser):
        parser.add_argument("--languages", default="")
        parser.add_argument("--samples", type=int, default=0, help="Print N example issues.")

    def _iter_fields(self):
        for obj in ModelVersion.objects.filter(published=True, entry_type="model"):
            for field in MODEL_FIELDS:
                value = getattr(obj, field, None)
                if isinstance(value, dict) and english_source(value):
                    yield obj, field, value
        for obj in Tool.objects.filter(published=True):
            for field in TOOL_FIELDS:
                value = getattr(obj, field, None)
                if isinstance(value, dict) and english_source(value):
                    yield obj, field, value

    def handle(self, *args, **options):
        selected = [c.strip() for c in options["languages"].split(",") if c.strip()]
        langs = [c for c in target_languages() if not selected or c in selected]
        checks = ("empty", "number_dropped", "identifier_dropped_latin", "identifier_transliterated",
                  "no_target_script", "passthrough", "escape_artifact", "length_extreme")
        per_lang = {l: {c: 0 for c in checks} for l in langs}
        per_lang_total = {l: 0 for l in langs}
        samples = []

        for obj, field, value in self._iter_fields():
            source = value["en"]
            src_numbers = NUMBER_RE.findall(source)
            src_idents = set(IDENT_RE.findall(source))
            for lang in langs:
                text = value.get(lang)
                if not text:
                    continue  # not translated (empty-source handled upstream)
                per_lang_total[lang] += 1
                issues = []
                if not text.strip():
                    issues.append("empty")
                for num in src_numbers:
                    if not number_present(num, text):
                        issues.append("number_dropped")
                        break
                # Non-Latin locales commonly transliterate proper nouns, which is
                # acceptable; only Latin-script targets must keep them verbatim.
                latin_target = lang in LATIN_LANGS
                for ident in src_idents:
                    if len(ident) >= 3 and ident not in text:
                        issues.append("identifier_dropped_latin" if latin_target else "identifier_transliterated")
                        break
                if lang in SCRIPT_RANGES and not has_script(text, SCRIPT_RANGES[lang]):
                    issues.append("no_target_script")
                if lang in LATIN_LANGS and text.strip() == source.strip():
                    issues.append("passthrough")
                if "\\u" in text:
                    issues.append("escape_artifact")
                ratio = len(text) / max(1, len(source))
                low = 0.15 if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else (0.3 if lang in SCRIPT_RANGES else 0.5)
                if ratio < low or ratio > 3.0:
                    issues.append("length_extreme")
                for issue in issues:
                    per_lang[lang][issue] += 1
                if issues and len(samples) < options["samples"]:
                    samples.append({"model": getattr(obj, "slug", obj.pk), "field": field,
                                    "lang": lang, "issues": issues,
                                    "en": source[:90], "tr": text[:90]})

        totals = {c: sum(per_lang[l][c] for l in langs) for c in checks}
        result = {
            "translations_checked": sum(per_lang_total.values()),
            "issue_totals": totals,
            "per_language_totals": {l: {c: v for c, v in per_lang[l].items() if v} for l in langs},
        }
        result["per_language_totals"] = {l: d for l, d in result["per_language_totals"].items() if d}
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        for s in samples:
            self.stdout.write(json.dumps(s, ensure_ascii=False))
