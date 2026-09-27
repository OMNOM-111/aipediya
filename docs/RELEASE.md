# Ручной выпуск AIpedia

Порядок допуска исполнителей — корневой `AGENTS.md`; этот файл описывает выпуск,
а не дублирует те правила. Текущая локальная работа — `docs/EXECUTION_STATE.md`;
строка ниже про опубликованный commit не означает, что GitHub и Local совпадают
с Production.

Push в GitHub **не** публикует сайт. Ярлык Local, кнопка Production, commit и push
сами по себе не выполняют deploy.

Текущий публичный выпуск — **Tools chronology + Cloudflare CSP**, 2026-09-27
19:13 UTC: commit `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`, tag
`release-2026-09-27-tools-chronology-csp`. Архив
`aipedia-code-cf4ac9a33f8d.zip`, SHA-256
`8af0a16c7044a8208e5ac38aa1d6a156621c670ccbaeb17640895c7f6e46c7a0`.
`/healthz` и серверная SQLite подтвердили 321 Models, 143 Tools, номера 1–143,
60 точных и 83 приблизительные даты. Backup и отчёт —
`docs/history/2026-09-27-tools-chronology-csp-release.md`.

### Предыдущий публичный выпуск — adaptive-ui

adaptive-ui, 2026-09-27 16:16 UTC: commit
`aa48e11bad7326340463654e33ba5e89769042b9`, tag `release-2026-09-27-adaptive-ui`
(`main` = опубликованная линия). По коду публичный сайт работает на commit `aa48e11bad7326340463654e33ba5e89769042b9`.
Архив `aipedia-code-aa48e11bad73.zip`, SHA-256
`51d7a45239b26c5400f3c0187960c2227ae7a2f04864d47fb6311c0eb524b453`; `/healthz` подтвердил
commit и production; 321 Models / 143 Tools. Отчёт — `docs/history/2026-09-27-adaptive-ui-release.md`.

### Предыдущий публичный выпуск — catalog-master-v015-final

catalog-master-v015-final, 2026-09-27 03:23 UTC: commit
`a51c0a1aed2f63047b0203b208eccf8def458ae7`, tag `release-2026-09-27-catalog-master-v015-final`.
На дату этого выпуска код публичного сайта — commit `a51c0a1aed2f63047b0203b208eccf8def458ae7`.
Архив `aipedia-code-a51c0a1aed2f.zip`, SHA-256
`e2f5485db53988bd7d66fd9fa5542665d2e232d157aa12071b1ae2446b3a92e1`; `/healthz` подтвердил
commit и production; 321 Models / 143 Tools. Отчёт — `docs/history/2026-09-27-catalog-master-v015-final.md`.

### Предыдущий публичный выпуск — catalog-master-v015

catalog-master-v015, 2026-09-27 01:35 UTC: commit
`e36acfa351b28f441ec7ad91587b67201cb8aa85`, tag `release-2026-09-26-catalog-master-v015`.
На дату этого выпуска код публичного сайта — commit `e36acfa351b28f441ec7ad91587b67201cb8aa85`.
Архив `aipedia-code-e36acfa351b2.zip`, SHA-256
`d5225a113f5c48193bef5df508afac3282901983117292e6cb7d44a012488b09`; `/healthz` подтвердил
commit и `environment=production`; 321 Models / 143 Tools. Отчёт —
`docs/history/2026-09-26-catalog-master-v015.md`.

### Предыдущий публичный выпуск — Search Visibility Optimization v2

Search Visibility Optimization v2, 2026-09-26
21:47 UTC: commit `61adedd6ea5e6a0955d51d87374fa2fa9bcc7799`, tag
`release-2026-09-26-search-visibility-optimization-v2`. На дату этого выпуска код публичного сайта — commit `61adedd6ea5e6a0955d51d87374fa2fa9bcc7799`:
`/healthz` подтвердил `environment=production` и commit; 310 Models / 139
Tools сохранены. Архив `artifacts/code-release/aipedia-code-61adedd6ea5e.zip`,
SHA-256 `8b8f2fa4bac3b6edce0868e4a963a795111d45695341c869ed824186e9ee625f`.
Отчёт и QA: `docs/history/2026-09-26-search-visibility-release.md`.
Более новый код публикуется только по новой конкретной команде владельца.

### Предыдущий публичный выпуск — catalog-master-v014

