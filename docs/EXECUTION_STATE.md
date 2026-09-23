# Текущее состояние AIpedia

Живой паспорт локальной разработки. Не дублирует `AGENTS.md`.
Отчёты законченных выпусков — `docs/history/`.
Пакет для нового чата собирается командой `.\.venv\Scripts\python.exe tools/pack_ai_context.py` и **не** редактируется как независимый источник.

- Обновлено (UTC): 2026-09-23T20:05:00Z
- Задача владельца: опубликовать на `https://aipediya.com/` точное текущее
  состояние Local и проверить полноту данных и актуальность версии.
- Реализация Local: **IMPLEMENTATION COMPLETE** (i18n 22 языка + UI-исправления
  правой панели и языкового меню).
- Автоматическая проверка: **PASS** — `catalog` 140 тестов.
- Local-браузерная проверка исправлений: **PASS** — панель закрывается по клику
  вне/Escape/крестику, клики внутри не закрывают, меню языков над панелью,
  смена языка сохраняет открытую карточку; desktop и mobile; EN/UK/AR(RTL).
- Разрешение на Production: **ПОЛУЧЕНО** (явный мандат владельца на выпуск
  итоговой исправленной версии по `docs/RELEASE.md`).
- Предыдущий Production: commit `43e2d3feba57cf67084cc2e3774c86a72ce361b5`.
- Production: **DEPLOYED AND VERIFIED** на commit
  `289d01b30c865a66adf674d5329b1133ee4c3e75` (tag `release-2026-09-23-i18n-ui`),
  2026-09-23. Деплой по `docs/RELEASE.md` через существующий SSH-доступ к общей
  машине (владелец подтвердил: AIpedia и StratForge — один сервер; тронуты только
  пути/службы AIpedia). Серверный online-backup боевой БД
  `aipedia-before-code-20260923T194848Z.sqlite3`; миграция `0015_contenttranslation`
  применена; перезапущена только программа `aipedia`; `/healthz` release совпал.
- Перенос переводов: 42 260 локализаций импортированы в боевую БД идемпотентной
  командой `import_translations` (по slug+поле+язык+sha256 английского источника,
  без провайдера, без копирования Local SQLite). Повторный запуск — 0 применённых.
  Боевые данные после: ContentTranslation 42 260; ядро без изменений
  (901/138/555/881/343, revisions 4354, integrity ok).
- Публичная проверка `https://aipediya.com/`: **PASS** — release 289d01b,
  EN/UK/AR(RTL)/FA, модель и инструмент, локализация и страны, панель (клик вне/
  Escape/крестик), меню языков над панелью, смена языка при открытой карточке,
  mobile, защита токена `1M`; секретов в развёрнутом коде нет.
- Поверх выпуска `43e2d3f` реализованы мультиязычность интерфейса на 22 языка,
  provider-agnostic translation pipeline и исправления UI. Подробности —
  раздел «Мультиязычность 22 языка и translation pipeline» ниже.

## Три слоя

Последний **подтверждённый** Production: commit
`289d01b30c865a66adf674d5329b1133ee4c3e75` (tag `release-2026-09-23-i18n-ui`),
2026-09-23, способ: code-only выпуск по `docs/RELEASE.md` через существующий
SSH-доступ к общей машине + идемпотентный импорт переводов (`import_translations`).
Предыдущий Production `43e2d3feba57cf67084cc2e3774c86a72ce361b5` (2026-09-22),
отчёт: `docs/history/2026-09-22-global-catalog-release.md`.

| Слой | Указатель | Примечание |
| --- | --- | --- |
| Local | post-release audit поверх `43e2d3f` + только локальные research/output файлы | runtime-код и каталог равны выпуску; Local работает на 127.0.0.1:18810 |
| GitHub | `origin/main` содержит `43e2d3f` и последующий audit-отчёт | runtime-код выпуска не менялся |
| Production | `43e2d3f` | `/healthz` и серверная БД проверены после deploy |

| Изменение | Local | GitHub | Production |
| --- | --- | --- | --- |
| Хронологические номера и даты выпуска | В коде и в Local-каталоге | Есть (с `6e901dc`) | Опубликовано как `6e901dc` |
| Local/Production, ярлыки, code-only выпуск | Реализовано | `901eb47` | Не опубликовано |
| `AGENTS.md` и правило Cursor | Реализовано | `7e66da2` | Не опубликовано |
| Живой статус, решения, сборщик `AI_CONTEXT` | Есть | Есть | Код есть; пакет остаётся локальным |
| Редизайн таблицы и правой панели | PASS | Есть | PASS |
| Финальная визуальная доводка по утверждённому PNG | PASS | Есть | PASS |
| Знаки разработчиков у моделей | PASS | Есть | PASS |
| Подгрузка строк при прокрутке (150 → 50…) | PASS | Есть | PASS |
| Дата релиза с днём и месяцем (RU/EN) | PASS | Есть | PASS |
| Раздельные каталоги моделей и инструментов | 763 / 138 | Есть | 763 / 138, PASS |
| Reconciliation Local + applicability-fixed research master | Импортировано; XLSX собран | Payload в Git | Импортировано |
| Визуальная проверка после reconciliation | PASS | Есть | PASS |
| Видимый бренд `AIpediya` и палитры Midnight/Day | PASS | Есть | PASS |
| Полный выпуск Local на Production | Завершён | `43e2d3f` | DEPLOYED AND VERIFIED |
| Ярлыки через `DesktopDirectory` | `install-shortcuts.ps1` изменён ранее, не этой задачей | Нет | Нет |
| Неотслеживаемые дампы `data/research/` | Только на диске | Нет | Нет |

## Мультиязычность 22 языка и translation pipeline (2026-09-23, Local, не опубликовано)

Реализовано поверх выпуска `43e2d3f` в рабочем дереве Local. Не закоммичено,
Production без изменений, серверная SQLite не трогалась. Существующая RU/EN
логика расширена, а не заменена.

- 22 языка интерфейса: `en, ru, zh-Hans, es, fr, ar, pt-BR, de, ja, ko, hi, id,
  tr, vi, it, pl, uk, fa, th, nl, bn, zh-Hant`. English — канонический,
  `x-default` и итоговый fallback.
