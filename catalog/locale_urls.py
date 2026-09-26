"""Central builder for language-specific public URLs (ADR D-2026-09-25-locale-paths).

Every public page has one address per language:

* English (``DEFAULT_LANG``) lives on the unprefixed root: ``/``, ``/tools/``,
  ``/models/<slug>``; it is also the ``x-default`` target.
* Every other locale lives under a lower-case path prefix: ``/ru/``,
  ``/zh-hans/models/<slug>``, ``/pt-br/tools/``.

The language of such an address never depends on cookies, Accept-Language,
country headers or the User-Agent. Legacy ``?lang=`` links answer with one
permanent redirect to the equivalent address (see :func:`legacy_target`).
Nothing else in the project should concatenate locale prefixes by hand.
"""
import re
from urllib.parse import urlencode

from django.conf import settings

from .i18n import DEFAULT_LANG, SUPPORTED_CODES, _ALIAS, normalize_lang

# Canonical path segment per language code, e.g. "zh-Hans" -> "zh-hans".
URL_CODE = {code: code.lower() for code in SUPPORTED_CODES}
FROM_URL_CODE = {segment: code for code, segment in URL_CODE.items()}
# Segments that are accepted and permanently redirected to the canonical one:
# case/underscore variants are handled separately; these are script/region
# aliases of the same language (zh-cn -> zh-hans, pt -> pt-br). Remaps to a
# *different* language (be -> ru, ca -> es) are deliberately not path aliases.
PATH_ALIASES = {
    key: value for key, value in _ALIAS.items()
    if key.split("-")[0] == value.lower().split("-")[0] and key != URL_CODE[value]
}

# Language-neutral page paths that exist in every locale. Everything else
# (static files, admin, robots, sitemaps, health, dataset downloads, IndexNow
# key) is language-neutral and only served unprefixed.
_LOCALIZED = re.compile(
    r"^/(?:"
    r"|tools/"
    r"|models/[-a-zA-Z0-9_]+"
    r"|tools/[-a-zA-Z0-9_]+"
    r"|methodology"
    r"|privacy"
    r"|history/"
    r"|history/source/[-a-zA-Z0-9_]+"
    r"|collections/"
    r"|collections/[-a-z0-9]+"
    r"|compare/model-context"
    r"|api-pricing"
    r"|datasets/"
    r"|datasets/(?:models|tools)"
    r")$"
)

# Never carried into a language-switcher link.
DROPPED_ON_SWITCH = frozenset({"lang", "kind", "partial"})


def is_localized_path(neutral_path):
    return bool(_LOCALIZED.match(neutral_path))


def prefix(lang):
    return "" if lang == DEFAULT_LANG else "/" + URL_CODE[lang]


def localize(neutral_path, lang):
    """``/models/x`` + ``ru`` -> ``/ru/models/x``; ``/`` + ``ru`` -> ``/ru/``."""
    if lang not in URL_CODE:
        lang = DEFAULT_LANG
    return prefix(lang) + neutral_path


def absolute(neutral_path, lang, **params):
    """Absolute public URL built from settings, never from the request Host."""
    query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
    return f"{settings.AIPEDIA_PUBLIC_ORIGIN}{localize(neutral_path, lang)}{'?' + query if query else ''}"


def parse_segment(segment):
    """Return ``(code, canonical)`` for a first path segment, or ``(None, False)``.

    ``canonical`` is False when the segment names a supported locale in a
    non-canonical spelling (``zh-Hans``, ``pt_BR``, ``zh-cn``, ``en``) that must
    be permanently redirected.
    """
    if not segment:
        return None, False
    if segment in FROM_URL_CODE:
        code = FROM_URL_CODE[segment]
        return code, code != DEFAULT_LANG
    low = segment.lower().replace("_", "-")
    if low in FROM_URL_CODE:
        return FROM_URL_CODE[low], False
    if low in PATH_ALIASES:
        return PATH_ALIASES[low], False
    return None, False


def split(path):
    """Split a request path into ``(lang, neutral_path, redirect_to)``.

    ``lang`` is None for an unprefixed path (English or a language-neutral
    endpoint). ``redirect_to`` is a canonical path when the prefix spelling,
    ``/en/`` or a missing trailing slash on a locale home must be normalized.
    """
    match = re.match(r"^/([^/]+)(/.*)?$", path)
    if not match:
        return None, path, None
    code, canonical = parse_segment(match.group(1))
    if code is None:
        return None, path, None
    rest = match.group(2) or ""
    neutral = rest or "/"
    if not is_localized_path(neutral):
        return code, neutral, None
    if not canonical or not rest:
        return code, neutral, localize(neutral, code)
    return code, neutral, None


def legacy_target(neutral_path, query_dict):
    """Clean canonical address for an old full-page ``?lang=`` / ``?kind=`` link.

    Returns ``(path_with_query, lang)``. Card and static-page presentation
    parameters are discarded so old card URLs resolve in one hop to the clean
    document. Catalog filters, sorting and pagination are retained for users;
    filtered listings remain robots-blocked and noindex. Fragment requests are
    handled separately by middleware. ``kind=tool`` on the catalog root maps
    to ``/tools/``.
    """
    lang = normalize_lang(query_dict.get("lang")) or DEFAULT_LANG
    kind = query_dict.get("kind")
    if neutral_path == "/" and kind == "tool":
        neutral_path = "/tools/"
    if neutral_path in ("/", "/tools/"):
        params = query_dict.copy()
        for key in ("lang", "kind"):
            params.pop(key, None)
        if params.get("page") == "1":
            params.pop("page", None)
        query = params.urlencode()
        return localize(neutral_path, lang) + ("?" + query if query else ""), lang
    return localize(neutral_path, lang), lang


def switch_url(request, code):
    """Same page in another locale, keeping presentation parameters."""
    neutral = getattr(request, "aipedia_neutral_path", request.path)
    if not is_localized_path(neutral):
        neutral = "/"
    params = request.GET.copy()
    for key in DROPPED_ON_SWITCH:
        params.pop(key, None)
    query = params.urlencode()
    return localize(neutral, code) + ("?" + query if query else "")