Предыдущий публичный выпуск (catalog-master-v014, 2026-09-26 18:18Z; 310 Models / 139 Tools;
отчёт — `docs/history/2026-09-26-catalog-master-v014-release.md`):
- release_id опубликованного пакета: `1a10421d9d7bcd68b2b1224ce74843bebd932e2c` — его
  возвращает `/healthz`; это digest файлов кандидата из
  `data/release/v014/CANDIDATE_FILES.txt` поверх `b3116cf6dc56`, **не** hash git-commit;
  архив `aipedia-code-1a10421d9d7b.zip`, SHA-256
  `c80469b298a8221655030c735475fef2c945524a81c6d4466e2eaa74e4ec4377`.
- Git-коммит с изменениями выпуска: `20807cd542ec474737840bf78677d57b31a37e98`,
  tag `release-2026-09-26-catalog-master-v014`. На дату этого выпуска публичный сайт работал на commit `20807cd542ec474737840bf78677d57b31a37e98`:
  300 из 308 файлов архива побайтно совпадают с этим коммитом; отличаются только шесть
  документов статуса (дописаны после выпуска) и служебные `BUILD.json`/`MANIFEST.json`
  сборки (сверка 2026-09-26 18:55Z).
- Ограничение сборщика (до исправления извлечения): `tools/pack_ai_context.py` читает
  из этого файла только Git-коммит (поле `production_commit_from_docs` в
  `AI_CONTEXT/MANIFEST.json`); release_id опубликованного пакета он не извлекает и
  живой `/healthz` не запрашивает. Фактический выпуск сверять по release_id выше и
  `/healthz`. Запрос исполнителю сборщика — `docs/EXECUTION_STATE.md`, блок v014.
Предыдущий: commit `634778807b2e82ca52dea1de150ea0810950d644`
(tag `release-2026-09-25-deploy-dispatch-lock`, 2026-09-25 22:54Z; отчёт —
`docs/history/2026-09-25-naver-indexnow-activation.md`). Перед ним в тот же день:
`386d4aaafd00` (`release-2026-09-25-indexnow-root-key`),
`160be0f37037` (`release-2026-09-25-naver-verification`) и `ba93f7ddf690`
(`release-2026-09-25-gsd-1-0`, отчёт `docs/history/2026-09-25-gsd-1-0-release.md`).
Позднее код этой ветки публикуется только по отдельной команде владельца.

`release-2026-09-25-naver-verification` (`160be0f37037`, meta-tag Naver) и
`release-2026-09-25-indexnow-root-key` (`386d4aaafd00`, ключ IndexNow в корне сайта)
выпущены 2026-09-25 по команде владельца.

GSD-1.0 выпущен (scope, зависимости и откат: `docs/history/GSD-1.0-release-scope.md`).
Проверка после выпуска: `tools/gsd_production_qa.py https://aipediya.com --commit <sha>`
и `tools/gsd_public_check.py https://aipediya.com` (старый `public_acceptance.mjs`
проверяет прежний `?lang=`-контракт).

## Процесс выпуска (подтверждено владельцем 2026-09-25)

Develop on Local → QA Local → владелец утверждает выпуск → Production
приводится к **утверждённому Local-состоянию** → выпуск получает commit, tag и
changelog.

- Утверждение владельцем относится ко всему проверенному Local-состоянию:
  что публично, скрыто, отсортировано, переведено и как отображается.
  Отдельные внутренние изменения, уже входящие в это состояние, повторно не
  согласуются.
- Local SQLite на сервер **никогда** не копируется. Код переносится архивом,
  схема — `migrate` существующей серверной БД, а публикационное состояние
  (какие Models/Tools публичны, их постоянные номера) — манифестом
  `data/release_state.json` из того же commit:
  `manage.py sync_publication_state export data/release_state.json --release <tag>`
  на Local, затем `deploy_code_release.py … --publication-state data/release_state.json`
  на сервере. Шаг идёт после `migrate`, пока `aipedia` остановлена; меняет только
  `published` через `save()` с записью `sync_release_state` в журнал; при любом
  расхождении номера/slug ничего не пишет, и deploy откатывается к backup.
- Перед выпуском: полный набор тестов PASS, Local QA PASS; после — public
  HTTPS QA. Tag вида `release-YYYY-MM-DD-<name>`, changelog — ниже и в
  `docs/history/`.

