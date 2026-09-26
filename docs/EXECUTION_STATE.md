# Текущее состояние AIpedia

Живой паспорт локальной разработки. Не дублирует `AGENTS.md`.
Отчёты законченных выпусков — `docs/history/`.
Пакет для нового чата собирается командой `\.\.venv\Scripts\python.exe tools/pack_ai_context.py` и **не** редактируется как независимый источник.

## Catalog master v014 — опубликовано и проверено — 2026-09-26 18:40 UTC

- Статус: **опубликовано и проверено** (выпуск catalog-master-v014, отчёт
  `docs/history/2026-09-26-catalog-master-v014-release.md`). Приёмка и разрешение
  владельца — `D-2026-09-26-owner-acceptance-v014`.
- Production: release `1a10421d9d7bcd68b2b1224ce74843bebd932e2c` (архив
  `aipedia-code-1a10421d9d7b.zip`, SHA-256
  `c80469b298a8221655030c735475fef2c945524a81c6d4466e2eaa74e4ec4377`), deploy
  2026-09-26 18:18Z, `deployed-origin-verified`, backup
  `/srv/aipedia/backups/aipedia-before-code-20260926T181857Z.sqlite3`. Публично
  310 Models / 139 Tools; публичная проверка — `artifacts/catalog-master-v014/public_check.json`.
- Исправлено по приёмке: порядок номеров (`D-2026-09-26-number-order`), GPT-Live 1
  (`D-2026-09-26-gpt-live-1-classification`). Первый серверный preflight остановил
  выпуск на расхождении pk цен (`offer-552…555`); план переведён на стабильные ключи
  строк, второй preflight и выпуск прошли.
- Master: `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` v014 (v013 — резервная
  копия в `backups/catalog-master-finalize-20260925/`).
- Local: 310 / 139, совпадает с Production по выдаче (списки EN/DE, 1 248 карточек,
  20 редиректов).
- Тесты: рабочее дерево 260 OK (1 skip); архив выпуска в чистом окружении 258: 257 OK,
  1 skip (`fcntl`, POSIX-only), 0 failed.
- Оставшийся шаг: нет обязательных. Очередь: 441 модель резерва, 30 публичных
  дополнений доступа/цен, 94 служебных расхождения, Kimi K3 (max), Grok Voice API,
  основание показа оценок AA, вычитка машинных переводов.

## Catalog master v013 — кандидат (заменён выпуском v014) — 2026-09-26 17:00 UTC

- Статус на тот момент: основной этап базы завершён; кандидат проверен; ожидалась
  приёмка. Заменён выпуском v014 (см. блок выше).
- Окончательный кандидат (полные SHA-256; сводка — `artifacts/catalog-master-v013-final/FINAL_CANDIDATE.json`):
  - код: `artifacts/code-release/aipedia-code-954db5a4586b.zip`,
    `c623be31641c4ad1175ac911599555ddab9646ceba8e5333e71ee0d5cc8c7618`; id выпуска
    `954db5a4586bf1d2b36fabb5ba0647b112bf17b3` = digest файлов из
    `data/release/v013/CANDIDATE_FILES.txt` поверх базового commit
    `b3116cf6dc563ccbd3c7e12eff8b428e40967547`; 304 файла, без SQLite/секретов;
  - план каталога `data/release/v013/catalog_plan.json`:
    `fd6281a04eb0962381cc9651374a90f3d69f99fc5276be6257e0b78cdace1c13`;
  - переводы `data/release/v013/translations.json`:
    `4c8f3c1354741cc6a12fddb40f450e2012b46d7ccc6cdd0a97074e513f58d075`;
  - манифест публикации `data/release_state.json` (309/140):
    `c13563fd4e9ff1d010c3ff0ca6b5b68e8996dfd9560361ada15264bcc70a2c33`;
  - master `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` (v013):
    `7e0081324012706d5e2ac06debe1eefc4929b2785fbbdaada0ec91607626203c`.
  Если после commit/tag пакет изменится — сверить с этими суммами и проверить
  заново; прежний PASS не переносится.
- Тесты архива (распакован вне проекта, чистое окружение: системный PATH + git,
  без `AIPEDIA_*`/`PYTHON*`, `.env.local` и рабочего дерева; `.venv` только с
  библиотеками; `python -E -s manage.py test catalog --settings=aipedia.test_settings -v 2`):
  найдено 246, успешно 245, пропущено 1 (`fcntl` только POSIX — проверяется на
  Linux-хосте), упало 0. Рабочее дерево: 248, OK (1 skip) — на 2 теста больше
  из-за незакоммиченных тестов параллельной работы над историей сайта.
  `test_import_research` больше не читает незакоммиченный `data/research/…json`:
  контролируемый архив создаётся в тесте, проверки сохранены и дополнены.