- Определение языка: URL `?lang=` → cookie `aipedia_lang` → `Accept-Language` →
  слабый хинт `CF-IPCountry` → English. Ручной выбор пишется в cookie и не
  переопределяется гео (`catalog/i18n.py`, `catalog/middleware.py`).
- URL не менялись: локаль остаётся в query-параметре `?lang=`. `canonical`,
  полный набор `hreflang` для 22 локалей и `hreflang="x-default"` (English),
  `<html lang dir>`, sitemap с `xhtml:link` alternates
  (`catalog/seo.py`, `templates/base.html`, `catalog/views.py`).
- Переключатель на 22 языка (родные названия, `<details>`-меню), сохраняет
  текущую страницу/карточку (`templates/includes/site_header.html`).
- RTL для `ar` и `fa` через логические CSS-свойства и точечный блок `[dir=rtl]`;
  бренд остаётся LTR (`static/site.css`, `static/table-layout.css`, `static/site.js`).
- Статические переводы UI (~299 ключей × 20 языков) и таксономии категорий
  (24 кода × 20 языков) хранятся в коде `catalog/ui_translations.py`;
  резолверы `catalog/context.t` и `category_label`. Отсутствующий перевод →
  English fallback, техно-ключи не показываются. Локализованные даты/месяцы для
  всех локалей (`catalog/templatetags/catalog_tags.py`).
- Фактические поля (названия, компании, URL, цены, числа, рейтинги, даты, API
  identifiers) не переводятся и общие для всех языков.
- Translation pipeline для будущих динамических данных: модель
  `ContentTranslation` (состояния `current`/`outdated`/`missing`/`reviewed`,
  привязка к sha-256 hash английского источника), провайдеры
  `catalog/translation_providers.py` (offline mock по умолчанию, adapter Azure
  Translator, null), сервис `catalog/translation_pipeline.py`, команда
  `translate_catalog` (status/dry-run/backfill/повторный перевод только
  missing/outdated), сигнал `pre_save` делает перевод устаревшим при изменении
  источника без вызова API. Ключ провайдера — только из env
  `AIPEDIA_AZURE_TRANSLATOR_KEY`; реальный внешний API в тестах не вызывается.
  Миграция `0015_contenttranslation` (только схема).

Проверки: **все автоматические тесты PASS** (`manage.py test catalog
--settings=aipedia.test_settings`). Включают `test_i18n` (20), `test_translation_pipeline`
(14), `test_translation_finalization` (9: auto-translate on-commit+рендер,
отключён по умолчанию, bulk-suppression, dedup translation memory, URL-agnostic
retrieval, country_label, семантика `missing`/`not_applicable`, GET не вызывает
Translator). Ранее единственный FAIL `test_pack_ai_context…install-shortcuts.ps1`
исправлен выравниванием `SOURCE_FILES` в `tools/pack_ai_context.py` (файл существует
и в Git; тест ожидал его в пакете — это pre-existing рассинхрон packer↔тест, не
связан с i18n). `manage.py check` PASS. Данные Local без потерь:
763 модели, 138 инструментов, 555 offers, 1205 accesses, 881 evaluations,
343 sources, 2900 research, 901 ModelVersion; **revisions = 4354 (baseline
восстановлен)**; **ContentTranslation = 42260 (state=current, provider=azure)**.

Реальный Azure backfill выполнен (провайдер F0, region eastus2, endpoint
глобальный): 901 объект, **360 запросов**, **1 680 285 биллинг-символов**
(< 2 000 000 бесплатного месячного лимита F0), 42 254 перевода, 42 254 reused
через translation memory (dedup по sha-256), 0 failed. Состояния переводов
(семантика исправлена: `missing` = «источник есть, актуального перевода нет»,
`not_applicable` = «английского источника нет»):
`current=42260, outdated=0, reviewed=0, missing=0, not_applicable=36800`. Все
36800 `not_applicable` — слоты полей с пустым английским источником (1840 полей
× 20 языков), переводить нечего; поля с содержимым переведены на 100%
(2113 × 20 = 42260). **Реальных недостающих переводов нет (missing=0).**
Аудит остаточной локализации `manage.py audit_localization` по всем 22 локалям:
`static_gaps=0`, `untranslated_with_source=0`, `ui_missing/category_missing/
country_missing = []` для каждого языка (allowlist универсальных ключей
api/cli/ide/github/ocr/3d/no_rating_yet).

Финализирующий QA-слой (без повторного вызова Azure):
- Семантическое качество: команда `audit_translation_quality` (offline) сверяет
  42 260 переводов с английским источником. После нормализации ложных срабатываний
  (персидские/арабские цифры ۱۲۳, десятичная запятая 1,05, компактность CJK):
  `empty=0, escape_artifact=0, no_target_script=0, length_extreme=0`;
  числа сохранены; идентификаторы для латинских локалей сохранены (62 остатка —
  косметическая нормализация регистра избыточного `exact version: gpt-5-pro` →
  `GPT-5-Pro`, имя модели сохранено); в индийских/CJK письменностях 1367
  транслитераций имён собственных (естественно; slug/ID/заголовки — латиница).
  Системных дефектов, требующих повторного перевода, нет.
- **Систематический rendered QA 22/22** (автоматический аудит через Django test
  client по реальной БД, не ручной браузер): для каждой из 22 локалей отрендерены
  карточка Model (Claude 3 Haiku) и Tool (GitHub Copilot) — HTTP 200,
  локализованные описание/страна в целевом письме, направление (`ar`/`fa` RTL),
  бренды/ID (Anthropic, claude-3-haiku, GitHub) сохранены: **0 fails**. Mobile:
  `<meta viewport>` + 8 `@media` брейкпоинтов; RTL: 39 логических CSS-свойств,
  бренд `direction: ltr`.
- **Targeted visual QA** (реальный браузер) для критичных представительных локалей
  и RTL: ar (карточка + privacy, зеркальная раскладка), плюс проверка контента
  в uk/de/ja/fa/zh-Hant. Не для всех 22 локалей визуально — это targeted, а 22/22
  выше — систематический rendered-аудит.
