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
def grouped(value):
    if value in (None, ""):
        return "0"
    return f"{int(value):,}".replace(",", " ")

@register.simple_tag(takes_context=True)
def query(context, **changes):
    params = context["request"].GET.copy()
    if "page" not in changes:
        params.pop("page", None)
    for key, value in changes.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = str(value)
    return "?" + params.urlencode()
