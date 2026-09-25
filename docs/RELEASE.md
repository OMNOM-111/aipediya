# Ручной выпуск AIpedia

Порядок допуска исполнителей — корневой `AGENTS.md`; этот файл описывает выпуск,
а не дублирует те правила. Текущая локальная работа — `docs/EXECUTION_STATE.md`;
строка ниже про опубликованный commit не означает, что GitHub и Local совпадают
с Production.

Push в GitHub **не** публикует сайт. Ярлык Local, кнопка Production, commit и push
сами по себе не выполняют deploy.

Текущий публичный сайт работает на commit `ba93f7ddf690f4a958405fbabfc65a59d3a9cfbf`
(tag `release-2026-09-25-gsd-1-0`, 2026-09-25; отчёт —
`docs/history/2026-09-25-gsd-1-0-release.md`). Предыдущий:
`ed103a3ff163` (`release-2026-09-25-local-approved`).
Позднее код этой ветки публикуется только по отдельной команде владельца.

Подготовлен, но **не опубликован** кандидат `release-2026-09-25-naver-verification`
(`160be0f37037e34845edc1dae1e38eead4460a60`): SSR meta-tag и конфигурация Naver.
Production остаётся на `ba93f7ddf690` до запуска штатного deploy на AIpedia host.

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
5. Скрипт останавливает только программу `aipedia`, делает online-backup
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
