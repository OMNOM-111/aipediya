from django.conf import settings
from django.utils.cache import patch_vary_headers

from .i18n import (
    LANG_COOKIE, LANG_COOKIE_MAX_AGE, direction, resolve_language,
)


class LanguageMiddleware:
    """Negotiate the request language once and remember an explicit choice.

    A single source of truth for both views and templates. A deliberate
    ``?lang=`` selection is stored in a cookie so the preference survives later
    visits and always outranks Accept-Language or any country hint. Negotiated
    (non-URL) responses vary by cookie and Accept-Language for correct caching.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang, explicit = resolve_language(request)
        request.aipedia_lang = lang
        request.aipedia_lang_explicit = explicit
        request.aipedia_dir = direction(lang)
        response = self.get_response(request)
        if explicit and request.COOKIES.get(LANG_COOKIE) != lang and not request.path.startswith("/admin/"):
            response.set_cookie(
                LANG_COOKIE, lang, max_age=LANG_COOKIE_MAX_AGE,
                secure=not settings.DEBUG, httponly=False, samesite="Lax",
            )
        if not explicit:
            patch_vary_headers(response, ("Cookie", "Accept-Language"))
        return response


class HeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.path.startswith("/admin/"):
            response["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        return response
