from django.conf import settings

from .i18n import DEFAULT_LANG, LANGUAGE_NAMES, direction, language_options
from .ui_translations import CATEGORY_TRANSLATIONS, TRANSLATIONS


TEXT = {
    "released": ("Релиз", "Release"),
    "release_unknown": ("Дата выпуска не подтверждена", "Release date not verified"),
    "chronology_note": ("№ — порядок по дате выпуска: от старых к новым. При одинаковой дате — по названию. Без подтверждённой даты — без номера, в конце хронологии.", "Numbers follow release dates, oldest first; same-day releases use name order. Unverified dates have no number and appear last in chronology."),
    "price_modality": ("Тип тарифицируемых токенов", "Billed token modality"),
    "text_tokens": ("Текстовые токены", "Text tokens"), "audio_tokens": ("Аудиотокены", "Audio tokens"), "image_tokens": ("Токены изображения", "Image tokens"),
    "coverage_note": ("Что проверено по оценкам", "Evaluation coverage check"),
    "why_no_score": ("Почему нет оценки", "Why no score"),
    "evaluator_score": ("Платформа и оценка", "Evaluator & score"),
    "filter": ("Фильтр", "Filter"), "mode": ("Режим", "Mode"),
    "snapshot": ("Снимок", "Snapshot"), "legacy_snapshot": ("Исходный снимок", "Original snapshot"),
    "unspecified_mode": ("Режим не указан источником", "Mode not specified by source"),
    "evaluated_only": ("Только с выбранной оценкой", "Only with selected score"),
    "free_tier": ("Бесплатный уровень", "Free tier"), "annual_plan": ("Годовая оплата", "Annual billing"),
    "base_context": ("Базовый / короткий контекст", "Base / short context"),
    "long_context": ("Длинный контекст", "Long context"), "all_contexts": ("Все контексты", "All contexts"),
    "base": ("Базовый / короткий контекст", "Base / short context"), "long": ("Длинный контекст", "Long context"),
    "standard": ("Стандартный тариф", "Standard rate"), "batch": ("Batch", "Batch"), "offpeak": ("Off-peak", "Off-peak"), "free": ("Бесплатный уровень", "Free tier"), "annual": ("Годовая оплата", "Annual billing"),
    "lowest_matching": ("Минимальная подходящая цена; условия в строке", "Lowest matching price; conditions in each row"),
    "price_basis": ("Основа цены", "Price basis"), "score_basis": ("Основа оценки", "Score basis"),
    "no_matching_price": ("Подходящих предложений нет — выберите другую единицу или условия.", "No matching offers — choose a different unit or conditions."),
    "no_selected_price": ("Нет цены в выбранных условиях", "No price for selected conditions"),
    "no_selected_score": ("Нет результата выбранного теста и режима", "No result for selected test and mode"),
    "more": ("ещё", "more"),
    "sort_explanation": ("Назначения и способы доступа: алфавитный порядок показанных значений; при равенстве — номер. Пропуски — в конце.", "Use cases and access: alphabetical order of displayed values; ties use the catalogue number. Missing values stay last."),
    "access_asc": ("Доступ: А–Я", "Access: A–Z"), "access_desc": ("Доступ: Я–А", "Access: Z–A"),
    "composite": ("Составной индекс", "Composite index"), "independent_run": ("Независимый прогон", "Independent run"),
    "developer": ("Разработчик", "Developer"), "preference": ("Пользовательские предпочтения", "User preferences"),
    "eci_note": ("Официальный индекс Epoch AI; объединяет собственные, сторонние и заявленные разработчиками результаты. Не является аудитом безопасности или оценкой генерации медиа.", "Official Epoch AI index; combines own, third-party and developer-reported results. It is not a safety audit or a media-generation score."),
    "theme": ("Тема", "Theme"), "search_short": ("Поиск", "Search"), "add_model": ("Добавить модель", "Add model"),
    "language": ("Язык", "Language"),
    "models": ("Моделей", "Models"), "products": ("Продуктов", "Products"), "found": ("Найдено", "Found"), "shown": ("Показано", "Shown"),
    "status": ("Статус", "Status"), "active": ("Активна", "Active"), "archived": ("Архив", "Archive"),
    "deprecated": ("Deprecated", "Deprecated"), "retired": ("Снята", "Retired"),
    "all_statuses": ("Все статусы", "All statuses"),
    "privacy": ("Конфиденциальность", "Privacy"), "advertising": ("Реклама", "Advertising"),
    "consent_text": ("Разрешить персонализированную рекламу?", "Allow personalized advertising?"),
    "consent_accept": ("Разрешить", "Allow"), "consent_decline": ("Отклонить", "Decline"),
    "all_offers": ("Все тарифы", "All prices"), "entries": ("записей", "entries"), "accepts": ("Принимает", "Accepts"),
    "produces": ("Создаёт", "Produces"), "computes": ("Вычисления", "Computing"), "suggest_edit": ("Предложить правку", "Suggest an edit"),
    "audit": ("Аудит", "Audit"), "product": ("Продукт", "Product"), "api_service": ("API-сервис", "API service"), "runtime": ("Среда запуска", "Runtime"),
    "ai_app": ("AI-приложение", "AI app"), "coding_assistant": ("Coding assistant", "Coding assistant"),
    "coding_agent": ("Coding agent", "Coding agent"), "api_platform": ("API-платформа", "API platform"),
    "ide_tool": ("IDE-инструмент", "IDE tool"), "client": ("Клиент / интерфейс", "Client / interface"),
    "agent_platform": ("Agent platform", "Agent platform"), "creative_app": ("Творческое AI-приложение", "Creative AI app"),
    "app": ("Приложение", "App"), "cli": ("CLI", "CLI"), "ide": ("IDE", "IDE"), "local": ("Локально", "Local"), "cloud": ("Облако", "Cloud"), "hybrid": ("Гибрид", "Hybrid"),
    "year": ("год", "year"), "hour": ("час", "hour"), "request": ("запрос", "request"), "credit": ("кредит", "credit"),
    "million_characters": ("1M символов", "1M characters"), "thousand_characters": ("1000 символов", "1,000 characters"),
    "other": ("единица из источника", "source unit"),
    "cache_read": ("1M чтения кэша", "1M cache-read tokens"), "cache_write": ("1M записи кэша", "1M cache-write tokens"),
    "image_generation": ("Генерация изображений", "Image generation"), "image_editing": ("Редактирование изображений", "Image editing"),
    "vision": ("Анализ изображений", "Vision"), "ocr": ("Распознавание текста", "OCR"),
    "video_generation": ("Генерация видео", "Video generation"), "video_editing": ("Редактирование видео", "Video editing"),
    "video_understanding": ("Анализ видео", "Video understanding"), "speech": ("Речь", "Speech"),
    "audio_processing": ("Обработка аудио", "Audio processing"), "music": ("Музыка", "Music"),
    "sound_effects": ("Звуковые эффекты", "Sound effects"), "3d": ("3D", "3D"),
    "retrieval": ("Поиск и данные", "Retrieval"), "forecasting": ("Прогнозирование", "Forecasting"),
    "safety": ("Безопасность", "Safety"), "agents": ("Агенты", "Agents"),
    "science": ("Наука", "Science"), "robotics": ("Робототехника", "Robotics"),
    "catalog": ("Каталог", "Catalog"), "methodology": ("Источники и методика", "Sources & methodology"),
    "env_nav": ("Окружение", "Environment"),
    "env_local_active": ("текущее окружение", "current environment"),
    "env_open_production": ("Открыть публичный сайт", "Open the public site"),
    "title": ("Энциклопедия нейросетей", "The AI model encyclopedia"),
    "subtitle": ("Возможности, цены и происхождение — с источниками.", "Capabilities, pricing and origins, with sources."),
    "search": ("Найти модель, разработчика или задачу", "Find a model, developer or task"),
    "find": ("Найти", "Search"), "all": ("Все модели", "All models"),
    "text": ("Текст и код", "Text & code"), "image": ("Изображения", "Images"),
    "video": ("Видео", "Video"), "audio": ("Аудио", "Audio"), "other": ("Другие", "Other"),
    "coding": ("Программирование", "Coding"), "documents": ("Документы", "Documents"),
    "reasoning": ("Рассуждения", "Reasoning"), "images": ("Генерация изображений", "Image generation"),
    "translation": ("Перевод", "Translation"), "task": ("Задача", "Task"),
    "price": ("Цена USD", "Price USD"), "any": ("Все", "All"),
    "priced": ("С проверенной ценой API", "Verified API pricing"), "unknown_price": ("Без цены API", "No API price"),
    "budget": ("Вход до $1 / 1M токенов", "Input up to $1 / 1M tokens"),
    "access": ("Доступ", "Access"), "api": ("API", "API"), "web": ("Сервис", "Service"),
    "download": ("Скачать", "Download"), "developer": ("Разработчик", "Developer"),
    "apply": ("Применить", "Apply"), "reset": ("Сбросить", "Reset"), "columns": ("Столбцы", "Columns"),
    "context": ("Контекст", "Context"), "license": ("Лицензия", "License"),
    "model": ("Модель", "Model"), "purpose": ("Для чего", "Use cases"), "checks": ("Проверки", "Evaluations"),
    "benchmark": ("Тест", "Benchmark"), "any_test": ("Все проверки", "All evaluations"),
    "sort": ("Порядок", "Sort by"), "price_metric": ("Единица цены", "Price unit"),
    "price_scope": ("Условия цены", "Price conditions"),
    "standard_prices": ("Стандартная оплата по использованию", "Standard pay-as-you-go"),
    "all_prices": ("Все условия, включая специальные", "All conditions, including special"),
    "number_asc": ("Выпуск: сначала старые", "Release: oldest first"),
    "number_desc": ("Выпуск: сначала новые", "Release: newest first"),
    "name_asc": ("Название: А–Я", "Name: A–Z"),
    "name_desc": ("Название: Я–А", "Name: Z–A"), "price_asc": ("Цена выбранной единицы: по возрастанию", "Selected price unit: low to high"),
    "price_desc": ("Цена выбранной единицы: по убыванию", "Selected price unit: high to low"),
    "purpose_asc": ("Назначение: А–Я", "Use case: A–Z"), "purpose_desc": ("Назначение: Я–А", "Use case: Z–A"),
    "check_best": ("Выбранный тест: лучший результат", "Selected test: best result"),
    "check_worst": ("Выбранный тест: худший результат", "Selected test: worst result"),
    "score": ("Результат выбранного теста", "Selected benchmark result"),
    "no_data": ("Нет проверенных данных", "No verified data"), "undisclosed": ("Не раскрыто", "Not disclosed"),
    "not_applicable": ("Не применимо", "Not applicable"), "checked": ("Проверено", "Verified"),
    "stale": ("Требует перепроверки", "Recheck needed"), "provider": ("Поставщик", "Provider"),
    "input": ("1M входных токенов", "1M input tokens"), "output": ("1M выходных токенов", "1M output tokens"),
    "unit_image": ("изображение", "image"), "megapixel": ("мегапиксель", "megapixel"),
    "second": ("секунда видео", "second of video"), "minute": ("минута аудио", "minute of audio"), "month": ("месяц", "month"),
    "weights": ("Открытые веса", "Open weights"), "local_cost": ("Локально: расходы на оборудование", "Local: hardware costs apply"),
    "service_unknown": ("Подписка: нет проверенной цены", "Subscription: no verified price"),
    "developer_eval": ("Данные разработчика", "Developer-reported"), "independent": ("Независимая проверка", "Independent evaluation"),
    "lower": ("Меньше — лучше", "Lower is better"), "higher": ("Больше — лучше", "Higher is better"),
    "shown": ("Показано", "Showing"), "of": ("из", "of"), "records": ("моделей", "models"),
    "previous": ("Назад", "Previous"), "next": ("Далее", "Next"),
    "retry": ("Повторить", "Retry"),
    "empty": ("Модели не найдены", "No models found"), "empty_help": ("Попробуйте другое название или измените фильтры.", "Try another name or change your filters."),
    "report": ("Сообщить об ошибке", "Report an error"), "editor": ("Редакция", "Editorial"),
    "sample": ("Стартовая выборка публичных моделей", "Initial selection of public models"),
    "back": ("Все модели", "All models"), "suitable": ("Подходит для", "Best suited for"),
    "limitations": ("Основные ограничения", "Key limitations"), "cost": ("Стоимость", "Pricing"),
    "details": ("Условия и источник", "Conditions & source"), "quality": ("Возможности и качество", "Capabilities & quality"),
    "resources": ("Скорость и расход", "Speed & resources"), "origin": ("Кто стоит за моделью", "Who is behind the model"),
    "creation": ("Как создавалась", "How it was built"), "philosophy": ("Философия разработки", "Development philosophy"),
    "specs": ("Технический паспорт", "Technical profile"), "sources": ("Источники", "Sources"),
    "changes": ("История изменений", "Change history"), "version": ("Версия", "Version"),
    "release": ("Дата выпуска", "Release date"), "country": ("Страна организации", "Organization country"),
    "country_origin": ("Страна происхождения", "Country of origin"),
    "modalities": ("Форматы", "Modalities"), "languages": ("Языки", "Languages"),
    "speed": ("Скорость ответа", "Response speed"), "memory": ("Память и оборудование", "Memory & hardware"),
    "energy": ("Энергопотребление", "Energy consumption"), "training": ("Обучение", "Training"),
    "ownership": ("Владение и финансирование", "Ownership & funding"), "service_price": ("Пользовательский сервис", "User-facing service"),
    "tokens": ("токенов", "tokens"), "yes": ("Да", "Yes"), "no": ("Нет", "No"),
    "measurement": ("Дата измерения", "Measurement date"), "conditions": ("Условия", "Conditions"),
    "documentation": ("Документация", "Documentation"), "source": ("Источник", "Source"),
    "search_models": ("Поиск моделей, инструментов, разработчиков…", "Search models, tools, developers…"),
    "all_entries": ("Все", "All"),
    "models_tab": ("Модели", "Models"),
    "tools_tab": ("Инструменты", "Tools"),
    "results": ("результатов", "results"),
    "type_col": ("Тип", "Type"),
    "model_or_tool": ("Модель / инструмент", "Model / tool"),
    "tool": ("Инструмент", "Tool"), "category_col": ("Категория", "Category"),
    "ecosystem": ("Модели / экосистема", "Models / ecosystem"),
    "platforms_access": ("Платформы / доступ", "Platforms / access"),
    "local_execution": ("Локально", "Local execution"),
    "official_link": ("Официальная ссылка", "Official link"),
    "supported_models": ("Поддерживаемые модели / экосистема", "Supported models / ecosystem"),
    "platforms": ("Платформы", "Platforms"),
    "empty_tools": ("Инструменты не найдены", "No tools found"),
    "aipedia_rating": ("Рейтинг AIpediya", "AIpediya rating"),
    "independent_checks": ("Независимые проверки", "Independent evaluations"),
    "share": ("Поделиться", "Share"),
    "save": ("Сохранить", "Save"),
    "save_hint": ("Сохранение станет доступно после запуска личного кабинета.", "Saving will be available after the personal account launches."),
    "copied": ("Ссылка скопирована", "Link copied"),
    "copy_manual": ("Скопируйте ссылку вручную", "Copy the link manually"),
    "close_panel": ("Закрыть", "Close"),
    "overview": ("Обзор", "Overview"),
    "cost_and_access": ("Стоимость и доступ", "Pricing & access"),
    "checks_tab": ("Проверки", "Evaluations"),
    "our_score": ("Наша сводная оценка", "Our composite score"),
    "release_date_short": ("Дата релиза", "Release date"),
    "context_window": ("Контекстное окно", "Context window"),
    "suited_for": ("Для чего подходит", "Best suited for"),
    "brief": ("Краткие сведения", "Snapshot"),
    "capabilities": ("Ключевые возможности", "Key capabilities"),
    "go_to_provider": ("Перейти к провайдеру", "Go to provider"),
    "github": ("GitHub", "GitHub"),
    "rows_per_page": ("Строк на странице", "Rows per page"),
    "panel_label": ("Карточка", "Card"),
    "slogan": ("Сделаем ИИ более открытым миру.", "Making AI more open to the world."),
    "type_asc": ("Тип: А–Я", "Type: A–Z"),
    "type_desc": ("Тип: Я–А", "Type: Z–A"),
    "developer_asc": ("Разработчик: А–Я", "Developer: A–Z"),
    "developer_desc": ("Разработчик: Я–А", "Developer: Z–A"),
    "context_asc": ("Контекст: по возрастанию", "Context: low to high"),
    "context_desc": ("Контекст: по убыванию", "Context: high to low"),
    "status_asc": ("Статус: А–Я", "Status: A–Z"),
    "status_desc": ("Статус: Я–А", "Status: Z–A"),
    "category_asc": ("Категория: А–Я", "Category: A–Z"),
    "category_desc": ("Категория: Я–А", "Category: Z–A"),
    "ecosystem_asc": ("Экосистема: А–Я", "Ecosystem: A–Z"),
    "ecosystem_desc": ("Экосистема: Я–А", "Ecosystem: Z–A"),
    "platform_asc": ("Платформы: А–Я", "Platforms: A–Z"),
    "platform_desc": ("Платформы: Я–А", "Platforms: Z–A"),
    "local_asc": ("Локальная работа: А–Я", "Local execution: A–Z"),
    "local_desc": ("Локальная работа: Я–А", "Local execution: Z–A"),
    "release_asc": ("Релиз: сначала старые", "Release: oldest first"),
    "release_desc": ("Релиз: сначала новые", "Release: newest first"),
    "clear_filter": ("Сбросить фильтр", "Clear filter"),
    "active_filters": ("Выбранные условия", "Selected filters"),
    "share_link": ("Ссылка на запись", "Record link"),
    "panel_loading": ("Загрузка карточки", "Loading the card"),
    "panel_error": ("Не удалось открыть карточку. Обновите страницу.", "Could not open the card. Refresh the page."),
    "no_rating_yet": ("", ""),
    "report_message": ("Что нужно исправить? Укажите источник, если он есть.", "What needs correcting? Include a source if available."),
    "send": ("Отправить", "Submit"), "thanks": ("Спасибо. Сообщение передано в редакцию.", "Thank you. Your report has been sent to the editors."),
    "created": ("Добавлено", "Added"), "updated": ("Обновлено", "Updated"), "deleted": ("Удалено", "Deleted"),
    "review_note": ("Сведения по источнику разработчика", "Information from the developer's source"),
    "not_found": ("Страница не найдена", "Page not found"),
    "ModelVersion": ("Версия модели", "Model version"), "Offer": ("Тариф", "Price"),
    "Evaluation": ("Результат теста", "Evaluation"), "Fact": ("Характеристика", "Fact"), "Access": ("Способ доступа", "Access method"),
}

