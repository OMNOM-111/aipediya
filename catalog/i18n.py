"""Central language registry and request language negotiation.

One canonical catalog record stays language-neutral; only presentation is
localized. English is the primary language, the ``x-default`` target and the
final fallback. Public URLs keep the existing ``?lang=`` query parameter so no
address changes and every locale stays indexable.
"""

# (code, native name, text direction). Order is the language-switcher order.
LANGUAGES = (
    ("en", "English", "ltr"),
    ("ru", "Русский", "ltr"),
    ("zh-Hans", "简体中文", "ltr"),
    ("es", "Español", "ltr"),
    ("fr", "Français", "ltr"),
    ("ar", "العربية", "rtl"),
    ("pt-BR", "Português", "ltr"),
    ("de", "Deutsch", "ltr"),
    ("ja", "日本語", "ltr"),
    ("ko", "한국어", "ltr"),
    ("hi", "हिन्दी", "ltr"),
    ("id", "Bahasa Indonesia", "ltr"),
    ("tr", "Türkçe", "ltr"),
    ("vi", "Tiếng Việt", "ltr"),
    ("it", "Italiano", "ltr"),
    ("pl", "Polski", "ltr"),
    ("uk", "Українська", "ltr"),
    ("fa", "فارسی", "rtl"),
    ("th", "ไทย", "ltr"),
    ("nl", "Nederlands", "ltr"),
    ("bn", "বাংলা", "ltr"),
    ("zh-Hant", "繁體中文", "ltr"),
)

DEFAULT_LANG = "en"
LANG_COOKIE = "aipedia_lang"
LANG_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # one year

SUPPORTED_CODES = tuple(code for code, _, _ in LANGUAGES)
SUPPORTED = frozenset(SUPPORTED_CODES)
LANGUAGE_NAMES = {code: native for code, native, _ in LANGUAGES}
LANGUAGE_DIR = {code: direction for code, _, direction in LANGUAGES}
RTL_CODES = frozenset(code for code, _, direction in LANGUAGES if direction == "rtl")

# BCP-47 tags (lower-cased) mapped to our canonical codes. Region variants and
# script variants collapse onto the neutral catalog locale; the structure keeps
# room for pt-PT, zh-TW or zh-HK to split off later without a redesign.
_ALIAS = {
    "en": "en",
    "ru": "ru", "be": "ru",
    "es": "es", "ca": "es", "gl": "es",
    "fr": "fr",
    "ar": "ar",
    "de": "de",
    "ja": "ja",
    "ko": "ko",
    "hi": "hi",
    "id": "id", "in": "id",
    "tr": "tr",
    "vi": "vi",
    "it": "it",
    "pl": "pl",
    "uk": "uk",
    "fa": "fa", "prs": "fa",
    "th": "th",
    "nl": "nl",
    "bn": "bn",
    "pt": "pt-BR", "pt-br": "pt-BR", "pt-pt": "pt-BR",
    "zh": "zh-Hans", "zh-hans": "zh-Hans", "zh-cn": "zh-Hans",
    "zh-sg": "zh-Hans", "zh-my": "zh-Hans", "zh-chs": "zh-Hans",
    "zh-hant": "zh-Hant", "zh-tw": "zh-Hant", "zh-hk": "zh-Hant",
    "zh-mo": "zh-Hant", "zh-cht": "zh-Hant",
}

# Weak country -> language hint. Used only when no stronger language signal
# exists, and never overrides an explicit choice or Accept-Language.
COUNTRY_LANG = {
    "RU": "ru", "BY": "ru", "KZ": "ru", "KG": "ru",
    "CN": "zh-Hans", "SG": "zh-Hans",
    "TW": "zh-Hant", "HK": "zh-Hant", "MO": "zh-Hant",
    "SA": "ar", "AE": "ar", "EG": "ar", "DZ": "ar", "MA": "ar",
    "IQ": "ar", "JO": "ar", "KW": "ar", "QA": "ar", "OM": "ar",
    "IR": "fa", "AF": "fa",
    "BR": "pt-BR", "PT": "pt-BR",
    "DE": "de", "AT": "de",
    "JP": "ja", "KR": "ko", "IN": "hi", "ID": "id", "TR": "tr",
    "VN": "vi", "IT": "it", "PL": "pl", "UA": "uk", "TH": "th",
    "NL": "nl", "BD": "bn",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es", "PE": "es",
    "FR": "fr",
}


def normalize_lang(value):
    """Return a supported canonical code for any BCP-47 tag, else ``None``."""
    if not value:
        return None
    code = str(value).strip().replace("_", "-")
    if not code:
        return None
    low = code.lower()
    if low in _ALIAS:
        return _ALIAS[low]
    primary = low.split("-", 1)[0]
    return _ALIAS.get(primary)


def parse_accept_language(header):
    """Return the best supported language from an Accept-Language header."""
    if not header:
        return None
    items = []
    for index, part in enumerate(header.split(",")):
        part = part.strip()
        if not part:
            continue
        bits = part.split(";")
        tag = bits[0].strip()
        quality = 1.0
        for bit in bits[1:]:
            bit = bit.strip()
            if bit.startswith("q="):
                try:
                    quality = float(bit[2:])
                except ValueError:
                    quality = 0.0
        items.append((quality, index, tag))
    items.sort(key=lambda item: (-item[0], item[1]))
    for quality, _, tag in items:
        if quality <= 0:
            continue
        code = normalize_lang(tag)
        if code:
            return code
    return None


def resolve_language(request):
    """Negotiate the request language.

    Priority: explicit ``?lang=`` in the URL, then the saved cookie choice,
    then Accept-Language, then a weak country hint, then English. Returns
    ``(code, explicit)`` where ``explicit`` marks a deliberate URL selection.
    """
    explicit = normalize_lang(request.GET.get("lang"))
    if explicit:
        return explicit, True
    saved = normalize_lang(request.COOKIES.get(LANG_COOKIE))
    if saved:
        return saved, False
    negotiated = parse_accept_language(request.META.get("HTTP_ACCEPT_LANGUAGE"))
    if negotiated:
        return negotiated, False
    country = request.META.get("HTTP_CF_IPCOUNTRY", "").upper()
    hinted = COUNTRY_LANG.get(country)
    if hinted:
        return hinted, False
    return DEFAULT_LANG, False


def fallback_chain(lang):
    """Ordered content lookup keys: requested language, then English, Russian."""
    chain = [lang]
    for code in (DEFAULT_LANG, "ru"):
        if code not in chain:
            chain.append(code)
    return chain


def is_rtl(lang):
    return lang in RTL_CODES


def direction(lang):
    return "rtl" if lang in RTL_CODES else "ltr"


def language_options():
    """(code, native name) pairs in switcher order."""
    return [(code, native) for code, native, _ in LANGUAGES]