- Восстановление: внутри `apply-plan` (подделанный план → отказ без записи; сбой
  посреди записи → откат); весь выпуск (сценарий
  `artifacts/catalog-master-v013-final/release_process_recovery_script.py` на
  окончательном архиве: сбой на переводах после успешного `apply-plan` и сбой
  после переключения приложения → код побайтно = предыдущее приложение
  (`634778807b2e`), БД = исходная: схема 0018, та же сумма каталога, 304
  публичных; `migrate --check` предыдущего кода OK). supervisor/права Linux не
  воспроизводились.
- Граница Production: испытан исходный снимок Local, сверенный с публичными
  данными Production построчно (304 + 138), — не копия серверной БД. Серверный
  preflight `apply-plan` обязателен; при несовпадении — остановка без
  принудительного применения и без перестроения плана на сервере.
- Рабочий Local (для визуальной приёмки, `127.0.0.1:18810`): 309/140, состав —
  `local_final_composition.json` (`a1e91589839cd280ca7468d16b682528abc4aa60b392bbd41648f651e63e79e3`),
  база `2fd2aa6350224b37f467e5371128032c2219b3107142010560764c66db6611ba`; в этом
  шаге не менялась. Проверка выдачи — текст/DOM/HTTP, не визуальная приёмка.
- Отложено (очередь, не блокирует): 441 модель резерва; 30 публичных дополнений
  доступа/цен; 94 служебных расхождения; Kimi K3 (max), Grok Voice API; основание
  показа оценок AA; вычитка машинных переводов.
- Реальных технических блокеров не осталось. Следующим выполнить: владельцу —
  визуальная приёмка Local; выпуск — только после отдельного разрешения на этот
  кандидат, по `docs/RELEASE.md`.

## История сайта: две среды и ярлык — Local, 2026-09-25 15:42 UTC

- Изменено: по указанию владельца верх страницы `/ru/history/` содержит только
  Local и Production; Git HEAD и состояние рабочего дерева находятся в панели
  последней открытой карточки таймлайна. В `AI_CONTEXT` создан ярлык
  `AIpedia — История сайта.lnk`; он указывает на штатный
  `tools/local/start-local.ps1 -OpenPath /ru/history/`. Восстановление ярлыка —
  `tools/local/install-history-shortcut.ps1`. Для следующих агентов обновлены
  `docs/PRODUCT_HISTORY.md`, `AI_CONTEXT/README.md`, `AGENTS.md`,
  `docs/timeline.json`; решение о композиции записано в `docs/DECISIONS.md`.
  Сборщик AI_CONTEXT теперь включает порядок истории, реестр и установщик;
  Git-список в сборке читает Unicode-имя ярлыка без escape-последовательностей.
- Слои: текущий Local работает на `127.0.0.1:18810`; состояние сохранённого
  кода видно в последней панели. Production не менялся; по отчёту последний
  подтверждённый выпуск — `ed103a3`, текущий онлайн-ответ не проверен.
  Предшествующие незакоммиченные файлы сохранены, включая
  `AIpediya_GSD_1_0_Claude_Task.md`.
- Проверки: полный `manage.py test catalog --settings=aipedia.test_settings`
  **216/216 PASS**; PowerShell parser для двух launcher-скриптов — 0 ошибок;
  `.lnk` указывает на ожидаемый script/аргумент; `start-local.ps1 -OpenPath`
  на работающем Local вернул нужный адрес; `git diff --check` PASS. В браузере
  Local: две карточки, Git только в последней панели; mobile viewport 390 px
  — две карточки в колонку, без горизонтального переполнения. Физический
  телефон не проверялся. Автоматическое открытие браузера из ограниченного
  shell получило Access denied; скрипт корректно оставил Local работающим и
  вывел адрес. Двойной клик по `.lnk` вне sandbox отдельно не проверен.
- Не завершено: личный просмотр владельцем новой композиции; другие открытые
  задачи GSD-1.0 и master сохраняют прежний статус. Production не публиковался.
- Следующим выполнить: владельцу посмотреть страницу и ярлык; следующему
  исполнителю перед новой работой прочитать открытый пакет и замечания,
  обновлять `docs/timeline.json` только при изменении фактического состояния.

## История развития сайта — Local, 2026-09-25 08:09 UTC