- Авто-перевод доказан end-to-end (mock): новый/изменённый English → авто-перевод
  на commit → сохранение (`ContentTranslation` + JSON) → рендер в целевой локали;
  и доказано, что GET/просмотр страниц **никогда** не вызывает Translator
  (тесты `test_saving_model_autotranslates_on_commit_and_renders`,
  `test_get_requests_never_call_the_translator`).

Локализация карточек (root-cause фиксы поверх статики UI):
- Страны — детерминированный код-слой `catalog/countries.py`
  (`COUNTRY_TRANSLATIONS` ISO2 × 22 языка, `country_label()`), фильтр
  `country_name`, подключён в `templates/panel.html` и
  `templates/includes/country_flag.html`. RU/EN — из БД (`name_ru/name_en`),
  прочие — из карты, fallback English.
- Модальности (text/image/video/audio), open weights, yes/no — уже
  локализованы через `t()`/`label:lang`; факты — только `service_price`
  (цены, не переводятся).
- Прозаические поля модели (`description/suitable/limitations/origin/philosophy`)
  и инструмента (`description`) переводятся pipeline и рендерятся `local:lang`.
  `ecosystem` инструментов исключён (бренд-названия, ru==en).

Автоматический перевод новых/изменённых данных (штатный путь):
- `pre_save` помечает переводы устаревшими при изменении английского источника
  (без вызова API).
- `post_save` хук `auto_translate` (`catalog/signals.py`) переводит новый/
  изменённый объект после commit (`transaction.on_commit`), пакетно и
  безопасно; включается `AIPEDIA_AUTO_TRANSLATE` (по умолчанию off в коде для
  тестов/миграций; включён в `deploy/aipedia.env.example` и в Local `.env.local`).
- Массовые импорты используют `suppress_auto_translation()` (подключено в
  `promote_research`) и один пакетный `translate_catalog` после загрузки.
- Провайдер батчит `translate_batch` с retry на 429/5xx (Retry-After), dedup
  через translation memory; `translate_catalog` умеет `--dry-run` с оценкой
  биллинг-символов, `--status`, `--batch-size`.

Публичные не-карточные страницы:
- `privacy.html` локализована на 22 языка (`catalog/static_pages.py` +
  overlay `data/static_page_translations.json`, команда `translate_static_pages`;
  15 500 символов, 20 запросов). Рендер из локализованных блоков.
- `methodology.html` — сейчас осиротевший шаблон без маршрута/навигации/рендера
  (`/methodology` → 404). **Не удалять**: следующая задача Global Search &
  Discovery отдельно решит публичную локализованную Methodology page (маршрут,
  контент, hreflang/sitemap для неё).
- Панельные заметки покрытия оценок (`evaluation_gap`). Классификация содержимого:
  (а) AIpediya-авторская проза — 105 уникальных `reason` (20 550 символов) +
  4 generic label («Checked source» и др., 91 символ) → **должно локализоваться**;
  (б) сторонние имена бенчмарков/источников/URL/ID (7 label: BFCL, Open ASR,
  AVGen-Bench, EvalPlus, репозитории, URL, а также имена моделей/бенчмарков внутри
  reason) → **сохраняются в оригинале**. Пересчёт уникальных биллинг-символов
  после классификации и dedup: **412 820 символов** (× 20 языков). В месячном
  лимите F0 осталось **304 215** → **не помещается, дефицит 108 605 символов**.
  Платные расходы запрещены, поэтому эта часть **не переведена и НЕ считается
  завершённой** — единственный quota-blocker. Переводимо при сбросе месячного
  лимита F0 тем же pipeline; template-level dedup (27 шаблонов ≈ 105 000 символов)
  влез бы, но требует реконструкции имён собственных по 20 разно-типологическим
  языкам — риск неестественности (QA качества), не выполняется без решения владельца.
  Окружающий UI секции (заголовок, «почему нет оценки», дата) локализован.
  Очередь на следующий доступный период F0 quota (не обходить template-хаком,
  платных расходов не создавать):
  `AIpediya-authored eval-gap remaining: 412,820 billable chars; current shortfall: 108,605`.

Защита технических токенов (реальный дефект «1M → ۱ متر» и класс риска):
- `catalog/token_guard.py` — оборачивает машиночитаемые токены (`1M`, `128K`,
  `32K`, `7B`, `70B`, `405B`, версии/ID `gpt-5-pro`, `GPT-5.2`, акронимы `API`/
  `OCR`, URL) в `<span translate="no">`; провайдер Azure шлёт `textType=html`,
  затем markup снимается — Azure не может превратить токен в слово/единицу.
  Подтверждено реальным минимальным запросом: fa «Context: 1M» → «زمینه: 1M»
  (без «متر»).
- Уже сохранённые переводы проверены `token_guard`: семантический класс
  «число+единица» (`1M`/`128K`/`7B`) — **328 строк / 232 уникальных (source,lang)
  пар** искажены. Точечный ремонт `manage.py repair_token_distortions --provider
  azure` (только этот класс, защищённый повторный перевод, dedup): 244 пары,
  **17 запросов, 23 396 символов**, 340 обновлений полей, 0 failed. После ремонта
  искажений класса «число+единица» = **0**. Записи ревизий не создаются
  (`_aipedia_translation_write`), revisions = 4354. Резервная копия БД:
  `backups/aipedia-before-token-repair-*.sqlite3`.
- Оставшиеся 6 262 «any-token» расхождения — это транслитерация имён собственных
  в индийских/CJK письменностях (не семантическое искажение, а смена письма;
  slug/ID/заголовки — латиница). Полный ремонт стоил бы ~376 500 символов (за
  остатком F0), поэтому не выполняется; защита `token_guard` предотвращает такие
  случаи во всех будущих переводах.

