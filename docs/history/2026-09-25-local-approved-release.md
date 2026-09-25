# Выпуск release-2026-09-25-local-approved

- Дата (UTC): 2026-09-25, deploy 03:21Z.
- Commit / tag: `ed103a3ff1637d24ad104e843a44f80a2c82ba78` /
  `release-2026-09-25-local-approved`. Предыдущий Production: `e8a4df761a87`.
- Процесс: `D-2026-09-25-release-process` — Production приведён к
  утверждённому владельцем Local-состоянию.
- Архив: `aipedia-code-ed103a3ff163.zip`, sha256
  `93c2fe3fdee26e7bbf0db744e59ff961f16feb37d3c6e4abde0f7c6ddbc68547`
  (сверен локально, на сервере и с commit), 252 файла, без SQLite/секретов.

## Changelog

- Полная локализация на 22 языка.
- Корректный публичный счётчик каталога.
- Проверенный набор 304 публичных Models (Tools — 138).
- Сортировка по умолчанию newest → oldest.
- Фильтры, поиск, клик по строке, правая панель.
- Улучшения responsive/mobile и RTL.
- 459 внутренних research-моделей сохранены вне публичного каталога.

## Шаги на сервере (только AIpedia)

1. Backup: `/srv/aipedia/backups/aipedia-before-release-2026-09-25-local-approved-20260925T032119Z.sqlite3`
   (integrity ok) + штатный `aipedia-before-code-20260925T032156Z.sqlite3`.
2. Dry-run `deploy_code_release.py … --publication-state data/release_state.json` — OK.
3. Deploy: остановлена только `aipedia`; `migrate` — 0016, 0017;
   `sync_publication_state apply --apply` — 459 моделей скрыто, 0 инструментов;
   `aipedia` запущена, `/healthz` = `ed103a3ff163`; статус
   `deployed-origin-verified`, `copied_sqlite=false`. Предыдущий код —
   `/srv/aipedia/releases/before-code-20260925T032156Z`; после —
   `aipedia-after-code-20260925T032156Z.sqlite3`.
4. `aipedia-backup` и `aipedia-tunnel` не перезапускались; StratForge не трогался.

## Боевая БД до → после

| | до | после |
| --- | --- | --- |
| Models публичные | 763 (459 без номера) | 304 (№1–304) |
| Models скрытые | 0 | 459 (№305–763, внутренние) |
| Tools публичные | 138 (121 без номера) | 138 (№1–138) |
| ModelVersion всего | 901 | 901 |
| Offers / Evaluations | 555 / 881 | 555 / 881 |
| ContentTranslation | 42 260 | 42 260 |
| Revision | 4 354 | 4 813 (+459 снимков `save()`) |
| Журнал публикации | — | +459 `assign_catalog_number`, +459 `sync_release_state`, +121 tool `assign_catalog_number` |

Integrity ok, нарушений внешних ключей 0.

## Проверки

- Тесты: 174 PASS (полный набор, рабочая копия).
- Local QA и public HTTPS QA (`https://aipediya.com`) — один и тот же аудит,
  0 fails: Models 304 / Tools 138, newest-first, номера 1–304, sitemap 304/138,
  все 459 скрытых — 404 и нет в списке/поиске/sitemap, 22 локали — 200,
  `lang/dir` (ar/fa RTL), 0 кириллицы вне ru/uk.
- Строки каталога Production (slug, дата, номер, порядок) совпадают с Local
  побайтно (одинаковый md5).
- Браузер Production: AR (RTL, панель, Escape), RU Tools (панель, X),
  UK mobile (без горизонтального скролла).
- Известное, не регрессия: `<title>` не локализован вне RU; при горизонтальной
  прокрутке таблицы заголовок «Model» перекрывает «Developer».