- Изменено: в существующий `docs/timeline.json` добавлен слой истории продукта
  с тремя подтверждёнными этапами (20.09, 22.09, 25.09) и открытым пакетом;
  GSD-1.0 берёт 10 задач и их критерии из прежней записи реестра. Отдельно
  показаны master и эта страница, не смешанные с уже опубликованной базой.
  Созданы Local-only `/history/` и allowlist `/history/source/<id>`, шаблон,
  стили, JS боковой панели и тесты; ссылка добавлена в Local footer. Процесс
  сопровождения — `docs/PRODUCT_HISTORY.md`, краткая ссылка в `AGENTS.md`.
- Слои: Local HEAD `791e4ac5bf7469de243464c640c4af05b7304b26`, рабочее
  дерево грязное (включая прежние чужие изменения и не затронутый этой задачей
  `AIpediya_GSD_1_0_Claude_Task.md`); GitHub по более ранней
  проверке GSD-1.0 совпадал с HEAD, сейчас повторно не проверялся. Production
  по `docs/RELEASE.md` и отчёту выпуска — commit `ed103a3ff163`, tag
  `release-2026-09-25-local-approved`; доступ к публичному `/healthz` из этого
  окружения отклонён сетевыми правами, поэтому онлайн-состояние на текущий
  момент не подтверждено. Production не менялся.
- Проверки: `manage.py check` PASS; полный `manage.py test catalog
  --settings=aipedia.test_settings` **213/213 PASS**; JS syntax PASS;
  `git diff --check` PASS. Local browser: 1920, 1440, 2560, mobile 390;
  горизонтальная/вертикальная композиция, RU/EN/AR RTL, Light/Dark,
  панель/кнопка/Escape/клик вне/возврат фокуса — PASS. Эти mobile-проверки
  выполнены эмуляцией viewport, не физическим устройством. Существующий
  сервер 18810 держал старый шаблон в памяти; точная финальная версия
  запущена отдельным Local-процессом на `127.0.0.1:18811` и открыта в браузере.
- Не завершено: личная приёмка страницы владельцем; выпуск GSD-1.0 и master
  sync-local остаются открытыми; опубликованный сайт не получил страницу.
  Подтверждённый публичный статус после 03:21 UTC не получен из-за сетевого
  ограничения. Для не-RU/EN локалей текст истории показан с пометкой `lang=en`
  внутри правильного направления страницы; перевод истории на 20 языков не
  утверждён и не заявлен.
- Следующим выполнить: владельцу просмотреть Local-страницу и дать замечания;
  исполнителю обновить реестр по решению, а перед выпуском подтвердить
  конкретный commit/tag по `docs/RELEASE.md` и после него проверить public
  runtime. Никаких публикаций в этом этапе не выполнялось.

- Выпуск GSD-1.0: **DEPLOYED AND VERIFIED** 2026-09-25 16:08Z. Production =
  `ba93f7ddf690` / `release-2026-09-25-gsd-1-0` (отчёт
  `docs/history/2026-09-25-gsd-1-0-release.md`). Backup
  `aipedia-before-release-2026-09-25-gsd-1-0-20260925T160739Z.sqlite3`;
  migrate 0018; publication state без изменений (304/138); integrity ok, FK 0,
  счётчики = baseline; Production GSD QA 1596/1596; public check 34/34; public
  sitemap 10 032 `<loc>`. Внешне: Brave re-fetch принят; остальное — действия
  владельца (`docs/SEARCH_DISCOVERY.md` §10). Следующим выполнить: владельцу —
  консоли Google/Bing/Yandex и ключ IndexNow; исполнителю после ключа —
  `notify_indexnow --all` + `indexnow_dispatch --send` на Production.
- История подготовки выпуска (до deploy):
  - Commit `ba93f7ddf690f4a958405fbabfc65a59d3a9cfbf`, tag
    `release-2026-09-25-gsd-1-0`, push в GitHub выполнен (push не деплоит).
    Включены: GSD-1.0, код catalog master, Local-only «История сайта».
    Не включены (публичный репозиторий): master XLSX, `data/research/`,
    ярлык `.lnk`, файл задания.
  - Gate: 216 тестов PASS (история 3/3, catalog master 10/10), `check` OK,
    `makemigrations --check` — нет изменений. Манифест
    `data/release_state.json` переэкспортирован: изменилась только метка
    release; 304 Models / 138 Tools, как на Production.
  - Архив `artifacts/code-release/aipedia-code-ba93f7ddf690.zip`, sha256
    `5ed63075cb59e6bc97b05fe4e290c53b3a31202a043056aebb069dad8f8facc4`,
    290 файлов, без SQLite/секретов; dry-run `deploy_code_release.py` OK.
  - Блокер: удалённое выполнение через существующий SSH-канал общей машины
    отклонено автоматическим классификатором разрешений этой сессии (ключ
    StratForge). Обход не выполнялся. Production по-прежнему `ed103a3`.
  - Следующим выполнить: владельцу — либо разрешить этот SSH-канал для сессии,
    либо выполнить серверные шаги (backup → dry-run → deploy с
    `--publication-state data/release_state.json`); затем исполнителю —
    `tools/gsd_production_qa.py https://aipediya.com --commit ba93f7ddf690f4a958405fbabfc65a59d3a9cfbf`
    и запись выпуска в `docs/history/`.