def t(key, lang):
    """Resolve one interface string for a language with English fallback.

    Base ru/en come from :data:`TEXT`; other locales come from
    :data:`catalog.ui_translations.TRANSLATIONS`. A missing translation falls
    back to English so the interface never shows a raw key.
    """
    pair = TEXT.get(key)
    if lang == "ru":
        return pair[0] if pair else key
    if lang == "en":
        return pair[1] if pair else key
    override = TRANSLATIONS.get(lang, {}).get(key)
    if override:
        return override
    return pair[1] if pair else key


def category_label(code, labels, lang):
    """Resolve a category / use-case label with English database fallback.

    The ru/en labels in the database stay the source of truth; other locales
    come from the code-based taxonomy translations and fall back to English.
    """
    labels = labels or {}
    if lang not in ("ru", "en"):
        override = CATEGORY_TRANSLATIONS.get(lang, {}).get(code)
        if override:
            return override
    return labels.get(lang) or labels.get("en") or labels.get("ru") or code


def site_context(request):
    from .locale_urls import absolute, localize, switch_url
    from .seo import json_ld_script

    lang = getattr(request, "aipedia_lang", None) or DEFAULT_LANG
    ui = {key: t(key, lang) for key in TEXT}
    ads_enabled = bool(
        settings.AIPEDIA_ADS_ENABLED
        and settings.AIPEDIA_ADS_CLIENT
        and settings.AIPEDIA_ADS_SLOT
    )
    from .static_pages import label_text
    return {
        "lang": lang,
        "dir": direction(lang),
        "lang_native": LANGUAGE_NAMES.get(lang, lang),
        "language_options": language_options(),
        "language_links": [(code, native, switch_url(request, code)) for code, native in language_options()],
        "nav": {
            "home": localize("/", lang),
            "models": localize("/", lang),
            "tools": localize("/tools/", lang),
            "methodology": localize("/methodology", lang),
            "privacy": localize("/privacy", lang),
            "history": localize("/history/", lang),
            "collections": localize("/collections/", lang),
            "datasets": localize("/datasets/", lang),
            "collections_label": label_text("collections", lang),
            "datasets_label": label_text("datasets", lang),
            "datasets_enabled": bool(getattr(settings, "AIPEDIA_DATASETS_PUBLIC", False)),
        },
        "ui": ui,
        "js_i18n": {
            "copied": ui["copied"],
            "copyManual": ui["copy_manual"],
            "panelError": ui["panel_error"],
            "retry": ui["retry"],
        },
        # Views replace this; the default (e.g. for error pages) is never indexable.
        "seo": {"title": "AIpediya", "description": "", "noindex": True, "canonical": "",
                "alternates": [], "x_default": "", "json_ld": [], "og_type": "website",
                "og_url": absolute("/", lang), "og_locale": lang.replace("-", "_")},
        "organization_ld": json_ld_script({
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "AIpediya",
            "url": absolute("/", "en"),
            "logo": f"{settings.AIPEDIA_PUBLIC_ORIGIN}/static/brand-512.png",
        }),
        "public_origin": settings.AIPEDIA_PUBLIC_ORIGIN,
        "verification": {
            "google": settings.GOOGLE_SITE_VERIFICATION,
            "bing": settings.BING_SITE_VERIFICATION,
            "yandex": settings.YANDEX_SITE_VERIFICATION,
            "naver": settings.NAVER_SITE_VERIFICATION,
        },
        "ads": {
            "enabled": ads_enabled,
            "client": settings.AIPEDIA_ADS_CLIENT,
            "slot": settings.AIPEDIA_ADS_SLOT,
            "privacy_contact": settings.AIPEDIA_PRIVACY_CONTACT,
        },
        "local_nav": settings.AIPEDIA_ENV == "local",
        "production_home": absolute("/", lang),
    }
