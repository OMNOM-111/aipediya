# Daily Catalog Update — 1 October 2026

Дата: 2026-10-01. Исполнитель: Codex. Timeline: `DAILY-CATALOG-UPDATE-2026-10-01`, Release #021 / `v0.18.0`.

Состояние: `review` — Local PASS, проверка владельцем ожидается, Production не разрешена и остаётся на Release #020 / `v0.17.0`.

## Решения по отчёту

Опубликованы в Local после проверки официальных источников:

- Model `gemini-4-argon-bcdaec0e` — Gemini 4 Argon, точная дата 2026-09-30, ограниченный доступ через Fairwind; будущая цена и общий API/GA не заявлены. Источник: [Google](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/).
- Model `pplx-embed-v2-context-9b-preview-88e13515` — preview contextual embedding, 2048 dimensions, Matryoshka 1024/2048, native INT8, MIT, скачивание с Hugging Face; параметры модели не выдумывались, hosted API не заявлен. Источники: [Perplexity](https://perplexity.ai/pl/hub/blog/contextual-embedding-beyond-the-gold-passage), [Hugging Face](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview).
- Tool `cloudflare-os-038daad4` — Cloudflare OS, дата первого публичного open-source существования 2026-08-05; сообщение 1 октября о managed deployments waitlist записано как обновление доступа, а не новая дата продукта. Источники: [первый релиз](https://blog.cloudflare.com/cloudflare-os/), [managed waitlist](https://blog.cloudflare.com/managed-cloudflare-os/).

Подтверждённые изменения существующих записей:

- GLM-5.3-Flash: мультимодальность, 320B total / 18B active, 1M context, MIT и веса; точная дата релиза сохранена 2026-08-26. Страница AutoClaw датирована 2 октября, поэтому она не использована как дата релиза. Источник: [Z.ai](https://autoclaw.z.ai/blog/model/glm-5.3-flash/).
- Gemini: Skills/Gems записаны как будущий rollout/deprecation внутри существующего Tool; карточка не архивирована. Источники: [Google](https://blog.google/products-and-platforms/products/gemini/automate-tasks-with-skills/), [Workspace Updates](https://workspaceupdates.googleblog.com/2026/09/skills-gemini-app-workspace.html).
- GitHub Copilot: HydraFusion сохранён как research-preview feature, а не отдельная Model. Источник: [GitHub](https://github.blog/changelog/2026-09-30-hydrafusion-in-vs-code-and-the-github-copilot-app/).
- Codex: версия обновлена до `0.159.3`. Источник: [официальный GitHub release](https://github.com/openai/codex/releases/tag/rust-v0.159.3).
- Perplexity: Computer Automations сохранены как функция существующего Tool, не отдельная карточка. Источник: [Perplexity](https://www.perplexity.ai/en-GB/hub/blog/computer-adds-automations-for-ongoing-work).
- SourceCraft: с 2026-10-01 активны четыре USD-тарифа — `9.754098`, `20.409836`, `45.000000`, `94.180328` в месяц. Источник: [SourceCraft](https://sourcecraft.dev/portal/docs/en/sourcecraft/pricing).

Оставлены только в master как `NEEDS_REVIEW`, без Local-публикации:

- Ling-3.1-Flash — нет достаточного официального источника для точной идентичности и даты;
- Cloudflare AI Search — GA подтверждён, но граница самостоятельной сущности относительно AutoRAG не разрешена;
- Cloudflare Monetization Gateway — closed beta подтверждена, но самостоятельная Tool-классификация не доказана;
- Robinhood Agents — вне временного окна отчёта и не разрешена связь с Agentic Trading/access.

Источники для двух Cloudflare-кандидатов: [AI Search GA](https://developers.cloudflare.com/changelog/post/2026-10-01-ai-search-generally-available/), [Monetization Gateway closed beta](https://developers.cloudflare.com/changelog/post/2026-09-30-closed-beta/).

## Master, Local и номера

- До: Models 808 (334 PUBLISHED / 474 NEEDS_REVIEW), Tools 159 (155 / 4).
- После: Models 811 (336 / 475), Tools 163 (156 / 7), Offers 684, Evaluations 5846, Access 1325, Facts 1926, Origins 862, Tool Platforms 279.
- Итог master SHA-256: `9A88216E1AC4A31B9E56EB8251848FD13453F66301C8DE6D61632FCCEAAFADB2`.
- Backup master: `backups/daily-catalog-20261001-021/master-before.xlsx`, SHA-256 `BDAAA1200C640DA07B42F7C5443C0CF91E9AB0F853E4C6E47862AA5749DAF33F`.
- Backup Local SQLite: `backups/daily-catalog-20261001-021/aipedia-before-release-021.sqlite3`, SHA-256 `4E9D5D7D05A0C54BAC406277582D961B071FBC012588AB6B3B820092BC8C277D`.

Cloudflare OS — поздно найденный исторический Tool. По подтверждённому правилу `D-2026-09-26-catalog-master` он вставлен хронологически под #146. Десять последующих Tool-номеров сдвинулись на +1:

- DeepSeek Harness 146→147; Qwen Intelligence 147→148; Muse 148→149;
- OpenAI Agents API 149→150; MiniMax Speech Recognition 150→151;
- Alice AI Pro for Business 151→152; Cue 152→153; Manus 153→154;
- Oracle Fusion Claw 154→155; Dots 155→156.

Record ID, slug и публичные URL всех записей неизменны; каждое изменение номера записано в master Changelog.

## Release manifests и Local QA

- `catalog_plan.json`: create 3, update 3, offer 4, access_new 1, number 10; dry-run на исходном backup — `pending/applicable`, рабочий Local — `already applied`. SHA-256 `CCA0805000DD488368C745787F1B9C7E715DC755781036D436E0AB46F106C90C`.
- `release_state.json`: 336 Models / 156 Tools, SHA-256 `9A8909C5B1D20A4C7DD6B78CC208C6A5D720368CBD1931177D70A96EAB6FFDBB`.
- `catalog_freshness.json`: 2 added Models, 1 added Tool, 1 updated Model, 2 updated Tools; SHA-256 `87AA900015E0EF91C7E01FDE25628FEBA7CC3F9ACE7D2F401D989FC6F061DFB4`.
- Изолированный trial и рабочий Local получили одинаковый план: 22 записи, повторное применение не содержит writable changes; SQLite integrity `ok`, foreign keys 0.
- `catalog_master check`: OK; `catalog_master qa`: PASS, quality queue 199; финал Local — 336 Models / 156 Tools.
- Полный `manage.py test catalog --settings=aipedia.test_settings`: 365 PASS, 1 штатный Windows skip; `manage.py check`: PASS; release-history validator: PASS.
- Browser QA: 10/10 сценариев RU/EN, desktop/mobile, dark/light; проверены новые карточки, GLM, Codex, Perplexity и четыре цены SourceCraft; JavaScript/page errors 0, видимого horizontal overflow нет.
- На мобильном viewport скрытый `catalog-freshness-popover` даёт одинаковый `document_overflow=203` и у новой Cloudflare OS, и у существующего Codex. Это существующее unrelated поведение невидимого элемента, не регрессия данных Release #021; CSS не менялся в рамках data-only поручения.

## Handoff

Local candidate commit: `29b52923da5ebe8c2509d8890a4a7cf87f537c11`. Release tag зарезервирован в Timeline, но не создан до отдельного разрешения на Production.

Local preview: `http://127.0.0.1:18810/ru/`. Владелец проверяет новые и обновлённые карточки и десять ожидаемых хронологических сдвигов Tool-номеров. Production, серверная SQLite, Supervisor, tunnel и публичный HTML не изменялись. Следующий шаг возможен только после отдельного разрешения владельца на Release #021 по `docs/RELEASE.md`.
