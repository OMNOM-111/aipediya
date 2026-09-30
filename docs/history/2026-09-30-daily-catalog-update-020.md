# Daily Catalog Update — 30 September 2026

Дата: 2026-09-30. Исполнитель: Codex. Timeline: `DAILY-CATALOG-UPDATE-2026-09-30`, Release #020 / `v0.17.0`.

Состояние: `done` — Local ✓ / Owner ✓ / Production ✓. Карточка создана до refresh, research и любых изменений canonical master; тот же проверенный пакет опубликован и подтверждён в Production.

## Решение по кандидатам

В Local опубликованы три проверенные Model:

- `gpt-6-1-sol-e3b8963b` — GPT-6.1 Sol, точная дата 2026-09-29, Public Number #332;
- `embed-5-fast-b11d573d` — Embed 5 Fast, точная дата 2026-09-30, #333;
- `embed-5-pro-e5a9c8ce` — Embed 5 Pro, точная дата 2026-09-30, #334.

В Local опубликованы шесть проверенных Tool:

- `codex-security-cloud-42719bcf` — Codex Security Cloud, `≈2026-03`, #135;
- `amazon-bedrock-managed-agents-642b579d` — Amazon Bedrock Managed Agents, 2026-04-28, #141;
- `muse-a8472d5d` — Muse, 2026-09-08, #148;
- `openai-agents-api-383fd219` — OpenAI Agents API, 2026-09-10, #149;
- `oracle-fusion-claw-0d0c72fe` — Oracle Fusion Claw, 2026-09-29, #154;
- `dots-b80b4fd6` — Dots, 2026-09-30, #155.

Два Tool сохранены только в master как скрытые `NEEDS_REVIEW` и не вошли в Local/Production package:

- `decisions-api-1912bc35` — `SOURCE`: нет устойчивой отдельной официальной API-документации; доступ описан как ограниченный preview;
- `honeycomb-ai-ecosystem-26de12a0` — `SCOPE`: не подтверждена самостоятельная Tool-классификация отдельно от ecosystem/feature.

Новых deprecations не добавлено. Из существующих записей обновлены только заданные темы: GitHub Copilot supported models; GPT-6 Astra ultrafast как service tier, а не новая модель; Codex DevDay capabilities; ChatGPT Space/Pages/team/shared tasks и Slack/Teams/Meetings availability; Meta Muse Last Verified. Muse опубликован отдельной Tool-записью. Независимые evaluation results не выдумывались и лист `Evaluations` не менялся.

## Exact master diff и release manifests

- Master до: Models 805 (331 PUBLISHED / 474 NEEDS_REVIEW), Tools 151 (149 / 2), Offers 676, Evaluations 5846, Access 1312, Facts 1889, Origins 856, Tool Platforms 265.
- Master после: Models 808 (334 / 474), Tools 159 (155 / 4), Offers 684, Evaluations 5846, Access 1320, Facts 1915, Origins 859, Tool Platforms 278; Changelog 28740.
- Добавлено: Models +3, Tools +8, Offers +8, Access +8, Facts +26, Origins +3, Tool Platforms +13; удалений нет. Помимо новых строк менялись только `Last Verified` у GPT-6 Astra и четырёх Muse model rows, GitHub Copilot `Last Verified` / `Supported Models`, ChatGPT/Codex `Last Verified` и 15 вычисляемых Tool numbers.
- Backup исходного master: `backups/daily-catalog-20260930-020/master-before.xlsx`, SHA-256 `DF4D4FDAFE48956E33E3BE1C4519FE2198E19522AB39C7B8EA207EFE2140F930`.
- Итоговый master SHA-256: `BDAAA1200C640DA07B42F7C5443C0CF91E9AB0F853E4C6E47862AA5749DAF33F`.
- `catalog_plan.json`: create 9, number changes 15, остальные категории 0; SHA-256 `D0773E2DF296D5FB525775E98F0F6CE07D4FB32687FC285A41CB4DB5EEE654B8`.
- `release_state.json`: 334 Models / 155 Tools; SHA-256 `49B6B3DA6110BBAF80ED286F8475E9763C52EE3A030687F02D1ED10D29454872`.
- `catalog_freshness.json`: 3 added Models / 6 added Tools / 0 updated; SHA-256 `70051E9C74D630067BAE9AD2358634637C71B1E79C30185BEC50E81C46D6EC2A`. NEW получают только записи с датой 2026-09-30: Embed 5 Pro, Embed 5 Fast и Dots.

## Scoped implementation

