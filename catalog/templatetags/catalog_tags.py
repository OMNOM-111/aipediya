from decimal import Decimal
from django import template
from catalog.context import TEXT
from catalog.comparison import localized

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
