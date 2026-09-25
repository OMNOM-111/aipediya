"""Authored English/Russian prose for GSD-1.0 public pages.

Methodology and collection (hub) texts are registered into
:data:`catalog.static_pages.STATIC_PAGES`, so they are localized through the
same source-hash overlay mechanism as the privacy page. Translations of these
new blocks into the other 20 locales live in
``data/discovery_translations.json`` with explicit provenance
(``agent-draft``: written by the implementing agent, not yet reviewed by a
person). A locale is only indexable for a page when every block of that page
has a translation for it; otherwise the page renders with English blocks
marked ``lang="en"`` and ``noindex``.

The methodology describes rules that are implemented today. Plans are listed
separately and never presented as existing practice.
"""

METHODOLOGY = [
    ("p",
     "AIpediya is an editorial reference catalog of AI models and AI tools. Models and tools are separate catalogs with their own numbering, filters and cards. It is a curated selection, not a complete registry of every model that exists.",
     "AIpediya — редакционный справочный каталог AI-моделей и AI-инструментов. Модели и инструменты — отдельные каталоги со своей нумерацией, фильтрами и карточками. Это отобранная выборка, а не полный реестр всех существующих моделей."),
    ("h2", "Sources and check dates", "Источники и даты проверки"),
    ("p",
     "Each record is based on sources: first the developer's official documentation, announcement, model card or pricing page; reputable secondary sources only where no official source exists. Every card links its source and shows when an editor last checked it. The check date is not the release date and not a test run by AIpediya.",
     "Каждая запись основана на источниках: прежде всего официальная документация, анонс, карточка модели или страница цен разработчика; авторитетные вторичные источники — только если официального нет. Каждая карточка ссылается на источник и показывает, когда редактор проверял его в последний раз. Дата проверки — это не дата выпуска и не тест, проведённый AIpediya."),
    ("h2", "What gets published", "Что публикуется"),
    ("p",
     "A record is published only after its existence, name, developer and sources have been reviewed. Candidates with open questions about existence, date, sources or data stay in an internal review queue and do not appear on the site, in sitemaps or in datasets. Removing a record from publication keeps its history; nothing is silently deleted.",
     "Запись публикуется только после проверки её существования, названия, разработчика и источников. Кандидаты с открытыми вопросами о существовании, дате, источниках или данных остаются во внутренней очереди проверки и не появляются на сайте, в картах сайта и в наборах данных. Снятие с публикации сохраняет историю записи; ничего не удаляется незаметно."),
    ("h2", "Release dates and catalog numbers", "Даты выпуска и номера каталога"),
    ("p",
     "An exact release date is shown only when a source confirms it. Otherwise the earliest reliable date of public existence is shown with the ≈ sign and month or day precision. Unknown dates stay empty and those records appear last in chronological order. Catalog numbers follow verified release dates from oldest to newest; releases on the same date are ordered by name.",
     "Точная дата выпуска показывается, только если её подтверждает источник. Иначе показывается самая ранняя надёжная дата публичного существования со знаком ≈ и точностью до месяца или дня. Неизвестные даты остаются пустыми, а такие записи идут последними в хронологии. Номера каталога следуют проверенным датам выпуска от старых к новым; выпуски одного дня упорядочены по названию."),
    ("h2", "Prices", "Цены"),
    ("p",
     "Prices are the provider's published list prices in US dollars with the unit stated, for example per 1 million input tokens, per image, per second of video or per month. Input and output tokens, batch, off-peak and other tiers are kept separate together with their conditions. A free tier is not free unlimited API access, and a subscription belongs to a service rather than to one model version. Taxes, quotas and regional terms can change the final cost. An unknown price stays empty, never zero.",
     "Цены — опубликованные поставщиком прейскурантные цены в долларах США с указанием единицы: например, за 1 млн входных токенов, за изображение, за секунду видео или за месяц. Входные и выходные токены, пакетный режим, непиковые часы и другие тарифы хранятся раздельно вместе с условиями. Бесплатный уровень — это не бесплатный неограниченный доступ к API, а подписка относится к сервису, а не к одной версии модели. Налоги, квоты и региональные условия могут изменить итоговую стоимость. Неизвестная цена остаётся пустой, а не нулевой."),
    ("h2", "Country of origin", "Страна происхождения"),
    ("p",
     "The country of origin reflects the documented location of the developer organization and is recorded with a source. A record can have more than one country.",
     "Страна происхождения отражает документально подтверждённое местонахождение организации-разработчика и записывается с источником. У записи может быть несколько стран."),
    ("h2", "Independent evaluations", "Независимые оценки"),
    ("p",
     "Only results of the same benchmark and protocol are comparable. Each result names the evaluator, benchmark, configuration, snapshot and check date. Developer-reported results are labelled separately from independent runs and composite indices. Third-party results are shown only after the identity of the model and permission to reuse the source have been verified. AIpediya does not calculate its own rating or a universal intelligence score.",
     "Сравнимы только результаты одного теста с одинаковым протоколом. У каждого результата указаны автор оценки, тест, конфигурация, снимок и дата проверки. Результаты, заявленные разработчиком, отделены от независимых прогонов и сводных индексов. Сторонние результаты показываются только после проверки соответствия модели и права на повторное использование источника. AIpediya не рассчитывает собственный рейтинг или универсальный «балл интеллекта»."),
    ("h2", "Open weights and licenses", "Открытые веса и лицензии"),
    ("p",
     "Open weights means the weights can be downloaded under the license stated by the developer. It is not the same as open source, and running a model locally still requires hardware and energy.",
     "Открытые веса означают, что веса можно скачать на условиях лицензии разработчика. Это не то же самое, что открытый исходный код, а локальный запуск модели всё равно требует оборудования и энергии."),
    ("h2", "Unknown values and conflicting sources", "Неизвестные значения и противоречия источников"),
    ("p",
     "Unknown is shown as empty, never as zero or as “no”. When sources disagree or a value cannot be confirmed, the value stays empty or the record stays in review; values are never averaged or guessed.",
     "Неизвестное показывается пустым, а не нулём и не словом «нет». Если источники расходятся или значение нельзя подтвердить, поле остаётся пустым или запись остаётся на проверке; значения не усредняются и не угадываются."),
    ("h2", "Updates and translations", "Обновления и переводы"),
    ("p",
     "Editors update records when sources change; changes to records, prices, facts and evaluations are kept in an internal history. There is no automatic daily monitoring. Card text is written in English and Russian and machine-translated into the other languages; a translation is refreshed when its English source changes, and text that is not translated yet is shown in English.",
     "Редакторы обновляют записи при изменении источников; изменения записей, цен, фактов и оценок сохраняются во внутренней истории. Автоматического ежедневного мониторинга нет. Текст карточек пишется на английском и русском и машинно переводится на остальные языки; перевод обновляется при изменении английского источника, а ещё не переведённый текст показывается на английском."),
    ("h2", "Not available yet", "Пока не реализовано"),
    ("p",
     "Planned, not implemented: a public change history, a public API and personal saved lists.",
     "Запланировано, но не реализовано: публичная история изменений, публичный API и личные сохранённые списки."),
]

