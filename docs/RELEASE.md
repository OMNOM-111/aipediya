# Ручной выпуск AIpedia

Порядок допуска исполнителей — корневой `AGENTS.md`; этот файл описывает выпуск,
а не дублирует те правила.

Push в GitHub **не** публикует сайт. Ярлык Local, кнопка Production, commit и push
сами по себе не выполняют deploy.

Текущий публичный сайт работает на commit `6e901dc938aedab0369a620176bc462ac195d615`.
Позднее код этой ветки публикуется только по отдельной команде владельца.

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
4. На сервере: `python3 tools/deploy_code_release.py /path/to/archive.zip --sha256 <digest>`.
5. Скрипт останавливает только программу `aipedia`, делает online-backup
   `/srv/aipedia/data/aipedia.sqlite3`, переносит код и статику, выполняет
   `migrate` существующей серверной БД, поднимает только `aipedia` и проверяет
   `/healthz` на loopback.
6. Он **никогда** не копирует локальную SQLite поверх серверной базы и не
   удаляет `/srv/aipedia/data`, `/srv/aipedia/backups` и `/srv/aipedia/config`.

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
