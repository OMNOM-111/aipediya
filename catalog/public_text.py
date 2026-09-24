"""Explicit translations for short, verified source terms shown to visitors.

English is the canonical fallback for these controlled catalog labels (developer
names, price plan labels, billing units, condition notes): any locale other than
Russian shows the English term instead of the original Russian source, so no
non-Russian page ever displays Russian. Values not listed here pass through
unchanged (proper nouns like ``OpenAI`` and already-localized text)."""

PUBLIC_ENGLISH = {
    "Самостоятельно": "Self-hosted",
    "Самостоятельно / Hugging Face": "Self-hosted / Hugging Face",
    "Самостоятельно · local_runtime": "Self-hosted · local_runtime",
    "Самостоятельно / Hugging Face · local_runtime": "Self-hosted / Hugging Face · local_runtime",
    "SpaceXAI / xAI (бренд документации)": "SpaceXAI / xAI (brand per documentation)",
    "SpaceXAI / xAI (бренд документации) API": "SpaceXAI / xAI (brand per documentation) API",
    "В составе Pro": "Included with Pro",
    "В составе Max · от": "Included with Max · from",
    "видео; конфигурация требует уточнения": "video; configuration needs verification",
    "1000 страниц": "1000 pages",
    "1M токенов; тип токенов по документации": "1M tokens; token type per documentation",
    "песня": "song",
    "Pro · от": "Pro · from",
    "Max · от": "Max · from",
    "ChatGPT Pro · от": "ChatGPT Pro · from",
    "Image editing · от": "Image editing · from",
    "Text-to-image · от": "Text-to-image · from",
    "Standard · текстовая составляющая": "Standard · text component",
    "Без аудио": "Without audio",
    "С аудио": "With audio",
    "Голосовая сессия": "Voice session",
    "Опубликованная оценка": "Published estimate",
    "Прямой API · с аудио · 1080p": "Direct API · with audio · 1080p",
    "Прямой API · с аудио · 4K": "Direct API · with audio · 4K",
    "Прямой API · с аудио · 720p": "Direct API · with audio · 720p",
    "Прямой API · с аудио · 720p / 1080p": "Direct API · with audio · 720p / 1080p",
    "Точный scope не нормализован; см. источник": "Exact scope not normalized; see source",
    "Pay-as-you-go · Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки.": (
        "Pay-as-you-go · Price per video, not per second; duration and configuration need verification."
    ),
}


def public_text(value, lang):
    if lang == "ru" or not isinstance(value, str):
        return value
    from .controlled_terms import localize_controlled
    localized = localize_controlled(value, lang)
    if localized is not None:
        return localized
    # Emergency fallback only: English, never the original Russian source term.
    return PUBLIC_ENGLISH.get(value, value)