## Changelog

### release-2026-09-27-tools-chronology-csp — Tools chronology и Cloudflare CSP

- Утверждённый план изменил только 27 дат Tools и 140 Public Numbers; 143
  опубликованных Tools имеют номера 1–143, 60 exact и 83 approximate дат.
- Узкий CSP разрешил обычный и версионный Cloudflare beacon и same-origin RUM;
  браузер Production получил beacon 200 и `/cdn-cgi/rum` 204.
- Models, цены, оценки, описания и publication state не изменились.
- Канонический серверный доступ через `python tools/server.py preflight` и
  SSH alias `aipediya-prod` стандартизирован отдельно от состава опубликованного
  архива; детали — `D-2026-09-27-canonical-production-server-access`.

### release-2026-09-27-adaptive-ui — адаптивный интерфейс

- Телефон: строки Models и Tools — карточки; панель записи — экран под шапкой (меню языка,
  поиск и тема доступны); Фильтр и Сортировка — нижние sheet-окна; без горизонтальной
  прокрутки страницы с 320 px.
- Планшет и небольшой ноутбук: второстепенные колонки сворачиваются по ширине каталога,
  панель — drawer под шапкой; desktop от 1280 px — таблица и панель; ultrawide ограничен
  `max(2400px, 60vw)`.
- Исправлено: подгрузка на телефоне доходит до полного списка (была 200 из 321), меню языка
  следует за открытой записью, «назад» сохраняет вкладку, документ app-shell больше не
  растягивается скрытыми подписями цены.
- Code-only: миграций и изменений данных нет; публикация 321 Models / 143 Tools без изменений.

### release-2026-09-27-catalog-master-v015-final — финальная синхронизация v015

- Счётчики: у каталога пояснено, сколько записей имеют № (подтверждённая дата) и
  сколько без даты — Tools 143 = 116 с № + 27 без даты (раньше «116» из колонки №
  читалось как количество).
- Страны и флаги с источниками: 11 моделей и 15 инструментов; валюта цены
  показывается по строке (₹, ₽, $), сравнения — только в USD.
- +70 официальных цен (GPT-5.x, Gemini 3.1 Flash-Lite Image, Qwen3-Coder, Qwen3.8-LiveTranslate,
  Kimi K2.6/K2.7 Code/K3, Solar Pro 2, Sarvam Vision 2.1, Speech TTS Live, SourceCraft с 01.10);
  +19 способов доступа; +25 независимых результатов Epoch AI (Claude Opus 5.5, GPT-6 Sol,
  Qwen3.8-Max, Qwen3.8 Max (0902), DeepSeek V4 Flash 0731); 9 проверенных пробелов оценок.
- Постоянная release-QA `catalog_master qa` (`D-2026-09-27-release-qa-gate`).
  Даты выпуска и номера моделей не изменялись; 321 Models / 143 Tools. Миграций нет.

### release-2026-09-26-catalog-master-v015 — новые модели 22–24 сентября

- 11 новых моделей с ценами, доступом, датами и переводами на 22 языка: Claude Opus 5.5,
  GPT-6 Sol, GPT-6 Luna, Gemini 3.8 Flash TTS, Gemini 3.8 Flash-Lite TTS, Nemotron 3
  Diarization, Speech TTS Live, Sarvam Vision 2.1, GLiNER2.5-Decide, FLUX 3 Action DROID,
  FLUX 3 Action SO-101 — номера 311–321 по подтверждённой дате выпуска; 1–310 без изменений.
- 4 новых инструмента (Alice AI Pro for Business, Qwen Intelligence, Yandex AI Studio,
  SourceCraft); 18 инструментов получили новый хронологический номер.
- Исправлены категория/задачи 9 моделей (GPT-5.6, GPT-6 Astra, Claude 5-серия,
  Claude Haiku 4.5 — контекст 200K); записи NEEDS_REVIEW не публикуются.
- Публично 321 Models / 143 Tools (было 310 / 139). Миграций нет.

### release-2026-09-26-search-visibility-optimization-v2 — Search Visibility Optimization

- 45 известных Google Search Console старых URL: 25 одношаговых 301 на чистые
  карточки, 19 корректных 404 для снятых сущностей, один технический ответ
  `200` с `X-Robots-Tag: noindex`. Исключения robots конечны и точны; широкие
  разрешения `?page=` на карточках удалены.