- Обновлено (UTC): 2026-09-25 (GSD-1.0, Local)
- Задача 2026-09-25 **GSD-1.0 «Глобальная поисковая доступность»** (Local-only):
  реализация и Local QA; Production **не менялся**, ничего не отправлялось,
  push/tag/deploy не выполнялись. Паспорт и критерии — `docs/timeline.json`
  (прогресс: `.venv\Scripts\python.exe tools/gsd_progress.py`), контракт —
  `docs/SEARCH_DISCOVERY.md`, решения — `D-2026-09-25-locale-paths`,
  `…-seo-readiness`, `…-facets-pagination`, `…-datasets-license-gate`,
  `…-discovery-outbox`; evidence — `artifacts/global-search-discovery/GSD-1.0/`.
  - Слои (проверено 2026-09-25 04:08Z): Local HEAD = GitHub `origin/main` =
    `791e4ac` (свежий `git ls-remote`); Production `/healthz` = `ed103a3ff163`,
    sitemap 443 `?lang=en` URL (1 + 304 + 138). Local рабочее дерево = HEAD +
    незакоммиченные изменения (ниже).
  - Существующие незакоммиченные изменения другого исполнителя (не трогались,
    снимок `artifacts/…/baseline/`): `AGENTS.md`, `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (разделы master), `docs/EXECUTION_STATE.md`,
    `catalog/catalog_master.py`, команды `catalog_master`, `reconcile_catalog`,
    `restore_core_catalog`, `catalog/tests/test_catalog_master.py`, XLSX,
    `data/research/`, `requirements-dev.txt`.
  - Изменено этой задачей: URL `/<locale>/…` (English на корне) + 301 для
    `?lang=`; `catalog/locale_urls.py`, `middleware.py`, `readiness.py`,
    `seo.py`, `hubs.py`, `datasets.py`, `discovery.py`, `discovery_content.py`,
    `aggregates.py`, `views.py`, `context.py`, `static_pages.py`, `signals.py`,
    `comparison.py` (скрытые модели не связываются с инструментами),
    `templatetags/catalog_tags.py`, `models.py` + миграция
    `0018_discovery_outbox`; команды `seo_report`, `indexnow_dispatch`,
    `export_datasets`, `catalog_stats`, `notify_indexnow` (теперь только
    ставит в журнал); шаблоны base/catalog/panel/tool_panel/rows/header/footer/
    methodology/404/report + новые `collections.html`, `datasets.html`;
    `static/site.js`, `site.css`, `share-card.png`, `brand-512.png`;
    `data/discovery_translations.json` (переводы новых строк на 20 языков —
    черновик агента, не проверен человеком); `aipedia/settings.py`,
    `test_settings.py`, `urls.py`; `tools/gsd_progress.py`,
    `tools/gsd_public_check.py`, `tools/local/start-local.ps1` (URL `/ru/`);
    тесты: новый `test_global_search_discovery.py` (38), переписаны тесты
    старого URL-контракта (`test_i18n`, `test_search_discovery`, частично
    `test_catalog`, `test_environments`, `test_redesign`, `test_split_catalog`;
    остальные вызовы `?lang=` идут через 301 с `follow=True`).
  - Исправленные по ходу дефекты: ссылки строк в подгружаемых чанках несли
    `partial=rows` (пред-существующий); заголовок `X-Aipedia-Title` для
    нелатинских названий приходил в RFC 2047 (`=?utf-8?b?…`); `rel=prev` на
    второй странице; HEAD отвечал 405; заголовок вкладки не возвращался после
    закрытия панели; `notify_indexnow --all` был сломан; собственный crawler
    не разрешал относительные ссылки (исправлено до финального прогона).
  - Reconciliation 2026-09-25 (по запросу владельца): в sitemap добавлена
    индексируемая `/privacy` (×22) и правила sitemap выровнены с правилами
    страниц (двусторонняя проверка 396/396 без расхождений); итог 10 035
    `<loc>`; BreadcrumbList теперь всегда сопровождается видимой цепочкой;
    тесты матрицы structured data (Organization, BreadcrumbList, Dataset,
    DataCatalog, DataDownload); §8 `SEARCH_DISCOVERY.md` — только официальные
    первоисточники (Naver и способы верификации Baidu — «не подтверждено»);
    Brave: исправлено — отправка URL существует; политика training-краулеров
    записана как не определённая владельцем (`D-2026-09-25-training-crawlers-undefined`).
  - Проверки: `catalog` **216 тестов PASS, 0 FAIL, 0 SKIP** (было 174);
    полный rendered-аудит `seo_report --html all`: 10 013 страниц × 22 локали,
    0 проблем (canonical/hreflang/noindex/lang/dir/H1/title/description vs
    sitemap); sitemap = реестр (9 724 entity-URL, 0 утечек скрытых);
    robots-crawler завершился на 2 142 страницах, 442/442 публичных записи
    достижимы обычными ссылками без JS; `check` OK;
    `makemigrations --check` — нет изменений; `export_datasets --check`
    (детерминизм) PASS; `gsd_public_check` Local 33/33; браузер (desktop/mobile,
    тёмная/светлая, RU/UK/PL/ZH/AR/FA/DE/JA/ES/FR/EN) — PASS; сохранность данных:
    счётчики всех ключевых таблиц = baseline, ContentTranslation 42 260 current,
    XLSX sha256 без изменений, `release_state.json` ↔ БД 0 расхождений.
    Local SQLite изменена только миграцией 0018 (новая пустая таблица).
  - Не завершено / вне Local: выпуск GSD-1.0 на Production (нужно отдельное
    утверждение); лицензия датасетов (решение владельца); регистрация в
    консолях и ключ IndexNow (владелец); проверка переводов-черновиков;
    отложенный eval-gap (412,820 billable chars; ранее записанный дефицит F0
    108,605) — отдельно; пред-существующее: карточка AR на мобильном обрезана
    по горизонтали так же, как на Production.
  - Следующим выполнить: владельцу — утвердить scope GSD-1.0
    (`docs/history/GSD-1.0-release-scope.md`) и решить лицензию данных;
    исполнителю после утверждения — commit/tag и выпуск по `docs/RELEASE.md`,
    затем `tools/gsd_public_check.py https://aipediya.com`.
