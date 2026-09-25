# Активация Naver и IndexNow — 2026-09-25

Разрешение владельца: операции только AIpedia (`/srv/aipedia`, backup, выпуск кода и
конфигурации, сервис `aipedia`, Production QA). StratForge, туннель и чужие сервисы не
затрагивались; Local SQLite не копировалась; перезапускалась только программа `aipedia`.

## Выпуски

| Commit / tag | Что | Backup перед выпуском | Результат |
|---|---|---|---|
| `160be0f37037` / `release-2026-09-25-naver-verification` | SSR meta `naver-site-verification` | `aipedia-before-release-2026-09-25-naver-verification-20260925T220148Z.sqlite3` + штатный `aipedia-before-code-20260925T220156Z` | `deployed-origin-verified`; миграций нет; публикация 304/138 без изменений |
| `386d4aaafd00` / `release-2026-09-25-indexnow-root-key` | ключ IndexNow в корне (`/<key>.txt`) и `keyLocation` в корне | `aipedia-before-release-2026-09-25-indexnow-root-key-20260925T220707Z.sqlite3` + штатный `aipedia-before-code-20260925T220709Z` | `deployed-origin-verified`; миграций нет; 304/138 |

Gate: 217 и 219 тестов PASS соответственно.

## Naver

`curl https://aipediya.com/` содержит
`<meta name="naver-site-verification" content="9c99ee04834598097c2ba9b6a809819418e5d74d">`.
Нажатие Verify и отправка sitemap в Naver Search Advisor — за владельцем: авторизованной
сессии Naver в доступных исполнителю браузерах не было (Claude in Chrome не подключён).

## IndexNow

- Конфигурация: `/srv/aipedia/supervisord.conf`, `[program:aipedia]` дополнен
  `AIPEDIA_INDEXNOW_KEY` (32 hex, сгенерирован на хосте) и `AIPEDIA_INDEXNOW_ENABLED="1"`;
  копия прежнего файла — `/srv/aipedia/backups/supervisord.conf.before-indexnow-20260925T220242Z`;
  `supervisorctl update aipedia` — перезапущена только `aipedia`.
- Первая попытка: `keyLocation` в `/indexnow/<key>.txt` → HTTP 422 (ключ в подпапке
  авторизует только URL этой подпапки). 5 016 событий помечены `failed`, вторая партия не
  отправлялась. Исправлено выпуском `386d4aaafd00`.
- После исправления: первая повторная партия → 403 (ключ ещё не принят сервисом; прямой
  запрос к Bing с тем же ключом — 200). Малая партия через ~1 минуту — 200.
- Итог: `notify_indexnow --all` поставил 10 032 URL (= публичный sitemap); отправлено тремя
  POST (100 + 5 000 + 4 932) — **10 032 accepted (HTTP 200), 0 pending, 0 retry**;
  5 016 строк `failed` (422) — история первой попытки, их URL затем приняты.
  Для этой разовой начальной отправки использован `--no-live-check`: состояние
  Production подтверждено сразу перед ней (QA 1596/1596, sitemap = реестр). Принятие ≠
  индексация.

## Проверки после

`/healthz` = `386d4aaafd00`; integrity ok; FK 0; Models 304/763, Tools 138, Offers 555,
Evaluations 881, ContentTranslation 42 260, Revision 4 813; outbox 15 048 строк;
Production GSD QA **1596/1596**; public sitemap 10 032.

## Автоматическая отправка (2026-09-25 22:41Z)

- Штатный механизм периодических задач AIpedia — программы собственного supervisord
  (`aipedia-backup` = цикл `sleep`). Cron на хосте нет. Добавлена программа
  `aipedia-indexnow` → `/srv/aipedia/bin/indexnow-dispatch-loop`
  (`deploy/indexnow-dispatch-loop.sh`, владелец `aipedia`, 0700): каждые 300 с
  `flock -n /srv/aipedia/data/indexnow-dispatch.lock … indexnow_dispatch --send --batch 1000`;
  только pending/retry события, dedup/retry/live-gate диспетчера без изменений, без `--all`.
  Окружение — копия `[program:aipedia]` + `AIPEDIA_INDEXNOW_INTERVAL_SECONDS="300"`.
- Конфигурация до изменения: `/srv/aipedia/backups/supervisord.conf.before-indexnow-scheduler-20260925T224101Z`.
  `supervisorctl update aipedia-indexnow` запустил только новую программу; `aipedia`,
  `aipedia-backup`, `aipedia-tunnel` не перезапускались.
- End-to-end: `notify_indexnow --url https://aipediya.com/methodology` (реальная
  публичная страница без изменений) → событие 15049 `pending` 22:41:37Z → очередной
  плановый цикл 22:46:02Z → IndexNow HTTP 200, `sent`. Публичные данные не менялись;
  строка журнала оставлена как аудит.
- Лог: ключ IndexNow в `indexnow.log`/`indexnow-error.log` — 0 вхождений. Проверка
  блокировки: вторая попытка при удержанной блокировке — `SECOND_RUN_BLOCKED`.
- Outbox после теста: sent 10 033, failed 5 016 (история попытки с 422), pending 0.
