import re

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect

from .i18n import DEFAULT_LANG, direction, normalize_lang
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
            request.path_info = neutral
        else:
            lang = DEFAULT_LANG
            neutral = path
        request.aipedia_lang = lang
        request.aipedia_dir = direction(lang)
        request.aipedia_neutral_path = neutral
        if redirect_to:
            if not request.GET.get("partial") and ("lang" in request.GET or "kind" in request.GET):
                # Prefix spelling and legacy query normalize together: one 301.
                legacy = self._legacy(request, neutral, prefixed=True)
                if legacy is not None:
                    return legacy
            return self._redirect(request, redirect_to, keep_query=True)
        if is_localized_path(neutral) and ("lang" in request.GET or "kind" in request.GET):
            legacy = self._legacy(request, neutral, prefixed=path != neutral)
            if legacy is not None:
                return legacy
        return self.get_response(request)

    def _legacy(self, request, neutral, prefixed):
        entity = _ENTITY.match(neutral)
        if entity and request.GET.get("partial"):
            # Old cached AJAX links still get fragments, never an indexable
            # full page. The path wins for prefixed URLs.
            if not prefixed:
                lang = normalize_lang(request.GET.get("lang")) or DEFAULT_LANG
                request.aipedia_lang = lang
                request.aipedia_dir = direction(lang)
            return None
        params = request.GET.copy()
        if prefixed:
            # The path already names the language; a stray ?lang= is dropped.
            params.pop("lang", None)
            params.setlist("lang", [request.aipedia_lang])
        if entity and neutral not in ("/tools/",):
            from .readiness import is_public_slug

            kind = "tool" if entity.group(1) == "tools" else "model"
            if not is_public_slug(kind, entity.group(2)):
                # A confirmed alias also resolves in one hop, even when both
                # the path prefix and query are noncanonical.
                alias_path = self._published_alias_path(kind, entity.group(2))
                if alias_path:
                    target, _ = legacy_target(alias_path, params)
                    return HttpResponsePermanentRedirect(target)
                # The view answers 404 for unknown/unpublished records.
                if not prefixed:
                    lang = normalize_lang(request.GET.get("lang")) or DEFAULT_LANG
                    request.aipedia_lang = lang
                    request.aipedia_dir = direction(lang)
                return None
        target, _ = legacy_target(neutral, params)
        return HttpResponsePermanentRedirect(target)

    @staticmethod
    def _published_alias_path(kind, slug):
        from .models import ModelVersion, Tool
        from .readiness import is_public_slug

        if kind == "model":
            target = ModelVersion.objects.filter(
                slug=slug, entry_type="model", published=False
            ).exclude(redirect_to="").values_list("redirect_to", flat=True).first()
        else:
            target = Tool.objects.filter(slug=slug, published=False).exclude(
                redirect_to=""
            ).values_list("redirect_to", flat=True).first()
        if target:
            for target_kind in (kind, "tool" if kind == "model" else "model"):
                if is_public_slug(target_kind, target):
                    return f"/{'tools' if target_kind == 'tool' else 'models'}/{target}"
        return None

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