- Обновлено ранее (UTC): 2026-09-25T01:46:36Z
- Follow-up (master finalize): `catalog_master import` (added 0, renumbered 0) и `catalog_master check` = OK подтверждены повторно; исправлены тесты `catalog/tests/test_catalog_master.py` под обязательное поле `Publication Decision`; `manage.py test catalog --settings=aipedia.test_settings` снова PASS (170/170). Production не трогался.
- Задача 2026-09-25 (выпуск утверждённого Local-состояния): **DEPLOYED AND
  VERIFIED**. Production = commit `ed103a3ff163` / tag
  `release-2026-09-25-local-approved` (отчёт
  `docs/history/2026-09-25-local-approved-release.md`, процесс
  `D-2026-09-25-release-process`).
  - Слои: Local = GitHub (`origin/main` + tag) = Production для кода выпуска;
    Production: 304 Models / 138 Tools публично, 459 research-моделей скрыты
    (№305–763, данные/переводы/история сохранены), `/healthz` = `ed103a3ff163`.
  - Проверки: тесты 174 PASS; Local и public HTTPS аудит — 0 fails (22 локали,
    sitemap 304/138, 459 скрытых = 404); строки каталога Production и Local
    совпадают побайтно; браузер AR/RU/UK, desktop/mobile.
  - Вне выпуска (остались незакоммиченными в рабочей копии, работа другого
    исполнителя): `catalog_master*`, XLSX, `AI_CONTEXT/README.md`,
    `requirements-dev.txt`, `data/research/`, разделы catalog master в
    `AGENTS.md`/`DECISIONS.md`/этом файле; а также `restore_core_catalog`,
    `reconcile_catalog`.
  - Следующим выполнить: отдельная Local-итерация Global Search / SEO /
    discoverability (в т.ч. локализованный `<title>`); Production — только по
    новому утверждению владельца.
