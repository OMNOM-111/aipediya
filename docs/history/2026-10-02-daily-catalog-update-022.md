# Daily Catalog Update — 2 October 2026

Дата: 2026-10-02. Исполнитель: Claude Code. Timeline: `DAILY-CATALOG-UPDATE-2026-10-02`,
Release #022 / `v0.19.0`, tag `release-2026-10-02-daily-catalog-update` (зарезервирован, не создан).

Состояние: `in_progress` — Local —, Owner —, Production —.

## Baseline (2026-10-02, до изменений)

- Git: branch `main`, `HEAD == origin/main == 4a348c76ec3c76f594ee78876c57664e32c17358`, рабочее дерево чистое.
- Production `/healthz`: HTTP 200, `environment=production`, release
  `a03d501b9ed25699c97e336188bd28215d3f1bd2` (Release #021 / `v0.18.0`).
- Local SQLite `data/local/aipedia.sqlite3`: 336 Models / 156 Tools опубликовано,
  SHA-256 `91bfa04f67f96516215362444fcaa63c01a1b86729f6d4571f3c66b04bd557d2`. Local-сервер на момент
  baseline не отвечал на `127.0.0.1:18810`.
- Canonical master SHA-256 `078cad227021b6d8de76cbb673532d7b81e0097e930d861acb190e5f70e0c448`
  (совпадает с итогом #021). Models 811 (336 PUBLISHED / 475 NEEDS_REVIEW), Tools 163 (156 / 7).
- Расхождение: Meta `Production Checked (UTC)` = `2026-09-29T00:03:41Z`, `Production Sitemap` = 325/147,
  `On Production` у 11 Models и 9 Tools пусто/NO — наблюдение устарело относительно опубликованного #021
  (336/156). Обновляется штатным read-only `catalog_master import --production`.

## Scope

- 3 новые Models текущего окна: Clef, Clef-flash, Strands Decider 2B.
- 4 historical model catch-ups: Kev-0.8B, Kev-4B, Kev-9B v2, Kev-27B v2 (Kev 1.0 — family release).
- 1 historical Tool catch-up: AnythingLLM.
- 1 existing Tool updated: GitHub Copilot (`github-copilot-179ab1d0`).
- Без отдельной Tool-карточки: Cloudflare RL fine-tuning, Computer Use, Dynamic Workflows.
- Без глобальных archive/status changes из Copilot-only retirements 2026-10-02.

Production не разрешена: требуется отдельное одобрение владельцем именно Release #022 / `v0.19.0`.

## Наблюдение Production в master (2026-10-02T19:00:29Z)

Штатный read-only `catalog_master import --production` (только публичный sitemap):
Meta `Production Checked` → `2026-10-02T19:00:29Z`, `Production Release` → `a03d501…`,
`Production Sitemap` → 336/156; все 336 Models и 156 Tools со `Status=PUBLISHED` теперь
`On Local=YES / On Production=YES`, непубличные — `NO`. Добавлено 0 записей, `check: OK`.
Baseline `sync-local` plan до изменений: 0 writable changes, 0 unsupported.

## Проверка дублей

Поиск по Record ID, Name, Aliases, Developer, Family/Version, Canonical / Parent, Notes,
Official Source и Supported Models во всех статусах (PUBLISHED / NEEDS_REVIEW / ARCHIVE):
совпадений для Clef, Clef-flash, Strands/Decider, Kev, AnythingLLM/Mintplex нет. Единственная
родственная запись — `gliner-2-5-decide` (другая модель; использована как образец факта).
GitHub Copilot обновлён в существующей `github-copilot-179ab1d0`.

## Источники и сверка фактов задания

| Запись | Первичные источники | Результат сверки |
|---|---|---|
| Clef | [Cloudflare blog 2026-10-01](https://blog.cloudflare.com/clef-decision-models/), [changelog](https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/), [Workers AI](https://developers.cloudflare.com/workers-ai/models/clef/), [HF](https://huggingface.co/cloudflare/clef) | Base `Qwen/Qwen3.8-27B` подтверждён model card; 27B; Apache-2.0; 65,536 (Workers AI); $0.24/1M input; 64 вопроса; лимиты изображений совпали. **Уточнение:** model card указывает default `max_length` 16,384 для локального `encode_record` — записано в Facts, Context = 65,536 окна Workers AI. H200 — тестовое окружение, не минимум. |
| Clef-flash | [Workers AI](https://developers.cloudflare.com/workers-ai/models/clef-flash/), [HF](https://huggingface.co/cloudflare/clef-flash) | Base `Qwen/Qwen3.5-9B` подтверждён; 9B; $0.09/1M input; vision по собственной model card и Workers AI page (images/video). Changelog формулирует изображения как optional «for the full Clef» — расхождение формулировки, приоритет собственных страниц Clef-flash. |
| Strands Decider 2B | [Strands blog 2026-10-01](https://strandsagents.com/blog/introducing-strands-decider/), [GitHub](https://github.com/strands-labs/strands-decider), [HF](https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19) | Base `Qwen/Qwen3.5-2B-Base`, rank-16 LoRA + pointer head (~1M), LM head удалён, 1.9B, 4,096 reference (3,072 preregistered eval), CPU/CUDA/MPS, `/v1/systemone`, bind 127.0.0.1 без auth, inference provider нет, ~11 ч RTX 3090 / ~1 ч 10 мин 8×H100 (training), results self-reported. Developer `Strands Agents / AWS` (шаблон «X / Y»; в master есть только `Amazon` / `Amazon Web Services`). |
| Kev ×4 | [Kev 1.0](https://github.com/jaredpalmer/kev/releases/tag/kev-1.0), HF commit history | Даты задания совпали с коммитами закреплённых весов: Kev-0.8B `9a45d25e` и Kev-4B `139fdd94` — 2026-09-24; Kev-9B v2 `b5d8c18e` и Kev-27B v2 `28be62e9` — 2026-09-30. Kev 1.0 (2026-10-01): «nothing newly trained». **Расхождение для владельца:** модели с теми же именами Kev-0.8B/4B (и Kev-9B v1) с более ранними весами были на Hub с 2026-09-20, GitHub release `kev-family` впервые опубликован 2026-09-20. Использованы даты закреплённых checkpoints по заданию; ранние даты — в Facts `version_history` и Notes. Страна: GitHub-профиль Jared Palmer — New York, NY (вторичные источники с «Vercel» устарели). |
| AnythingLLM | [сайт](https://anythingllm.com/), [pricing](https://anythingllm.com/pricing), [repo](https://github.com/Mintplex-Labs/anything-llm), [v1.17.0](https://github.com/Mintplex-Labs/anything-llm/releases/tag/v1.17.0) | MIT; v1.17.0 опубликован 2026-10-01T22:17:40Z; Cloud $50 / $99 / Enterprise contact sales; Docker self-host и Desktop бесплатны, модели/API отдельно; Mintplex Labs — USA (GitHub org). Первичный анонс 2023-06-07 (Medium) вернул HTTP 403 — **Exact пуст, `≈2023-06-07` (day)**; initial commit 2023-06-04 не доказывает публичность. |
| GitHub Copilot | [Computer Use](https://github.blog/changelog/2026-10-01-github-copilot-can-now-interact-with-desktop-apps), [Dynamic Workflows](https://github.blog/changelog/2026-10-01-dynamic-workflows-in-copilot-cli-and-the-copilot-app), [retirements 10-02](https://github.blog/changelog/2026-10-02-selected-models-in-github-copilot-deprecated) | Подтверждены оба public preview. **Расхождение:** анонс 2026-09-16 называл замену Claude Opus 4.7 → Claude Opus 5, пост 2026-10-02 — **Claude Opus 5.5**; использован более свежий. |

## Owner diff (trial, до рабочего Local)

Canonical master SHA-256 после изменений: `04b23ff56680bd2885618e331839c3f65a776d285c5d3f073405a79fdf79c027`.
Script: `tools/daily_catalog_update_2026_10_02.py` (идемпотентен; повтор = 0 изменений).
Master: Models 811 → 818, Tools 163 → 164, Offers 684 → 690, Access 1325 → 1338,
Facts 1926 → 1958, Origins 862 → 869, Evaluations 5846 (без изменений), Tool Platforms 279
(строки листа создаёт `import` из Local после sync; на trial `import` добавил 8).

**Создано (8 записей):**

- 3 новые модели текущего окна: `clef-bdc7df20` Clef #341, `clef-flash-4eaa2224` Clef-flash #342, `strands-decider-2b-81831af4` Strands Decider 2B #343 — все 2026-10-01.
- 4 historical model catch-ups: `kev-0-8b-46011d0e` Kev-0.8B #323 (2026-09-24), `kev-4b-2ab542cc` Kev-4B #324 (2026-09-24), `kev-27b-v2-59a82a0e` Kev-27B v2 #338 (2026-09-30), `kev-9b-v2-7e1fcef1` Kev-9B v2 #339 (2026-09-30).
- 1 historical Tool catch-up: `anythingllm-90d04ca3` AnythingLLM #60 (≈2023-06-07).

**Обновлено (1 существующая запись):** `github-copilot-179ab1d0` — Platforms `web; cli; ide` → `+desktop; windows; macos`; Facts `release_update` Computer Use и Dynamic Workflows; `ecosystem_model_retirement` (только Copilot, 0 глобальных архиваций, 0 удалений из Supported Models); Notes / Last Verified (master-only).

**Хронологические номера (119 изменений, 111 у существующих записей):** Models — 14 сдвигов: #323–#335 → +2 (Sarvam Vision 2.1 … Gemini 4 Argon), pplx-embed-v2-context-9b-preview 336 → 340. Tools — 97 сдвигов: #60–#156 → +1 (вставка AnythingLLM). Record ID и URL не меняются; каждый сдвиг в master Changelog.

**Связанные объекты на trial:** offers +6 (Clef $0.24/1M input, Clef-flash $0.09/1M input, AnythingLLM $0 Docker self-host, $0 Desktop, $50 Cloud Basic, $99 Cloud Pro — условия явно отделяют стоимость моделей/API/оборудования); access +13; origins +7 (US); organizations +3 (`Jared Palmer`, `Strands Agents / AWS`, `Mintplex Labs Inc`, все USA); tool platforms +8; evaluation rows 0; у существующих строк изменён только `public_number`.

**Trial result:** plan 8 create / 111 number / 1 platforms; applied; `import` 0 записей кроме 8 Tool Platforms; повторный plan — 0 writable, 0 unsupported (SHA-256 повторного плана = baseline). SQLite integrity `ok`, FK 0. `check: OK`; `qa: PASS`, 343 Models / 157 Tools, 0 errors, 17 прежних warnings, quality queue 199 → 206 (+7 `developer_reported` для всех новых моделей — намеренно, независимых результатов нет).

**Намеренно не создано:** Tool-карточки Cloudflare RL fine-tuning / Workers AI / Computer Use / Dynamic Workflows; Evaluation rows из vendor/self-reported результатов; Max Output у decision-моделей; Offers/API для Kev и Strands; отдельные карточки Kev-9B v1 / Kev-27B v1; AnythingLLM Mobile в Platforms; `docker` как платформа (нет controlled term — оформлено Access/Offer/Facts). RL fine-tuning — `Facts.fine_tuning_service` у Clef (design partners, не self-serve).

**Остающиеся неизвестные:** точный первичный анонс AnythingLLM (≈ дата); Max Output (не применимо); параметры LoRA-адаптеров Kev/Strands; независимые оценки всех 7 моделей; цена Enterprise AnythingLLM (contact sales).

## Owner gate

Рабочий Local SQLite не изменён. Следующий шаг — только после приёмки владельцем этого diff:
backup рабочей Local, `sync-local --apply`, import/check/qa, тесты и браузерный QA.

## Owner acceptance и рабочий Local (2026-10-02)

Владелец принял diff Release #022 / `v0.19.0` и поручил применить его к рабочему Local,
подготовить точный Production candidate и остановиться перед Production.

- Backup рабочей Local перед sync: `backups/daily-catalog-20261002-022/aipedia-before-sync-022.sqlite3`
  (SHA-256 `5036034f…e65a`, integrity ok, 336/156; содержимое каталога идентично первому backup).
- Release manifests на копии исходного снимка (= публичное состояние Production #021):
  `data/release/daily-catalog-20261002/catalog_plan.json` SHA-256
  `bcdf3d752bf21ac45496b17f79ec952e8df5492957f53db8231cae4018532e47` — create 8, number 111,
  platforms 1, всего 128 writes; `apply-plan` dry-run `pending/applicable`, на второй копии
  применён («final state matches the plan»), повтор `already applied`.
  `release_state.json` (корень и `data/release/daily-catalog-20261002/`) SHA-256
  `60bac5092018ed28ff81143eba2f31ffc157b05ba2e08867823b81f6838fda16`, 343/157; dry-run apply на
  release-копии и рабочем Local — 0 изменений. `data/catalog_freshness.json` SHA-256
  `db4bcfeff71961292a2940ecb3143d65ff59a76cb1532269941fda028fe4e36e`: 7 added Models, 1 added Tool.
- Рабочий Local: `sync-local --apply` 128 changes; план идентичен trial (SHA-256 совпал);
  `import` — 0 записей кроме 8 Tool Platforms; повторный plan = baseline (0 writable, 0 unsupported);
  `apply-plan` на рабочем Local — `already applied`. Итог **343 Models / 157 Tools**, номера 1–343 и
  1–157 непрерывны, integrity `ok`, FK 0, Evaluations 5010 (без изменений). Каталожные строки
  рабочего Local совпадают с release-копией. `catalog_master check` OK; `catalog_master qa` PASS —
  0 errors, 17 прежних warnings, quality queue 206.
- Итоговый master SHA-256 (после `import`, On Local=YES у 8 новых, On Production=NO):
  `adfa21e69d41fe4c7f8d58e3b4d260774fd392dba3f7624f93c3983a0665332f`.
- Переводы: по прецеденту #020/#021 daily-выпуск переносит EN/RU; остальные 20 локалей — штатный fallback.

### Catalog Freshness

Snapshot выпуска содержит 8 записей `NEW` (7 Models + AnythingLLM) с фактическими датами релиза.
Бейджи строк каталога скрыты для всех восьми: правило фактической даты (только сегодняшняя
дата) не даёт ложного NEW ни Kev, ни AnythingLLM, ни Clef/Strands от 01.10. Механика не менялась.
Классифицированное расхождение: обновление GitHub Copilot передаётся операцией `platforms`, а
существующий `snapshot_from_plan` считает `updated` только операции `update` — поэтому в
popover нет `UPD Copilot`. Механику по поручению не переписывал.

### Исправление вёрстки, найденное в QA

Мобильный браузерный QA обнаружил, что открытый popover свежести при ширине 375–480 px выходит
за правый край (на Local и **так же на публичном Production #021**: кнопка на x≈238, popover до
581 px, `scrollWidth` 581). Это существующий дефект #021, не связанный с данными #022 (прежний QA
его не поймал). Исправлено минимально в `static/site.css` (только `@media (max-width: 480px)`):
popover привязан к правому краю строки toolbar, а не к кнопке. Проверено 7 маршрутов
(RU/EN/DE/AR-RTL/JA, Models/Tools) × 10 ширин 320–1440: 0 переполнений; десктоп не затронут.

### Local QA

- `manage.py test catalog --settings=aipedia.test_settings`: 368 tests OK (1 штатный Windows skip);
  `manage.py check` (local и test settings) — 0 issues; `makemigrations --check` — No changes;
  `node --check static/site.js` и `git diff --check` — PASS.
- Браузер (headless Edge, `tools/daily_catalog_browser_qa_2026_10_02.py`): PASS, 44 проверки —
  RU/EN desktop 1440, RU/EN mobile 375, dark/light; Models 343 / Tools 157; сортировка
  newest (343 Strands, 342 Clef-flash, 341 Clef, 340 pplx) и oldest (Jurassic-1 Jumbo); поиск по
  имени, alias `@cf/cloudflare/clef` и `jaredpalmer/kev-9b`; прямые URL всех 7 моделей, AnythingLLM,
  GitHub Copilot, Cloudflare OS (#147) и сдвинутых Sarvam Vision 2.1 (#325), Gemini 4 Argon (#337),
  pplx (#340); цены $0.24 / $0.09 / $0 / $50 / $99 и условия «не бесплатный inference»; страна США и
  флаги; Checks — «Публикуемых независимых результатов для точной версии нет»; Copilot Windows/macOS;
  popover 8 NEW; 0 JS/page errors, 0 HTTP ≥400, 0 visible overflow. Отчёт и 12 кадров:
  `artifacts/daily-catalog-20261002-022/browser-qa.json`, `…/browser/`.
- Locale-switch gate (`docs/RELEASE.md`, обязателен для code release из-за правки CSS):
  первый прогон показал FAIL во всех случаях на одном шаге «close outside click» — скрипт
  кликал по `.catalog-counts`, который стал `sr-only` в owner-fix #021 (последний полный
  88/88 был в #015). Скрипт исправлен: на desktop клик по нейтральной точке каталога вне
  панели; на 375 px шаг помечен `N/A`, потому что панель — fixed full-screen лист под шапкой,
  а клики по шапке намеренно не закрывают её (закрытие X и Escape проверяется в том же случае).
  Результат полного прогона — ниже, в разделе Release candidate.