- Убраны параметрические ссылки на карточки из SSR-строк каталога; сохранён
  возврат к странице пагинации в интерфейсе. Две конечные EN/RU страницы
  сравнения контекста и официальных API-цен используют только проверенные данные.
- IndexNow-диспетчер принимает 301/302 для уведомлений о старых URL. После
  выпуска штатный scheduler обработал 334 точечных уведомления (330 старых
  redirect URL и четыре новые страницы); принятие не означает индексацию.
- Local: 268 тестов (267 PASS, один ожидаемый skip), `seo_report` без проблем.
  Production: 45/45 старых URL и 1657/1657 проверок публичного Search QA PASS.


### release-2026-09-26-catalog-master-v014 — единая база каталога

- Публично 310 моделей и 139 инструментов (было 304 / 138): 21 проверенное
  дополнение (Gemma 1–3, SAM / SAM 2 / 2.1, Whisper large-v3-turbo, Janus-серия,
  AlphaFold 3, MusicGen, AudioGen, ComfyUI, Google AI Studio), GPT-Live 1 в Models.
- Скрыты 14 дублей той же модели с 301 на основную карточку (датированные ID
  Claude, FLUX1.1 pro Raw, Nemotron 3 Super BF16); ошибочная карточка GPT-Live 1 в
  Tools заменена 301 на модель.
- Номера — хронологическая позиция публичной записи; порядок по номеру и по дате
  строго монотонен в обе стороны (исправлен разворот записей одной даты).
- Альтернативные названия находятся поиском; уточнены даты, лицензии, описания
  30 инструментов, источники, платформы; 11 оценок Artificial Analysis скрыты до
  подтверждения права показа.
- Миграция `0019_catalog_master_aliases` (поля `aliases`, `redirect_to`).

### release-2026-09-25-gsd-1-0 — «Глобальная поисковая доступность» (GSD-1.0)

- Постоянные адреса на каждом из 22 языков (`/ru/…`, `/zh-hans/…`; английский на
  корне); старые ссылки `?lang=` ведут на ту же страницу одним 301.
- Карточки моделей и инструментов полностью доступны без JavaScript, с источниками
  и датами проверки.
- Локализованные заголовки и описания, взаимные hreflang, sitemap index и карта
  сайта на каждый язык; фильтры и сортировки не индексируются.
- Страница «Источники и методика», 10 тематических подборок (9 индексируются).
- Открытые наборы данных подготовлены, но на Production выключены до решения о
  лицензии (`AIPEDIA_DATASETS_PUBLIC=0`).
- Журнал изменений для IndexNow (отправка выключена до ключа владельца).
- В составе утверждённого Local-состояния: код catalog master и страница
  «История сайта» (только Local; на Production — 404).
- Публикационное состояние не меняется: 304 Models / 138 Tools; миграция
  `0018_discovery_outbox` добавляет одну пустую таблицу.

### release-2026-09-25-local-approved

- Полная локализация интерфейса и каталога на 22 языка.
- Корректный публичный счётчик каталога.
- Проверенный набор из 304 публичных Models (Tools — 138).
- Сортировка по умолчанию newest → oldest для Models и Tools.
- Фильтры, поиск, клик по строке и правая панель (Escape / X / клик вне).
- Улучшения responsive/mobile и RTL (ar, fa).
- 459 внутренних research-моделей сохранены в базе вне публичного каталога
  (без удаления данных, переводов и истории; постоянные номера 305–763 внутренние).

## Общая серверная машина и SSH

### Server access — единая точка входа

В начале server phase выполнить **`python tools/server.py preflight`**. При
`SERVER ACCESS = PASS` использовать тот же wrapper для `health`, `status`,
`upload <archive> --sha256 <digest>`, `release-preflight <archive> --sha256
<digest> [--catalog-plan ... --publication-state ...]` и `deploy <archive>
--sha256 <digest> [--catalog-plan ... --publication-state ...]`. `deploy` требует
успешный matching `release-preflight` report; `--dry-run` доступен отдельно.
После выпуска `catalog` проверяет живые счётчики/целостность, а
`verify-release <aipedia-before-code-...sqlite3>` сравнивает фактические данные
с online backup до выпуска.
Архив передаётся только в `/tmp/aipedia-*`, SHA-256 сверяется автоматически.
Не собирать SSH/SCP-команду вручную и не искать credentials заново.

