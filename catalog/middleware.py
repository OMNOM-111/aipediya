import re

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect

from .i18n import DEFAULT_LANG, direction
from .locale_urls import is_localized_path, legacy_target, split

_ENTITY = re.compile(r"^/(models|tools)/([-a-zA-Z0-9_]+)$")


class LanguageMiddleware:
    """Take the language from the URL path only (ADR D-2026-09-25-locale-paths).

    ``/ru/models/x`` is Russian, ``/models/x`` is English, whatever the cookie,
    Accept-Language, country header or User-Agent say. The locale prefix is
    stripped from ``path_info`` so one language-neutral URLconf serves all 22
    locales; ``request.path`` keeps the public address. Old ``?lang=`` links
    get exactly one permanent redirect to the equivalent address; unknown or
    unpublished entities are answered with 404, never redirected home.
    Responses therefore never vary on Cookie or Accept-Language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        lang, neutral, redirect_to = split(path)
        if lang is not None:
            if not is_localized_path(neutral):
                return self._not_found(request, lang)
            if redirect_to:
                return self._redirect(request, redirect_to, keep_query=True)
            request.path_info = neutral
        else:
            lang = DEFAULT_LANG
            neutral = path
        request.aipedia_lang = lang
        request.aipedia_dir = direction(lang)
        request.aipedia_neutral_path = neutral
        if is_localized_path(neutral) and ("lang" in request.GET or "kind" in request.GET):
            legacy = self._legacy(request, neutral, prefixed=path != neutral)
            if legacy is not None:
                return legacy
        return self.get_response(request)

    def _legacy(self, request, neutral, prefixed):
        entity = _ENTITY.match(neutral)
        if entity and neutral not in ("/tools/",):
            from .readiness import is_public_slug

            kind = "tool" if entity.group(1) == "tools" else "model"
            if not is_public_slug(kind, entity.group(2)):
                return None  # the view answers 404 for unknown/unpublished records
        params = request.GET.copy()
        if prefixed:
            # The path already names the language; a stray ?lang= is dropped.
            params.pop("lang", None)
            params.setlist("lang", [request.aipedia_lang])
        target, _ = legacy_target(neutral, params)
        return HttpResponsePermanentRedirect(target)

    @staticmethod
    def _redirect(request, target, keep_query):
        query = request.META.get("QUERY_STRING", "")
        return HttpResponsePermanentRedirect(target + ("?" + query if keep_query and query else ""))

    @staticmethod
    def _not_found(request, lang):
        request.aipedia_lang = lang
        request.aipedia_dir = direction(lang)
        request.aipedia_neutral_path = "/"
        return HttpResponseNotFound("Not found", content_type="text/plain; charset=utf-8")


class HeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.path.startswith("/admin/"):
            response["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        if not getattr(settings, "AIPEDIA_INDEXING_ALLOWED", False):
            # Local (and any non-production run) must never be indexed.
            response["X-Robots-Tag"] = "noindex, nofollow"
        elif request.GET.get("partial"):
            response["X-Robots-Tag"] = "noindex"
        return response
