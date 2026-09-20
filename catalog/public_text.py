"""Explicit translations for short, verified source terms shown to visitors."""

PUBLIC_ENGLISH = {
    "Самостоятельно": "Self-hosted",
    "Самостоятельно / Hugging Face": "Self-hosted / Hugging Face",
    "В составе Pro": "Included with Pro",
    "В составе Max · от": "Included with Max · from",
    "видео; конфигурация требует уточнения": "video; configuration needs verification",
    "Pay-as-you-go · Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки.": (
        "Pay-as-you-go · Price per video, not per second; duration and configuration need verification."
    ),
}


def public_text(value, lang):
    if lang == "en" and isinstance(value, str):
        return PUBLIC_ENGLISH.get(value, value)
    return value
