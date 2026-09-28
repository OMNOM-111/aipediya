# AIpediya автономная история — аудит статусов 2026-09-27

Аудит выполнен только чтением публичного сайта и существующих отчётов,
с правкой Local документации/реестра. Production приложение, база и Cloudflare
cache не изменялись. Источники: `docs/RELEASE.md`, `docs/EXECUTION_STATE.md`,
`docs/DECISIONS.md`, `docs/timeline.json`, отчёты `docs/history/`, публичный
`/healthz` и сырой HTML. Владелец в текущем поручении подтвердил визуальную
приёмку системы версий.

## Все 15 карточек

| Карточка | Итог Local / Owner / Production | Основание |
| --- | --- | --- |
| Release #001 Chronology | ✓ / ✓ / ✓, done | `2026-09-20-chronology-release.md` |
| Release #002 Global catalog | ✓ / ✓ / ✓, done | `2026-09-22-global-catalog-release.md` |
| Release #003 Approved Local catalog | ✓ / ✓ / ✓, done | `2026-09-25-local-approved-release.md` |
| Release #004 GSD-1.0 | ✓ / ✓ / ✓, done | `2026-09-25-gsd-1-0-release.md` |
| Release #005 Search activation | ✓ / ✓ / ✓, done | `2026-09-25-naver-indexnow-activation.md` |
| Release #006 Search visibility | ✓ / ✓ / ✓, done | `2026-09-26-search-visibility-release.md` |
| Offline history viewer | ✓ / ✓ / —, done | `2026-09-26-offline-history-reference-match.md`; Local-only |
| Release #007 Catalog master v015 | ✓ / ✓ / ✓, done | `2026-09-26-catalog-master-v015.md` |
| Release #008 Catalog master v015 final | ✓ / ✓ / ✓, done | `2026-09-27-catalog-master-v015-final.md` |
| Paid Search Experiment | — / — / —, planned | Нет запущенной кампании; дата контрольного замера 30.09.2026 ещё впереди |
| Release #009 Adaptive UI | ✓ / ✓ / ✓, done | `2026-09-27-adaptive-ui-release.md` |
| Release #010 Tools chronology + CSP | ✓ / ✓ / ✓, done | `2026-09-27-tools-chronology-csp-release.md` |
| Release #011 Catalog 325/147 | ✓ / ✓ / ✓, done | `2026-09-27-catalog-325-147-release.md`; live `/healthz` = `9ddba83c176aa3f6793362d6345b797c76ddf987` |
| Release # / SemVer / mandatory history | ✓ / ✓ / —, done | 312 catalog tests PASS, 1 skip; validator/check/diff PASS; явная приёмка владельца в текущем поручении; отдельного Production deploy не было |
| AIpediya Cloudflare Web Analytics | ✓ / ✓ / ✓, done | Выпуск Tools/CSP `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`; beacon 200, `/cdn-cgi/rum` 204, no CSP load failure. Последующий аудит не был новым deploy |

Идентификаторы карточек уникальны: 15 из 15. В `review` и `in_progress`
карточек не осталось; `planned` — только Paid Search Experiment. Закрытый
Local-only этап не считается опубликованным. Работа Cloudflare Web Analytics
связана с уже существующим Release #010 и не получила второй Release #.
Поздний аудит трафика отдельно выявил блокировку StratForge; она не меняет
статус AIpediya и не входит в этот выпуск.

`current_local` и `current_production` остаются Release #011 · v0.11.0.
Публичный `/healthz` с обычным браузерным и social crawler User-Agent вернул
HTTP 200, `release=9ddba83c176aa3f6793362d6345b797c76ddf987`.

## Social-link preview, read-only

GET сырого HTML от `facebookexternalhit/1.1`: **22/22** языковых корня HTTP
200. Каждый содержит непустые локализованные `og:title` и `og:description`,
корректный собственный абсолютный `og:url`, одинаковый абсолютный `og:image`
`https://aipediya.com/static/share-card.png`, размеры `1200`×`630` и
`twitter:card=summary_large_image`. `/` и `/ru/` также вернули HTTP 200 для
обычного браузерного и Twitterbot User-Agent; обе страницы имеют
`cf-cache-status: DYNAMIC` и не показывают `Age`.

GET share-card с `facebookexternalhit/1.1`, `Twitterbot/1.0` и
`LinkedInBot/1.0`: HTTP 200, `image/png`, реальные размеры 1200×630,
30 277 байт, одинаковый SHA-256
`0d65357165767da5d029c42faae4046ec4498b476bd936409cc6a7470fa5e314`.
Локальный `static/share-card.png` имеет тот же SHA-256.
На Cloudflare изображение отдавалось `REVALIDATED`/`HIT` с корректными байтами;
`Cache-Control: public, max-age=14400`. Сайтового дефекта HTML/headers или
устаревшего Cloudflare-ответа не найдено. Если конкретная социальная сеть
показывает старую карточку для конкретного URL, вероятная причина — её
URL-specific preview cache; сам факт сбоя в конкретной сети этим аудитом
не воспроизводился. Cloudflare purge не требуется и не выполнялся.

Local-проверки после исправлений: 11/11 прицельных тестов истории и версий,
полный catalog suite — 313 тестов OK, 1 skip; Django check,
`tools/release_history.py --html` и `git diff --check` — PASS.

## Остаток

- Будущий Release #012 пока не зарезервирован для конкретного пакета.
- Paid Search остаётся планом без кампании и owner release approval.
- Визуальное открытие автономного `file://` HTML инструментом браузера было
  заблокировано его политикой; владелец подтвердил приёмку предшествующего
  этапа, обновлённый файл оставлен для повторного просмотра.
