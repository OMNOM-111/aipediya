# Автономный просмотр истории продукта — 2026-09-26

## Ревизия 2 — Local-only, 2026-09-26

Владелец не принял первую визуальную редакцию: она наследовала общий `base.html`
и стили публичного каталога. Исправление выполнено отдельными
`templates/product_history_standalone.html` и `static/product-history-offline.css`.
Автономный файл теперь рендерится без внешней оболочки: две равные карточки Local и
Production; GSD-01…GSD-10 как стабильные номера исходных возможностей; шесть записей
ленты (включая отдельные опубликованные GSD-1.0 и Search activation и отдельную
Local-only правку истории); детальная панель для сделано/проверено/решение владельца/
остаток/следующий шаг/публикация. Отдельно остаются RU/EN, тёмная тема по умолчанию,
локальный theme preference, горизонтальная прокрутка и встроенные источники.

Публичный Production commit независимо проверен по HTTPS `/healthz` 2026-09-26:
`634778807b2e82ca52dea1de150ea0810950d644`, `status=ok`; он совпадает с
`docs/RELEASE.md`. Устаревший `ed103a3` остаётся в карточке исторического выпуска
25.09. Production не менялся. Локальная автономная история не требует серверного
deploy.

Текущая проверка: `manage.py test catalog --settings=aipedia.test_settings` —
237 PASS, 1 skip; `System check` чистый; отдельные тесты истории 4/4. Generated
`timeline.html` — 304 041 bytes, 6 release/task cards на edition, 12 source
templates, 0 external asset tags; оба inline JS скрипта прошли `node --check`.
Static checks подтвердили точку открытия, обе среды, языки, theme toggle, source
markup и отсутствие email, числовых tab IDs и UUID session IDs в generated HTML.
Порт Local 18810 не слушал; shortcut по-прежнему направлен на проектный
`timeline.html` без аргументов. В этот раз браузерный DOM и полная отрисовка
не осматривались: инструмент Browser Use блокирует `file://`, обход не выполнялся.
Новая визуальная приёмка владельцем ожидается; 196 ms из первой проверки были лишь
запуском Windows file association, а не полной отрисовкой.

Поиск проверен настолько, насколько позволили текущие средства. `/`, `robots.txt`,
`sitemap.xml`, `/healthz`, RU/AR страницы, модель GPT-5.3-Codex, инструменты Codex и
Claude Code — 200; sitemap index перечисляет 22 карты, проверенные RU/AR/EN карты
содержат по 456 URL; sample содержит canonical, 23 hreflang, x-default и правильный
RTL. Naver meta присутствует в server HTML. Публичный DNS TXT resolver возвратил
Google/Yandex root значения. Live GSC, Bing и Cloudflare вкладки вызовы Browser Use
отклонили со ссылкой на сохранённое user-permission правило, при прежних allow
настройках; Yandex Browser в подключённом списке отсутствовал. Кабинетные метрики,
дубликаты Cloudflare DNS, полный DNS record set, текущий IndexNow key-file HTTP
статус и outbox не заявляются свежепроверенными. Naver verification/sitemap ранее
подтверждены скриншотами владельца; recovery request принят по сообщению владельца,
номер не показан, email ожидается. Browser Use отказ остаётся отдельным инцидентом.
Подробная таблица и content coverage находятся в `docs/SEARCH_DISCOVERY.md`.

Следующий шаг: владелец визуально проверяет эту редакцию при открытии ярлыка; после
доступа к кабинетам снимается первый snapshot индексации/показов Google, Bing и
Yandex. Baidu / Китай остаётся отдельным следующим этапом и здесь не начинался.

---

## Причина

Существующий ярлык `AI_CONTEXT/AIpedia — История сайта.lnk` запускал
`tools/local/start-local.ps1 -OpenPath /ru/history/`. Launcher подготавливал
Local-каталог, выполнял `migrate` и `check`, затем выбирал/запускал Waitress и
открывал `http://127.0.0.1:<port>/ru/history/`. Поэтому просмотр зависел от Local,
Python/Django и PowerShell.

## Изменено

- Добавлен сборщик `tools/build_product_history.py`: он рендерит существующий
  Local history view на Django test client из `docs/timeline.json`, allowlist
  `catalog/product_history.py` и разрешённых документов-источников. Базу не
  меняет и Local-сервер не запускает.
- Сгенерирован `timeline.html` в корне рабочей папки `C:\Users\dimon\Documents\AIpedia`,
  не в отдельной копии/архиве AI_CONTEXT. Данные этапов, карточки, подробности,
  источники, RU/EN, тема и локатор языков встроены. Картинки, CSS и JS встроены;
  CSP запрещает сетевые fetch/resource-загрузки. Обновление HTML запускается
  автоматически перед обычной сборкой AI_CONTEXT.
- Существующий ярлык в `AI_CONTEXT` теперь указывает напрямую на корневой
  `timeline.html`, без PowerShell arguments. Local `/ru/history/` и его
  source routes сохранены.
- История и новые статусы не содержат фото удостоверения, реквизитов или личных
  полей Naver recovery. В источниках автономной страницы email-адреса и ID
  сессии дополнительно редактируются для приватности.

## Проверки

- `manage.py test catalog --settings=aipedia.test_settings`: **224 PASS, 1 skip**;
  Django test-client проверил существующие RU/EN/RTL Local routes и source allowlist.
- Generated HTML содержит 4 milestones на каждую из двух editions и 10
  встроенных templates source-документов; CSS/JS/SVG встроены. Статический аудит
  нашёл 0 внешних asset requests; `connect-src 'none'` и `default-src 'none'`; все
  3 inline scripts прошли `node --check`.
- `tools/pack_ai_context.py` штатно пересобрал HTML после обновления
  `docs/EXECUTION_STATE.md`; актуальный Naver recovery status появился в output,
  а видимое UTC-время обновления поставлено в HTML.
- Штатный stop script подтвердил остановку только AIpedia Local на
  `127.0.0.1:18810`; PID-файл отсутствует, порт после остановки закрыт. Запуск
  существующего `.lnk` через Windows file association создал в Edge вкладку
  `file:///C:/Users/dimon/Documents/AIpedia/timeline.html` с заголовком страницы.
  Target ярлыка — корневой HTML, arguments пустые, поэтому ярлык не запускает
  PowerShell или Local.
- Вызов Windows file association вернулся за **196 ms**; это время передачи файла
  default browser, не время полной отрисовки. Чтение/взаимодействие с `file:///`
  через Browser Use отказано политикой URL (разрешены только http/https; tool
  запретил alternate browser/CDP/command workaround). Поэтому фактическая визуальная
  отрисовка, работа кликов/переключателя темы/языков и секундомер в браузере не
  проверены; требуется ручная визуальная приёмка владельцем.
- Production deploy не выполнялся.

## Разделение статусов

- Реализация: Local-only автономная сборка; Production не менялся.
- Owner approval: не заявлен и не выведен из автоматических тестов.
- Production: действующий production release не содержит эту доработку.
- Следующий шаг: после последней сборки владелец заново открывает ярлык, чтобы
  получить актуальное содержимое, и визуально проверяет карточки, документы-источники,
  языковой переключатель и тему; фактическое время полной отрисовки замеряется в
  браузере владельца. Production release не разрешён.

