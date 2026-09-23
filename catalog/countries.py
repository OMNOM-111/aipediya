"""Deterministic country-name localisation for all supported languages.

Country names are structural reference data, not free prose, so they are
resolved from this fixed table instead of the machine-translation pipeline.
The base ru/en names stay the database source of truth (see
:func:`country_label`); every other locale is filled from :data:`COUNTRY_TRANSLATIONS`
and falls back to English so a card never shows a raw code.

Keys are the ISO 3166-1 alpha-2 codes used by :class:`catalog.models.Country`
and by the tool developer-country badges in :mod:`catalog.comparison`.
"""

# {ISO2 code: {language code: localized country name}}
COUNTRY_TRANSLATIONS = {
    "US": {
        "en": "United States", "ru": "США", "zh-Hans": "美国", "zh-Hant": "美國",
        "es": "Estados Unidos", "fr": "États-Unis", "de": "Vereinigte Staaten",
        "it": "Stati Uniti", "pt-BR": "Estados Unidos", "nl": "Verenigde Staten",
        "pl": "Stany Zjednoczone", "uk": "США", "tr": "Amerika Birleşik Devletleri",
        "ar": "الولايات المتحدة", "fa": "ایالات متحده", "hi": "संयुक्त राज्य अमेरिका",
        "bn": "মার্কিন যুক্তরাষ্ট্র", "id": "Amerika Serikat", "vi": "Hoa Kỳ",
        "th": "สหรัฐอเมริกา", "ja": "アメリカ合衆国", "ko": "미국",
    },
    "GB": {
        "en": "United Kingdom", "ru": "Великобритания", "zh-Hans": "英国", "zh-Hant": "英國",
        "es": "Reino Unido", "fr": "Royaume-Uni", "de": "Vereinigtes Königreich",
        "it": "Regno Unito", "pt-BR": "Reino Unido", "nl": "Verenigd Koninkrijk",
        "pl": "Wielka Brytania", "uk": "Велика Британія", "tr": "Birleşik Krallık",
        "ar": "المملكة المتحدة", "fa": "بریتانیا", "hi": "यूनाइटेड किंगडम",
        "bn": "যুক্তরাজ্য", "id": "Britania Raya", "vi": "Vương quốc Anh",
        "th": "สหราชอาณาจักร", "ja": "イギリス", "ko": "영국",
    },
    "CA": {
        "en": "Canada", "ru": "Канада", "zh-Hans": "加拿大", "zh-Hant": "加拿大",
        "es": "Canadá", "fr": "Canada", "de": "Kanada", "it": "Canada",
        "pt-BR": "Canadá", "nl": "Canada", "pl": "Kanada", "uk": "Канада",
        "tr": "Kanada", "ar": "كندا", "fa": "کانادا", "hi": "कनाडा",
        "bn": "কানাডা", "id": "Kanada", "vi": "Canada", "th": "แคนาดา",
        "ja": "カナダ", "ko": "캐나다",
    },
    "CN": {
        "en": "China", "ru": "Китай", "zh-Hans": "中国", "zh-Hant": "中國",
        "es": "China", "fr": "Chine", "de": "China", "it": "Cina",
        "pt-BR": "China", "nl": "China", "pl": "Chiny", "uk": "Китай",
        "tr": "Çin", "ar": "الصين", "fa": "چین", "hi": "चीन",
        "bn": "চীন", "id": "Tiongkok", "vi": "Trung Quốc", "th": "จีน",
        "ja": "中国", "ko": "중국",
    },
    "FR": {
        "en": "France", "ru": "Франция", "zh-Hans": "法国", "zh-Hant": "法國",
        "es": "Francia", "fr": "France", "de": "Frankreich", "it": "Francia",
        "pt-BR": "França", "nl": "Frankrijk", "pl": "Francja", "uk": "Франція",
        "tr": "Fransa", "ar": "فرنسا", "fa": "فرانسه", "hi": "फ़्रान्स",
        "bn": "ফ্রান্স", "id": "Prancis", "vi": "Pháp", "th": "ฝรั่งเศส",
        "ja": "フランス", "ko": "프랑스",
    },
    "DE": {
        "en": "Germany", "ru": "Германия", "zh-Hans": "德国", "zh-Hant": "德國",
        "es": "Alemania", "fr": "Allemagne", "de": "Deutschland", "it": "Germania",
        "pt-BR": "Alemanha", "nl": "Duitsland", "pl": "Niemcy", "uk": "Німеччина",
        "tr": "Almanya", "ar": "ألمانيا", "fa": "آلمان", "hi": "जर्मनी",
        "bn": "জার্মানি", "id": "Jerman", "vi": "Đức", "th": "เยอรมนี",
        "ja": "ドイツ", "ko": "독일",
    },
    "IN": {
        "en": "India", "ru": "Индия", "zh-Hans": "印度", "zh-Hant": "印度",
        "es": "India", "fr": "Inde", "de": "Indien", "it": "India",
        "pt-BR": "Índia", "nl": "India", "pl": "Indie", "uk": "Індія",
        "tr": "Hindistan", "ar": "الهند", "fa": "هند", "hi": "भारत",
        "bn": "ভারত", "id": "India", "vi": "Ấn Độ", "th": "อินเดีย",
        "ja": "インド", "ko": "인도",
    },
    "IL": {
        "en": "Israel", "ru": "Израиль", "zh-Hans": "以色列", "zh-Hant": "以色列",
        "es": "Israel", "fr": "Israël", "de": "Israel", "it": "Israele",
        "pt-BR": "Israel", "nl": "Israël", "pl": "Izrael", "uk": "Ізраїль",
        "tr": "İsrail", "ar": "إسرائيل", "fa": "اسرائیل", "hi": "इज़राइल",
        "bn": "ইসরায়েল", "id": "Israel", "vi": "Israel", "th": "อิสราเอล",
        "ja": "イスラエル", "ko": "이스라엘",
    },
    "NL": {
        "en": "Netherlands", "ru": "Нидерланды", "zh-Hans": "荷兰", "zh-Hant": "荷蘭",
        "es": "Países Bajos", "fr": "Pays-Bas", "de": "Niederlande", "it": "Paesi Bassi",
        "pt-BR": "Países Baixos", "nl": "Nederland", "pl": "Holandia", "uk": "Нідерланди",
        "tr": "Hollanda", "ar": "هولندا", "fa": "هلند", "hi": "नीदरलैंड",
        "bn": "নেদারল্যান্ডস", "id": "Belanda", "vi": "Hà Lan", "th": "เนเธอร์แลนด์",
        "ja": "オランダ", "ko": "네덜란드",
    },
    "RU": {
        "en": "Russia", "ru": "Россия", "zh-Hans": "俄罗斯", "zh-Hant": "俄羅斯",
        "es": "Rusia", "fr": "Russie", "de": "Russland", "it": "Russia",
        "pt-BR": "Rússia", "nl": "Rusland", "pl": "Rosja", "uk": "Росія",
        "tr": "Rusya", "ar": "روسيا", "fa": "روسیه", "hi": "रूस",
        "bn": "রাশিয়া", "id": "Rusia", "vi": "Nga", "th": "รัสเซีย",
        "ja": "ロシア", "ko": "러시아",
    },
    "KR": {
        "en": "South Korea", "ru": "Южная Корея", "zh-Hans": "韩国", "zh-Hant": "南韓",
        "es": "Corea del Sur", "fr": "Corée du Sud", "de": "Südkorea", "it": "Corea del Sud",
        "pt-BR": "Coreia do Sul", "nl": "Zuid-Korea", "pl": "Korea Południowa",
        "uk": "Південна Корея", "tr": "Güney Kore", "ar": "كوريا الجنوبية",
        "fa": "کره جنوبی", "hi": "दक्षिण कोरिया", "bn": "দক্ষিণ কোরিয়া",
        "id": "Korea Selatan", "vi": "Hàn Quốc", "th": "เกาหลีใต้",
        "ja": "韓国", "ko": "대한민국",
    },
    "JP": {
        "en": "Japan", "ru": "Япония", "zh-Hans": "日本", "zh-Hant": "日本",
        "es": "Japón", "fr": "Japon", "de": "Japan", "it": "Giappone",
        "pt-BR": "Japão", "nl": "Japan", "pl": "Japonia", "uk": "Японія",
        "tr": "Japonya", "ar": "اليابان", "fa": "ژاپن", "hi": "जापान",
        "bn": "জাপান", "id": "Jepang", "vi": "Nhật Bản", "th": "ญี่ปุ่น",
        "ja": "日本", "ko": "일본",
    },
    "SA": {
        "en": "Saudi Arabia", "ru": "Саудовская Аравия", "zh-Hans": "沙特阿拉伯",
        "zh-Hant": "沙烏地阿拉伯", "es": "Arabia Saudita", "fr": "Arabie saoudite",
        "de": "Saudi-Arabien", "it": "Arabia Saudita", "pt-BR": "Arábia Saudita",
        "nl": "Saoedi-Arabië", "pl": "Arabia Saudyjska", "uk": "Саудівська Аравія",
        "tr": "Suudi Arabistan", "ar": "المملكة العربية السعودية", "fa": "عربستان سعودی",
        "hi": "सऊदी अरब", "bn": "সৌদি আরব", "id": "Arab Saudi", "vi": "Ả Rập Xê Út",
        "th": "ซาอุดีอาระเบีย", "ja": "サウジアラビア", "ko": "사우디아라비아",
    },
    "SG": {
        "en": "Singapore", "ru": "Сингапур", "zh-Hans": "新加坡", "zh-Hant": "新加坡",
        "es": "Singapur", "fr": "Singapour", "de": "Singapur", "it": "Singapore",
        "pt-BR": "Singapura", "nl": "Singapore", "pl": "Singapur", "uk": "Сінгапур",
        "tr": "Singapur", "ar": "سنغافورة", "fa": "سنگاپور", "hi": "सिंगापुर",
        "bn": "সিঙ্গাপুর", "id": "Singapura", "vi": "Singapore", "th": "สิงคโปร์",
        "ja": "シンガポール", "ko": "싱가포르",
    },
    "CH": {
        "en": "Switzerland", "ru": "Швейцария", "zh-Hans": "瑞士", "zh-Hant": "瑞士",
        "es": "Suiza", "fr": "Suisse", "de": "Schweiz", "it": "Svizzera",
        "pt-BR": "Suíça", "nl": "Zwitserland", "pl": "Szwajcaria", "uk": "Швейцарія",
        "tr": "İsviçre", "ar": "سويسرا", "fa": "سوئیس", "hi": "स्विट्ज़रलैंड",
        "bn": "সুইজারল্যান্ড", "id": "Swiss", "vi": "Thụy Sĩ", "th": "สวิตเซอร์แลนด์",
        "ja": "スイス", "ko": "스위스",
    },
    "AE": {
        "en": "United Arab Emirates", "ru": "Объединённые Арабские Эмираты",
        "zh-Hans": "阿拉伯联合酋长国", "zh-Hant": "阿拉伯聯合大公國",
        "es": "Emiratos Árabes Unidos", "fr": "Émirats arabes unis",
        "de": "Vereinigte Arabische Emirate", "it": "Emirati Arabi Uniti",
        "pt-BR": "Emirados Árabes Unidos", "nl": "Verenigde Arabische Emiraten",
        "pl": "Zjednoczone Emiraty Arabskie", "uk": "Об'єднані Арабські Емірати",
        "tr": "Birleşik Arap Emirlikleri", "ar": "الإمارات العربية المتحدة",
        "fa": "امارات متحده عربی", "hi": "संयुक्त अरब अमीरात",
        "bn": "সংযুক্ত আরব আমিরাত", "id": "Uni Emirat Arab",
        "vi": "Các Tiểu vương quốc Ả Rập Thống nhất", "th": "สหรัฐอาหรับเอมิเรตส์",
        "ja": "アラブ首長国連邦", "ko": "아랍에미리트",
    },
    "AU": {
        "en": "Australia", "ru": "Австралия", "zh-Hans": "澳大利亚", "zh-Hant": "澳洲",
        "es": "Australia", "fr": "Australie", "de": "Australien", "it": "Australia",
        "pt-BR": "Austrália", "nl": "Australië", "pl": "Australia", "uk": "Австралія",
        "tr": "Avustralya", "ar": "أستراليا", "fa": "استرالیا", "hi": "ऑस्ट्रेलिया",
        "bn": "অস্ট্রেলিয়া", "id": "Australia", "vi": "Úc", "th": "ออสเตรเลีย",
        "ja": "オーストラリア", "ko": "오스트레일리아",
    },
    "CZ": {
        "en": "Czech Republic", "ru": "Чехия", "zh-Hans": "捷克", "zh-Hant": "捷克",
        "es": "Chequia", "fr": "Tchéquie", "de": "Tschechien", "it": "Cechia",
        "pt-BR": "Tchéquia", "nl": "Tsjechië", "pl": "Czechy", "uk": "Чехія",
        "tr": "Çekya", "ar": "التشيك", "fa": "جمهوری چک", "hi": "चेक गणराज्य",
        "bn": "চেক প্রজাতন্ত্র", "id": "Ceko", "vi": "Cộng hòa Séc", "th": "เช็กเกีย",
        "ja": "チェコ", "ko": "체코",
    },
    "SE": {
        "en": "Sweden", "ru": "Швеция", "zh-Hans": "瑞典", "zh-Hant": "瑞典",
        "es": "Suecia", "fr": "Suède", "de": "Schweden", "it": "Svezia",
        "pt-BR": "Suécia", "nl": "Zweden", "pl": "Szwecja", "uk": "Швеція",
        "tr": "İsveç", "ar": "السويد", "fa": "سوئد", "hi": "स्वीडन",
        "bn": "সুইডেন", "id": "Swedia", "vi": "Thụy Điển", "th": "สวีเดน",
        "ja": "スウェーデン", "ko": "스웨덴",
    },
}


def country_label(country, lang):
    """Localized country name for a Country row or a developer-country badge.

    ``country`` exposes ``code``/``name_ru``/``name_en`` (both the database
    model and the tool badge namespace do). Base ru/en use the stored names;
    other locales use :data:`COUNTRY_TRANSLATIONS` and fall back to English.
    """
    code = (getattr(country, "code", "") or "").upper()
    name_ru = getattr(country, "name_ru", "") or ""
    name_en = getattr(country, "name_en", "") or ""
    if lang == "ru":
        return name_ru or name_en or code
    if lang == "en":
        return name_en or name_ru or code
    names = COUNTRY_TRANSLATIONS.get(code)
    if names:
        return names.get(lang) or names.get("en") or name_en or name_ru or code
    return name_en or name_ru or code