На этой Windows-машине пользовательский `~/.ssh/config` содержит alias
`aipediya-prod`: `HostName ssh-canary.stratforges.com`, `User stratforge`,
`IdentityFile ~/.ssh/codex_stratforge_stage9`, `IdentitiesOnly yes`,
`ProxyCommand "C:\Program Files (x86)\cloudflared\cloudflared.exe" access ssh
--hostname %h`, `UserKnownHostsFile ~/.ssh/known_hosts`,
`StrictHostKeyChecking yes`, `BatchMode yes`, `ConnectTimeout 20`. Это только
параметры транспорта, без содержимого ключа/секретов. Если alias отсутствует
на новом компьютере, настроить его из этого контракта и проверить `ssh -G
aipediya-prod`; если он есть, сначала проверить его и вывести конкретную
ошибку, не подбирать альтернативные ключи. Не ослаблять host-key verification.

Физическая машина общая; project scope AIpediya: `/srv/aipedia`, его
backups/releases/SQLite, программа `aipedia` и `/tmp/aipedia-*`. StratForge,
TradeForge, будущие проекты и общесистемный tunnel вне scope AIpediya. Для
нового проекта нужен отдельный alias/root/service/DB/backup namespace/tooling,
а не повторный поиск транспорта.

Codex выполняет эти команды напрямую в рамках разрешённого выпуска. Claude Code
использует **тот же** wrapper и alias: если Auto блокирует серверную команду,
сообщить владельцу `Server access is configured. Claude Auto blocked execution.
Switch Claude Code to Manual/Ask and rerun the same server command.` После
переключения повторить ту же команду. Handoff Codex — запасной путь.

### Executor preflight (обязательно перед первой серверной командой)

1. Определить исполнителя серверной фазы.
2. Исполнитель Claude Code:
   - Local/release preparation (тесты, tag, архив, SHA-256, `--dry-run`, публичная
     базовая линия) может выполняться в `Auto`;
   - если Auto блокирует wrapper, владелец переводит сессию в Manual / Default / Ask
     (режим с подтверждением команд); затем повторить ту же команду и выполнять
     серверные команды только через подтверждение интерфейса;
   - если режим изменить нельзя или владелец не хочет — **STOP SERVER PHASE** и
     подготовить handoff для Codex (ниже).
3. Исполнитель Codex — обычный порядок этого документа.

Блокировку SSH в Claude Code `Auto` не считать доказательством отсутствия
доступа или неправильного сервера. Не искать альтернативные credentials, не
читать private key, не расширять permissions исполнителем, не повторять SSH
многократно (`D-2026-09-27-claude-server-permission-mode`, `AGENTS.md`).

Handoff серверной фазы для Codex (Codex не повторяет завершённую и проверенную
Local-работу, а продолжает с этого состояния): project AIpediya; release commit;
previous Production commit; release tag; путь/имя готового архива и SHA-256;
результаты Local tests и тестов распакованного архива; результат `--dry-run`;
Production baseline (`/healthz`, штатные публичные проверки); требуемые server
preflight checks; ограничения выпуска; ожидаемые counts Models/Tools и манифест
публикации; post-deploy QA; точный следующий шаг.

### Граница и способ подключения

AIpediya и StratForge размещены на одной серверной машине. Исполнителям
AIpediya разрешено использовать существующий настроенный SSH-доступ к этой
общей машине для работ исключительно в контуре AIpediya. Запрет «не трогать
StratForge» относится к файлам, данным, процессам, сервисам, туннелям,
конфигурации и секретам StratForge, а не к самому факту SSH-подключения к общей
машине. Не читать, не копировать, не изменять и не раскрывать приватные
SSH-ключи; разрешено использовать уже настроенную SSH identity для подключения
к общей машине, если действия строго ограничены контуром AIpediya. После входа
сначала read-only: hostname, пользователь, `/srv/aipedia`, состояние только
программы `aipedia`, текущий release (`/healthz`), серверный preflight.
Каталоги StratForge не исследовать, его программы не трогать
(`D-2026-09-26-shared-server-ssh`, `AGENTS.md`).