Ревизии: старый процесс backfill (до добавления guard) создал 765 технических
translation-ревизий (`ModelVersion`, `updated`, снимок прозы получил ключи
машинных языков). Идентифицированы точно по контент-сигнатуре (ни одна
до-backfill ревизия не могла содержать эти ключи; id 4355–5119, contiguous),
доказано: `distinct_models=763`, ни одна модель не теряет историю, non-artificial
= 4354 (baseline). Перед удалением снята полная резервная копия БД
(`backups/aipedia-before-translation-revision-cleanup-*.sqlite3`). Удалены только
765 искусственных ревизий в транзакции с assert-проверками; переводы сохранены
в `ContentTranslation` (42260) и в JSON моделей. Далее guard
(`_aipedia_translation_write` в `translation_pipeline`/`signals`) исключает
машинные записи перевода из журнала ревизий.

Безопасность секрета Azure: ключ читается только из env
`AIPEDIA_AZURE_TRANSLATOR_KEY` (в коде/Git/тестах/логах/AI_CONTEXT отсутствует).
На Local settings.py авто-загружает несекретную/секретную конфигурацию из
неотслеживаемого `.env.local` рядом с `manage.py` (реальное значение env
побеждает; **пустое** значение env трактуется как отсутствующее, чтобы
`.env.local` мог его заполнить). Endpoint и region — несекретные defaults
(`…microsofttranslator.com`, `eastus2`). `.gitignore` исключает `.env`/`.env.*`
(кроме `.env.example`), `secret.key`, `data/local/`; `git check-ignore .env.local`
→ ignored; в отслеживаемых файлах значения ключа нет. `check_translator`
(default azure) делает один минимальный запрос и печатает только PASS/FAIL,
provider, region; ключ/части/длину не печатает.

Targeted visual QA после backfill (реальный браузер, 127.0.0.1:18815, отдельный
dev-сервер; чужой Local на 18810 не трогался) — критичные представительные локали
и RTL: карточка модели (Claude 3 Haiku) и панель инструмента (GitHub Copilot) в
uk/de/ja/ar/fa/zh-Hant — описание, ограничения, страна, модальности, статусы,
ярлыки, yes/no локализованы; бренды (Anthropic, GitHub, Microsoft, AI21 Labs,
DeepMind, Meta AI, OpenAI), model IDs, `API`, `Cloudflare`, `IP`, URL остаются
оригинальными; ar/fa `dir=rtl` с зеркальной раскладкой и LTR-брендом; privacy
(визуально ar RTL). Полное покрытие всех 22 локалей обеспечено систематическим
rendered-аудитом выше (0 fails), а не ручным браузером по каждой локали.

Хранилище переводов не привязано к конкретной URL-схеме. Переводы адресуются
исключительно по коду локали (`ContentTranslation`, JSON-поля моделей,
`TRANSLATIONS`, страны/категории, overlay статических страниц); текущее
согласование языка (`resolve_language()`) читает `?lang=` лишь как один из
сигналов и возвращает код. Поэтому **сами данные и pipeline перевода переживут
смену URL-схемы без миграции переводов** (доказано тестом
`UrlAgnosticContentTests`). Отдельный будущий этап Global Search & Discovery,
если переведёт локали в путь (`/uk/…`, `/de/…`, `/ar/…`), изменит именно слой
маршрутизации: routing, обратное построение URL (reverse), `canonical`,
`hreflang`, `sitemap`, переключатель языка и редиректы — это работа того этапа,
а не translation pipeline.

Изменено/добавлено (Local, не закоммичено): `aipedia/settings.py`,
`aipedia/test_settings.py`, `catalog/{i18n,middleware,context,seo,comparison,
views,signals,models,ui_translations,translation_providers,translation_pipeline,
countries,static_pages,token_guard}.py`, `catalog/templatetags/catalog_tags.py`,
`catalog/management/commands/{translate_catalog,check_translator,audit_localization,
audit_translation_quality,translate_static_pages,repair_token_distortions,
promote_research}.py`,
`catalog/migrations/0015_contenttranslation.py`, `contributions/views.py`,
`tools/pack_ai_context.py`, `templates/{base,catalog,privacy,panel,
includes/site_header,includes/country_flag}.html`,
`static/{site.css,table-layout.css,site.js}`, `.env.example`,
`deploy/aipedia.env.example`, `data/static_page_translations.json`, тесты
`test_i18n.py`, `test_translation_pipeline.py`, `test_translation_finalization.py`,
`test_token_guard.py`.
Данные Local: `data/local/aipedia.sqlite3` получила 42260 ContentTranslation и
переводы в JSON моделей/инструментов; класс «число+единица» отремонтирован
защищёнными переводами; резервные копии до чистки ревизий и до ремонта токенов в
`backups/`. Не завершено: ручная приёмка владельцем; commit/push/Production —
только по отдельной команде владельца. Production без изменений, серверная SQLite
не трогалась.

## Текущая работа: полный выпуск Local на Production (2026-09-22)

- Перед любыми изменениями серверная SQLite проверена: `integrity_check=ok`,
  `foreign_key_check=0`, 255 published legacy `ModelVersion`, 503 offers,
  280 accesses, 854 evaluations, 63 sources, 2163 research records.
- Создан отдельный online-backup без остановки и без копирования Local SQLite:
  `/srv/aipedia/backups/aipedia-before-global-catalog-20260922T062133Z.sqlite3`,
  SHA-256 `b40fe0d0baeb05c941a2afbf5d10e7b02b12d24009eb09f7608f54ac7503b47d`.
- Production baseline до миграции подтверждён как точная копия сохранённого
  локального snapshot `backups/chronology-production-after.sqlite3` по SHA-256.
- Подготовлена атомарная natural-key миграция `0014_global_catalog_20260922`.
  Она сначала сверяет точное исходное состояние Production, не удаляет записи,
  сохраняет существующую историю и импортирует переносимый payload без SQLite.
- Payload: `catalog/migrations/data/global_catalog_20260922.json`, SHA-256
  `5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2`;
  персональных путей, секретов и Local SQLite в нём нет.
- На изолированной копии точного Production baseline миграции `0011`–`0014`
  применились успешно. Итоговые таблицы семантически совпали с Local по всему
  переносимому payload; `integrity_check=ok`, внешних ключей с ошибками — 0.
