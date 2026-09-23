"""Localized labels for controlled, Russian-authored evaluation metadata.

A few evaluation ``configuration`` values and benchmark ``protocol`` notes were
entered in Russian in the source data and were previously rendered raw, so every
locale (English, Korean, ...) showed the Russian text. They are a tiny, closed
set, so they are localized at render time here. Unknown or technical values
(``Standard``, ``Free tier``, benchmark version strings, ...) pass through
unchanged, and the canonical stored data is never modified.
"""
from .context import t

# "Модель" reuses the existing 22-language "model" UI label (모델, Model, ...).
_EVAL_LABEL_TRANSLATIONS = {
    "Точная версия / API snapshot": {
        "en": "Exact version / API snapshot", "ru": "Точная версия / API snapshot",
        "zh-Hans": "精确版本 / API 快照", "es": "Versión exacta / API instantánea",
        "fr": "Version exacte / API instantané", "ar": "النسخة الدقيقة / API اللقطة",
        "pt-BR": "Versão exata / API snapshot", "de": "Exakte Version / API Snapshot",
        "ja": "正確なバージョン / API スナップショット", "ko": "정확한 버전 / API 스냅샷",
        "hi": "सटीक संस्करण / API स्नैपशॉट", "id": "Versi persis / snapshot API",
        "tr": "Tam versiyon / API anlık görüntü", "vi": "Phiên bản chính xác / ảnh chụp API",
        "it": "Versione esatta / API istantanea", "pl": "Dokładna wersja / API migawka",
        "uk": "Точна версія / API знімок", "fa": "نسخه دقیق / API اسنپ‌شات",
        "th": "เวอร์ชันที่แน่นอน / ภาพสแนปช็อต API", "nl": "Exacte versie / API snapshot",
        "bn": "সঠিক সংস্করণ / API স্ন্যাপশট", "zh-Hant": "精確版本 / API 快照",
    },
    "как указано на leaderboard": {
        "en": "as stated on the leaderboard", "ru": "как указано на leaderboard",
        "zh-Hans": "如排行榜所示", "es": "como se indica en la tabla de clasificación",
        "fr": "comme indiqué dans le classement", "ar": "كما هو مذكور في لوحة المتصدرين",
        "pt-BR": "conforme declarado no ranking", "de": "wie auf der Bestenliste angegeben",
        "ja": "リーダーボードに記載されている通り", "ko": "리더보드에 명시된 바와 같이",
        "hi": "जैसा कि लीडरबोर्ड पर कहा गया है", "id": "seperti yang tertera di papan peringkat",
        "tr": "liderlik tablosunda belirtildiği gibi", "vi": "như đã ghi trên bảng xếp hạng",
        "it": "come indicato nella classifica", "pl": "jak podano na tablicy wyników",
        "uk": "як зазначено на таблиці лідерів", "fa": "همان‌طور که در جدول امتیازات ذکر شده",
        "th": "ตามที่ระบุในกระดานผู้นำ", "nl": "zoals vermeld op het klassement",
        "bn": "লিডারবোর্ডে যেমন বলা হয়েছে", "zh-Hant": "如排行榜所示",
    },
}


def evaluation_label(value, lang):
    """Localize a controlled evaluation label; pass technical values through."""
    if not value:
        return value
    key = value.strip()
    if key == "Модель":
        return t("model", lang)
    entry = _EVAL_LABEL_TRANSLATIONS.get(key)
    if entry:
        return entry.get(lang) or entry.get("en") or value
    return value