# Hub text blocks: ("title" | "intro" | "criterion", English, Russian).
HUBS = {
    "coding-models": [
        ("title", "AI models for programming", "AI-модели для программирования"),
        ("intro", "Published AI models whose documented uses include writing, explaining or reviewing code, with prices, access and independent evaluations.",
         "Опубликованные AI-модели, среди документированных задач которых есть написание, объяснение или проверка кода, — с ценами, доступом и независимыми оценками."),
        ("criterion", "Included: published models tagged with the programming use case. Inclusion does not rank quality.",
         "Критерий: опубликованные модели с задачей «программирование». Включение не означает оценку качества."),
    ],
    "video-models": [
        ("title", "AI models for video", "AI-модели для видео"),
        ("intro", "Published AI models in the video category: generating, editing or understanding video, with sources and prices where known.",
         "Опубликованные AI-модели категории «видео»: создание, редактирование или анализ видео — с источниками и ценами, где они известны."),
        ("criterion", "Included: published models whose catalog category is video.",
         "Критерий: опубликованные модели, у которых категория каталога — видео."),
    ],
    "music-models": [
        ("title", "AI models for music", "AI-модели для музыки"),
        ("intro", "Published AI models documented for generating music, with sources and prices where known.",
         "Опубликованные AI-модели, документированные для создания музыки, — с источниками и ценами, где они известны."),
        ("criterion", "Included: published models tagged with the music use case.",
         "Критерий: опубликованные модели с задачей «музыка»."),
    ],
    "free-tier-models": [
        ("title", "AI models with a free tier", "AI-модели с бесплатным уровнем"),
        ("intro", "Published AI models for which a provider lists a free tier with a price of zero. Free tiers have limits; this is not free unlimited API access.",
         "Опубликованные AI-модели, для которых поставщик указывает бесплатный уровень с нулевой ценой. У бесплатных уровней есть ограничения; это не бесплатный неограниченный доступ к API."),
        ("criterion", "Included: published models with at least one active listed price of 0 USD.",
         "Критерий: опубликованные модели хотя бы с одной действующей ценой 0 долларов США."),
    ],
    "api-models": [
        ("title", "AI models available through an API", "AI-модели с доступом через API"),
        ("intro", "Published AI models that a provider offers through a programmatic API, with list prices where they are published.",
         "Опубликованные AI-модели, которые поставщик предоставляет через программный API, — с опубликованными ценами, где они есть."),
        ("criterion", "Included: published models with at least one documented API access route.",
         "Критерий: опубликованные модели хотя бы с одним документированным способом доступа через API."),
    ],
    "open-weight-models": [
        ("title", "Open-weight AI models", "AI-модели с открытыми весами"),
        ("intro", "Published AI models whose weights can be downloaded under the developer's license. Open weights are not the same as open source; check each license.",
         "Опубликованные AI-модели, веса которых можно скачать на условиях лицензии разработчика. Открытые веса — не то же самое, что открытый исходный код; проверяйте каждую лицензию."),
        ("criterion", "Included: published models marked as open weights.",
         "Критерий: опубликованные модели с отметкой «открытые веса»."),
    ],
    "models-from-china": [
        ("title", "AI models developed in China", "AI-модели, разработанные в Китае"),
        ("intro", "Published AI models whose developer organization is documented as based in China, with sources for the country of origin.",
         "Опубликованные AI-модели, организация-разработчик которых документально находится в Китае, — с источниками о стране происхождения."),
        ("criterion", "Included: published models with China among the recorded countries of origin.",
         "Критерий: опубликованные модели, среди стран происхождения которых указан Китай."),
    ],
    "models-released-2025": [
        ("title", "AI models released in 2025", "AI-модели, выпущенные в 2025 году"),
        ("intro", "Published AI models with a confirmed exact release date in 2025, from the oldest to the newest.",
         "Опубликованные AI-модели с подтверждённой точной датой выпуска в 2025 году, от старых к новым."),
        ("criterion", "Included: published models with an exact, source-confirmed release date in 2025. Approximate (≈) dates are not included.",
         "Критерий: опубликованные модели с точной, подтверждённой источником датой выпуска в 2025 году. Приблизительные даты (≈) не включаются."),
    ],
    "long-context-models": [
        ("title", "AI models with a context window of 1 million tokens or more", "AI-модели с контекстным окном от 1 млн токенов"),
        ("intro", "Published AI models with a documented context window of at least 1,000,000 tokens. A larger context window does not mean better quality.",
         "Опубликованные AI-модели с документированным контекстным окном не менее 1 000 000 токенов. Большее окно контекста не означает более высокое качество."),
        ("criterion", "Included: published models with a recorded context window of 1,000,000 tokens or more.",
         "Критерий: опубликованные модели с указанным контекстным окном от 1 000 000 токенов."),
    ],
    "coding-tools": [
        ("title", "AI tools for programming", "AI-инструменты для программирования"),
        ("intro", "Published AI coding assistants, coding agents and IDE tools, with platforms, supported models and prices.",
         "Опубликованные AI-ассистенты и агенты для программирования и инструменты для IDE — с платформами, поддерживаемыми моделями и ценами."),
        ("criterion", "Included: published tools in the coding assistant, coding agent or IDE tool categories.",
         "Критерий: опубликованные инструменты категорий «ассистент для кода», «агент для кода» или «инструмент для IDE»."),
    ],
}

