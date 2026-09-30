# Catalog Freshness UI final polish — Local review

Дата: 2026-09-30. Исполнитель: Codex. Timeline: `CATALOG-FRESHNESS-UI-POLISH-2026-09-30`, Release #019 / `v0.16.1`.

Состояние перед выпуском: `review` — Local ✓ / Owner ✓ / Production —. Владелец принял дизайн и в поручении от 30.09 явно разрешил Production #019 после PASS трёх финальных замечаний. Production baseline до процедуры остаётся Release #018, commit `74cf7269c991c121e549c67e863bdfcd0449387a`.

## Узкий scope

- Механика Catalog Freshness из #018 сохранена без переделки.
- В popover убран ellipsis только у имён восьми последних записей. Ширина — компактные 350 px; release date остаётся выровненной справа, а длинное имя может переноситься вместо обрезки.
- Текущие восемь строк помещаются без видимой полосы прокрутки. Для будущего переполнения сохранены wheel/touch scroll и тонкая 4 px полоса с прозрачным track, слабым thumb и усилением на hover.
- На ширине 375 px popover имеет фактическую ширину 343.5 px и границы примерно `12…355.5`, поэтому закрытое и открытое окно не создаёт горизонтальный page overflow.
- Блок часов использует язык интерфейса для `Intl.DateTimeFormat`: EN показывает `Sep 30, 2026`, не наследуя русский месяц из Windows; локальное время продолжает тикать каждую секунду.
- Изображения других записей каталога не менялись; каталог, master XLSX и Local SQLite не менялись.

## Проверка восьми marks

| Запись | Результат |
|---|---|
| Claude Sonnet 5.5 | Существующий официальный Anthropic SVG сохранён. |
| Eleven v4 | Существующий официальный ElevenLabs SVG сохранён. |
| Eleven v4 Turbo | Существующий официальный ElevenLabs SVG сохранён. |
| Holo4-27B | Официальный H Company brand mark; общий для трёх Holo-моделей. |
| Holo4-35B-A3B | Официальный H Company brand mark; общий для трёх Holo-моделей. |
| Holotron4-30B-A3B | Официальный H Company brand mark; общий для трёх Holo-моделей. |
| Cue | Официальный Cue product favicon с `https://cue.im/assets/cue/favicon.svg`; применяется точным Record ID override. |
| Manus | Официальный Manus compact brand icon с официальной brand page / `manus.im`. |

Официальные источники: H Company press pack `https://hcompany.ai/press` и `https://hcompany.ai/icon.png`; Cue `https://cue.im/` и официальный favicon; Manus brand assets `https://events.manus.im/fr/brand` и `https://manus.im/icon.png`.

Сохранённые SHA-256: `hcompany.png` — `99E65AB9AA604DFCC748BE2CC2C70C6553956C760C792F70B72FF18E7C2D9284`; `cue.svg` — `CDF8FA09D529075CD075CAD6D88E7417AC231EDCFCA15BC51FE74DE41013CEE3`; `manus.png` — `1A0BCCF04FCD912C4099E6A59D57263278264D079959722A03B39D427242CFB5`.

## Local QA

- `catalog.tests.test_marks` + `CatalogTests.test_catalog_freshness_indicator` + `catalog.tests.test_catalog_freshness` — 9/9 PASS.
- `manage.py check` — PASS.
- `node --check static/site.js` — PASS.
- `git diff --check` — PASS; четыре ранее отмеченных файла catalog master/requirements подтверждены как CRLF-only без содержательной разницы и безопасно нормализованы до clean state.
- RU desktop 1440×900 — PASS: восемь полных имён, даты выровнены, popover 350 px, все строки помещаются без scrollbar, overflow отсутствует, clock tick / hover / focus / Enter / Escape / row highlight проверены.
- RU ultrawide 2502×1314 (текущая ширина владельца) — PASS: popover 350 px, полные имена и даты, overflow отсутствует, hover и подсветка строк работают.
- RU mobile 375×812 — PASS: tap открывает, Escape закрывает; popover 343.5 px в границах около 12…355.5, внутренний и page-level overflow отсутствуют, имена и даты полные.
- EN desktop 1440×900 smoke — PASS: `Latest update`, EN clock date `Sep 30, 2026`, восемь полных имён, восемь дат `Sep 28, 2026`, popover 350 px, overflow отсутствует.
- Правило release-date не менялось: у записей от 28 сентября видимых `NEW` нет.
- Загрузка marks подтверждена в DOM: Anthropic/ElevenLabs/Cue SVG, три H Company PNG и Manus PNG; PNG имеют ненулевую `naturalWidth`. Console/page errors — 0.

Не запускались и не требовались: общий SEO, GSC, Cloudflare, performance, 22-language matrix, полный catalog audit и Production-проверки.

## Handoff

Targeted Local QA трёх финальных замечаний прошёл. Владелец заранее разрешил Production именно #019; следующий шаг — code-only процедура `docs/RELEASE.md`, затем targeted public smoke и закрытие этой же карточки только при полном PASS.
