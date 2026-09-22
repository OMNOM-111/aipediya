from decimal import Decimal
from django import template
from catalog.context import TEXT
from catalog.comparison import format_context, localized

register = template.Library()

@register.filter
def local(value, lang):
    return localized(value, lang)

@register.filter
def label(key, lang):
    return TEXT.get(str(key), (key, key))[lang == "en"]

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
    "ru": ("Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"),
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
}

@register.filter
def month_year(value, lang):
    """Release date for the table/panel: day + abbreviated month + year.

    RU (day first): 29 Июн 2021
    EN US (month first): Jun 29, 2021
    """
    if not value:
        return ""
    month = MONTHS["en" if lang == "en" else "ru"][value.month - 1]
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
