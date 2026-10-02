# Daily Catalog Update — 2 October 2026

Дата: 2026-10-02. Исполнитель: Claude Code. Timeline: `DAILY-CATALOG-UPDATE-2026-10-02`,
Release #022 / `v0.19.0`, tag `release-2026-10-02-daily-catalog-update` (зарезервирован, не создан).

Состояние: `done` — Local ✓, Owner ✓, Production ✓ (343 Models / 158 Tools).

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

## Release candidate (ожидает решения владельца)

- Release #022 / `v0.19.0`, Timeline `DAILY-CATALOG-UPDATE-2026-10-02`, reserved tag
  `release-2026-10-02-daily-catalog-update` (создаётся только на опубликованном commit после
  Production PASS, как в #021).
- Candidate commit (код + данные + манифесты): `7caa3e7a0730b297eb0335ccbc1badd59cb66213`.
- Locale-switch gate: **88/88 PASS** (22 локали × Models/Tools × 1440/375), 0 console / network /
  HTTP errors; на 375 px шаг outside-click `N/A` (44 случая). Отчёт —
  `artifacts/locale-switch-browser-qa.json` (сведён из 4 партиций `artifacts/daily-catalog-20261002-022/locale-part*.json`).
- Build gate: `release_history.validate` для #022 даёт только «Candidate missing owner_approved»;
  с симулированным approval — 0 ошибок. Состав `git archive HEAD` — 411 файлов без SQLite,
  `.env`, ключей, backups, artifacts и `data/local/`.
- Серверная фаза после разрешения: `tools/build_code_release.py --release-id
  DAILY-CATALOG-UPDATE-2026-10-02` на commit с записанным approval, затем по `docs/RELEASE.md`
  server preflight → backup → release-preflight/trial на снимке Production → dry-run →
  `deploy_code_release.py <archive> --sha256 <digest> --catalog-plan
  data/release/daily-catalog-20261002/catalog_plan.json --publication-state data/release_state.json`
  → `/healthz`, service, integrity/FK, 343/157, `verify-release`, `catalog_master qa --production`,
  GSD/Production QA, public browser QA. Local SQLite на сервер не копируется.

Production, серверная SQLite, Supervisor, tunnel и публичный HTML не изменялись.

## Owner-fix pass (2026-10-02, после возврата владельцем)

Владелец вернул #022 с замечаниями P0/P1 и заранее разрешил Production именно
Release #022 / `v0.19.0` только после всех исправлений и полного PASS. Новый
Release не создавался; карточка #022 возвращена из `review` в `in_progress`.
Candidate `7caa3e7` из предыдущего раздела **заменён** — после него изменились
код, данные и документы.

### P0 — инцидент «Максимум на выходе» (forensic)

Обнаружено новое обстоятельство: публичная summary card «Максимум на выходе» /
`Max output` в Overview каждой Model, у большинства пустая (пример владельца —
Gemini 3.8 Live).

| Вопрос | Факт / evidence |
|---|---|
| Шаблон | `templates/panel.html`, `.stat-grid` в `#tab-overview`, 4-я `article.stat-card`, `{{ ui.max_output }}` |
| Данные | `ModelVersion.max_output` (`catalog/models.py:48`, миграция `0020_modelversion_max_output`), master колонка `Max Output`, sync `catalog/master_sync.py`, dataset `max_output_tokens` (`catalog/datasets.py`) |
| CSS / JS / i18n / тесты | `.stat-grid` `repeat(3)`→`repeat(4)` (`static/site.css`); JS нет; `TEXT["max_output"]` и `TEXT["input_context"]` только RU/EN (`catalog/context.py`) → на 20 локалях английские «Max output» / «Input context»; тест `test_model_panel_distinguishes_input_context_and_max_output` |
| Первый commit | `036de2020bee8ce5859932bf9f9c1c96a9c46719`, 2026-10-01 11:26:16 -0700, «Fix Release 021 owner review defects» (`git log -S max_output`) |
| Автор / исполнитель | git-автор `Dimon_pro`; исполнитель — Codex (Timeline #021 `executor`, статус «01.10 — Release #021 … owner-fix») |
| Release / Timeline | Release #021 / `v0.18.0`, `DAILY-CATALOG-UPDATE-2026-10-01`; опубликован в Production в `a03d501` (`036de20` — предок) |
| Исходное основание | Записанная исполнителем формулировка замечания владельца: «у Gemini 4 Argon отсутствует официальное значение Max Output `1,000,000` tokens в canonical master и Local» (`docs/EXECUTION_STATE.md`, checkpoint #021); Timeline `review_findings` #021 №3; решение `D-2026-10-01-separate-input-context-and-max-output` (о раздельных полях данных). Исходный текст сообщения владельца в репозитории не сохранён. |
| Явное требование владельца | Значение Max Output для Argon — да (по записи исполнителя). Отдельная публичная summary card — **не найдено**. Показ для всех Model records — **не найдено**. |
| Показ при Local acceptance | Владелец видел кадр `artifacts/daily-catalog-20261001-021/owner-fixes/browser/01-models-argon-logo-max-output.png` (карточка Argon с `1M`), перед разрешением #021. Что карточка появится и будет пустой у всех остальных моделей, отдельно не показывалось и не согласовывалось. |
| Production | Да, опубликована побочно в составе #021. |
| Охват (343 Models) | Значение: 1 (Gemini 4 Argon, 1 000 000); пусто, но понятие применимо (вывод — текст): 207; неприменимо (изображения, видео, аудио, эмбеддинги, решения): 135 |
| Поле до UI | Поле и UI добавлены одним commit; ранее поля не было. |

**Вывод:** неутверждённое UI-дополнение. **Решение по поручению владельца:**
карточка удалена из публичного UI на всех 22 локалях (`templates/panel.html`),
сетка возвращена к 3 колонкам, третий заголовок — к прежнему локализованному
`context_window` («Контекстное окно» / «Context window» / 20 переводов), ключи
`max_output` / `input_context` удалены. Сохранено: поле БД, колонка master,
поле открытого dataset и значение Argon. Новый показ Max Output — только
отдельным решением владельца (`D-2026-10-02-no-unrequested-public-ui`).
Исторические отчёты #021 не переписывались. Регрессионный тест:
`CatalogTests.test_model_panel_has_no_unapproved_max_output_card` (EN/RU/DE/AR,
значение задано, но не выводится; ровно 3 карточки).

### Иконки

- Clef, Clef-flash, Cloudflare OS, Cloudflare Web Search API — developer mark
  Cloudflare: CC0-путь Simple Icons `cloudflare` в фирменном `#F38020`
  (`static/marks/cloudflare.svg`).
- Strands Decider 2B — официальный `https://strandsagents.com/favicon.svg`
  (`static/marks/strands.svg`, только добавлен `aria-hidden`).
- AnythingLLM — product override официальным
  `Mintplex-Labs/anything-llm/frontend/public/favicon.png` (тёмная плитка с
  белым глифом, читается в обеих темах; прозрачный `anythingllm.com/icon.png`
  отклонён: тёмный глиф пропадает на тёмной теме).
- Kev — собственного логотипа нет: в `jaredpalmer/kev` только шаблонные
  `next.svg`/`vercel.svg` playground, на Hugging Face — личная фотография
  автора. Это не brand mark; политика `catalog/marks.py` допускает только
  официальные марки, поэтому оставлен fallback `JP`.

### Catalog Freshness

- Popover «Последнее обновление»: `ADD` / «Добавлено в каталог» и `UPD` /
  «Обновлено в каталоге». UPD теперь учитывает изменения связанных строк
  (platforms, offers, access, origins, evaluations, reassign, org_country);
  перенумерация, метаданные общих объектов и master-only Facts не дают UPD.
  Итог #022: ADD — Clef, Clef-flash, Strands Decider 2B, Kev ×4, AnythingLLM,
  Cloudflare Web Search API; UPD — GitHub Copilot.
- Новый блок «Новые релизы за последние 24 часа»: по подтверждённой дате
  релиза (UTC, сегодня или вчера), ≈ даты не участвуют; честная подпись, что
  время релиза каталог не хранит. Сейчас: Clef, Clef-flash, Strands Decider 2B
  (2026-10-01), Cloudflare Web Search API (2026-10-02).
- `NEW` в строке решается один раз на сервере (`is_recent_release`), JS-guard и
  ежесекундная перепроверка удалены. Причина flicker: сервер рендерил бейдж для
  всех записей snapshot, а JS скрывал его по дате; строки, пришедшие при
  навигации и подгрузке, оставались с NEW до следующего тика `setInterval(1000)`.
- Тесты: `test_related_row_changes_update_the_existing_card_but_renumbering_does_not`,
  `test_recent_release_predicate_uses_confirmed_dates_only`,
  `test_row_new_badge_is_server_side_and_follows_the_release_date`.
- Подписи popover, как и с #018, есть для RU/EN, остальные 20 локалей получают
  английский fallback штатного `t()`; это существующее ограничение, не новое.

### Fresh research (до 2026-10-02 ~21:00 UTC)

- **Cloudflare Web Search API** — новый PUBLIC Tool `cloudflare-web-search-api-0bb0f08e`,
  #158, 2026-10-02, beta. Источники:
  [changelog](https://developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/),
  [docs](https://developers.cloudflare.com/web-search/),
  [providers](https://developers.cloudflare.com/web-search/providers/). Самостоятельный
  продукт (свой тег changelog, docs, REST `…/ai/websearch/`, binding
  `env.AI.websearch`), работает через AI Gateway, BYOK; провайдеры Ceramic.ai
  (по умолчанию, $0.25 / 1 000 запросов), Exa ($7.00), Linkup ($5.00) — прайс
  провайдера без наценки Cloudflare. **Расхождение:** changelog — ZDR у всех
  трёх; страница Providers — ZDR No у Exa (записаны оба). Дубля нет;
  Cloudflare AI Search (RAG) — другая сущность.
- **xAI** `grok-voice-transcribe-1.0` EOL 2026-10-02, запросы маршрутизируются
  на `grok-voice-transcribe-2.0` по той же цене
  ([release notes](https://docs.x.ai/developers/release-notes),
  [STT docs](https://docs.x.ai/developers/model-capabilities/audio/speech-to-text)).
  Отдельной Model-записи 1.0/2.0 нет; параметр `model` относится и к REST, и к
  WebSocket, поэтому в существующие Tools `grok-speech-to-text-cfab200f` и
  `grok-speech-to-text-streaming-1109f624` добавлен `Facts.release_update`.
  Продукты активны, архивации нет.
- **GLM-5.3-Flash** — Z.ai release notes по-прежнему датируют модель
  2026-08-26; дата не менялась.

### Master → trial → Local (owner-fix)

- Backup: `backups/daily-catalog-20261002-022/owner-fix/master-before-owner-fix.xlsx`
  (`adfa21e6…332f`), `aipedia-before-owner-fix.sqlite3` (`5665241…e55c`).
- Master: +1 Tool, +1 Access, +3 Offers, +3 Facts; `refresh` — 1 новый номер
  (Tool #158), сдвигов нет; `check` OK.
- Release-plan заново от исходного снимка (= Production #021):
  `data/release/daily-catalog-20261002/catalog_plan.json` SHA-256
  `436b434b1d5fad042ddf85c0d53e816197f64ce2f7a5b993d88ec1620cbd597f` — create 9,
  number 111, platforms 1; на копии 129 writes, «final state matches the plan»,
  повтор `already applied`; повторный sync plan 0 writable / 0 unsupported;
  trial `qa` PASS 343/158, 0 errors, queue 206; integrity ok, FK 0.
- Рабочий Local: sync 1 create, import, повтор 0; `apply-plan` — `already applied`;
  343 Models / 158 Tools, номера непрерывны; integrity ok, FK 0; `check` OK; `qa` PASS.
- `release_state.json` SHA-256 `768777935f381e752fa8d4dc66a67167af635a281ef42fe438b0bfc5914409ff`
  (343/158); `catalog_freshness.json` `356a2430…676f` (9 ADD + 1 UPD).
- Local-сервер: launcher переиспользовал чужой экземпляр AIpedia на 18811
  (321/143, другой worktree, `C:\Python312\python.exe tools\serve.py`), который
  не останавливался; QA выполнен на сервере этого репозитория (`.venv`
  `tools/serve.py --port 18813`, та же база `data/local/aipedia.sqlite3`).

### Local QA (финал owner-fix)

- Django catalog suite: 372 tests OK (1 штатный Windows skip); `manage.py check`,
  `makemigrations --check`, `node --check static/site.js`, `git diff --check` — PASS.
- Browser QA #022 (`tools/daily_catalog_browser_qa_2026_10_02.py --base http://127.0.0.1:18813`):
  PASS, 59 проверок + 44 шага NEW-flicker (Models ↔ Tools ×3, back/forward,
  поиск, infinite load; 1440 и 375; MutationObserver до скриптов страницы — ни
  одного NEW на несвежей записи и ни одного скрытия бейджа). Отсутствие
  «Максимум на выходе» и ровно 3 stat cards на RU/EN/DE/AR, в том числе Gemini 3.8 Live
  и Gemini 4 Argon; марки; цены; страны; Checks; popover 320–1440 RU/EN/AR без
  overflow; tablet 768, ultrawide 2560; 0 JS/HTTP ошибок. Отчёт —
  `artifacts/daily-catalog-20261002-022/owner-fix/browser-qa.json`.
- Locale-switch gate 88/88 PASS (4 партиции), 0 console/network/HTTP ошибок.

## Production release result (authoritative)

Владелец заранее разрешил Production именно Release #022 / `v0.19.0` после всех
исправлений и полного PASS; все условия выполнены.

- Candidate `8a4fe86a75ebcb5d2548aa57fdd8f6517058407d`, ревизия записана в
  `f46cc435c10effcf9b4815e689f22f07378093ca`; archive `aipedia-code-f46cc435c10e.zip`, SHA-256 `ed9e725f1852692165cb4c9b3507cb5670fc7d49757a0fb84b099a73d8b4cb14`, 415 файлов, без SQLite/секретов/backups/artifacts
  (master XLSX — штатный tracked-файл, как в #021).
- Server: preflight PASS (`/srv/aipedia`, сервис `aipedia`); upload в `/tmp/aipedia-*`
  с проверкой SHA-256; release-preflight PASS — изолированный trial на снимке
  Production: plan pending → 129 writes, final state matches the plan, 343/158,
  integrity ok, FK 0, `production_database_untouched`; deploy dry-run PASS;
  deploy PASS (`copied_sqlite: false`, backup
  `/srv/aipedia/backups/aipedia-before-code-20261002T220728Z.sqlite3`).
- После выпуска: `/healthz` 200, `environment=production`, release `f46cc435c10effcf9b4815e689f22f07378093ca`;
  Supervisor `aipedia` RUNNING; `catalog` — 343 Models / 158 Tools, номера
  непрерывны, integrity ok, FK 0; `verify-release` PASS, problems [], только
  ожидаемые catalog-таблицы; `catalog_master qa --production` PASS (0 errors,
  queue 206); GSD public 34/34; Production QA 1659/1659 (698 запросов,
  `artifacts/daily-catalog-20261002-022/owner-fix/production-qa.json`); публичный
  browser QA 59 проверок + 44 шага flicker PASS, 0 JS/network ошибок
  (`…/owner-fix/production-browser/browser-qa.json`).
- `tools/finalize_release_history.py` закрыл ту же карточку #022 (Production ✓,
  `current_production`). StratForge, tunnel, DNS и секреты не затрагивались.

### Остатки вне выпуска (реальные)

- Подписи popover свежести (и прочие строки `catalog/context.py` `TEXT`) заданы для
  RU/EN; 20 локалей получают английский fallback — так с #018. Следующий шаг —
  отдельная задача перевода по решению владельца.
- Max Output сохранён только как данные (1 значение — Gemini 4 Argon). Публичный
  показ — только отдельным решением владельца.