Канонический способ подключения — `tools/server.py` и alias `aipediya-prod`
(контракт выше). Проверка ключа сервера остаётся включённой. Каталоги AIpediya принадлежат пользователю `aipedia` —
чтение и выпуск через `sudo -n` (без интерактива); выпускной скрипт запускается
`sudo -n python3 …/tools/deploy_code_release.py`. Граница: `/srv/aipedia`, программа
`aipedia` в `/srv/aipedia/supervisord.conf`, `/tmp/aipedia-*` для архивов и preflight.
Разрешение среды (подтверждение команд в Claude Code) — отдельно от разрешения
владельца на выпуск; порядок — «Executor preflight» выше.

Серверный preflight (перед боевым запуском, живую БД не меняет): онлайн-копия
`/srv/aipedia/data/aipedia.sqlite3` в `/srv/aipedia/backups/aipedia-preflight-*.sqlite3`
(sqlite backup API от `aipedia`), распаковка архива в `/tmp/aipedia-preflight-*`, на
копии `migrate` → `catalog_master apply-plan` (без `--apply`, затем с ним) →
`import_translations` → `sync_publication_state apply` (dry-run) → повтор `apply-plan`.

## Выпуск catalog-master-v014 (разрешён владельцем 2026-09-26)

Разрешение: приёмка и разрешение владельца 2026-09-26
(`D-2026-09-26-owner-acceptance-v014`) — кандидат `954db5a4586b` + исправление
порядка номеров + исправление классификации GPT-Live 1. Состав после выпуска:
310 Models / 139 Tools (было 304 / 138). Отчёт —
`docs/history/2026-09-26-catalog-master-v014-release.md`.

Данные выпуска: `data/release/v014/catalog_plan.json`,
`data/release/v014/translations.json`, `data/release_state.json`; список файлов
кандидата — `data/release/v014/CANDIDATE_FILES.txt`. Архив собирается из
commit/tag выпуска обычной сборкой (`tools/build_code_release.py`); его
соответствие испытанному кандидату проверяется по манифестам (отличаются только
документы), и распакованный архив проходит полный набор тестов заново.

На сервере (только контур AIpediya):
1. read-only проверка (см. раздел выше) и `--dry-run`;
2. `python3 tools/deploy_code_release.py <archive> --sha256 <digest> --catalog-plan data/release/v014/catalog_plan.json --translations data/release/v014/translations.json --publication-state data/release_state.json`.
   Скрипт делает online-backup, `migrate`, `catalog_master apply-plan` (сначала
   проверка всех ожидаемых старых значений по Record ID; любое несовпадение —
   остановка и откат к backup, без принудительного применения и без
   перестроения плана на сервере), `import_translations`,
   `sync_publication_state` (контроль), переключение кода и проверку `/healthz`.
3. Публичная проверка https://aipediya.com: версия, обе таблицы, порядок номеров
   в обоих направлениях, подгрузка, фильтры, GPT-Live 1 в Models, 301 со старого
   адреса Tools, поиск aliases, цены и единицы, sitemap (310/139), RU/EN.

Граница проверки до выпуска: испытан исходный снимок Local, сверенный с
публичными данными Production построчно; не копия серверной БД — поэтому
серверный preflight обязателен.

Предыдущий кандидат catalog-master-v013 (`954db5a4586b`) заменён этим выпуском и
отдельно не публикуется.

## Выпуск adaptive-ui

Состав и проверки — `docs/history/2026-09-27-adaptive-ui-release.md`. Code-only: без
`--catalog-plan`/`--translations`; `data/release_state.json` — контроль (0 изменений). Порядок:
Executor preflight (Claude Code — режим с подтверждением команд), read-only, preflight на
онлайн-копии (migrate, integrity/foreign keys, `sync_publication_state apply` dry-run), серверный
`--dry-run`, `deploy_code_release.py <archive> --sha256 <digest> --publication-state
data/release_state.json`; после — `final_check.py`, `gsd_production_qa --commit`,
`gsd_public_check`, `catalog_master qa --production` и публичная responsive-проверка
(`artifacts/adaptive-ui/qa-harness.mjs`, `qa-interactions.mjs`, обычный браузер).
`tools/verify_isolated_release.py` — исторический инструмент выпуска 22.09, для текущих
выпусков не применяется и пересобирает архив по тому же пути.

## Выпуск catalog-master-v015-final

