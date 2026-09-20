from urllib.parse import urlencode

from django.conf import settings

from .models import ModelVersion


def public_url(path, lang=None, **params):
    values = {"lang": lang} if lang else {}
    values.update({key: value for key, value in params.items() if value not in (None, "")})
    query = urlencode(values)
    return f"{settings.AIPEDIA_PUBLIC_ORIGIN}{path}{'?' + query if query else ''}"


def sitemap_entries():
    yield public_url("/", "ru"), None
    yield public_url("/", "en"), None
    for model in ModelVersion.objects.filter(published=True).only("slug", "checked"):
        path = f"/models/{model.slug}"
        yield public_url(path, "ru"), model.checked
        yield public_url(path, "en"), model.checked
