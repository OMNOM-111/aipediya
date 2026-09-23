from urllib.parse import urlencode

from django.conf import settings

from .i18n import DEFAULT_LANG, SUPPORTED_CODES
from .models import ModelVersion, Tool


def public_url(path, lang=None, **params):
    values = {"lang": lang} if lang else {}
    values.update({key: value for key, value in params.items() if value not in (None, "")})
    query = urlencode(values)
    return f"{settings.AIPEDIA_PUBLIC_ORIGIN}{path}{'?' + query if query else ''}"


def alternate_links(path, page=None):
    """Return ``(alternates, x_default)`` for a page.

    ``alternates`` lists every supported locale as ``(code, url)`` for
    ``hreflang`` tags; ``x_default`` is the English URL used for
    ``hreflang="x-default"``.
    """
    alternates = [(code, public_url(path, code, page=page)) for code in SUPPORTED_CODES]
    return alternates, public_url(path, DEFAULT_LANG, page=page)


def localized_paths():
    yield "/", None
    for model in ModelVersion.objects.filter(published=True, entry_type="model").only("slug", "checked"):
        yield f"/models/{model.slug}", model.checked
    for tool in Tool.objects.filter(published=True).only("slug", "checked"):
        yield f"/tools/{tool.slug}", tool.checked


def sitemap_entries():
    """One entry per page with the English loc and every hreflang alternate."""
    for path, checked in localized_paths():
        alternates, x_default = alternate_links(path)
        yield {
            "loc": public_url(path, DEFAULT_LANG),
            "lastmod": checked,
            "alternates": alternates,
            "x_default": x_default,
        }
