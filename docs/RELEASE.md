# Ручной выпуск AIpedia

Порядок допуска исполнителей — корневой `AGENTS.md`; этот файл описывает выпуск,
а не дублирует те правила. Текущая локальная работа — `docs/EXECUTION_STATE.md`;
строка ниже про опубликованный commit не означает, что GitHub и Local совпадают
с Production.

Push в GitHub **не** публикует сайт. Ярлык Local, кнопка Production, commit и push
сами по себе не выполняют deploy.

Текущий публичный сайт работает на commit `1a10421d9d7bcd68b2b1224ce74843bebd932e2c`
(catalog-master-v014, tag `release-2026-09-26-catalog-master-v014`, 2026-09-26 18:18Z;
310 Models / 139 Tools; отчёт — `docs/history/2026-09-26-catalog-master-v014-release.md`).
Это id кандидата (digest файлов из `data/release/v014/CANDIDATE_FILES.txt` поверх
`b3116cf6dc56`), а не hash git-commit; tag указывает на commit с теми же файлами кода.
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

Проверенный способ подключения (выпуск 2026-09-26; секреты в документ не входят):
`ssh -o "ProxyCommand=cloudflared access ssh --hostname %h" -i <настроенная identity> stratforge@ssh-canary.stratforges.com`
(Windows: `cloudflared` из `C:\Program Files (x86)\cloudflared\`; identity — уже
настроенный файл в `~/.ssh`, его содержимое не читать и не выводить). Проверка ключа
сервера остаётся включённой. Каталоги AIpediya принадлежат пользователю `aipedia` —
чтение и выпуск через `sudo -n` (без интерактива); выпускной скрипт запускается
`sudo -n python3 …/tools/deploy_code_release.py`. Граница: `/srv/aipedia`, программа
`aipedia` в `/srv/aipedia/supervisord.conf`, `/tmp/aipedia-*` для архивов и preflight.
Разрешение среды (подтверждение команд в Claude Code) — отдельно от разрешения
владельца на выпуск.

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
