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

- Release commit: `43e2d3feba57cf67084cc2e3774c86a72ce361b5`
- GitHub: `origin/main` получил release commit
- code archive SHA-256:
  `33be8e0054f1909bcb2ad891caae8558f61c58fc03932a80b3542af6199c3625`
- deploy status: `deployed-origin-verified`; Local SQLite не копировалась
- Production migrations: `0011`–`0014` PASS
- `/healthz`: `status=ok`, `environment=production`, release совпадает
- SQLite: `integrity_check=ok`, `foreign_key_check=0`
- Production: 763 published моделей, 138 published инструментов, 555 offers,
  1205 accesses, 881 evaluations, 343 sources, 2900 ResearchRecord, 3590
  ResearchRevision, 4354 Revision, 3049 PublicationRevision и 158
  ToolPublicationRevision
- нумерация: модели 001–304 без пропусков; инструменты 001–017 без пропусков;
  неизвестные даты остаются без номера
- контрольные записи PASS: retired Jurassic-1 Jumbo, current API GPT-6 Astra,
  open-weight Llama 3 70B Instruct, TTS Eleven v3, ChatGPT, Grok Voice API
- server backups:
  `/srv/aipedia/backups/aipedia-before-code-20260922T065139Z.sqlite3` и
  `/srv/aipedia/backups/aipedia-after-code-20260922T065139Z.sqlite3`
- previous app: `/srv/aipedia/releases/before-code-20260922T065139Z`

Public Browser PASS: бренд `AIpediya`, 763/138, 001–018, флаги, RU/EN,
dark/light, retired-панель и переход Models→Tools при активных фильтрах.
Browser console warn/error: 0. Публичные ответы: models 200 / 0.288 s total;
tools 200 / 0.414 s total.
