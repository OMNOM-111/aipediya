# Выпуск полного Local-каталога — 2026-09-22

## Разрешение и границы

Владелец явно разрешил опубликовать текущее состояние Local на
`https://aipediya.com/` и потребовал сверить полноту данных и версию. Выпуск
идёт только по `docs/RELEASE.md`: без копирования Local SQLite, без изменения
StratForge, туннеля, секретов или других серверных программ.

## Исходное состояние Production

- commit: `6e901dc938aedab0369a620176bc462ac195d615`
- миграции каталога: `0001`–`0010`
- SQLite: `integrity_check=ok`, `foreign_key_check=0`
- published legacy ModelVersion: 255
- offers/accesses/evaluations/sources: 503 / 280 / 854 / 63
- ResearchRecord/Revision/PublicationRevision: 2163 / 2564 / 1888
- online-backup:
  `/srv/aipedia/backups/aipedia-before-global-catalog-20260922T062133Z.sqlite3`
- backup SHA-256:
  `b40fe0d0baeb05c941a2afbf5d10e7b02b12d24009eb09f7608f54ac7503b47d`

## Перенос данных

`catalog/migrations/0014_global_catalog_20260922.py` импортирует JSON payload
по natural keys и запускается атомарно. Перед первой записью проверяются точные
количества и SHA-256 наборов slugs, source URLs, offer keys и research IDs
исходной Production. Существующие записи обновляются без удаления; новые
исторические записи только добавляются. Reverse migration намеренно не удаляет
историю: полномочным rollback-источником остаётся online-backup.

Payload: `catalog/migrations/data/global_catalog_20260922.json`, SHA-256
`5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2`.
Это переносимый набор данных, а не SQLite; секретов и локальных путей нет.

## Проверка кандидата

- 82 Django tests: PASS
- Django check: PASS
- migrations check: PASS
- JavaScript syntax: PASS
- `git diff --check`: PASS
- изолированная миграция точного Production baseline: PASS
- semantic comparison всего экспортируемого каталога с Local: PASS
- candidate SQLite integrity/FK: `ok` / 0

## Результат публикации

Ожидает фиксации точного release commit, deploy и публичной проверки. Этот
раздел обновляется после фактической публикации; подготовка архива сама по себе
не считается выпуском.
