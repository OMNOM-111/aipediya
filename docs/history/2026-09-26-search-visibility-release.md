# Search Visibility Optimization — выпуск 2026-09-26

**DEPLOYED AND VERIFIED**, 21:47 UTC. Основание: аудит
`outputs/01a0df19-0f44-7c40-8d47-280b013f5d84/AIpediya_Search_Visibility_Audit_2026-09-26.xlsx`,
45 URL из GSC и последующий Local P0. Разрешение владельца дано на этот
законченный поисковый пакет. GSD-1.0, каталог, master и дизайн сохранены.

## Что опубликовано

Commit `61adedd6ea5e6a0955d51d87374fa2fa9bcc7799`, tag
`release-2026-09-26-search-visibility-optimization-v2`, branch
`codex/search-visibility-update`. Code-only архив
`artifacts/code-release/aipedia-code-61adedd6ea5e.zip`, SHA-256
`8b8f2fa4bac3b6edce0868e4a963a795111d45695341c869ed824186e9ee625f`.
Промежуточный `7a582…` и первоначальный tag выпуска заменены финальной v2:
после первой публичной проверки убрано слишком широкое robots Allow карточного
`?page=`. Cloudflare Custom Purge применён **только** к `/robots.txt`, затем
публично подтверждён свежий ответ без широкого Allow.

Пакет содержит точные 45 GSC legacy исключений в robots (с `$`), 25
одношаговых 301 на чистые опубликованные карточки, 19 ответов 404 для снятых
или неизвестных сущностей, один `partial=rows` ответ 200 с `noindex`.
Любое добавление параметра к исключению опять блокируется. Убраны
параметрические SSR-ссылки на карточки, при этом UI восстанавливает страницу
списка после закрытия карточки. Диспетчер IndexNow принимает 301/302 для
уведомлений о прежних URL. Добавлены только четыре индексируемых URL: EN/RU
`/compare/model-context` и `/api-pricing`. Первая страница использует
подтверждённое окно контекста 97 опубликованных моделей, вторая — семь
сопоставимых пар официальных стандартных цен primary text-token одного
провайдера. Неизвестные цены и несопоставимые тарифы исключены; массовых
фасетных страниц нет.

## Проверки и безопасность выпуска

- Local: 268 catalog tests, 267 PASS и один ожидаемый skip; `node --check` PASS;
  `seo_report` — 10 193 sitemap URL (три Local-only dataset URL), 359 HTML
  страниц и 320 взятых в лимит обхода ответов без проблем. Лимит обхода не
  является доказательством завершения всего графа. Все 45 старых URL дают
  ожидаемые статусы. Браузерный сценарий `?page=2` → чистая карточка →
  закрытие → `?page=2` прошёл.
- Перед deploy: backup Production SQLite
  `/srv/aipedia/backups/aipedia-before-code-20260926T214700Z.sqlite3`;
  после — `/srv/aipedia/backups/aipedia-after-code-20260926T214700Z.sqlite3`;
  rollback дерева кода `/srv/aipedia/releases/before-code-20260926T214700Z`.
  Серверный preflight, целостность БД и FK проверены; миграций и изменений
  состояния публикации не потребовалось (0), 310 Models / 139 Tools сохранены.
  Local SQLite на сервер не переносилась. Затронут только контур AIpediya.
- Production `/healthz` подтвердил commit, `status=ok`,
  `environment=production`. `tools/search_visibility_qa.py`: 45/45 старых URL
  (25 × 301, 19 × 404, 1 × 200/noindex) без ошибок.
  `tools/gsd_public_check.py`: 34/34 PASS.
  `tools/gsd_production_qa.py`: 697 HTTPS-запросов, 1657/1657 проверок PASS,
  включая 22 локали, robots, sitemap, canonical/hreflang, JSON-LD, новые
  страницы и скрытые записи. Публичный sitemap: 22 child XML, 10 190 URL.

## До → после и поисковые кабинеты

| Показатель | До (аудит) | После выпуска, 2026-09-26 | Вывод |
|---|---:|---:|---|
| Известные GSC legacy URL с неправильной миграцией/недоступными сигналами | 45 | 45/45 ожидаемых публичных ответов; 0 ошибок QA | Технически исправлено; поисковику нужен recrawl |
| Публичные sitemap URL | 10 186 | 10 190 | +4 конечные EN/RU страницы, без фасетных дублей |
| Публичный Search QA | 1596/1596 на прежнем GSD baseline | 1657/1657 | Новые проверки включают миграцию и страницы |
| Local SEO report | P0: 10 189 URL, 355 HTML, 0 проблем | 10 193 URL, 359 HTML, 0 проблем | Local имеет ещё 3 выключенных на Production dataset URL |
| IndexNow unresolved | 330 до исправления диспетчера | 0 | 330 старых 301 URL + 4 новые страницы приняты scheduler |
| GSC performance | 41 impressions, 0 clicks, avg position 8.5 (24.09) | Те же последние доступные данные | Обновлённой статистики ещё нет |
| GSC indexed pages | Отчёт обрабатывается | Отчёт обрабатывается | Нельзя утверждать рост индексации |
| Bing performance | Подготовка данных | Подготовка данных | Нельзя утверждать рост кликов/позиций |

IndexNow до отправки: `sent_events=14845`, `urls_accepted=10076`,
`failed_unresolved=330`. Существующий Production scheduler обработал
**ровно 334** точечных события (330 подтверждённых старых 301 URL и четыре
новые страницы); после: `sent_events=15179`, `urls_accepted=10080`,
`active_pending=0`, `active_retry=0`, `failed_unresolved=0`. Исторические
ошибки не удалены. Массовый `--all` не запускался. GSC/Bing sitemap повторно
не отправлялись: они уже были зарегистрированы. GSC sitemap Success, но
показывает старые 10 032 discovered; Bing sitemap Success, 22 карты,
порядка 1,4 тыс. discovered, 0 errors/warnings. Naver требует восстановить
доступ к кабинету; доступного свежего состояния Yandex/Baidu нет.

Контрольная Google выдача после выпуска всё ещё показывала по бренд-запросу
`AIpediya AI models` на первом органическом месте старый `/?lang=en`, рядом
чистый `/` и старую параметрическую карточку: Google ещё не обновил выбранные
URL. Для `AI model comparison` AIpediya не было среди первых восьми видимых
органических результатов, как и в исходном замере. Это наблюдение, **не**
утверждение роста ranking. Базовый аудит содержит 52 более широких SERP-замера.

Осталось после повторного обхода снять в GSC/Bing выбор canonical, indexed
pages, ошибки, queries, страны, impressions, clicks и позиции; затем повторить
те же SERP-запросы. Authority/backlinks и конкурентоспособность контента
остаются отдельной долгосрочной задачей. Новые недоказанные страницы или
массовые doorway URL в этот выпуск не входят.