- Local после регистрации миграции сохранил 763 модели, 138 инструментов,
  555 offers, 1205 accesses, 881 evaluations, 343 sources, 2900 research
  records, 4354 revisions, 3049 model publication revisions и 158 tool
  publication revisions.

Проверки кандидата: **82 Django tests PASS**; `manage.py check` PASS;
`makemigrations --check --dry-run` — изменений нет; `node --check` PASS;
`git diff --check` PASS. Точный архив commit `43e2d3f…`, SHA-256
`33be8e0054f1909bcb2ad891caae8558f61c58fc03932a80b3542af6199c3625`,
прошёл изолированную миграцию и semantic comparison с Local.

Production после deploy: `/healthz` = `status: ok`, `environment: production`,
release `43e2d3f…`; SQLite `integrity_check=ok`, `foreign_key_check=0`; payload
SHA совпал; 763 published моделей, 138 published инструментов, 901 legacy
ModelVersion, 555 offers, 1205 accesses, 881 evaluations, 343 sources, 2900
research records, 3590 research revisions, 4354 revisions, 3049 model и 158
tool publication revisions. Номера моделей непрерывны 001–304, инструментов
001–017; записи без точной даты остаются без выдуманного номера.

Server deploy backups:
`/srv/aipedia/backups/aipedia-before-code-20260922T065139Z.sqlite3` и
`/srv/aipedia/backups/aipedia-after-code-20260922T065139Z.sqlite3`.
Предыдущий код сохранён в
`/srv/aipedia/releases/before-code-20260922T065139Z`.

Public Browser PASS: AIpediya; 763/138; номера 001–018 видны; флаги IL/GB/US
и другие отображаются; переключение из `status=retired&q=jurassic` в Tools
очищает фильтры и показывает 138/138; RU/EN, dark/light и карточка
Jurassic-1 Jumbo проверены; ошибок console warn/error — 0. HTTP: models 200,
TTFB 0.234 s, total 0.288 s; tools 200, TTFB 0.369 s, total 0.414 s.

Изменено: release commit опубликован на GitHub и Production, серверная SQLite
мигрирована на месте с сохранением истории, отчёт и audit verifier обновлены.
Не завершено: очередь качества данных остаётся 711 записей / 1376 Required
полей и 108 записей / 110 Needs verification; это явные пробелы источников,
не дефект выпуска. Следующим выполнить: дальнейшую независимую проверку этой
очереди отдельными пакетами; новый Production выпуск — только по новой команде.

## Текущая работа: видимый бренд AIpediya и проверка дизайна (2026-09-22)

- Видимое имя в шапке, footer, SEO title, карточках, методологии,
  конфиденциальности и административных подписях изменено с `AIpedia` на
  `AIpediya`. Внутренние имена Python/Django, совместимые HTTP-заголовки,
  пути, база и исторические имена файлов намеренно не переименовывались.
- `static/brand.svg` заменён на аккуратный векторный ленточный знак по
  предоставленному логотипу; растр с тёмным фоном напрямую не использован,
  поэтому знак корректно работает и в светлой теме.
- Базовая тёмная палитра приведена к предоставленной теме «Полночь»
  (`#080F14`, `#0F1A21`, `#00E0C6`, `#22D9FF`, `#E6F7FF`), светлая — к теме
  «День» (`#F5F8FA`, `#FFFFFF`, `#00C2AC`, `#0B6E99`, `#0E1B22`). Новые
  переключатели тем не добавлялись: сохранено существующее поведение dark/light.
- При проверке на ширине встроенного браузера выявлено и исправлено сжатие
  колонки названия до одной иконки. До 1180 px таблица теперь сохраняет
  читаемую колонку 188 px и использует собственную горизонтальную прокрутку.
- Browser Local PASS: dark/light, RU/EN, модели и инструменты, переход на
  «Инструменты» при активном поисковом фильтре, номера с `001`, флаги и правая
  карточка `Jurassic-1 Jumbo`; document title — `Jurassic-1 Jumbo | AIpediya`.

Проверки: **79 Django tests PASS**; `manage.py check` PASS; `makemigrations
--check --dry-run` — изменений нет; `git diff --check` — без ошибок (только
предупреждения Git о нормализации окончаний строк). Local слушает только
`127.0.0.1:18810`.

Изменено: `static/brand.svg`, `static/site.css`, `static/table-layout.css`,
видимые шаблоны и тексты контекста/views/admin/apps, regression tests и этот
статус. Не завершено: ручная визуальная приёмка владельцем. Следующим выполнить:
владелец проверяет Local; commit/push/Production возможны только по отдельной
команде.

## Архив: визуальная проверка каталога после reconciliation (2026-09-22)

- Причина начала списка с 018 установлена: данные не были потеряны. Позиции
  001–017 сохранены в SQLite, но все они historical: 10 `retired` и 7
  `archived`; прежний неявный фильтр `status=active` скрывал их. Обычный вид
  теперь открывает `all` и показывает полную подтверждённую хронологию; явный
  фильтр `active` по-прежнему доступен и не перенумеровывает результаты.
- Счётчики вкладок приведены к фактически доступным published-записям:
  763 модели и 138 инструментов. В браузере первые 18 номеров проверены как
  непрерывная последовательность `001`–`018`.
- Переключатели «Модели» / «Инструменты» теперь ведут на чистый корень своего
  независимого каталога. Параметры, сортировка, выбранная карточка и маршрут
  другой таблицы не переносятся. Проверен переход из отфильтрованной карточки
  `/models/<slug>` на 138 инструментов и обратный переход после tool-фильтров.
- Исправлен неполный список значений status в двух фильтрах модели; `all`,
  `active`, `deprecated`, `retired`, `archived` отображаются согласованно.
- Локальный `flags.svg` дополнен `IL`, `JP`, `NL`, `SA`, `AU`, `CZ`, `SE`.
  Автопроверка: отсутствующих символов — 0 для всех 16 кодов стран моделей и
  всех 14 кодов, извлечённых из подтверждённого `Organization.country`
  инструментов. Составные значения (`USA/UK`, `India/USA`) показывают оба
  флага; `Open source` / `International` не получают выдуманный флаг.