# Short labels used by the new pages (English, Russian). The other locales are
# looked up in the same overlay as the blocks above.
LABELS = {
    "collections": ("Collections", "Подборки"),
    "collections_intro": ("Curated selections of published catalog records, each with an explicit inclusion rule.",
                          "Подборки опубликованных записей каталога, у каждой — явное правило включения."),
    "entries_count": ("Records in this collection", "Записей в подборке"),
    "criterion": ("Inclusion rule", "Правило включения"),
    "models_catalog_title": ("AI model catalog: prices, access and independent evaluations",
                             "Каталог AI-моделей: цены, доступ и независимые оценки"),
    "models_catalog_description": ("Compare verified AI models by developer, purpose, pricing, access, context window and independent evaluations, with sources.",
                                   "Сравнивайте проверенные AI-модели по разработчику, назначению, ценам, доступу, контекстному окну и независимым оценкам — с источниками."),
    "tools_catalog_title": ("AI tools catalog: platforms, supported models and pricing",
                            "Каталог AI-инструментов: платформы, поддерживаемые модели и цены"),
    "tools_catalog_description": ("Compare verified AI tools by category, developer, platforms, supported models, local execution and pricing, with sources.",
                                  "Сравнивайте проверенные AI-инструменты по категории, разработчику, платформам, поддерживаемым моделям, локальному запуску и ценам — с источниками."),
    "model_title_suffix": ("AI model", "AI-модель"),
    "tool_title_suffix": ("AI tool", "AI-инструмент"),
    "page_n": ("Page", "Страница"),
    "methodology_description": ("How AIpediya selects sources, publishes records, dates releases, records prices and origins and shows independent evaluations.",
                                "Как AIpediya выбирает источники, публикует записи, датирует выпуски, записывает цены и происхождение и показывает независимые оценки."),
    "datasets": ("Open data", "Открытые данные"),
    "home": ("Home", "Главная"),
}

HUB_SLUGS = tuple(HUBS)
