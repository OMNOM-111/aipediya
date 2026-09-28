# Пассивная аналитика AIpediya и StratForge — аудит 2026-09-27

Проверено в авторизованной панели Cloudflare и в настоящих desktop-браузерах
27.09.2026 около 20:00 UTC. Это аудит; нового выпуска кода нет.

## AIpediya

- Web Analytics Automatic Setup уже работал. Реальный `https://aipediya.com/`
  загрузил `static.cloudflareinsights.com/beacon.min.js/v31...` с HTTP 200 и
  отправил same-origin `POST /cdn-cgi/rum` с HTTP 204; ошибок CSP/JS в
  консоли не было. В панели Web Analytics за последние 24 часа появились
  15 page views и 11 visits (включая наши контрольные открытия), доступны
  страны, referrers, paths, devices, browsers и Core Web Vitals.
- HTTP Traffic и Security Analytics показывают реальные запросы: около
  34,83 тыс. HTTP requests и 30,67 тыс. Security Analytics events за
  отображённые последние 24 часа. Эти счётчики не являются числом людей;
  окна, фильтры и задержка панелей различаются.
- AI Crawl Control содержит запросы известных операторов: GPTBot,
  OAI-SearchBot, Googlebot, Amazonbot, Applebot, ChatGPT-User, BingBot,
  ClaudeBot, Claude-User, Claude-SearchBot, Meta-ExternalAgent,
  PerplexityBot и др. Это наблюдаемые user-agent-категории, не доказательство
  индексации или переходов людей. Common Crawl в показанном срезе не увиден.
- Авторизованный Google Search Console для `aipediya.com` работает:
  sitemap принят, 10 032 обнаруженных URL; за показанные 3 месяца 41
  impression, 0 clicks. Bing Webmaster принял sitemap и показывает около
  1,4 тыс. найденных URL, но Search Performance ещё готовит данные.
  Microsoft Clarity предлагает начальную установку и не показывает
  действующего проекта. В Production HTML обнаружен только Cloudflare
  analytics script; GA/GTM/Clarity script не найден.
- Публичный каталог открылся на desktop без новых ошибок. Настройки
  Cloudflare не менялись.

## StratForge

- Cloudflare Web Analytics в зоне `stratforges.com` первоначально был OFF.
  Пробное Automatic Setup внедрило beacon в реальную страницу
  `https://app.stratforges.com/ui/index.html`, но браузер отклонил загрузку
  скрипта по CSP (`Network.loadingFailed`, `blockedReason: csp`): ответа
  beacon и `POST /cdn-cgi/rum` не было. Настройка возвращена в OFF;
  повторная загрузка страницы прошла без новой CSP-ошибки. Значит RUM
  по-прежнему **не работает**; ON без успешного beacon оставлять нельзя.
- Конкретное место исправления перед отдельным Local/Canary/Production
  выпуском: `app/server.py`, `STATIC_CSP` около строк 306–312, а также
  `<meta http-equiv="Content-Security-Policy">` на строке 6 всех
  `app/static/aurora/*.html`. В `script-src` добавить оба узких источника
  `https://static.cloudflareinsights.com/beacon.min.js` и
  `https://static.cloudflareinsights.com/beacon.min.js/` для versioned URL;
  `connect-src 'self'` уже разрешает `/cdn-cgi/rum`. После Local и Canary
  QA нужен отдельный утверждённый выпуск; затем включить Automatic Setup
  и подтвердить beacon 200, RUM 204 и поступление page views в панель.
- HTTP Traffic, Domain Dashboard и Security Analytics работают. По фильтру
  `Host = app.stratforges.com` за последние 24 часа около 29,65 тыс.
  requests; `Path contains /api/` — около 27,17 тыс. (≈92%),
  `/ws/market-data` — около 1,4 тыс. (≈5%). Значит как минимум ≈96%
  запросов этого hostname — API/WebSocket, включая polling, heartbeat,
  health и автоматику; эти requests нельзя называть посещениями.
  Вся зона дополнительно содержит canary и ssh-canary hosts, которые
  необходимо исключать при оценке Production web UI. Dashboard также
  показывает страны, hostnames, paths, browsers, user agents, cache,
  bandwidth и Security actions.
- AI Crawl Control доступен, но в показанном срезе 0 crawler requests.
  Получение статистики известного AI crawler на этом домене фактически
  подтвердить нечем; Allow/Block не менялись.
- Production browser показал desktop Aurora shell `[BETA] v0.10.0-beta.97`
  и HTML-ссылки на отдельные `/ui/*.html` страницы. Внутри есть History API
  `replaceState` для фильтров/вкладок; Cloudflare заявляет автоматический
  учёт soft navigations, но на этом приложении он не проверен из-за CSP.
  API, WebSocket и серверные/Telegram операции RUM не измеряет; Telegram
  webview сможет попасть в RUM лишь при загрузке того же proxied HTML и
  успешном выполнении beacon. Корневой `https://stratforges.com/` при
  отдельном браузерном открытии не разрешился в DNS; рабочая поверхность —
  `app.stratforges.com`.
- В текущих авторизованных GSC/Bing аккаунтах видна только AIpediya; это
  не исключает другую учётную запись StratForge. В Production HTML Aurora
  и проверенном фронтенд-коде GA/GTM/Clarity scripts не обнаружены;
  собственная support telemetry есть, но не является агрегированным
  счётчиком рекламной аудитории. UI shell после отката открылся с HTTP 200
  и без новых ошибок консоли; карточки данных показывали «Загрузка…»,
  поэтому сквозная функциональность приложения этим аудитом не подтверждена.

## Границы измерения и изменения

Cloudflare Web Analytics даёт browser visits/page views и country, referrer,
path, device разрезы там, где beacon выполняется. HTTP/Security Analytics
измеряет запросы, включая API, polling, bots и проверки. На Free AI Crawl
Control распознаёт известных self-identifying crawlers по User-Agent; он
не выявляет надёжно маскирующихся роботов. Beacon может не сработать из-за
CSP, блокировщика, отключённого JS или WebView; он не доказывает
человеческое внимание, видимость рекламного баннера или уникальных людей
между устройствами. Рекламные показы/клики потребуют отдельного агрегатного
измерения после согласования размещения; не добавляли cookies, IDs или
персональное отслеживание.

Единственное изменение Cloudflare — временное Enable, затем восстановление
Disable для StratForge после воспроизводимого CSP-FAIL. AIpediya, DNS,
Tunnel, SSL, WAF/Bot Fight, robots.txt, crawler Allow/Block, приложения,
Production SQLite, секреты и подписки не менялись.

Local документация и история собраны штатным `tools/pack_ai_context.py`;
`manage.py test catalog --settings=aipedia.test_settings`: 308 OK,
1 expected skip на финальном реестре; targeted
`catalog.tests.test_product_history`: 7 OK. GitHub commit/push не выполнялись.
Визуальное открытие автономного Local `timeline.html` через `file://`
заблокировано политикой браузера; сборка и тесты истории прошли.

Источники Cloudflare:

- https://developers.cloudflare.com/web-analytics/faq/
- https://developers.cloudflare.com/web-analytics/get-started/web-analytics-spa/
- https://developers.cloudflare.com/ai-crawl-control/features/manage-ai-crawlers/