- Высота строки 55 px сохранена. Внутри неё увеличены основной текст таблицы,
  названия, вторичные подписи, назначения, цена/доступ/дата, badges, флаги и
  знаки разработчика. Проверено в RU/EN и dark/light без наложений.
- Для сортировки по номеру SQLite теперь выбирает только нужный кусок
  150/50 строк, а не загружает и декорирует весь набор. Повторный Local-ответ
  обычного каталога моделей сократился примерно с 600–700 мс до 250–320 мс;
  проверенные сложные фильтры — примерно 110–200 мс. Набор и lazy loading не
  урезаны.
- `prepare_local_catalog.py` больше не отвергает уже существующую Local SQLite
  из-за устаревших фиксированных размеров исходного snapshot. Строгие старые
  числа проверяются только при первичном копировании snapshot; существующая
  база всё так же проходит integrity и проверку отсутствия users/sessions.

Проверки: **78 Django tests PASS**; `manage.py check` PASS; `makemigrations
--check --dry-run` — изменений нет; SQLite `integrity_check=ok`,
`foreign_key_check=0`; `git diff --check` — без ошибок. Browser Local PASS:
RU/EN, dark/light, полная хронология, active/retired/category/access/price
filters, tool platform/local/sort filters, обе вкладки, переход из правой
карточки и флаги. Local слушает только `127.0.0.1:18810`.

Изменено: `catalog/views.py`, `catalog/comparison.py`, `templates/catalog.html`,
`templates/tool_rows.html`, `static/site.css`, `static/flags.svg`,
`tools/local/prepare_local_catalog.py`, regression tests и этот статус. Не
завершено: ручная визуальная приёмка владельцем. Следующим выполнить: владелец
проверяет Local; commit/push/Production возможны только по отдельной команде.

## Архив: reconciliation Local + research master (2026-09-22)

- Новый источник:
  `C:/Users/dimon/Desktop/AIpedia_global_research_master_2026-09-21_applicability_fixed.xlsx`;
  SHA-256 и каждая исходная строка сохранены в provenance `ResearchRecord`.
- До импорта в Local было 234 модели и 21 инструмент. После reconciliation —
  763 модели и 138 инструментов: добавлены 529 моделей и 117 инструментов,
  уточнены 80 существующих моделей и 11 инструментов. `LM Studio` сопоставлен
  с существующей записью `LM Studio / Bionic`; созданных дубликатов — 0.
- Сохранены все исходные pk/slug/URL, даты существующих записей, 503 цены,
  280 доступов, 854 оценки, 89 источников и вся история ревизий; потерь и
  изменения прежних строк этих таблиц нет. Позиционные `public_number`
  пересчитаны только по подтверждённой хронологии после вставки более ранних
  дат; относительный порядок прежних моделей/инструментов сохранён, значения
  до reconciliation записаны в канонической книге и истории ревизий.
- Частичные даты не превращались в фиктивный день: они сохранены в evidence и
  XLSX, а `released` заполнен только для точной даты. Неизвестные значения
  остались пустыми. Рейтинг AIpedia не рассчитывался.
- Добавлены 52 подтверждённых ценовых предложения и 27 наблюдений benchmark;
  цена хранится с единицей/scope/источником/датой, оценка — с точной версией,
  evaluator/benchmark/score/snapshot/source. Всего Local: 555 offers,
  1205 accesses, 881 evaluations, 343 sources и 737 provenance-записей партии.
- Применимость исправлена для image/video/STT/TTS и historical/retired: modern
  LLM-поля не обязательны там, где они не применяются. Дополнительно очищены
  ошибочные требования контекста у 9 TTS/audio-записей источника.
- Канонический файл:
  `outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_catalog_master.xlsx`.
  В нём ровно две таблицы/вкладки: `Модели` (763 строки, 73 колонки) и
  `Инструменты` (138 строк, 53 колонки); provenance и verification находятся
  внутри этих таблиц, формульных ошибок не найдено, оба листа отрендерены и
  визуально проверены.
- Остаток очереди качества: Required — 711 записей / 1376 полей; Needs
  verification — 108 записей / 110 пунктов. Это явные пробелы, не нули и не
  догадки. Состав: модели 600/1265 Required и 103/104 Needs; инструменты
  111/111 Required и 5/6 Needs.
- Резервная копия до импорта:
  `backups/aipedia-before-global-master-reconcile-20260922T035236Z.sqlite3`,
  SHA-256 `7a0a0584e505ec4392eec4647752e280611b91862d6f1f1c65d0c00f974a1a8e`.
- Браузер Local PASS: RU/EN, вкладки моделей/инструментов, `status=all` (763),
  retired-поиск, сортировка, API-фильтр инструментов, правая карточка, а также
  historical McCulloch-Pitts, retired Jurassic-1 Jumbo, API GPT-6 Astra,
  open-weight Llama 3 70B, TTS Eleven v3, ChatGPT и Grok Voice API.
  Active-срез показывает 412 моделей и 137 инструментов; полный набор доступен
  в обычном виде и через явный статус `Все`.
- Автоматические проверки PASS: 75 Django tests; `manage.py check` без ошибок;
  `makemigrations --check --dry-run` — изменений нет; SQLite `integrity_check`
  — `ok`, `foreign_key_check` — 0; `git diff --check` — без ошибок.

Изменено: только Local SQLite, этот статус, свежий `AI_CONTEXT` и итоговый XLSX;
интерфейс, маршруты, модели Django и Production не менялись. Не завершено:
явно перечисленные Required/Needs verification требуют будущей проверки по
источникам; это не препятствует сохранению подтверждённой части. Следующим
выполнить: владелец проверяет канонический XLSX и задаёт приоритет очереди
Required/Needs verification; публикация возможна только отдельной командой на
конкретный commit/tag по `docs/RELEASE.md`.

## Доказательства для архива

- tools/pack_ai_context.py
- docs/EXECUTION_STATE.md
- outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_catalog_master.xlsx

## Архив: глобальный research master (2026-09-21)

- Сопоставлены `AIpedia_global_catalog_2026-09-21.xlsx`,
  `AIpedia_global_catalog_2026-09-21_pass2.xlsx` и
  `AIpedia_site_data_2026-09-21_pass3.xlsx`.