- Задача 2026-09-24 (catalog master — единая каноническая база, Local-only):
  **COMPLETE, Local PASS**. Production **не менялся**; ничего не публиковалось;
  Local SQLite не изменялась (sha256 до/после import/check совпадает).
  - Слои: Local — изменения не закоммичены. GitHub — `origin/main` = `6ce09b2`
    (без этой задачи). Production — не трогался; `/healthz` (только чтение)
    release `e8a4df761a87`, sitemap 763 модели / 138 инструментов.
  - Изменено: `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` пересобран как
    catalog master (схема `aipediya-catalog-master/2`): листы Models (763 =
    304 PUBLISHED + 459 NEEDS_REVIEW, 54 колонки), Tools (138 PUBLISHED, 44
    колонки), Offers 555, Evaluations 881, Access 1205, Facts 10, Origins 812,
    Tool Platforms 224, Changelog, Meta, Rules, Lists. Код:
    `catalog/catalog_master.py`, `catalog/management/commands/catalog_master.py`
    (`import [--production] [--rebuild]`, `check [--production]`),
    `catalog/tests/test_catalog_master.py`. Удалены созданные ранее этой же
    задачей и не закоммиченные `catalog/verification_master.py`,
    команда `verification_master` и её тест (старый XLSX: копия в
    `%TEMP%\old_registry_backup.xlsx`, ручных правок в нём не было). Правила:
    `AGENTS.md` («Каноническая база каталога (master)»), `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (`D-2026-09-24-catalog-master`; прежние
    `…-model-verification-registry` и нумерация из
    `…-permanent-catalog-numbers` — «заменено»; два открытых вопроса).
  - Результат импорта: drift master↔Local = 0 во всех листах; Public Number
    master (хронология) совпал с Local у всех 304 моделей и 17 датированных
    инструментов. Предупреждения `check` (ожидаемые): 580 записей имеют номер
    в Local без Public Number в master (459 NEEDS_REVIEW с 305–763 и 121
    инструмент без даты с 18–138); 459 NEEDS_REVIEW опубликованы на Production;
    121 PUBLISHED инструмент без verified date.
  - Проверки: `catalog_master import` повторно — added 0, renumbered 0;
    `check --production` — OK; Excel (COM) открывает все 12 листов, списки и
    подсветка (NEEDS_REVIEW + On Production=YES — красным) работают;
    `catalog` **170 тестов PASS**.
  - Не завершено: синхронизация master → Local (и затем Production) не
    реализована; Local-код (незакоммиченный) ещё выдаёт постоянные номера;
    верификация 459 кандидатов не выполнялась; открытые вопросы владельцу —
    номера 121 инструмента без даты и снятие 459 NEEDS_REVIEW с Production.
  - Следующим выполнить: владельцу — ответить на два открытых вопроса в
    `docs/DECISIONS.md`; исполнителю — реализовать `catalog_master sync-local`
    (master → Local, с журналом, без `QuerySet.update`), затем верифицировать
    кандидатов пачками (`import` + `check` после каждой).
- Ранее в этот день (реестр верификации, заменён catalog master): ниже — его
  исходная запись для истории.
  - Слои: Local — изменения ниже, не закоммичены. GitHub — `origin/main` =
    `6ce09b2` (без этой задачи). Production — этой задачей не трогался (текущий
    по этому файлу — `e8a4df761a87`; строка `docs/RELEASE.md` «публичный сайт
    работает на commit `43e2d3f…`» устарела — расхождение, не исправлялось).
  - Параллельно: в 00:27 UTC другой исполнитель записал ниже блок о выпускном
    прогоне (архив `artifacts/code-release/aipedia-code-6ce09b289d3f.zip`, deploy
    заблокирован). Имя архива указывает на commit `6ce09b2`, в который файлы
    этой задачи не входят; блок не изменялся, кроме пометки «Обновлено ранее».
  - Изменено: создан `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx`
    (листы Models / Rules / Lists; 459 строк = все скрытые модели Local, все
    `TO_VERIFY`; 15 колонок владельца + служебные Slug, Research Entity ID,
    Category, Catalog Status (DB), Reserved Number (Local DB), Research Date Hint,
    Import Sources (unverified), DB Checked, Import Batch, Missing Count;
    выпадающие списки, условная подсветка недостающего, закреплённая шапка,
    автофильтр). Код: `catalog/verification_master.py`,
    `catalog/management/commands/verification_master.py` (`sync|check`),
    `catalog/tests/test_verification_master.py`, `requirements-dev.txt`
    (`openpyxl`, только Local; установлен в `.venv`). Правила: `AGENTS.md`
    (раздел «Реестр верификации моделей»), `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (`D-2026-09-24-model-verification-registry` + открытый
    вопрос о номерах).
  - Данные в реестре: Official/Secondary Source, даты, Exists, Release Stage,
    Last Verified **пустые** у всех 459 (ничего не верифицировано); Missing Data
    у всех = `exists; date (exact or ≈); release_stage; official_source;
    last_verified`. Подсказки импорта: дата у 412, ссылки у 459 (служебные
    колонки, не доказательство). У 29 записей импортный источник — заглушка
    Smithsonian Mark I Perceptron.
  - Расхождения, найденные при сверке: (1) 459 моделей скрыты 2026-09-24 в
    23:37 UTC незакоммиченной командой `restore_core_catalog --apply` (журнал
    `move_to_research_layer`); блок ниже про «опубликованные 763» устарел —
    сейчас в Local опубликовано 304 модели (№1–304), скрытые 459 держат
    предварительные номера 305–763. (2) `restore_core_catalog` снимает
    публикацию через `QuerySet.update` (журнал пишется отдельно), а
    незакоммиченный `reconcile_catalog` описывает «clear all model numbers and
    assign fresh 1..N» — противоречит `D-2026-09-24-permanent-catalog-numbers`;
    не запускать без решения владельца.
  - Проверки: `verification_master sync` (повторный — added=0) и `check: OK`;
    `openpyxl` round-trip (правка агентом сохраняется, Missing Data
    пересчитывается, кандидат без slug сохраняется); негативный `check` ловит
    7/7 нарушений; Excel (COM) открывает файл без восстановления, списки и
    подсветка работают, введённая дата остаётся текстом; сохранить из Excel на
    этой машине нельзя — истекла лицензия Office. `catalog` **169 тестов PASS**.
  - Не завершено: сама верификация 459 кандидатов (источники/даты) не
    выполнялась; публикация кандидатов — только после `VERIFIED` →
    `READY_FOR_SITE` и отдельного решения владельца; вопрос о номере
    публикуемого кандидата (предварительный 305–763 или следующий свободный)
    открыт.
  - Следующим выполнить: владельцу — решить вопрос о номерах и при желании
    закоммитить; исполнителю — верифицировать кандидатов пачками, после каждой
    `verification_master sync` + `check`.

