"""Deterministic 22-locale translations for controlled catalog terminology.

Some catalog metadata (developer/provider labels, billing units, price-condition
labels) was authored in Russian. These are a small, closed vocabulary, so they
are translated here for every supported locale without any external service and
without touching stored data. Brands, model names/IDs, plan/product proper names
(``Pro``, ``Max``, ``Standard``, ``ChatGPT Pro``), API/SDK/IDE, resolutions and
URLs are kept verbatim. English is only an emergency fallback (see
``public_text``), never the normal result for a supported locale.

A value is localized by splitting it on the middle-dot separator and translating
each segment that is a known term, keeping allowlisted tokens; a value is only
rewritten when *every* segment is recognized, so ordinary localized prose is left
untouched.
"""
from .context import t

# Segments kept verbatim: plan/product proper names, technical identifiers,
# resolutions and API surface. These are never translated.
KEEP = {
    "Pro", "Max", "Standard", "ChatGPT Pro", "Pay-as-you-go", "API", "SDK", "IDE",
    "local_runtime", "Hugging Face", "1080p", "4K", "720p", "720p / 1080p",
}

# Segments that reuse an existing 22-language UI label for consistency.
REUSE_UI = {"Image editing": "image_editing"}

# language order kept for authoring reference:
# en ru zh-Hans es fr ar pt-BR de ja ko hi id tr vi it pl uk fa th nl bn zh-Hant
TERMS = {
    "Самостоятельно": {
        "en": "Self-hosted", "ru": "Самостоятельно", "zh-Hans": "自托管",
        "es": "Autoalojado", "fr": "Auto-hébergé", "ar": "استضافة ذاتية",
        "pt-BR": "Auto-hospedado", "de": "Selbstgehostet", "ja": "セルフホスト",
        "ko": "자체 호스팅", "hi": "स्व-होस्टेड", "id": "Hosting mandiri",
        "tr": "Kendi barındırma", "vi": "Tự lưu trữ", "it": "Self-hosted",
        "pl": "Samodzielny hosting", "uk": "Власний хостинг", "fa": "میزبانی شخصی",
        "th": "โฮสต์เอง", "nl": "Zelf gehost", "bn": "স্ব-হোস্টেড", "zh-Hant": "自架",
    },
    "Самостоятельно / Hugging Face": {
        "en": "Self-hosted / Hugging Face", "ru": "Самостоятельно / Hugging Face",
        "zh-Hans": "自托管 / Hugging Face", "es": "Autoalojado / Hugging Face",
        "fr": "Auto-hébergé / Hugging Face", "ar": "استضافة ذاتية / Hugging Face",
        "pt-BR": "Auto-hospedado / Hugging Face", "de": "Selbstgehostet / Hugging Face",
        "ja": "セルフホスト / Hugging Face", "ko": "자체 호스팅 / Hugging Face",
        "hi": "स्व-होस्टेड / Hugging Face", "id": "Hosting mandiri / Hugging Face",
        "tr": "Kendi barındırma / Hugging Face", "vi": "Tự lưu trữ / Hugging Face",
        "it": "Self-hosted / Hugging Face", "pl": "Samodzielny hosting / Hugging Face",
        "uk": "Власний хостинг / Hugging Face", "fa": "میزبانی شخصی / Hugging Face",
        "th": "โฮสต์เอง / Hugging Face", "nl": "Zelf gehost / Hugging Face",
        "bn": "স্ব-হোস্টেড / Hugging Face", "zh-Hant": "自架 / Hugging Face",
    },
    "от": {
        "en": "from", "ru": "от", "zh-Hans": "起", "es": "desde", "fr": "à partir de",
        "ar": "من", "pt-BR": "a partir de", "de": "ab", "ja": "から", "ko": "부터",
        "hi": "से", "id": "dari", "tr": "itibaren", "vi": "từ", "it": "da", "pl": "od",
        "uk": "від", "fa": "از", "th": "เริ่มต้น", "nl": "vanaf", "bn": "থেকে",
        "zh-Hant": "起",
    },
    "с аудио": {
        "en": "with audio", "ru": "с аудио", "zh-Hans": "含音频", "es": "con audio",
        "fr": "avec audio", "ar": "مع الصوت", "pt-BR": "com áudio", "de": "mit Audio",
        "ja": "音声あり", "ko": "오디오 포함", "hi": "ऑडियो के साथ", "id": "dengan audio",
        "tr": "sesli", "vi": "có âm thanh", "it": "con audio", "pl": "z dźwiękiem",
        "uk": "зі звуком", "fa": "با صدا", "th": "มีเสียง", "nl": "met audio",
        "bn": "অডিও সহ", "zh-Hant": "含音訊",
    },
    "С аудио": {
        "en": "With audio", "ru": "С аудио", "zh-Hans": "含音频", "es": "Con audio",
        "fr": "Avec audio", "ar": "مع الصوت", "pt-BR": "Com áudio", "de": "Mit Audio",
        "ja": "音声あり", "ko": "오디오 포함", "hi": "ऑडियो के साथ", "id": "Dengan audio",
        "tr": "Sesli", "vi": "Có âm thanh", "it": "Con audio", "pl": "Z dźwiękiem",
        "uk": "Зі звуком", "fa": "با صدا", "th": "มีเสียง", "nl": "Met audio",
        "bn": "অডিও সহ", "zh-Hant": "含音訊",
    },
    "Без аудио": {
        "en": "Without audio", "ru": "Без аудио", "zh-Hans": "无音频", "es": "Sin audio",
        "fr": "Sans audio", "ar": "بدون صوت", "pt-BR": "Sem áudio", "de": "Ohne Audio",
        "ja": "音声なし", "ko": "오디오 없음", "hi": "ऑडियो के बिना", "id": "Tanpa audio",
        "tr": "Sessiz", "vi": "Không có âm thanh", "it": "Senza audio", "pl": "Bez dźwięku",
        "uk": "Без звуку", "fa": "بدون صدا", "th": "ไม่มีเสียง", "nl": "Zonder audio",
        "bn": "অডিও ছাড়া", "zh-Hant": "無音訊",
    },
    "Прямой API": {
        "en": "Direct API", "ru": "Прямой API", "zh-Hans": "直接 API", "es": "API directa",
        "fr": "API directe", "ar": "API مباشر", "pt-BR": "API direta", "de": "Direkte API",
        "ja": "直接 API", "ko": "직접 API", "hi": "प्रत्यक्ष API", "id": "API langsung",
        "tr": "Doğrudan API", "vi": "API trực tiếp", "it": "API diretta",
        "pl": "Bezpośrednie API", "uk": "Пряме API", "fa": "API مستقیم",
        "th": "API โดยตรง", "nl": "Directe API", "bn": "সরাসরি API", "zh-Hant": "直接 API",
    },
    "текстовая составляющая": {
        "en": "text component", "ru": "текстовая составляющая", "zh-Hans": "文本部分",
        "es": "componente de texto", "fr": "composante texte", "ar": "المكوّن النصي",
        "pt-BR": "componente de texto", "de": "Textanteil", "ja": "テキスト部分",
        "ko": "텍스트 구성 요소", "hi": "टेक्स्ट घटक", "id": "komponen teks",
        "tr": "metin bileşeni", "vi": "phần văn bản", "it": "componente testo",
        "pl": "część tekstowa", "uk": "текстова складова", "fa": "بخش متنی",
        "th": "ส่วนข้อความ", "nl": "tekstcomponent", "bn": "টেক্সট উপাদান",
        "zh-Hant": "文字部分",
    },
    "Голосовая сессия": {
        "en": "Voice session", "ru": "Голосовая сессия", "zh-Hans": "语音会话",
        "es": "Sesión de voz", "fr": "Session vocale", "ar": "جلسة صوتية",
        "pt-BR": "Sessão de voz", "de": "Sprachsitzung", "ja": "音声セッション",
        "ko": "음성 세션", "hi": "वॉइस सत्र", "id": "Sesi suara", "tr": "Sesli oturum",
        "vi": "Phiên thoại", "it": "Sessione vocale", "pl": "Sesja głosowa",
        "uk": "Голосова сесія", "fa": "جلسه صوتی", "th": "เซสชันเสียง",
        "nl": "Spraaksessie", "bn": "ভয়েস সেশন", "zh-Hant": "語音工作階段",
    },
    "Опубликованная оценка": {
        "en": "Published estimate", "ru": "Опубликованная оценка", "zh-Hans": "已公布的估算",
        "es": "Estimación publicada", "fr": "Estimation publiée", "ar": "تقدير منشور",
        "pt-BR": "Estimativa publicada", "de": "Veröffentlichte Schätzung",
        "ja": "公表された概算", "ko": "공개된 추정치", "hi": "प्रकाशित अनुमान",
        "id": "Perkiraan yang dipublikasikan", "tr": "Yayınlanmış tahmin",
        "vi": "Ước tính đã công bố", "it": "Stima pubblicata", "pl": "Opublikowany szacunek",
        "uk": "Опублікована оцінка", "fa": "برآورد منتشرشده", "th": "ประมาณการที่เผยแพร่",
        "nl": "Gepubliceerde schatting", "bn": "প্রকাশিত অনুমান", "zh-Hant": "已公佈的估算",
    },
    "песня": {
        "en": "song", "ru": "песня", "zh-Hans": "歌曲", "es": "canción", "fr": "chanson",
        "ar": "أغنية", "pt-BR": "música", "de": "Song", "ja": "曲", "ko": "곡",
        "hi": "गाना", "id": "lagu", "tr": "şarkı", "vi": "bài hát", "it": "canzone",
        "pl": "utwór", "uk": "пісня", "fa": "آهنگ", "th": "เพลง", "nl": "nummer",
        "bn": "গান", "zh-Hant": "歌曲",
    },
    "1000 страниц": {
        "en": "1000 pages", "ru": "1000 страниц", "zh-Hans": "1000 页",
        "es": "1000 páginas", "fr": "1000 pages", "ar": "1000 صفحة",
        "pt-BR": "1000 páginas", "de": "1000 Seiten", "ja": "1000 ページ",
        "ko": "1000 페이지", "hi": "1000 पेज", "id": "1000 halaman", "tr": "1000 sayfa",
        "vi": "1000 trang", "it": "1000 pagine", "pl": "1000 stron", "uk": "1000 сторінок",
        "fa": "۱۰۰۰ صفحه", "th": "1000 หน้า", "nl": "1000 pagina's", "bn": "১০০০ পৃষ্ঠা",
        "zh-Hant": "1000 頁",
    },
    "1M токенов; тип токенов по документации": {
        "en": "1M tokens; token type per documentation",
        "ru": "1M токенов; тип токенов по документации",
        "zh-Hans": "1M 词元；词元类型见文档", "es": "1M tokens; tipo de token según la documentación",
        "fr": "1M tokens ; type de token selon la documentation", "ar": "1M رمز؛ نوع الرمز حسب الوثائق",
        "pt-BR": "1M tokens; tipo de token conforme a documentação",
        "de": "1M Tokens; Token-Typ laut Dokumentation", "ja": "1M トークン、トークン種別はドキュメント参照",
        "ko": "1M 토큰, 토큰 유형은 문서 참조", "hi": "1M टोकन; टोकन प्रकार दस्तावेज़ अनुसार",
        "id": "1M token; jenis token sesuai dokumentasi", "tr": "1M jeton; jeton türü belgelere göre",
        "vi": "1M token; loại token theo tài liệu", "it": "1M token; tipo di token secondo la documentazione",
        "pl": "1M tokenów; typ tokenu wg dokumentacji", "uk": "1M токенів; тип токенів за документацією",
        "fa": "۱M توکن؛ نوع توکن طبق مستندات", "th": "1M โทเคน; ประเภทโทเคนตามเอกสาร",
        "nl": "1M tokens; tokentype volgens documentatie", "bn": "1M টোকেন; টোকেনের ধরন ডকুমেন্টেশন অনুযায়ী",
        "zh-Hant": "1M 詞元；詞元類型見文件",
    },
    "видео; конфигурация требует уточнения": {
        "en": "video; configuration needs verification",
        "ru": "видео; конфигурация требует уточнения",
        "zh-Hans": "视频；配置需核实", "es": "vídeo; la configuración requiere verificación",
        "fr": "vidéo ; la configuration doit être vérifiée", "ar": "فيديو؛ التهيئة تحتاج إلى تحقق",
        "pt-BR": "vídeo; a configuração precisa de verificação",
        "de": "Video; Konfiguration muss geprüft werden", "ja": "動画、構成は要確認",
        "ko": "동영상, 구성 확인 필요", "hi": "वीडियो; कॉन्फ़िगरेशन सत्यापन आवश्यक",
        "id": "video; konfigurasi perlu diverifikasi", "tr": "video; yapılandırma doğrulama gerektirir",
        "vi": "video; cấu hình cần xác minh", "it": "video; la configurazione va verificata",
        "pl": "wideo; konfiguracja wymaga weryfikacji", "uk": "відео; конфігурація потребує уточнення",
        "fa": "ویدیو؛ پیکربندی نیاز به بررسی دارد", "th": "วิดีโอ; ต้องตรวจสอบการกำหนดค่า",
        "nl": "video; configuratie moet worden geverifieerd", "bn": "ভিডিও; কনফিগারেশন যাচাই প্রয়োজন",
        "zh-Hant": "影片；設定需核實",
    },
    "В составе Pro": {
        "en": "Included with Pro", "ru": "В составе Pro", "zh-Hans": "包含在 Pro 中",
        "es": "Incluido con Pro", "fr": "Inclus avec Pro", "ar": "مضمّن مع Pro",
        "pt-BR": "Incluído no Pro", "de": "Im Pro enthalten", "ja": "Pro に含まれる",
        "ko": "Pro에 포함", "hi": "Pro के साथ शामिल", "id": "Termasuk dalam Pro",
        "tr": "Pro'ya dahil", "vi": "Bao gồm trong Pro", "it": "Incluso in Pro",
        "pl": "W zestawie z Pro", "uk": "У складі Pro", "fa": "همراه با Pro",
        "th": "รวมอยู่ใน Pro", "nl": "Inbegrepen bij Pro", "bn": "Pro-এর সাথে অন্তর্ভুক্ত",
        "zh-Hant": "包含在 Pro 中",
    },
    "В составе Max": {
        "en": "Included with Max", "ru": "В составе Max", "zh-Hans": "包含在 Max 中",
        "es": "Incluido con Max", "fr": "Inclus avec Max", "ar": "مضمّن مع Max",
        "pt-BR": "Incluído no Max", "de": "Im Max enthalten", "ja": "Max に含まれる",
        "ko": "Max에 포함", "hi": "Max के साथ शामिल", "id": "Termasuk dalam Max",
        "tr": "Max'a dahil", "vi": "Bao gồm trong Max", "it": "Incluso in Max",
        "pl": "W zestawie z Max", "uk": "У складі Max", "fa": "همراه با Max",
        "th": "รวมอยู่ใน Max", "nl": "Inbegrepen bij Max", "bn": "Max-এর সাথে অন্তর্ভুক্ত",
        "zh-Hant": "包含在 Max 中",
    },
    "Text-to-image": {
        "en": "Text-to-image", "ru": "Text-to-image", "zh-Hans": "文生图",
        "es": "Texto a imagen", "fr": "Texte vers image", "ar": "نص إلى صورة",
        "pt-BR": "Texto para imagem", "de": "Text-zu-Bild", "ja": "テキストから画像",
        "ko": "텍스트-이미지", "hi": "टेक्स्ट-से-इमेज", "id": "Teks ke gambar",
        "tr": "Metinden görüntüye", "vi": "Văn bản thành hình ảnh", "it": "Testo in immagine",
        "pl": "Tekst na obraz", "uk": "Текст у зображення", "fa": "متن به تصویر",
        "th": "ข้อความเป็นภาพ", "nl": "Tekst naar afbeelding", "bn": "টেক্সট থেকে ইমেজ",
        "zh-Hant": "文生圖",
    },
    "SpaceXAI / xAI (бренд документации)": {
        "en": "SpaceXAI / xAI (brand per documentation)",
        "ru": "SpaceXAI / xAI (бренд документации)",
        "zh-Hans": "SpaceXAI / xAI（品牌以文档为准）", "es": "SpaceXAI / xAI (marca según la documentación)",
        "fr": "SpaceXAI / xAI (marque selon la documentation)", "ar": "SpaceXAI / xAI (العلامة حسب الوثائق)",
        "pt-BR": "SpaceXAI / xAI (marca conforme a documentação)",
        "de": "SpaceXAI / xAI (Marke laut Dokumentation)", "ja": "SpaceXAI / xAI（ブランドはドキュメント準拠）",
        "ko": "SpaceXAI / xAI (문서 기준 브랜드)", "hi": "SpaceXAI / xAI (दस्तावेज़ अनुसार ब्रांड)",
        "id": "SpaceXAI / xAI (merek sesuai dokumentasi)", "tr": "SpaceXAI / xAI (belgelere göre marka)",
        "vi": "SpaceXAI / xAI (thương hiệu theo tài liệu)", "it": "SpaceXAI / xAI (marchio secondo la documentazione)",
        "pl": "SpaceXAI / xAI (marka wg dokumentacji)", "uk": "SpaceXAI / xAI (бренд за документацією)",
        "fa": "SpaceXAI / xAI (برند طبق مستندات)", "th": "SpaceXAI / xAI (แบรนด์ตามเอกสาร)",
        "nl": "SpaceXAI / xAI (merk volgens documentatie)", "bn": "SpaceXAI / xAI (ডকুমেন্টেশন অনুযায়ী ব্র্যান্ড)",
        "zh-Hant": "SpaceXAI / xAI（品牌以文件為準）",
    },
    "SpaceXAI / xAI (бренд документации) API": {
        "en": "SpaceXAI / xAI (brand per documentation) API",
        "ru": "SpaceXAI / xAI (бренд документации) API",
        "zh-Hans": "SpaceXAI / xAI（品牌以文档为准）API", "es": "SpaceXAI / xAI (marca según la documentación) API",
        "fr": "SpaceXAI / xAI (marque selon la documentation) API", "ar": "SpaceXAI / xAI (العلامة حسب الوثائق) API",
        "pt-BR": "SpaceXAI / xAI (marca conforme a documentação) API",
        "de": "SpaceXAI / xAI (Marke laut Dokumentation) API", "ja": "SpaceXAI / xAI（ブランドはドキュメント準拠）API",
        "ko": "SpaceXAI / xAI (문서 기준 브랜드) API", "hi": "SpaceXAI / xAI (दस्तावेज़ अनुसार ब्रांड) API",
        "id": "SpaceXAI / xAI (merek sesuai dokumentasi) API", "tr": "SpaceXAI / xAI (belgelere göre marka) API",
        "vi": "SpaceXAI / xAI (thương hiệu theo tài liệu) API", "it": "SpaceXAI / xAI (marchio secondo la documentazione) API",
        "pl": "SpaceXAI / xAI (marka wg dokumentacji) API", "uk": "SpaceXAI / xAI (бренд за документацією) API",
        "fa": "SpaceXAI / xAI (برند طبق مستندات) API", "th": "SpaceXAI / xAI (แบรนด์ตามเอกสาร) API",
        "nl": "SpaceXAI / xAI (merk volgens documentatie) API", "bn": "SpaceXAI / xAI (ডকুমেন্টেশন অনুযায়ী ব্র্যান্ড) API",
        "zh-Hant": "SpaceXAI / xAI（品牌以文件為準）API",
    },
    "Точный scope не нормализован; см. источник": {
        "en": "Exact scope not normalized; see source",
        "ru": "Точный scope не нормализован; см. источник",
        "zh-Hans": "确切范围未标准化；见来源", "es": "Alcance exacto no normalizado; ver la fuente",
        "fr": "Périmètre exact non normalisé ; voir la source", "ar": "النطاق الدقيق غير مُوحّد؛ راجع المصدر",
        "pt-BR": "Escopo exato não normalizado; ver a fonte",
        "de": "Genauer Umfang nicht normalisiert; siehe Quelle", "ja": "正確な範囲は未正規化、ソース参照",
        "ko": "정확한 범위 미정규화, 출처 참조", "hi": "सटीक स्कोप सामान्यीकृत नहीं; स्रोत देखें",
        "id": "Cakupan pasti belum dinormalkan; lihat sumber", "tr": "Kesin kapsam normalleştirilmedi; kaynağa bakın",
        "vi": "Phạm vi chính xác chưa chuẩn hóa; xem nguồn", "it": "Ambito esatto non normalizzato; vedi la fonte",
        "pl": "Dokładny zakres nieznormalizowany; zobacz źródło", "uk": "Точний обсяг не нормалізовано; див. джерело",
        "fa": "دامنه دقیق نرمال‌سازی نشده؛ به منبع مراجعه کنید", "th": "ยังไม่ได้ปรับมาตรฐานขอบเขต; ดูแหล่งที่มา",
        "nl": "Exacte scope niet genormaliseerd; zie bron", "bn": "সঠিক স্কোপ নর্মালাইজড নয়; উৎস দেখুন",
        "zh-Hant": "確切範圍未標準化；見來源",
    },
    "Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки.": {
        "en": "Price per video, not per second; duration and configuration need verification.",
        "ru": "Цена за видео, не за секунду; конкретная длительность/конфигурация требует проверки.",
        "zh-Hans": "按视频计价，而非按秒；具体时长/配置需核实",
        "es": "Precio por vídeo, no por segundo; la duración/configuración concreta requiere verificación",
        "fr": "Prix par vidéo, pas par seconde ; la durée/configuration exacte doit être vérifiée",
        "ar": "السعر لكل فيديو، وليس لكل ثانية؛ المدة/التهيئة المحددة تحتاج إلى تحقق",
        "pt-BR": "Preço por vídeo, não por segundo; a duração/configuração específica precisa de verificação",
        "de": "Preis pro Video, nicht pro Sekunde; konkrete Dauer/Konfiguration muss geprüft werden",
        "ja": "秒単位ではなく動画単位の価格。具体的な長さ・構成は要確認",
        "ko": "초당이 아닌 동영상당 가격, 구체적 길이/구성 확인 필요",
        "hi": "प्रति वीडियो मूल्य, प्रति सेकंड नहीं; विशिष्ट अवधि/कॉन्फ़िगरेशन सत्यापन आवश्यक",
        "id": "Harga per video, bukan per detik; durasi/konfigurasi spesifik perlu diverifikasi",
        "tr": "Saniye başına değil video başına fiyat; belirli süre/yapılandırma doğrulama gerektirir",
        "vi": "Giá theo video, không theo giây; thời lượng/cấu hình cụ thể cần xác minh",
        "it": "Prezzo per video, non al secondo; durata/configurazione specifica da verificare",
        "pl": "Cena za wideo, nie za sekundę; konkretny czas/konfiguracja wymaga weryfikacji",
        "uk": "Ціна за відео, а не за секунду; конкретна тривалість/конфігурація потребує перевірки",
        "fa": "قیمت به‌ازای هر ویدیو، نه هر ثانیه؛ مدت/پیکربندی مشخص نیاز به بررسی دارد",
        "th": "ราคาต่อวิดีโอ ไม่ใช่ต่อวินาที; ต้องตรวจสอบระยะเวลา/การกำหนดค่าที่เฉพาะเจาะจง",
        "nl": "Prijs per video, niet per seconde; specifieke duur/configuratie moet worden geverifieerd",
        "bn": "প্রতি সেকেন্ডে নয়, প্রতি ভিডিওতে মূল্য; নির্দিষ্ট সময়কাল/কনফিগারেশন যাচাই প্রয়োজন",
        "zh-Hant": "按影片計價，而非按秒；具體時長/設定需核實",
    },
}


def _segment(seg, lang):
    if seg in KEEP:
        return seg
    if seg in REUSE_UI:
        return t(REUSE_UI[seg], lang)
    entry = TERMS.get(seg)
    if entry:
        return entry.get(lang) or entry.get("en")
    return None


def localize_controlled(value, lang):
    """Return the localized controlled term, or None if not fully recognized."""
    if not isinstance(value, str) or not value:
        return None
    entry = TERMS.get(value)
    if entry:
        return entry.get(lang) or entry.get("en")
    if " · " in value:
        pieces = [_segment(part, lang) for part in value.split(" · ")]
        if all(piece is not None for piece in pieces):
            return " · ".join(pieces)
    return None