- Pass 3 выбран структурной основой: он содержит все названия из двух ранних
  книг, добавляет к pass 2 ещё 22 модели и 3 инструмента, а к первому проходу —
  94 модели и 10 инструментов; потерь по названиям не найдено.
- Создан
  `outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_global_research_master_2026-09-21.xlsx`:
  609 моделей/нейросистем, 128 инструментов, обзор, очередь проверки,
  аудит актуальных источников, происхождение данных и словарь полей.
- В очередь вынесена 621 запись с конкретным незакрытым вопросом. Неизвестные
  значения не заменялись нулями или догадками; хронологические номера сохранены.
- По официальным источникам точечно перепроверены GPT-6 Astra, Claude Fable 5.1,
  Grok 4.7, Qwen3.8-Flash, Gemini CLI, Antigravity CLI и Grok Voice API.
  Для GLM-5.3-Flash отдельно зафиксировано различие между первым публичным
  preview 2026-08-20 и официальным материалом Z.ai 2026-09-21.
- У Grok Voice API обнаружено расхождение официальных страниц: developer docs
  показывают `$0.08/min`, продуктовая страница — `$0.05/min`; в master оставлена
  цена developer docs и явное требование перепроверки.

Проверки: XLSX ZIP integrity PASS; 7 листов и 6 Excel tables открываются через
`openpyxl`; 609/128 строк сохранены; формулы протянуты до последних строк;
скан ошибок `#REF!/#VALUE!/#NAME?/#N/A/...` — 0; визуально проверены 9 рендеров
всех листов и обеих половин широких таблиц.

Изменено: создан только отдельный research workbook и обновлён этот статус;
код, Local SQLite, GitHub и Production не менялись. Не завершено: 621 пункт
очереди не прошёл независимую построчную web-проверку, данные не импортированы
в Local. Следующим выполнить: владелец подтверждает границы каталога и приоритет
очереди; затем отдельной задачей провести пакетную верификацию и подготовить
безопасный preview-импорт в Local без перенумерации и без перезаписи SQLite.

## Текущая работа: разделение моделей и инструментов (2026-09-22)

- В интерфейсе ровно две вкладки; смешанного режима «Все» нет.
- Используются разные query, view model, таблицы, фильтры, сортировки, URL и панели.
- Создана отдельная сущность `Tool`, связанная с исходной legacy-записью через
  `PROTECT`; все 255 исходных `ModelVersion` и связанные цены/доступ сохранены.
- Страны нормализованы через `Country` / `ModelOriginCountry`, платформы — через
  `Platform` / `ToolPlatform`. Неизвестное происхождение остаётся пустым.
- Независимая нумерация: модели №001 — Eleven Multilingual v2; инструменты
  №001 — GitHub Copilot. Фильтры и сортировки номера не меняют.
- Штатный Local launcher валидирует обе хронологии.

Фактические данные Local: 234 модели всего, 233 active, 1 archived; 21 active
инструмент; 198 пронумерованных моделей и 14 инструментов; страна указана у
230/234 моделей (229/233 active), 4 карточки `ai-sage` остаются пустыми.

Проверки: 75 тестов PASS; Django check PASS; migrations check PASS; `node --check`
PASS; SQLite quick_check `ok`, foreign_key_check 0; `git diff --check` PASS.

Браузер Local после явного разрешения владельца: desktop 1672×941 и mobile
390×844 PASS; RU/EN, dark/light, поиск, сортировка, обе панели и Escape PASS.
Панель инструмента не содержит модельных проверок, рейтинга или контекста.

Резервная копия до миграции:
`backups/aipedia-before-model-tool-split-20260921.sqlite3`.

## Архив предыдущей текущей работы (до разделения каталогов)

### Этап «дата релиза: день + месяц» (2026-09-21)

- Поручение: сокращённый месяц как раньше, плюс число дня; EN в американском порядке.
- Изменено: `catalog/templatetags/catalog_tags.py` (`month_year`), таблица и панель,
  `docs/visual-spec.md`, тест в `test_redesign.py`.
- Формат: RU `29 Июн 2021`, EN `Jun 29, 2021`.
- Проверено в Local; тест OK.
- Commit, push и публикация не выполнялись.

### Этап «дата релиза с числом» (2026-09-21) — заменён

- Кратко был `дд.мм.гггг`; заменён форматом выше по просьбе владельца.

### Этап «подгрузка при прокрутке» (2026-09-21)

- Поручение: убрать 12/25/50; сначала 150 строк, при долистывании вниз ещё по 50.
- Изменено: `catalog/views.py` (`CatalogPaginator` / `CatalogPage`, `INITIAL_PAGE_SIZE=150`,
  `CHUNK_SIZE=50`), `templates/catalog.html` (`#infinite-scroll`, счётчик `#shown-count`,
  без селектора строк), `static/site.js` (IntersectionObserver на `.table-scroll`, Retry),
  `static/site.css`, тесты пагинации/SEO.
- Проверено в Local: первая отрисовка 150; скролл → 200 → 250 → 254; счётчик обновляется;
  `partial=rows` отдаёт по 50 и `X-Aipedia-Next`.
- Тесты: `manage.py test catalog --settings=aipedia.test_settings` — после правки evidence.
- Commit, push и публикация на этом этапе не выполнялись.

### Предыдущий этап «знаки разработчиков» (2026-09-21)

- Знаки 34 разработчиков в таблице и правой панели; Local 34/34 published со знаком.
- Незакоммичено вместе с редизайном.

### Предыдущий этап «воспроизведение утверждённой оболочки»

- Спецификация и пиксельные измерения — `docs/visual-spec.md` §10.
- Орбита, бренд, палитра, геометрия таблицы/панели — в Local, незакоммичено.

### Архивная карта смешанной таблицы (элемент → источник → есть/нет → показ)

