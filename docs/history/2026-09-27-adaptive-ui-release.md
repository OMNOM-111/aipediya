# Выпуск release-2026-09-27-adaptive-ui — Adaptive Interface / Mobile & Tablet UX

- Дата выпуска: 2026-09-27, deploy 16:16:46Z, публичная проверка завершена ~16:30Z.
- Разрешение владельца: 2026-09-27 — «Разрешаю опубликовать на Production утверждённое
  текущее состояние AIpediya из `main`, commit `aa48e11`, строго по `docs/RELEASE.md`».
  Приёмка Local — `D-2026-09-27-owner-acceptance-adaptive-ui`.
- Release commit: `aa48e11bad7326340463654e33ba5e89769042b9`, tag
  `release-2026-09-27-adaptive-ui`. Предыдущий Production: `a51c0a1aed2f63047b0203b208eccf8def458ae7`
  (`release-2026-09-27-catalog-master-v015-final`).
- Исполнитель серверной фазы: Claude Code в режиме Manual (подтверждение команд владельцем),
  по `D-2026-09-27-claude-server-permission-mode`; первая попытка в `Auto` ожидаемо
  заблокирована средой, сервер тогда не затрагивался.

## 1. Состав

Code-only выпуск: адаптивная вёрстка каталога (телефон — карточки строк и панель под шапкой;
планшет — сворачивание колонок и drawer; desktop — таблица и панель от 1280 px; ultrawide —
оболочка `max(2400px, 60vw)`), Filter/Sort sheets, touch 44 px, safe-area, RTL; исправления
подгрузки на телефоне (было 200 из 321), языковых ссылок при открытой панели, вкладки при
«назад», вытягивания документа скрытыми подписями цены; состояние `review` в истории сайта.
Миграций, моделей и данных каталога нет (`git diff a51c0a1..aa48e11` — static, templates,
tests, docs, `catalog/product_history.py`). Манифест `data/release_state.json` — контроль,
321 Models / 143 Tools, 0 изменений.

## 2. Local и архив

- Тесты `main` на `aa48e11`: 302 — 301 OK + 1 skip (`fcntl`, POSIX); `manage.py check` чист;
  `node --check`; responsive-матрица 89 сценариев 320×568…5120×1440 — page overflow 0,
  ошибок консоли 0; smoke 16/16; 89/89 снимков = утверждённый Local.
- Архив `artifacts/code-release/aipedia-code-aa48e11bad73.zip`, 328 файлов, SHA-256
  `51d7a45239b26c5400f3c0187960c2227ae7a2f04864d47fb6311c0eb524b453`; без SQLite, секретов,
  `.env` (только tracked `*.env.example`), XLSX. Распакованный архив — 302 теста (301 OK + 1 skip).
  Локальный `--dry-run` PASS. `tools/verify_isolated_release.py` не применялся: исторический
  инструмент выпуска 22.09 (зашитые ожидания `global_catalog_20260922.json`); обязательная
  проверка — серверный preflight на онлайн-копии (ниже). Этот инструмент пересобирает архив по
  тому же пути: digest фиксировался после него.
- Базовая линия Production до выпуска: `/healthz` `a51c0a1…`, `final_check.py` 207/207,
  `gsd_public_check` 34/34, `catalog_master qa --production` PASS.

## 3. Сервер (только контур AIpedia)

- Read-only: хост `1cdfd28f030e`, пользователь `stratforge`, `/srv/aipedia` на месте, программа
  `aipedia` RUNNING, loopback `/healthz` и `app/BUILD.json` = `a51c0a1`.
- Архив в `/tmp/aipedia-release-aa48e11/`, SHA-256 на сервере совпал.
- Preflight на онлайн-копии `/srv/aipedia/backups/aipedia-preflight-adaptive-ui-20260927T161617Z.sqlite3`:
  integrity `ok`, foreign keys 0; 321 / 143; 660 цен, 1250 доступов, 906 оценок, 844 страны,
  43 120 переводов; архив распакован с проверкой 328 хэшей; `check` чист; новых миграций нет;
  `sync_publication_state apply` (dry-run) — 0 изменений; отпечаток до и после совпал.
- Серверный `--dry-run` PASS (`copies_sqlite=false`).
- Deploy `deploy_code_release.py … --publication-state data/release_state.json` (16:16:46Z):
  backup до выпуска `/srv/aipedia/backups/aipedia-before-code-20260927T161646Z.sqlite3`;
  миграций нет; манифест `apply=True`, 0 изменений; статус `deployed-origin-verified`,
  `copied_sqlite=false`; предыдущий код `/srv/aipedia/releases/before-code-20260927T161646Z`;
  после — `/srv/aipedia/backups/aipedia-after-code-20260927T161646Z.sqlite3`. StratForge и
  другие программы не затрагивались.
- После: loopback `/healthz` и `BUILD.json` = `aa48e11`; `aipedia` RUNNING; живая БД
  (read-only) — integrity `ok`, foreign keys 0, отпечаток (321 / 143, хэши номеров моделей и
  инструментов, цен, оценок, переводов) идентичен backup до выпуска.

## 4. Публичная проверка https://aipediya.com

- `/healthz`: release `aa48e11bad73…`, production.
- `final_check.py` 207/207 (sitemap 321 / 143, счётчики, флаги, цены, оценки);
  `gsd_production_qa --commit aa48e11…` 1657/1657, 0 ошибок; `gsd_public_check` 34/34;
  `catalog_master qa --production` PASS (master = Local = Production).
- Responsive (headless Chrome со своим обычным User-Agent, без обходов защиты): 89 сценариев
  320×568 … 5120×1440, EN/RU/DE/AR/FA/JA/ZH, тёмная и светлая темы — page overflow 0,
  вертикальный overflow app-shell 0. Взаимодействия: подгрузка Models 321/321 (телефон,
  планшет RU, desktop, ultrawide DE), Tools 143/143; панель на телефоне / drawer / desktop —
  клик по строке, клик внутри, меню языка над панелью, Escape, X, клик вне, back/forward;
  прямые URL (EN `?tab=pricing`, AR Tools, JA); Filter-sheet (применение при закрытии, возврат
  контролов), Sort-sheet, поиск — 15/15 функциональных PASS. Обычный браузер (встроенный):
  RU телефон, Sort-sheet, Escape, светлая тема, панель под шапкой, X — PASS.
- Консоль: новых ошибок нет. Единственное сообщение — Cloudflare (на краю) вставляет
  `static.cloudflareinsights.com/beacon.min.js`, CSP приложения `script-src 'self'` его
  блокирует; CSP и middleware с `a51c0a1` не менялись — поведение существовало до выпуска.
- Снимки: Production отличается от Local только подвалом (на Production нет Local-ссылок
  «Local / Production», «Site history»), дизайн каталога тот же.
- Доказательства (git-ignored): `artifacts/adaptive-ui/release/` (preflight, dry-run, deploy,
  postcheck, публичные проверки) и `artifacts/adaptive-ui/production/` (матрица, взаимодействия).

## 5. Откат

Не требуется. При необходимости — по `docs/RELEASE.md` «Откат кода»: остановить только
`aipedia`, вернуть `/srv/aipedia/releases/before-code-20260927T161646Z` на место
`/srv/aipedia/app`, запустить `aipedia`; БД не менялась (0 изменений публикации, миграций нет).

**Статус: Local PASS → Owner PASS → GitHub synced → Production PASS → Public PASS.**