- Обновлено ранее (UTC): 2026-09-25T00:27:23Z
- Текущий выпускной прогон: `catalog --settings=aipedia.test_settings` PASS; Local smoke PASS (`127.0.0.1:18810`, `healthz`, каталог 304/138, newest-first, row-click проверен частично); isolated release verify FAIL по fingerprint базы (`publication_revisions`/`tool_publication_revisions` расходятся с ожиданием на Local-данных); code-only deploy из этого Windows окружения заблокирован, потому что серверный шаг выполняется на хосте `/srv/aipedia`, а здесь нет SSH-доступа к нему.
- Изменено: рабочее дерево содержит локальные правки каталога/вёрстки/документации и неотслеживаемые `data/research/`; архив кода собран как `artifacts/code-release/aipedia-code-6ce09b289d3f.zip`.
- Не завершено: публикация текущего Local-состояния в Production.
- Следующим выполнить: на серверном хосте AIpedia запустить по `docs/RELEASE.md` `python3 tools/deploy_code_release.py /path/aipedia-code-6ce09b289d3f.zip --sha256 6054b382624c31d00dd437e60245bfa921067089f34a5109fd7ed2600da88459` после отдельной проверки того, как должны трактоваться локальные revision counts для скрытых research-строк.

- Задача 2026-09-24 (три UX/data-нюанса, Local-only): **IMPLEMENTATION COMPLETE,
  Local PASS**. Production **не менялся** (нет применимого разрешения на выпуск).
  - Изменено:
    - (1) Чистый `/` открывает каталог по дате выпуска убыв. (newest-first) для
      Моделей и Инструментов; явные `?sort=…` переопределяют; детерминизм после
      перезагрузки (`catalog/views.py` default `release_desc`).
    - (2) Клик по всей строке открывает нужную панель; ссылки/кнопки/поля/фильтры
      и выделение текста не перехватываются; клик по строке не закрывает панель
      (`static/site.js`, `static/site.css` cursor).
    - (3) `catalog/public number` — постоянный ID (одна простановка, не
      пересчитывается на дате/цене/оценке/сортировке; существующие сохранены;
      остальные опубликованные проставлены один раз детерминированно; новая
      запись получает следующий свободный). Отдельная приблизительная дата
      `approx_released`/`approx_precision`/`approx_evidence` (рендер `≈`, никогда
      не выдаётся за точную). Сортировка по выпуску: точная → приблизительная →
      неизвестные в конце. Файлы: `catalog/models.py`, `catalog/chronology.py`,
      `catalog/comparison.py`, `catalog/templatetags/catalog_tags.py`, шаблоны
      строк/панелей, миграция `0016_approx_dates_and_permanent_numbers`.
  - Данные Local после миграции: модели опубликованные 763 → пронумерованы 763
    (0 null); инструменты 138 → 138 (0 null); номера уникальны и непрерывны
    (1..763 / 1..138); существующие 1..304 / 1..17 сохранены (первый `#1`
    jurassic-1-jumbo / github-copilot).
  - Проверки: `catalog` **160 тестов PASS** (5 старых тестов правила «номер по
    дате» переписаны на постоянные номера; добавлен `test_permanent_numbers.py`).
    Local-браузер: чистый `/` newest-first, `?sort=number_asc` даёт 1..5,
    `release_asc` oldest-first, клик по ячейке строки открывает панель, клик вне
    закрывает; Tools newest-first.
  - Решения: добавлено `D-2026-09-24-permanent-catalog-numbers`;
    `D-2026-09-20-chronology-numbers` и `D-2026-09-20-undated-last` помечены
    «заменено новым решением»; обновлён numbering-абзац
    `D-2026-09-21-model-tool-catalog-split`.
  - Не завершено: приблизительные даты как инфраструктура — конкретные `approx_*`
    значения для 459 недатированных моделей владельцем не вносились (по замыслу).
    Публикация на Production не выполнялась.
  - Следующим выполнить: дождаться явного разрешения владельца на выпуск этого
    состояния по `docs/RELEASE.md`; при желании — наполнить `approx_*` доказанными
    приблизительными датами.
