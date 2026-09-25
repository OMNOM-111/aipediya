from decimal import Decimal
from django import template
from catalog.context import TEXT, t, category_label
from catalog.comparison import format_context, localized
from catalog.countries import country_label
from catalog.evaluation_labels import evaluation_label

register = template.Library()

@register.filter
def local(value, lang):
    return localized(value, lang)

@register.filter
def label(key, lang):
    return t(str(key), lang)

@register.filter
def eval_label(value, lang):
    return evaluation_label(value, lang)

@register.filter
def catlabel(cat, lang):
    return category_label(cat.code, cat.labels, lang)

@register.filter
def country_name(country, lang):
    return country_label(country, lang)

@register.filter
def unit_label(key, lang):
    return label('unit_image' if key == 'image' else key, lang)

@register.filter
def money(value):
    if value is None:
        return ""
    result = format(Decimal(value), "f").rstrip("0").rstrip(".")
    return result or "0"

@register.filter
def catnum(value):
    if value in (None, ""):
        return ""
    number = int(value)
    return f"{number:03d}" if number < 1000 else str(number)

@register.filter
def tokens(value):
    return format_context(value)

MONTHS = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "ru": ("Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"),
    "es": ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"),
    "fr": ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."),
    "ar": ("يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"),
    "pt-BR": ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"),
    "de": ("Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."),
    "hi": ("जन॰", "फ़र॰", "मार्च", "अप्रैल", "मई", "जून", "जुल॰", "अग॰", "सित॰", "अक्तू॰", "नव॰", "दिस॰"),
    "id": ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"),
    "tr": ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"),
    "vi": ("Thg 1", "Thg 2", "Thg 3", "Thg 4", "Thg 5", "Thg 6", "Thg 7", "Thg 8", "Thg 9", "Thg 10", "Thg 11", "Thg 12"),
    "it": ("gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"),
    "pl": ("sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"),
    "uk": ("січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру"),
    "fa": ("ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"),
    "th": ("ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."),
    "nl": ("jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"),
    "bn": ("জানু", "ফেব্রু", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টে", "অক্টো", "নভে", "ডিসে"),
}

@register.filter
def month_year(value, lang):
    """Release date shown in the table and panel, formatted for the locale.

    CJK locales use the native year/month/day order; English is month-first;
    every other locale is day-first. Locales without a month table fall back to
    English month names.
    """
    if not value:
        return ""
    if lang in ("ja", "zh-Hans", "zh-Hant"):
        return f"{value.year}年{value.month}月{value.day}日"
    if lang == "ko":
        return f"{value.year}년 {value.month}월 {value.day}일"
    month = MONTHS.get(lang, MONTHS["en"])[value.month - 1]
    if lang == "en":
        return f"{month} {value.day}, {value.year}"
    return f"{value.day} {month} {value.year}"

@register.filter
def month_only(value, lang):
    """Month + year without a day, for 'month'-precision approximate dates."""
    if not value:
        return ""
    if lang in ("ja", "zh-Hans", "zh-Hant"):
        return f"{value.year}年{value.month}月"
    if lang == "ko":
        return f"{value.year}년 {value.month}월"
    month = MONTHS.get(lang, MONTHS["en"])[value.month - 1]
    return f"{month} {value.year}"

@register.filter
def approx_label(obj, lang):
    """≈-prefixed approximate release-evidence date, at the stored precision.

    Never used when an exact ``released`` date exists. 'day' precision renders
    the full date; 'month' (or unset) renders month + year. Always carries the
    ≈ prefix so it is never read as an exact release.
    """
    approx = getattr(obj, "approx_released", None)
    if not approx:
        return ""
    prec = getattr(obj, "approx_precision", "")
    if prec == "day":
        return f"≈ {month_year(approx, lang)}"
    if prec == "year":
        return f"≈ {approx.year}"
    return f"≈ {month_only(approx, lang)}"

@register.filter
def grouped(value):
    if value in (None, ""):
        return "0"
    return f"{int(value):,}".replace(",", " ")

# Parameters that must never be carried into a link: fragments (partial),
# the language (it is in the path) and the old catalog switch (kind).
_NEVER_LINKED = ("partial", "lang", "kind")


@register.simple_tag(takes_context=True)
def query(context, **changes):
    params = context["request"].GET.copy()
    for key in _NEVER_LINKED:
        params.pop(key, None)
    if "page" not in changes:
        params.pop("page", None)
    for key, value in changes.items():
        if value is None or value == "" or (key == "page" and str(value) == "1"):
            params.pop(key, None)
        else:
            params[key] = str(value)
    encoded = params.urlencode()
    return "?" + encoded if encoded else context["request"].path


@register.simple_tag(takes_context=True)
def qsuffix(context, **changes):
    """Like ``query`` but returns "" when nothing remains (for appending)."""
    result = query(context, **changes)
    return result if result.startswith("?") else ""


@register.simple_tag(takes_context=True)
def lurl(context, name, *args):
    """Localized path of a named route for the page language."""
    from django.urls import reverse
    from catalog.locale_urls import localize
    return localize(reverse(name, args=args), context.get("lang") or "en")


@register.simple_tag(takes_context=True)
def lpath(context, neutral_path):
    from catalog.locale_urls import localize
    return localize(neutral_path, context.get("lang") or "en")


@register.simple_tag
def jsonld(data):
    from django.utils.safestring import mark_safe
    from catalog.seo import json_ld_script
    return mark_safe(json_ld_script(data))


@register.filter
def fallback_attr(value, lang):
    """' lang="en"' when a localized JSON value has no text for ``lang``.

    Marks English fallback prose honestly in HTML instead of presenting it as
    a translation. Brand names and numbers are not affected (they are not
    localized fields)."""
    from django.utils.safestring import mark_safe
    if isinstance(value, dict) and lang not in ("en",) and not (value.get(lang) or "").strip():
        if (value.get("en") or "").strip():
            return mark_safe(' lang="en"')
        if (value.get("ru") or "").strip():
            return mark_safe(' lang="ru"')
    return ""