| Элемент | Источник | В Local сейчас | Показ |
| --- | --- | --- | --- |
| № | `public_number` | 212 из 255 | пусто, если нет |
| Название | `name`, `version`, знак разработчика | все | SVG/PNG из `static/marks/`; иначе инициал |
| Тип | `entry_type` | все | текущая классификация |
| Разработчик | `family.developer` | есть | как сохранено |
| Для чего | задачи / категории | есть | токены назначений |
| Стоимость | `Offer` | 503, не у всех карточек | вход и выход раздельно; без «Бесплатно» из макета |
| Доступ | `Access` / `Service` | есть | виды запуска |
| Независимые проверки | `Evaluation` independent | 752 | первичные/составные подписи сохранены |
| Составные индексы (ECI и т.п.) | `result_kind=composite` | 58 | вкладка «Проверки», не рейтинг AIpedia |
| Отчёты разработчика | `independent=False` | есть в БД | не в колонке независимых; во вкладке с подписью |
| Рейтинг AIpedia | нет утверждённого поля | 0 | пустая колонка и блок |
| Контекст | `ModelVersion.context` | 18 | иначе пусто |
| Релиз | `released` + источник | 212 | иначе пусто |
| Fact / аудит | `Fact`, `AuditReport` | 0 | блоки пустые |
| GitHub-кнопка | только реальный репозиторий | по ссылкам | не у каждой модели |
| Сохранить | кабинет | нет | неактивно, подсказка |

### Архивные проверки предыдущего этапа

| Что | Когда | Версия | Результат |
| --- | --- | --- | --- |
| Browser Local: scroll 150→200→250→254 | 2026-09-21T23:30Z | http://127.0.0.1:18810/?lang=ru | **PASS** |
| `partial=rows` page=2 → 50 строк + Next | 2026-09-21T23:30Z | Local | **PASS** |
| `manage.py test catalog --settings=aipedia.test_settings` | 2026-09-21T23:31Z | после infinite scroll | **PASS, 69 тестов** |
| Покрытие published → mark | 2026-09-21T23:25Z | Local SQLite | **34/34**, 0 без знака |
| Production | эта сессия | — | **не запускалось** |

### Архивные расхождения документов

- `docs/ACCEPTANCE.md` всё ещё пишет, что приёмка владельцем ожидается. Хронология 2026-09-20 опубликована; редизайн Local — к новой приёмке вида, не к публикации.
- `docs/VERIFICATION.md` старше текущего GitHub (`7e66da2`) и незакоммиченных файлов.
- Пустые рейтинг AIpedia, факты, аудиты и большинство контекстов — согласованное ограничение этого этапа, не дефект вёрстки.

### Архивные ограничения предыдущего этапа

- Рейтинг AIpedia не рассчитывается.
- «Сохранить» неактивна.
- 43 карточки без доказанной даты и номера остаются в конце хронологии.
- У части моделей нет офферов (пример: GPT-4.1) — вкладка стоимости пустая, не «Бесплатно».
- Знак — у разработчика, не у отдельной версии модели (так в эталоне и в `D-2026-09-21-developer-marks`).
- Адрес с хвостовым слэшем `/models/<slug>/` по-прежнему 404 (было до редизайна).
- Local слушает 127.0.0.1:18810; это не публичный сайт.
- Грязные незакоммиченные файлы: редизайн, знаки, infinite scroll, docs, artifacts, AI_CONTEXT, data/research.
- Без JS остаётся ссылка «Далее» на следующую порцию (полная перезагрузка страницы).

### Доказательства предыдущего этапа

Относительные пути; сборщик копирует их в zip, если файл есть и не секрет:

- docs/history/2026-09-20-chronology-release.md
- docs/RELEASE.md
- docs/DECISIONS.md
- docs/visual-spec.md
- tools/pack_ai_context.py
- artifacts/reference-plan-design.png
- artifacts/visual-rebuild/local-final-1672x941.png
- static/marks/

## Передача на Production (серверные шаги, выполняет владелец на хосте)

Развёртывание и перенос переводов запускаются **на самом сервере** `/srv/aipedia`
(в этом окружении нет SSH к хосту AIpedia; StratForge-ключи не используются).
Порядок строго по `docs/RELEASE.md`; Local SQLite на сервер не копируется;
туннель, секреты и StratForge не трогаются.

1. Локально собрать архив на релизном commit и сохранить SHA256:
   `.\.venv\Scripts\python.exe tools/build_code_release.py`
   (архив в `artifacts/code-release/aipedia-code-<commit12>.zip`, только
   tracked-файлы, без SQLite/секретов).
2. Локально проверить изолированно и dry-run:
   `.\.venv\Scripts\python.exe tools/verify_isolated_release.py`
   `.\.venv\Scripts\python.exe tools/deploy_code_release.py <archive> --sha256 <digest> --dry-run`
3. Скопировать на сервер **два** файла (без Local SQLite): архив кода и
   `artifacts/translation-data-release/translations-export.json` (42 260 записей,
   15.3 MB, только переводы, без секретов).
4. На сервере развернуть код:
   `python3 tools/deploy_code_release.py /path/aipedia-code-<commit12>.zip --sha256 <digest>`
   (останавливает только `aipedia`, online-backup серверной БД, перенос кода и
   статики, `migrate` существующей БД, старт `aipedia`, проверка `/healthz`).
5. На сервере перенести переводы в существующую серверную БД, идемпотентно и без
   провайдера, сначала dry-run:
   `python3 manage.py import_translations /path/translations-export.json --dry-run`
   затем боевой прогон без `--dry-run`. Импорт применяет перевод только там, где
   английский источник на сервере совпадает по sha256; несовпадения безопасно
   пропускаются (остаётся английский), повторный запуск ничего не меняет.
6. Публичная проверка `https://aipediya.com/`: `/healthz`, Модели и Инструменты,
   карточка модели и инструмента, EN/UK/AR(RTL), локализованные описания и
   страны, оригинальные бренды/ID/API/бенчмарки, правая панель (клик вне/Escape/
   крестик), меню языков над панелью, смена языка сохраняет карточку, desktop и
   mobile, защита числовых токенов (например «1M»).

Экспорт переводов проверен на Local: `import_translations --dry-run` против той
же базы даёт applied=0, unchanged=42 260 (полная идемпотентность).
