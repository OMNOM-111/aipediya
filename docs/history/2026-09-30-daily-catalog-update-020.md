# Daily Catalog Update — 30 September 2026

Дата: 2026-09-30. Исполнитель: Codex. Timeline: `DAILY-CATALOG-UPDATE-2026-09-30`, Release #020 / `v0.17.0`.

Состояние: `review` — Local ✓ / Owner ✓ / Production —. Карточка создана до refresh, research и любых изменений canonical master. Условие предварительного разрешения владельца выполнено полным Local PASS; Production на этом этапе ещё остаётся #019.

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

## Local QA

- Trial: отдельные `master-trial.xlsx` и `local-trial.sqlite3`; sync создал 9 записей и изменил 15 номеров, повторный план — 0; `catalog_master check` OK, `catalog_master qa` PASS, SQLite integrity `ok`, FK 0.
- Working Local: online backup `backups/daily-catalog-20260930-020/aipedia-20260930T185219133638Z.sqlite3`; sync применил тот же точный план. Итог: 334 Models / 155 Tools; repeat sync не имеет writable changes, остаются только намеренные master-only записи.
- Финальные проверки после touch-fix: `catalog_master check` OK; `catalog_master qa` PASS (queue 198, warnings 17 — существующая quality queue); `manage.py check` PASS; полный catalog suite 362 PASS, один Windows skip; `node --check static/site.js` и `git diff --check` PASS.
- Настоящий Local browser: RU desktop 1440, RU ultrawide 2502, RU mobile 375 и EN desktop 1440 PASS. Полные девять имён и даты в freshness popover, компактные границы 350 px desktop / 343 px mobile, отсутствие horizontal overflow, clock/date, focus/Enter/Escape, mouse hover, реальный mobile tap, row highlight, affected cards/marks и 0 console/page errors подтверждены.
- Все девять новых публичных карточек открываются без Server Error/Traceback; номера и даты соответствуют master. EN smoke для GPT-6.1 Sol и Dots подтвердил заголовок, release date/access и отсутствие overflow.

## Текущий остаток

Local полностью принят автоматическими и визуальными проверками; предварительное разрешение владельца на Production стало действующим. Следующий шаг — commit/push точного проверенного состояния, сборка архива #020 и штатный server preflight/release-preflight/dry-run/deploy/verification по `docs/RELEASE.md`. До завершения этой процедуры Production остаётся #019.