Состав и проверки — `docs/history/2026-09-27-catalog-master-v015-final.md`. Данные:
`data/release/v015-final/catalog_plan.json` (план на исходном снимке Local, равном
состоянию Production после v015), `data/release_state.json`; переводы не требуются.
Порядок на сервере — как для v015: read-only, preflight на онлайн-копии, `--dry-run`,
`deploy_code_release.py <archive> --sha256 <digest> --catalog-plan
data/release/v015-final/catalog_plan.json --publication-state data/release_state.json`;
после — `catalog_master qa --production` на Local и
`artifacts/catalog-master-v015-final/final_check.py https://aipediya.com`.

## Выпуск catalog-master-v015

Состав и проверки — `docs/history/2026-09-26-catalog-master-v015.md`. Данные:
`data/release/v015/catalog_plan.json`, `data/release/v015/translations.json`,
`data/release_state.json` (321 / 143); список файлов — `data/release/v015/CANDIDATE_FILES.txt`.
Ветка `release/catalog-master-v015` продолжает опубликованную линию `0702405`
(код `61adedd`), а не `main`. Порядок на сервере — как для v014: read-only проверка,
`--dry-run`, затем `deploy_code_release.py <archive> --sha256 <digest> --catalog-plan
data/release/v015/catalog_plan.json --translations data/release/v015/translations.json
--publication-state data/release_state.json`; публичная проверка —
`artifacts/catalog-master-v015/v015_check.py https://aipediya.com`.

## Собрать архив кода

Из корня проекта, на проверенном commit/tag:

```powershell
.\.venv\Scripts\python.exe tools/build_code_release.py
```

Архив содержит только tracked Git-файлы. SQLite, `.env`, секреты, backups,
artifacts и `.venv` туда не входят. Скрипт отказывается упаковывать базу.

## Проверка на изолированной копии

Не трогает `/srv/aipedia` и публичный сайт:

```powershell
.\.venv\Scripts\python.exe tools/verify_isolated_release.py
.\.venv\Scripts\python.exe tools/deploy_code_release.py <archive> --sha256 <digest> --dry-run
```

Сценарий копирует каталог во временный файл, применяет миграции, сверяет
отпечаток карточек/цен/оценок и проверяет, что production-HTML не содержит
группы Local/Production.

## Публикация выбранной версии

Только на существующем хосте AIpedia, без изменения туннеля, секретов и StratForge.

1. Зафиксировать commit/tag и прогнать `manage.py test catalog --settings=aipedia.test_settings`.
2. Собрать архив `tools/build_code_release.py` и сохранить SHA256.
3. Скопировать архив на сервер **без** Local SQLite.
4. На сервере: `python3 tools/deploy_code_release.py /path/to/archive.zip --sha256 <digest> --publication-state data/release_state.json`
   (сначала то же с `--dry-run`).
5. Скрипт берёт блокировку `/srv/aipedia/data/indexnow-dispatch.lock` (плановая
   отправка IndexNow `aipedia-indexnow` на это время пропускается; блокировка
   снимается и после успеха, и после отката, и при аварийном завершении),
   останавливает только программу `aipedia`, делает online-backup
   `/srv/aipedia/data/aipedia.sqlite3`, переносит код и статику, выполняет
   `migrate` существующей серверной БД, поднимает только `aipedia` и проверяет
   `/healthz` на loopback.
6. Он **никогда** не копирует локальную SQLite поверх серверной базы и не
   удаляет `/srv/aipedia/data`, `/srv/aipedia/backups` и `/srv/aipedia/config`.

Проверить манифест заранее на копии, приведённой к схеме Production:
`manage.py sync_publication_state apply data/release_state.json` (dry-run) с
`AIPEDIA_DB=<копия>`.

Не использовать `tools/deploy_release.py` и `tools/deploy_chronology.py` для
этого изменения: они рассчитаны на прошлые выпуски с импортом источников /
хронологии.

## Откат кода

Если приложение не успели запустить, `deploy_code_release.py` возвращает
предыдущий `/srv/aipedia/app` и восстанавливает БД из `aipedia-before-code-*.sqlite3`.

Если приложение уже отвечало, база **не** откатывается автоматически — чтобы не
стереть правки, сделанные после публикации. Откат кода: остановить только
`aipedia`, вернуть предыдущий каталог приложения
`/srv/aipedia/releases/before-code-*` на место `/srv/aipedia/app`, запустить
только `aipedia`. Восстановление БД — отдельное решение владельца.
