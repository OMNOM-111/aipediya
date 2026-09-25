"""Localization for public static-page prose and editorial gap notes.

The catalog cards are localized through the ContentTranslation pipeline; this
module covers the remaining public prose that is not tied to a catalog object:
the privacy page and (optionally) the methodology page. Canonical text is
authored in English and Russian here; the other languages are machine-filled by
``manage.py translate_static_pages`` into ``data/static_page_translations.json``
and looked up by language code, so the same rules and URL-agnostic behaviour as
the catalog pipeline apply. Missing languages fall back to English.
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings

# Ordered blocks per page: (html tag, English source, Russian source).
STATIC_PAGES = {
    "privacy": [
        ("p", "AIpediya is a public reference catalog. It does not offer public accounts or public editing.",
         "AIpediya — публичный справочный каталог. Публичной регистрации и пользовательского редактирования нет."),
        ("h2", "Technical data", "Технические данные"),
        ("p", "The server and Cloudflare may process IP address, browser and request information for delivery, security and troubleshooting. The catalog itself does not require an account.",
         "Сервер и Cloudflare могут обрабатывать IP-адрес, сведения о браузере и запросе для доставки, безопасности и поиска ошибок. Для работы каталога аккаунт не требуется."),
        ("h2", "Advertising and consent", "Реклама и согласие"),
        ("p", "Advertising is currently disabled. If it is enabled later, one clearly labelled placement may be shown. Advertising scripts will load only after the visitor chooses Allow; Decline keeps them disabled in that browser.",
         "Реклама сейчас отключена. При её включении может быть показано одно ясно помеченное место. Рекламные скрипты загружаются только после выбора «Разрешить»; «Отклонить» оставляет их выключенными в этом браузере."),
        ("h2", "Choices", "Выбор посетителя"),
        ("p", "Consent is stored locally in the browser and can be changed by clearing the AIpediya site data. Before advertising is enabled, the editorial team must publish a responsible contact and complete the applicable advertising-system review.",
         "Согласие хранится локально в браузере и меняется очисткой данных сайта AIpediya. До включения рекламы редакция должна опубликовать ответственный контакт и пройти проверку применимой рекламной системы."),
    ],
}

SOURCE_LANGUAGE = "en"
MANUAL_LANGUAGES = frozenset({"en", "ru"})
_OVERLAY_PATH = Path(settings.BASE_DIR) / "data" / "static_page_translations.json"

# Short inline labels (English, Russian) used next to dynamic values.
STATIC_LABELS = {
    "privacy_contact": ("Privacy contact", "Контакт по конфиденциальности"),
}


def all_source_strings():
    """Every English source string that needs a machine translation."""
    strings = [english for blocks in STATIC_PAGES.values() for _tag, english, _ru in blocks if english]
    strings += [english for english, _ru in STATIC_LABELS.values() if english]
    return strings


def source_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _overlay():
    if _OVERLAY_PATH.exists():
        return json.loads(_OVERLAY_PATH.read_text(encoding="utf-8"))
    return {}


def clear_overlay_cache():
    _overlay.cache_clear()


def page_label(key, lang):
    """Localized short inline label with English fallback."""
    english, russian = STATIC_LABELS.get(key, ("", ""))
    if lang == "ru":
        return russian or english
    if lang == "en":
        return english
    return _overlay().get(source_hash(english), {}).get(lang) or english


def page_blocks(page, lang):
    """Return ``[(tag, text)]`` for a page in the requested language.

    ru/en use the authored source; other languages use the machine-translated
    overlay and fall back to English so a block is never blank.
    """
    overlay = _overlay()
    blocks = []
    for tag, english, russian in STATIC_PAGES.get(page, []):
        if lang == "ru":
            text = russian or english
        elif lang == "en":
            text = english
        else:
            text = overlay.get(source_hash(english), {}).get(lang) or english
        blocks.append((tag, text))
    return blocks


# --- GSD-1.0 pages: methodology and collections -----------------------------
# Their English/Russian source lives in catalog.discovery_content; drafts for
# the other locales live in a separate overlay with explicit provenance so they
# are never confused with the machine-translation overlay above.
from . import discovery_content as _dc  # noqa: E402

STATIC_PAGES["methodology"] = _dc.METHODOLOGY
for _slug, _blocks in _dc.HUBS.items():
    STATIC_PAGES[f"hub:{_slug}"] = _blocks
for _key, (_en, _ru) in _dc.LABELS.items():
    STATIC_LABELS[_key] = (_en, _ru)

_DISCOVERY_PATH = Path(settings.BASE_DIR) / "data" / "discovery_translations.json"


@lru_cache(maxsize=1)
def _discovery_overlay():
    if _DISCOVERY_PATH.exists():
        return json.loads(_DISCOVERY_PATH.read_text(encoding="utf-8")).get("strings", {})
    return {}


def _translated(english, lang):
    """Return ``(text, is_fallback)`` for one English source string."""
    digest = source_hash(english)
    text = _overlay().get(digest, {}).get(lang) or _discovery_overlay().get(digest, {}).get(lang)
    return (text, False) if text else (english, True)


def localized_blocks(page, lang):
    """``[(tag, text, fallback)]``; ``fallback`` marks English shown in another locale."""
    blocks = []
    for tag, english, russian in STATIC_PAGES.get(page, []):
        if lang == "en":
            blocks.append((tag, english, False))
        elif lang == "ru":
            blocks.append((tag, russian or english, not russian))
        else:
            text, fallback = _translated(english, lang)
            blocks.append((tag, text, fallback))
    return blocks


def label_text(key, lang):
    english, russian = STATIC_LABELS.get(key, ("", ""))
    if lang == "en":
        return english
    if lang == "ru":
        return russian or english
    return _translated(english, lang)[0]


def page_ready(page, lang):
    """A page is indexable in a locale only when no block falls back to English."""
    blocks = STATIC_PAGES.get(page)
    return bool(blocks) and not any(fallback for _tag, _text, fallback in localized_blocks(page, lang))


def labels_ready(keys, lang):
    if lang in ("en", "ru"):
        return True
    return all(not _translated(STATIC_LABELS[key][0], lang)[1] for key in keys)


def clear_discovery_cache():
    _discovery_overlay.cache_clear()
    _overlay.cache_clear()