- Новые Tool получают локализованный ecosystem из `Ecosystem EN/RU`; JSON-поля master сравниваются семантически без ложного diff от форматирования/порядка ключей.
- Approx Date нормализуется без двойного `≈` в freshness snapshot.
- Добавлен существующий официальный Cohere mark mapping; изображения других записей не менялись.
- Обязательная мобильная проверка обнаружила реальный дефект tap: touch-click открывал popover и сразу закрывался generic `pointerleave`. Обработчики `pointerenter`/`pointerleave` теперь меняют состояние только для mouse; добавлена regression-проверка. Механика #018 и закрытая история #019 не переписывались.
- Первый remote release-preflight безопасно завершился до deploy с точным расхождением: 9 catalog creates дали 8 новых `ModelVersion`. Причина — Codex Security Cloud не имеет price/access и поэтому корректно не требует legacy holder. Универсальный trial gate теперь выводит ожидаемое число legacy rows из фактических nested/new price, access и evaluation changes; отдельный тест покрывает новый Tool без holder. Production при этом не менялась.

## Local QA

- Trial: отдельные `master-trial.xlsx` и `local-trial.sqlite3`; sync создал 9 записей и изменил 15 номеров, повторный план — 0; `catalog_master check` OK, `catalog_master qa` PASS, SQLite integrity `ok`, FK 0.
- Working Local: online backup `backups/daily-catalog-20260930-020/aipedia-20260930T185219133638Z.sqlite3`; sync применил тот же точный план. Итог: 334 Models / 155 Tools; repeat sync не имеет writable changes, остаются только намеренные master-only записи.
- Финальные проверки после всех release-gate fixes: `catalog_master check` OK; `catalog_master qa` PASS (queue 198, warnings 17 — существующая quality queue); `manage.py check` PASS; полный catalog suite 364 PASS, один Windows skip; `node --check static/site.js` и `git diff --check` PASS.
- Настоящий Local browser: RU desktop 1440, RU ultrawide 2502, RU mobile 375 и EN desktop 1440 PASS. Полные девять имён и даты в freshness popover, компактные границы 350 px desktop / 343 px mobile, отсутствие horizontal overflow, clock/date, focus/Enter/Escape, mouse hover, реальный mobile tap, row highlight, affected cards/marks и 0 console/page errors подтверждены.
- Все девять новых публичных карточек открываются без Server Error/Traceback; номера и даты соответствуют master. EN smoke для GPT-6.1 Sol и Dots подтвердил заголовок, release date/access и отсутствие overflow.

## Production

- Release commit `1f412c70634713f8dbf2ea10ee47115fef997450`; tag `release-2026-09-30-daily-catalog-update`. Archive `aipedia-code-1f412c706347.zip`, SHA-256 `6ca2858b4cc2c8a8f99e5033766ba73144507d119c22b191a471c0077ba2882d`, 399 tracked files, Local SQLite отсутствует.
- Server preflight PASS на baseline #019. Первый trial корректно остановил процесс до deploy из-за неверного ожидания legacy row; после исправления новый archive прошёл release-preflight на backup `aipedia-preflight-020-20260930T194223Z.sqlite3`: 32 writes, 8 ModelVersion rows, 6 Tool rows, Production DB untouched, final 334/155. Dry-run PASS, `copies_sqlite=false`.
- Deploy PASS: migrations 0, catalog plan applied exactly (9 creates + 15 renumbers, 32 writes), publication-state changes 0; pre-deploy backup `aipedia-before-code-20260930T194252Z.sqlite3`, after backup `aipedia-after-code-20260930T194252Z.sqlite3`, Local SQLite не копировалась.
- `/healthz` 200 подтверждает `1f412c70634713f8dbf2ea10ee47115fef997450`, service RUNNING. Server catalog: integrity `ok`, FK 0, 334/334 numbered Models, 155/155 numbered Tools, непрерывная нумерация. `verify-release` по исходному pre-deploy backup PASS; changed factual tables ровно plan-derived, Evaluations/Benchmarks не менялись.
- `catalog_master qa --production` PASS; GSD Public 34/34 PASS; полный Production QA 1659/1659 PASS (698 requests, 22 HTTP locales, hidden 492/492). Первоначальный 1656/1657 показал stale ожидание `/tools/?page=2 -> 404`; при 155 Tools это валидная вторая страница. QA теперь вычисляет pagination bounds из release manifest; повторный полный прогон PASS.
- Настоящий Public browser: RU 1440 и mobile 375, EN 1440 smoke PASS. Freshness popover показывает полные 9 имён и даты, 350 px desktop / 343 px mobile, horizontal overflow отсутствует, mobile tap остаётся открытым, row highlight = 3. Все девять новых карточек открываются с правильными #332–334 и #135/#141/#148/#149/#154/#155; EN GPT-6.1 Sol и Dots имеют release date/access. Console/page errors: 0.

## Закрытие

Release #020 закрыт без остатков в пределах заданного scope. Decisions API и Honeycomb AI Ecosystem остаются намеренными hidden `NEEDS_REVIEW`, а quality queue 198 / warnings 17 — ранее существующая документированная очередь, не дефект выпуска. Общий SEO/GSC/Cloudflare/performance, массовый icon audit и новый catalog audit не выполнялись.