- Обновлено ранее (UTC): 2026-09-24T00:20:00Z

- Документация имён: правило «бренд AIpediya / техкод aipedia» закреплено в
  `AGENTS.md` и `D-2026-09-23-brand-vs-tech-name` (`docs/DECISIONS.md`). Код,
  сервер и Production не менялись.
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
- Локализация контролируемых меток (после публичного QA нашлись русские слова в
  нерусских локалях, например «Модель» на корейской странице). Два code-only
  выпуска по `docs/RELEASE.md`, без изменения БД и без Azure:
  - `bababd103ff0` (`release-2026-09-23-locale-fix`): метки конфигурации/
    протокола оценок локализуются (`catalog/evaluation_labels.py`); `public_text`
    даёт английский fallback вместо русского для остальных контролируемых меток.
  - `e8a4df761a87` (`release-2026-09-23-controlled-i18n`, **текущий Production**):
    полноценная детерминированная локализация контролируемых меток на все 22
    локали (`catalog/controlled_terms.py`); английский — только аварийный
    fallback. Бренды/ID/тарифы/API/разрешения/URL не переводятся.
  Оба задеплоены через существующий SSH к общей машине (только пути/службы
  AIpedia); боевой online-backup перед каждым; `copied_sqlite=false`; миграций
  нет. Аудит всех 22 локалей (Local и Production): 0 русских утечек, 0
  английского fallback на поддерживаемых локалях. Тесты: 155 PASS.
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
| Правило имён бренд vs техкод в AGENTS/DECISIONS | Закреплено Local | Нет (ещё не commit) | Не требуется (docs) |
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

## Документация: бренд vs техкод (2026-09-23)

Изменено: в `AGENTS.md` добавлен раздел «Имена: бренд и техкод»; в
`docs/DECISIONS.md` — `D-2026-09-23-brand-vs-tech-name` (подтверждено
владельцем). Публично **AIpediya** / aipediya.com; внутренний техкод
**aipedia** не переименовывать без поручения. Не завершено: commit этих
docs по желанию владельца. Следующим выполнить: ничего обязательного по
именам; runtime и сервер не трогать.

## Текущая работа: видимый бренд AIpediya и проверка дизайна (2026-09-22)

- Видимое имя в шапке, footer, SEO title, карточках, методологии,
  конфиденциальности и административных подписях изменено с `AIpedia` на
  `AIpediya`. Внутренние имена Python/Django, совместимые HTTP-заголовки,
  пути, база и исторические имена файлов намеренно не переименовывались
  (с 2026-09-23 то же зафиксировано в `AGENTS.md` и
  `D-2026-09-23-brand-vs-tech-name`).
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
(в этом окружении нет SSH к хосту AIpedia; [ЗАМЕНЕНО 2026-09-26: правило «StratForge-ключи не используются» неверно — см. AGENTS.md, раздел «Общая серверная машина и SSH»: разрешено использовать настроенную SSH identity к общей машине строго в контуре AIpediya, ключи не читать и не раскрывать]).
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
)]).
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
