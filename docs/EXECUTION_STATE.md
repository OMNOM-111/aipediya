# Текущее состояние AIpedia

## 29.09 — Daily Catalog Update #016 / v0.14.0 опубликован, Production PASS (GitHub Copilot)

- Создана и продолжена та же Timeline-карточка `DAILY-CATALOG-UPDATE-2026-09-29`, Release #016 / `v0.14.0`; новых карточек не создавалось. Исполнитель карточки записан как GitHub Copilot, старт `2026-09-29T20:42:02Z`. Владелец в поручении 29.09 явно разрешил Production #016 после успешной Local-проверки; повторное подтверждение не запрашивалось.
- Master/Local: через `tools/daily_catalog_update_2026_09_29.py` добавлены 6 PUBLISHED Models — Claude Sonnet 5.5, Eleven v4, Eleven v4 Turbo, Holo4-27B, Holo4-35B-A3B, Holotron4-30B-A3B — и 2 PUBLISHED Tools — Cue и Manus 2.0. Meta Enterprise Platform и Claude Haiku 5.5 не опубликованы. Exact master/Local records для shutdown IDs `gpt-3.5-turbo-instruct`, `babbage-002`, `davinci-002`, `gpt-3.5-turbo-1106` не найдены; семейные/чужие записи не закрывались вместо них, `ft-babbage-002` и `ft-davinci-002` не менялись.
- Local QA: `catalog_master refresh/check` OK; trial sync на копии PASS; рабочий `sync-local --apply` создал 8 записей, затем `catalog_master import`, `check` OK, `qa` PASS (331 Models / 149 Tools, queue 198, warnings 17, errors 0), SQLite integrity OK, FK 0. Full catalog suite — 341 tests OK (1 skip). Browser Local touched-card QA: 8/8 direct URLs 200, #326–#331 Models и #148/#149 Tools в таблице/панелях, no console/network errors, no overflow.
- Production: archive `aipedia-code-7c18e9f078f4.zip`, SHA-256 `4abb3c4bb76ee248902d0d459787a0bc6106555d952f89f463a73e1c8e145f6a`; `/healthz` release `7c18e9f078f457d313ef69b8c70de564c050e231`. Server preflight, isolated preflight, dry-run, deploy, `verify-release`, server catalog, `catalog_master qa --production`, GSD Public 34/34, full Production QA 1657/1657 and public touched-card browser QA PASS. Backup before deploy: `aipedia-before-code-20260929T213309Z.sqlite3`. Production catalog is now 331 Models / 149 Tools; evaluations unchanged 5010 / public 2741.
- Timeline #016 closed as `done`, Production ✓; `timeline.html` rebuilt. GitHub `origin/main` and tag `release-2026-09-29-daily-catalog-update` point to release commit `f52d7a479995f3ccc1664aae0341e911a5d13f03`; deployed release id remains the verified code-candidate `7c18e9f078f457d313ef69b8c70de564c050e231`. **Изменено:** master XLSX, Local SQLite, release manifests, release tooling checks for #016, Timeline/report/status/history tests and generated history. **Не завершено:** финальный AI_CONTEXT rebuild and clean closeout commit still pending in this turn. **Следующим выполнить:** rebuild AI_CONTEXT, commit/push final closeout if files change, then handoff.

## 29.09 — Release #015 / v0.13.2 опубликован, Performance PASS; Local-only история отдельно

- **Production:** точный code commit `b8f07026630124f179fd386d60cddbc9beaf2751`, tag `release-2026-09-28-performance-audit`; архив SHA-256 `19436aab5928860c412c9f1ddf4afd2174062d1de6f0e286ee65f88b467527eb`. Server preflight → online backup → isolated trial → dry-run → deploy → `/healthz` PASS. Backup `aipedia-before-code-20260929T194250Z.sqlite3`; SQLite integrity `ok`, FK 0, 325 Models / 147 Tools и доказательные таблицы неизменны; catalog plan не применялся.
- **Public QA:** GSD Production 1657/1657, public check 34/34, `catalog_master qa --production` PASS. Chromium на публичном сайте 88/88: 22 локали, Models/Tools, desktop/375 px, открытые карточки, Back/Forward, поиск, фильтр, sort, infinite loading, темы и RTL; 0 console/network/HTTP errors.
- **Performance:** Models `/` TTFB 484→347 мс, `/es/` 472→325 мс, обычная Model 468→360 мс, тяжёлая 474→353 мс (медианы трёх live GET). Local matched CPU 1 719→1 016 мс и Python peak allocations 37,89→19,81 МиБ для Models root. PID `aipedia` после выпуска при спокойном трафике 3,2–3,6% одного ядра; при 4 параллельных Chromium группах 57,77%, без ошибок страниц. Общий load сервера не приписывался AIpediya. Неизвестный класс исторического посетителя больше не блокирует исправление. Телеметрия безопасных агрегатов сохранена выключенной по умолчанию.
- **Local / GitHub:** проверенный #015 Local gate: browser 88/88, catalog suite 340 tests (1 skip), GSD 33/33, master check/qa PASS. Отдельный Local-only экран истории завершён в commit `856d80ce0aa19550c0f7c7afdeba36250ee329bc`: `/ru/history/` и `timeline.html` показывают #001–#015, 4/4 браузерных сценария и 60 открытий карточек PASS, финальный catalog suite 341 tests (1 skip), GSD Local 33/33. После fast-forward основной Local `127.0.0.1:18810` штатно поднят на #015: SQLite сохранена, 325 Models / 147 Tools, миграций нет; на нём повторены история 4/4 и 60/60, GSD 33/33. Карточка `HISTORY-LOCAL-SHELL-2026-09-29` завершена технической/визуальной проверкой исполнителя; нового владельческого approval не заявлено. GitHub `origin/main` и точный release tag сохраняют это состояние после финального push; post-release commit не входит в уже опубликованный архив #015. **Изменено:** Production только код #015 с нулевым изменением каталога; внутренний экран истории только в Local/GitHub. **Не завершено:** по данному поручению ничего. **Следующим отдельным пакетом:** только при новой задаче и отдельном разрешении владельца; текущий выпуск закрыт.

## 29.09 — предыдущий снимок #015 до полного browser gate

- Worktree/ветка `codex/aipedia-performance-015` объединена с опубликованным #014; `main`, его release tag и Production этим этапом не менялись. После новой Local-телеметрии полный Django suite: 340 tests OK (1 skip), дополнительный bounded-group тест targeted 6/6 PASS. Карточка #015 / v0.13.2 остаётся `in_progress`, owner approval и Production release отсутствуют.
- Два новых read-only замера только процесса `aipedia` после #014: 4,03% и 3,07% одного CPU, RSS 190 920–191 492 KiB, пять потоков, 0 предупреждений очереди, 1 и 0 новых 404 за 30 секунд. Общая load average машины около 2,9–3,3 не принадлежит только AIpediya; другие приложения не исследовались. Прошлые пики AIpediya до 94,2% одного CPU были реальными. Per-process I/O и фактический path/User-Agent mix остаются недоступны по существующей телеметрии.
- Новый парный read-only профиль того же Local SQLite: Models root 1 910 → 1 085 мс wall, 1 719 → 1 016 мс CPU, 264/23 → 261/26 мс SQL/queries, 37,89 → 19,81 МиБ пиковых Python-выделений. Размер ответа одинаковый; другие маршруты с неизменённым кодом не приписываются оптимизации. Optional 10-секундная per-PID телеметрия классов route/UA/status, request/SQL time, CPU/RSS/I/O реализована и по умолчанию отключена; query, cookie, IP, raw UA и slug не сохраняются. На отдельном Local Waitress 18811 проверены затронутые маршруты, GSD 33/33, секретные sentinel не попали в лог. Накладные расходы microbenchmark: 36–50 мкс wall на запрос. Контролируемые 16 одновременных запросов Local: 16/16 200, 135,8% одного CPU точного PID за 11,6 с, активное окно агрегатора 138,31%; это воспроизводит механизм app CPU burst, но не устанавливает источник исторического Production пика.
- Публичные шесть последовательных запросов к текущему #014 дали TTFB 0,256–0,633 с, 200; это спокойный baseline до #015, не сравнение после выпуска. Cloudflare Dashboard требует входа, access log AIpediya отсутствует; доля crawler traffic и точная причина исторического ~94% по route/UA не установлены. Отчёт и сырые данные: `docs/history/2026-09-28-performance-audit-local.md`, ignored `artifacts/` в worktree.
- **Изменено:** только ветка #015: Local-only middleware/тесты/профилировщики, Timeline и отчёт аудита. **Не завершено:** независимая атрибуция route/UA/bot трафика исторического Production пика, browser gate 88/88 после Python-оптимизации, Local визуальная приёмка и отдельное разрешение на выпуск #015. **Следующим выполнить:** получить безопасную историческую read-only Cloudflare HTTP Analytics выборку либо отдельно разрешённый будущий сбор AIpediya-only агрегатов; сопоставить пик с PID/окнами/route/SQL, завершить Local browser QA и представить конкретный #015 на приёмку без публикации по одному Local speedup.

## 29.09 — Release #014 / v0.13.1 опубликован и проверен

- **Local:** владелец принял рабочий `127.0.0.1:18810` и прежнюю browser-матрицу 88/88; перед выпуском повторно пройдены 44/44 locale roots, 44/44 открытые Model/Tool и 1 936 language links. Исправление общего `syncLanguageLinks()` входит в проверенный baseline `77e7f53cd8aa621b392d52d5b5ae8851ab77456c`.
- **Production:** штатный code-only deploy #014 выполнен из архива `aipedia-code-1ac95d75b7a6.zip`, SHA-256 `2d3859774837a7d9f4a256554b153811c3da8105195bb6afda0240da07e7588a`. `/healthz` показывает `1ac95d75b7a6d80eb24301f352a88275c28d4bce`, программа `aipedia` RUNNING. Preflight, online trial, backup, dry-run, deploy, `verify-release` PASS; catalog tables не менялись. Pre-deploy backup: `aipedia-before-code-20260929T130406Z.sqlite3`.
- **Public QA:** `gsd_production_qa` 1 657/1 657 PASS (697 запросов), `gsd_public_check` 34/34 PASS, `catalog_master qa --production` PASS. Публичный браузер: Español `/es/` через меню; Model/Tool сохраняются при смене языка; Back/Forward, desktop/mobile 375 px, RTL ar/fa PASS, console errors 0, критических failed network requests 0. Финальный полный Django suite 333 OK (1 skip), история после последнего текста 11/11 PASS. Timeline #014 переведена в `done` и собрана в `timeline.html`. Отчёт: `docs/history/2026-09-29-language-switch-release.md`.
- **GitHub:** `main` / `origin/main` и tag `release-2026-09-28-language-switch` хранят закрытие #014; точный deployed code-candidate id указан выше и отличается от Git SHA документационного closeout. **Изменено:** release report, Timeline, указатель Production, тесты истории и read-only сравнение backup для code-only #014. **Не завершено:** отдельный #015 Performance Audit; его ветка `codex/aipedia-performance-015` не включена в #014. **Следующим выполнить:** на #015 установить root cause нагрузки измерениями на общей машине с разделением приложений и внешнего трафика, исправить в Local и представить отдельный пакет на приёмку.

## 29.09 — владелец принял Local #014 и разрешил конкретный выпуск

- Владелец явно принял реальную Local-проверку, свежие 44/44 roots и 44/44 panels, 1 936 language links, полный Django suite и прежнюю browser-матрицу 88/88. Ограничение браузерного инструмента на loopback не блокирует #014. Разрешён именно Release #014 / v0.13.1 на проверенном кодовом baseline `77e7f53cd8aa621b392d52d5b5ae8851ab77456c`; производительная ветка #015 в выпуск не входит.
- Изолированная проверка первого архива обнаружила устаревшее ожидание `owner_approved=false` в тесте истории после фактического решения владельца. Исправлен только regression `catalog/tests/test_product_history.py`, чтобы проверять допустимый переход #014 `review → done`; runtime-код языкового контура не менялся. Первый архив не выпущен, кандидат пересобирается из того же base commit.
- **Local:** штатный сервер остаётся на 127.0.0.1:18810. **GitHub:** `main` / `origin/main` перед подготовкой кандидата равны `77e7f53`, рабочее дерево было чистым. **Production:** ещё #013 / `5ba1e566`; публикация только после archive/isolated verification, server trial, backup и dry-run. **Изменено:** в Timeline #014 записаны решение владельца и exact base revision, а эта запись фиксирует переход к release phase. **Не завершено:** архив, Production deploy и Public QA. **Следующим выполнить:** собрать code-only candidate из `77e7f53` без catalog plan, провести preflight и полный public browser/HTTP QA, затем закрыть карточку и Git tag только при PASS.

## 29.09 — повторная приёмка языкового #014 после недоступного Local

- После просьбы владельца проверить самостоятельно браузерный инструмент повторно отклонил Local tab политикой URL и явно запретил другой браузерный контур/обход. Свежая самостоятельная read-only проверка живого Local: 44/44 Models/Tools roots и 44/44 representative Model/Tool panel URLs отвечают 200 без redirect, с верными `lang`/`dir`, строками таблиц/открытыми карточками; 1 936 серверных menu `href` совпали с canonical URL, 0 расхождений. Языковые Django regression 3/3 PASS. Это HTTP/SSR, не новый browser-click PASS. Local после команд продолжает слушать 127.0.0.1:18810. До снятия буквального условия собственного browser-прохождения Production #014 остаётся без deploy.
- Владелец отклонил первую визуальную приёмку: `http://127.0.0.1:18810/es/` показывал `ERR_CONNECTION_REFUSED`. Проверка подтвердила: 18810 не слушал, PID-файл указывал на отсутствующий PID `37480`. Штатный `start-local.ps1` запускает Waitress дочерним процессом и ждёт его; прежний запуск из временной командной сессии не пережил handoff. Лог не фиксирует точное событие завершения старого PID, поэтому это вероятный механизм, а непосредственно доказанная причина отказа — отсутствие процесса/слушателя.
- Local запущен тем же штатным `start-local.ps1` в отдельном скрытом launcher, а не на временном QA-порту. После изоляции performance WIP возвращён чистый `main` с языковым #014; только AIpediya Local штатно перезапущен. На момент проверки PID Waitress `32860` слушает **127.0.0.1:18810**; `/healthz`, `/`, `/es/`, `/ru/`, `/tools/`, `/es/tools/` отвечают 200. Проверка повторена после завершения команд запуска. Local SQLite и master не заменялись.
- Владелец лично подтвердил, что после первого восстановления ES/RU открываются и выбор Español через меню из RU/EN и из открытой Model сохраняет карточку. После возвращения чистого #014 запрошена повторная визуальная приёмка именно этого состава. Браузерный инструмент Codex запретил доступ к loopback URL политикой безопасности и прямо запретил обход другим browser surface; исполнитель не выдаёт HTTP-проверку за собственный свежий браузерный прогон. Постоянная матрица 88/88 browser PASS была выполнена на том же коде #014 до сбоя жизненного цикла Local; после повторного запуска её текущая доступность подтверждается HTTP и владельцем, но не повторным исполнением инструмента.
- Read-only `python tools/server.py preflight` на Production прошёл: всё ещё опубликован #013 commit `5ba1e566`; выпуск #014 не выполнялся. Владелец дал условное разрешение именно на #014 после восстановления и проверки Local. До окончательной визуальной приёмки и разрешения указанного browser-tool ограничения карточка остаётся `review` / `owner_approved=false`; tag и архив не создавались.
- Серьёзный аудит нагрузки и изменение серверной пагинации изолированы в ветке `codex/aipedia-performance-015` (GitHub HEAD `92852316`), отдельная Timeline-карточка #015 / v0.13.2 имеет `in_progress` и не входит в #014. Измеренный baseline: CPU процесса `aipedia` 12.8–94.2% одного ядра, RSS около 202–240 МиБ, в пике четыре worker thread заняты, 11 предупреждений очереди за 30 секунд при нуле новых 404; Local Models root 1 634 → 861 мс после SQL-пагинации в ветке #015. Ветка прошла 331 catalog tests (1 skip), check, master check/qa, 44/44 Local HTTP roots и GSD Local 33/33; её post-change 88-case browser gate ещё не пройден. Точный route/UA mix Production не установлен: access log отсутствует, per-process I/O/network counters недоступны. Подробности и границы вывода: `docs/history/2026-09-28-performance-audit-local.md` на ветке #015.
- При подготовке code-only #014 обнаружен отдельный дефект штатного release wrapper: он подставлял старый catalog-plan, а server trial preflight принимал только #012/#013. `tools/server.py` теперь передаёт план только явно, `tools/server_release_preflight.py` испытывает #014 без плана на online backup и сверяет SHA-256 всех `catalog_*` таблиц; regression tests проверяют отсутствие неявного плана и обнаружение изменения перевода. Полный `manage.py test catalog`: 332 OK / 1 skip; `gsd_public_check --local`: 33/33 PASS; Local SQLite integrity ok, FK 0, 325 Models / 147 Tools. Production не изменялась.
- **Local / GitHub / Production:** штатный Local слушает 127.0.0.1:18810; языковой UI-код #014 не менялся. GitHub `origin/main` содержит release-prep commit `fc035cd` и обновление чистой Timeline `ed5b4e1`; рабочее дерево после упаковки AI_CONTEXT чистое. Полезные QA JSON/log сохранены в ignored `artifacts/`. Production остаётся #013, серверная база и программа не изменялись. **Не завершено:** согласование браузерного допуска для #014, release archive/tag/deploy/public QA; отдельно #015 browser gate и атрибуция валидного Production-трафика. **Следующим выполнить:** получить ответ владельца по замене недоступного browser-прогона текущими проверками, затем по `docs/RELEASE.md` подготовить и испытать точный кандидат; для #015 продолжить безопасную телеметрию и QA после #014.

## Переключение 22 языков — Release #014 / v0.13.1, Local REVIEW (Codex, 2026-09-28)

- Создана отдельная карточка `LANGUAGE-SWITCH-2026-09-28` до правок кода. Исходный `main` / `origin/main`: `8b904f3`, рабочее дерево было чистым; Production оставлена на #013 / v0.13.0.
- Публичное воспроизведение: клик пункта Español в раскрытом меню с `/`, `/tools/` и открытых Model/Tool дал `/es/`, `/es/tools/` и соответствующие `/es/models/<slug>` / `/es/tools/<slug>`, HTTP 200, таблица и карточки видны, ошибок консоли 0. Дополнительный проход кликом по меню: 22/22 Models root и 22/22 Tools root ответили 200 с нужными `<html lang>` и строками.
- Найден воспроизводимый дефект того же языкового контура: при сохранённом в cookie `es` быстрая ссылка Español рядом с меню оставалась `/es/` после открытия карточки через History API, хотя пункт меню уже был `/es/models/<slug>`; клик сбрасывал карточку и показывал корень. В Production исходный `/models/longcat-2-5-preview` → быстрая ссылка `href=/es/` → итог `/es/`, HTTP 200, без redirect, ошибок консоли и критических failed requests 0. Исправлен общий `syncLanguageLinks()` в `static/site.js`: обновляются и ссылки меню, и ссылка сохранённого языка без особого условия для `es`.
- Добавлены `catalog/tests/test_language_switch.py` и `tools/locale_switch_browser_qa.py`; README и `requirements-dev.txt` описывают воспроизводимый запуск. Local `manage.py test catalog`: 330 OK / 1 skip; `gsd_public_check --local`: 33/33 PASS; `node --check` и `git diff --check` PASS. Браузерный Español в Local прошёл Models/Tools на 1440/375 px, включая карточку, X/Escape/клик вне, Back/Forward, поиск, фильтр, сортировку, догрузку, тему; тест сохранённой ссылки после исправления также PASS.
- Отдельный точный Local-клик по исправленной быстрой ссылке на 375 px: `/models/longcat-2-5-preview` → обе ссылки Español `/es/models/longcat-2-5-preview` → итоговый URL совпал, HTTP 200, карточка открыта, console errors 0, failed requests 0. Контроль текущего опубликованного #013 read-only: `gsd_production_qa` 1657/1657 PASS; это baseline Production, а не проверка нового Local-кода. Обнаруженное при чтении исторического документа устаревшее указание baseline #012 исправлено в `docs/PRODUCT_HISTORY.md` по фактическому #013 из Timeline/RELEASE.
- Новый browser regression запущен read-only против неизменённого Production #013 (`artifacts/locale-switch-production-es-baseline.json`): оба случая Español на 375 px закономерно FAIL — сохранённая ссылка Models `/es/` вместо `/es/models/longcat-2-5-preview`, Tools `/es/tools/` вместо `/es/tools/alice-ai-pro-business`. Тот же тест на исправленном Local PASS; `docs/RELEASE.md` теперь требует 88/88 browser menu gate для следующих code releases.
- Полная Local browser-матрица `artifacts/locale-switch-local-22.json`: 88/88 PASS (22 локали × Models/Tools × 1440/375 px), 1 712 проверок интерфейса, 264 реальных перехода через меню, 0 redirect, 0 non-200, console errors 0, failed requests 0, HTTP errors 0. `ar` и `fa` прошли RTL/overflow на обоих размерах; модели догружали строки, у Tools все 147 строк помещаются на первой странице. Timeline #014 переведена в `review`: Local ✓, Owner —, Production —; `current_local` указывает на #014, `current_production` остаётся #013.
- После изменения Python-истории Local Waitress штатно перезапущен только скриптами `stop-local.ps1`/`start-local.ps1`. `prepare_local_catalog.py` сохранил текущую SQLite, миграций 0; живой `/ru/history/` показывает #014 `review`, `/history/source/2026-09-28-language-switch` отвечает 200, `/es/` — 150 строк, `/es/tools/` — 147. Повторный браузерный Español Models/Tools на 375 px после рестарта — 2/2 PASS, console errors 0, failed requests 0 (`artifacts/locale-switch-post-restart-es.json`).
- **Изменено:** `static/site.js`, `catalog/tests/test_language_switch.py`, `tools/locale_switch_browser_qa.py`, `catalog/product_history.py`, `catalog/tests/test_product_history.py`, `catalog/tests/test_release_history.py`, `templates/product_history_standalone.html` (убраны whitespace-only строки в SVG нового значка), `docs/timeline.json`, `docs/history/2026-09-28-language-switch-local.md`, `docs/PRODUCT_HISTORY.md`, `docs/RELEASE.md`, `requirements-dev.txt`, `README.md`, этот статус и производный `timeline.html`. Полезные JSON/log/screenshots QA сохранены в ignored `artifacts/`; отменённый неполный log нашего прогона удалён как производный. Local SQLite и master не менялись, посторонних dirty/untracked файлов на старте не было. Повторный полный `manage.py test catalog`: 330 OK / 1 skip; адресные тесты истории после сборки — 11 OK; финальный Local `gsd_public_check` 33/33 PASS, `release_history --html` PASS, `node --check` и `git diff --check` PASS. Local-код и документация зафиксированы commit `5ba0a4e` и отправлены в `origin/main`; после финального документационного commit проверяется чистый Git и пересобирается AI_CONTEXT. **Не завершено:** визуальная приёмка владельца; Production не авторизована, release tag только зарезервирован в карточке и не создавался. **Следующим выполнить:** владелец просматривает Local #014; после принятия и отдельной команды на конкретный выпуск — процедура `docs/RELEASE.md`.

## Reconciliation / cleanup #013 — Production и Public QA PASS (Codex, 2026-09-28)

- Владелец поручил полное закрытие и заранее разрешил выпуск именно этого проверенного cleanup/reconciliation состояния. Timeline-карточка `release-2026-09-28-reconciliation-cleanup`, Release #013 / `v0.13.0`, прошла `in_progress` → `review` → `done`; Local ✓, Owner authorization ✓, Production ✓, Public QA ✓. Карточка исходного read-only аудита также закрыта после выполнения follow-up. Постоянное Definition of Done записано в `AGENTS.md` и `docs/PRODUCT_HISTORY.md`.
- Отчёт и индивидуальные решения по 19 значениям: `docs/history/2026-09-28-reconciliation-cleanup.md`. Исходно 1 067 `unsupported` (954 ложных SQL PK, 113 содержательных). После сравнения по natural keys: 0 ложных, 0 текущих `unsupported`, 513 явных `intentional_master_only` (включая 402 значения Score с хранением до трёх знаков). Применено 13 поддерживаемых публичных операций: 11 точных Access URL, один общий провайдер Kimi API и одна категория Furniture Assembly. Исправлено 6 ячеек canonical Master с Changelog.
- Master и Local до изменения сохранены в `backups/reconciliation-cleanup-20260928/`. Пробное применение на копиях Local и Production PASS; release-plan на снимке Production содержит ровно 13 writes, повторный `apply-plan` idempotent. Рабочий Local применил 13 changes, `catalog_master check` OK, `qa` PASS, repeat sync-plan: 0 writes, 0 unsupported; SQLite integrity ok, FK 0; `manage.py check` 0 issues. Полный catalog suite: 327 OK, 1 пропуск на Windows.
- Штатный Local перезапущен, `/healthz` OK. Браузер: 325 Models / 147 Tools, все 11 новых ссылок видны в затронутых карточках; Checks, RU/EN/ar RTL, тёмная/светлая темы, мобильные 375 px и desktop 1440 px без горизонтального переполнения; browser console errors 0. Production baseline `artifacts/catalog-release-20260927/production-baseline-20260928T234044Z.sqlite3` совпал с исходным снимком SHA-256 `8393660832892e1f422358be892b86bb2050eba9745de82b6b972da093837cce`.
- Release commit/tag `5ba1e566338fc17d9b8965d3be180bc1df268e2e` / `release-2026-09-28-reconciliation-cleanup` отправлены на GitHub; архив SHA-256 `1ce9f36d3400785dc9c98fb6f8a71ce38c57048ae520bda919619f784bfd290d` (369 файлов, SQLite 0). `tools/server.py` preflight, точный online trial, dry-run, deploy и verify-release PASS. Backup перед deploy: `aipedia-before-code-20260928T235552Z.sqlite3`; `/healthz` подтверждает release commit, сервис `aipedia` RUNNING. Только `catalog_access`, `catalog_benchmark`, `catalog_service` изменились фактически; 325/147 и номера сохранены, integrity ok, FK 0. Postdeploy snapshot SHA-256 `565085f9818873bde279e783d3b0680a4afc1e5f6f57cf3027ee5172ce25af29`.
- Public: `catalog_master qa --production` PASS, GSD Public 34/34 PASS, полный Production QA 1657/1657 PASS (697 запросов, 472 скрытые записи, 0 ошибок); реальный браузер подтвердил 11 ссылок и Kimi/Moonshot, RU/EN/ar RTL, mobile/desktop, dark/light, overflow 0, console errors 0. Повторный Master ↔ Production plan: 0 writes / 0 unsupported, 513 намеренных отличий. После выпуска штатный `import --production` обновил лишь восемь наблюдаемых `On Production` флагов и Meta; `catalog_master check` OK, `qa` PASS.
- Рабочие файлы классифицированы: четыре Windows cache-копии перемещены без удаления в ignored quarantine; локальные `.claude/launch.json`, ярлык истории и `data/research/` оставлены и явно ignored; официальные исторические материалы сохранены. Изменено: Master XLSX, `catalog/master_sync.py`, `catalog/catalog_master.py`, тесты, Timeline, документация, release-plan и правила. Local / GitHub / Production: проверенный Local соответствует опубликованному #013; GitHub содержит release commit/tag и финальную документацию; Production подтверждён Public QA. Не завершено в рамках #013: ничего. Следующим выполнить только новые отдельно поставленные задачи; плановый paid-search эксперимент остаётся отдельной карточкой.

## Read-only аудит 1 067 unsupported master ↔ Production — исторический baseline, закрыт #013 (Codex, 2026-09-28)

- Отдельная Local Timeline-карточка `UNSUPPORTED-MASTER-PROD-AUDIT-2026-09-28`: первоначально `in_progress` → `review` без выпуска; после реализации follow-up #013 и Public QA закрыта как `done` без собственного Release #.
- Штатный серверный read-only preflight: `/healthz` release `d349d6de42cb…`, программа `aipedia` RUNNING. Новый снимок Production в игнорируемом `artifacts/catalog-release-20260927/production-baseline-20260928T193212Z.sqlite3`: SHA-256 `8393660832892e1f422358be892b86bb2050eba9745de82b6b972da093837cce`, integrity OK, FK 0. `catalog_master sync-local` только dry-run на снимке: 0 writes, 1 067 unsupported (971 public, 96 service).
- Разбор по полям и provenance — `docs/history/2026-09-28-unsupported-master-production-audit.md`; игнорируемые детальные артефакты `artifacts/catalog-release-20260927/unsupported-audit-20260928-{plan,analysis}.json`. 954/1 067 — ложное сравнение разных SQL PK при совпадающих значениях по natural key; содержательных расхождений 113. Классы: 13 вероятно полезных, 93 Master-only/research, 955 ошибочных сравнений/скрытый дубль, 6 требуют проверки.
- На этапе первоначального аудита были изменены только документация, Timeline-карточка и Local allowlist отчёта `catalog/product_history.py` с обновлением счётчиков `catalog/tests/test_product_history.py`; Master XLSX, рабочая Local SQLite и Production данные тогда не изменялись. Следующий этап #013 разобрал все 19 индивидуальных пунктов, устранил исходные предупреждения и завершил проверку в Production; отдельного хвоста у аудита нет.

## Evaluation Evidence — Release #012 / v0.12.0, Production и Public QA PASS (Codex, 2026-09-28)

- Владелец в переданном Codex handoff явно принял последнее проверенное Local-состояние и разрешил именно его выпуск в Production. Handoff вызван лимитом Claude. Карточка `EVAL-EVIDENCE-AUDIT-2026-09-27` продолжена без дублирования; Local ✓, Owner Approved ✓, Production ✓, Public QA ✓.
- Baseline: `main` HEAD `2fd442cb487c2c9ff2ea2acc00070a0c17164f47` плюс перечисленные ниже незакоммиченные файлы; Local `127.0.0.1:18810/healthz` OK. Master после штатного refresh SHA-256 `014c9f23b60a6182664f7d4cddc1841d6b7dc2f2c0f1a867cbec5f23035f5110`. Рабочая Local SQLite не переносится на сервер.
- Local gate повторён: `catalog_master refresh`, `check` OK, `qa` PASS, `manage.py check` 0 issues, 315 тестов OK (1 skip), SQLite integrity ok, FK 0, повторный `sync-local` dry plan 0 записываемых изменений (113 прежних unsupported). Browser smoke: девять указанных карточек, RU/EN/ar, desktop/375 px, dark/light; Checks открыт, page overflow 0, console errors 0. MTEB показан компактно (3 + раскрытие).
- Production baseline read-only через `python tools/server.py preflight/status/catalog/snapshot`: `/healthz` release `9ddba83c176aa3f6793362d6345b797c76ddf987`, service `aipedia` RUNNING, 325 Models / 147 Tools, integrity ok, FK 0. Online snapshot: `artifacts/catalog-release-20260927/production-baseline-20260928T161029Z.sqlite3`, SHA-256 `896ccef92ffa70c02f30069a138ffece7d1e3981d83ce4076c12c6f0e4b2d642` (ignored Local artifact).
- Точный release-plan от этого снимка: `data/release/eval-evidence-20260928/catalog_plan.json`, SHA-256 `6673697d432f80ffbfe9a4b45145a2566e6373604e4bd2358ad22dcdd92e17a3`; 4 104 новых Evaluation, 16 изменений visibility, 0 изменений Models/Tools/Offers/Access/номеров. Зависимости новых строк: +563 Source, +947 Benchmark. Trial на отдельной копии Production: 4 120 writes, QA PASS, повторный plan 0, integrity ok, FK 0, Evaluations 906 → 5 010, public evaluations 851 → 2 741. Production не менялась.
- Документационная проверка «7 против 6»: в текущем `stage2/REPORT.md` и этом статусе уже записаны шесть перечисленных моделей; правка master не нужна.
- Изменено на этапе выпуска: `docs/timeline.json` (существующая карточка #012, owner approval), `tools/server.py`, `tools/server_release_preflight.py`, `tools/server_compare.py` (preflight для текущего baseline и candidate), этот статус, точный release-plan. Ранее незакоммиченные UI, master, локализации, Timeline и тесты сохраняются как принятый Local baseline; посторонние untracked и runtime-файлы не включаются.
- Candidate archive `artifacts/code-release/aipedia-code-d349d6de42cb.zip`, release id `d349d6de42cbe49dd55134a7ca792f6bce85ab7e`, SHA-256 `faf755db0497b0e3c718ab3b655edb46d51499936a7f247d8e93a280ed0b3127`: manifest 357 файлов, SQLite/секреты 0, isolated suite 315 OK (1 skip), серверный preflight PASS на online backup и dry-run PASS.
- Production deploy выполнен штатным `tools/server.py deploy`: backup `/srv/aipedia/backups/aipedia-before-code-20260928T163724Z.sqlite3`, previous app `/srv/aipedia/releases/before-code-20260928T163724Z`; 4 120 writes, publication state 0 changes, перезапущена только программа `aipedia`. `/healthz` подтвердил `d349d6de...`, service RUNNING. Серверная SQLite integrity ok, FK 0. `verify-release` PASS: изменились только `catalog_source` (+563), `catalog_benchmark` (+947), `catalog_evaluation` (+4104 и 16 visibility); Models/Tools/Offers/Access/прочие фактические таблицы не менялись.
- Public QA PASS: `catalog_master qa --production` PASS, `gsd_public_check` 34/34 PASS, полный `gsd_production_qa` 1657/1657 PASS (697 запросов, 472 скрытые модели, 0 failures), браузер 12 карточек/локалей RU/EN/ar/fa/de/zh-hans, RTL, desktop/phone, dark/light: overflow 0, console errors 0; публичный MTEB 123 дополнительных результата раскрывается и сворачивается. Post-deploy online snapshot SHA-256 `849aa8ed312fa284256c63ab07a13c9a7c6c995d5bf5c990bc27f56c88da9a1f`, integrity ok, FK 0, повторный sync-plan 0 writes.
- Ограничение: post-deploy master ↔ Production показывает 1 067 неподдерживаемых расхождений (971 public, 96 service). Ровно столько же было в сохранённом **pre-deploy** Production snapshot; они не вызваны этим выпуском и не входят в утверждённый evaluation diff. Рабочий Local имеет 113 таких расхождений. Не скрывать эту разницу при отчёте об «точном Local-состоянии»; не менять посторонние цены/происхождения/платформы без отдельного плана.
- Timeline #012 закрыта штатным `finalize_release_history.py` после живого `/healthz` и полного Public QA; Local ✓, Owner Approved ✓, Production ✓, Public QA ✓. Git candidate commit `655fb90185b76a8597b53a5829db4e8e8c63dc97`, tag `release-2026-09-28-eval-evidence`; проверены 356 файлов deployed-архива против tag после нормализации Git, 0 несовпадений.
- Изменено: отчёт выпуска, `docs/RELEASE.md`, существующая карточка Timeline и тесты истории приведены к фактическому Production #012. GitHub `main` содержит release commit `655fb90185b76a8597b53a5829db4e8e8c63dc97` и post-release документационный commit; tag `release-2026-09-28-eval-evidence` отправлен и указывает на release commit. Исправлен указатель пакета AI_CONTEXT: manifest теперь различает deployed release id `d349d6de...` и Git commit `655fb90...`; сборка автономной истории не переписывает файл без изменения источников. Не завершено в рамках текущего выпуска: ничего; сохраняются 1 067 прежних unsupported master ↔ Production различий и отдельная очередь evidence-пробелов. Следующим отдельным этапом подготовить план по этим существовавшим ранее различиям и источникам, не смешивая его с закрытым #012.

Живой паспорт локальной разработки. Не дублирует `AGENTS.md`.
Отчёты законченных выпусков — `docs/history/`.
Пакет для нового чата собирается командой `\.\.venv\Scripts\python.exe tools/pack_ai_context.py` и **не** редактируется как независимый источник.

## Evaluation Evidence — окончательный Local готов, REVIEW (ждёт визуальной приёмки), 2026-09-28

- Владелец принял направление этапа 2 и подтвердил политику «Результаты разработчика»
  (публично, с явной маркировкой, не как независимая проверка, вне Independent Rating;
  `DECISIONS.md` обновлён). Карточка: `in_progress` → `review` после полного Local QA.
- **Расхождение 280 против 277 объяснено:** 159 + 33 + 88 = 280 считали по статусам; из 33
  research-only у 5 был только статус без чисел (Jurassic-1 Jumbo, Jurassic-2 Ultra/Mid/Light —
  HELM; Gemini 3.8 Live), а 2 карточки имели числа только в составном индексе вне трёх
  классов (Kimi K3 (max) — ECI 158; Qwen3.8 2.4T — индекс Artificial Analysis, Public=NO):
  280 − 5 + 2 = 277. Исправлено по существу: ECI у Kimi K3 (max) — округлённый дубль ECI
  родительской Kimi K3 (`evaluation-807`, 157.63) на карточке конфигурации → Public=NO и
  пометка `superseded_duplicate_of` (все 15 дублей ECI помечены и исключены из счёта);
  индекс AA у Qwen3.8 2.4T учтён как research-only. Метрики считаются из одного поля
  `final_class` / `has_numeric_evidence` факта.
- **Последний адресный проход по моделям без чисел** (официальные отчёты, карточки, статьи,
  таблицы, GitHub/HF, посты): найдены и добавлены (+95 наблюдений, Evaluations 5 751 → 5 846) —
  GPT-4o Transcribe и GPT-4o Mini Transcribe (FLEURS, 33 языка, значения из aria-label
  графика OpenAI), GPT-Live 1 и GPT Realtime 2.1 (Tau3/Tau Banking/Full Duplex Bench из
  SVG-графиков OpenAI; график Artificial Analysis исключён), Jurassic-1 Jumbo (white paper
  AI21, таблица 6), PLaMo 2 8B (технический отчёт PLaMo 2) — всего **6 моделей**; из них 4 ранее
  не имели чисел (GPT-Live 1, GPT Realtime 2.1, Jurassic-1 Jumbo, PLaMo 2 8B), у обеих GPT-4o
  Transcribe уже были замеры конкурентов: 277 + 4 − 1 (дубль ECI у Kimi K3 (max)) = 280. Проверены без результата:
  Apertus v1.5 70B (отчёт ещё не вышел), MagenticBrain (блог MagenticLite — только схемы),
  LongCat-2.5-Preview, Hunyuan3D-2mini, Wan2.2 TI2V-5B, Nova 2 Pro (PDF недоступен),
  GPT Transcribe / Live Transcribe (цифра только в посте на X), прочие — статусы с источниками.
- **Итог (325 PUBLISHED, взаимоисключающие классы):** independent_public 126;
  independent_and_developer 50; independent_research_only 17 (из них 4 — только статус);
  developer_reported 91; no_published_numerical_evaluation 23; exact_version_not_found 8;
  identity_ambiguous 9; not_applicable 1. Публичная независимая (любая) 159/325 (48,9%).
  **Любая проверенная численная оценка 280/325 (86,2%)**; без чисел 45 = 23 + 8 + 9 + 1 + 4.
  По категориям (independent → any): text 54,3% → 89,1%; image 67,7% → 91,9%;
  video 47,2% → 72,2%; audio 0% → 79,5%; other 0% → 62,5%.
- **UI:** блоки «Независимая проверка» / «Результаты разработчика» (пояснение «Результаты
  опубликованы разработчиком модели. Это не сторонняя независимая проверка.») / строки
  research-only и замеров конкурентов без баллов / «Статус оценок» с локализованной строкой
  статуса по `final_class` (в т.ч. «Есть результаты разработчика и независимые исследования
  без права публикации баллов» — вместо противоречивого «только…»). Все новые подписи
  переведены на 20 языков + RU/EN (`catalog/ui_translations.py`, тест
  `test_evaluation_evidence_labels_are_localized_everywhere`). Технические названия не переводятся;
  текст причины статуса — данные evidence (RU/EN).
- **Local:** backup `backups/catalog-master-eval-audit-20260927/final-20260928/`; refresh/check OK;
  план 96 (95 evaluation_new + 1 видимости); копия: apply, check OK, qa PASS, integrity ok, FK 0;
  рабочий Local — штатный `sync-local --apply` (96), check OK, qa PASS (0 ошибок), integrity ok,
  FK 0, повторный план 0 записываемых изменений (113 прежних unsupported), `manage.py check` —
  0 issues, оценок 5 010; Local перезапущен (`stop-local`/`start-local`), `/healthz` ok.
- **Тесты:** 315 (история — после перевода карточки в review). **Браузер:** 18 карточек × ru/en/
  ar/fa/zh-Hans/de без проблем (нет пустых секций, у developer-блока есть пояснение, у статуса
  есть подпись, нет противоречивых «только»), RTL ar/fa, тёмная/светлая тема, 375 px без
  горизонтального переполнения, MTEB — 3 + «Показать все (+123)».
- **Production:** не менялась. Выпуск — только после сообщения владельца «принимаю / публикуем».
- Local URL для приёмки: http://127.0.0.1:18810/ru/

## Evaluation Evidence — этап 2 выполнен в Local, REVIEW (ждёт приёмки владельца), 2026-09-28

- Карточка `EVAL-EVIDENCE-AUDIT-2026-09-27`: `in_progress` (27.09) → `review` (28.09),
  Local ✓, Owner —, Production —. Release # не резервировался.
- **Изменено (master):** `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx`, backup до этапа 2 —
  `backups/catalog-master-eval-audit-20260927/stage2-20260928/` (master `a6765737…`,
  рабочая SQLite `fb8ea943…`). Импорт — `tools/master_eval_audit_2026_09_27_stage2.py`
  (идемпотентен, всё в Changelog), данные — `tools/eval_audit_2026_09_27_stage2_data.py`
  (720 наблюдений, 50 явных статусов; страницы/изображения с SHA-256 в
  `artifacts/eval-audit-2026-09-27/stage2/`), статистика —
  `tools/eval_audit_2026_09_27_stage2_report.py` → `stage2/STAGE2_STATS.md`, отчёт — `stage2/REPORT.md`.
  - Evaluations 5 031 → 5 751 (+720: developer-reported из model/system cards, тех. отчётов,
    статей, официальных таблиц/графиков; независимые research-only и замеры конкурентов — Public=NO).
  - 268 строк самоотчётов разработчиков этапа 1 → Public=YES как «Результаты разработчика»
    (`rating_eligible=false`); строки из сабмитов в лидерборды — без изменений.
  - Факт `independent_evaluation_status` у всех 799 — новый словарь (independent_public,
    independent_nonpublic, developer_reported, no_published_numerical_evaluation,
    exact_version_not_found, identity_ambiguous, not_applicable; `gap` — только NEEDS_REVIEW вне scope).
  - Спорные: 2 строки Epoch `promax` у GPT-5.6 Sol = отдельный продукт GPT-5.6 Sol Pro → Public=NO,
    вне рейтинга; `evaluation-867`: значение ECI 155 верно для DeepSeek V4 Pro 0813 (Epoch 155.39),
    Source Model исправлен, строка — округлённый дубль `evaluation-816` → скрыта вместе с 13
    такими же дублями ECI (конфигурация «Модель», 21.09); LMArena: README
    `lmarena-ai/leaderboard-dataset@a4e245e5` — `license: cc-by-4.0` (сохранён, SHA `1ab86c5c…`).
- **Изменено (код Local):** `catalog/comparison.py` (слои: independent / composite / developer,
  группы по оценщику, research-only и конкуренты из master), `catalog/views.py` (выбор теста и
  сортировка — только independent/composite), `templates/panel.html`,
  `templates/includes/evaluation_group.html`, `evaluation_row.html`, `static/site.css`,
  `catalog/context.py` (подписи RU/EN, прочие языки — английский fallback), `catalog/catalog_qa.py`
  (очередь качества понимает новые статусы), `data/evaluation_gap_notes.json` (генерируется
  скриптом этапа 2), тесты `test_catalog.py`, `test_redesign.py`, `test_product_history.py`.
- **BEFORE → AFTER (PUBLISHED 325):** публичная независимая ≥1 159 (48.9%) → 159 (48.9%) —
  новых публичных независимых источников нет (у найденных нет открытой лицензии);
  ≥2 102, ≥3 60, ≥4 29 — без изменений. Любые проверенные численные оценки 177 (54.5%) →
  **277/325 (85.2%)**. Классы после: independent public 159; только independent research-only 33
  (28 с баллами Public=NO + 5 только статус); только developer 88; developer + independent 47
  (пересечение); без опубликованных численных тестов 23; точная версия не найдена 12;
  идентичность неоднозначна 9; конфигурация 1; gap 0. По категориям (independent → any):
  text 54.3% → 87.7%, image 67.7% → 92.9%, video 47.2% → 72.2%, audio 0% → 75.0%, other 0% → 62.5%.
- **Проверки:** refresh/check OK; sync-local план 4 024 (4 009 evaluation_new + 15 видимости);
  копия Local: apply, check OK, qa PASS, integrity ok, FK 0, повторный план 0; рабочий Local:
  тот же штатный `sync-local --apply` (4 024), check OK, qa PASS (0 ошибок, 17 предупреждений,
  очередь 191), integrity ok, FK 0, повторный план 0 изменений (113 прежних unsupported, в т.ч.
  Source Model `evaluation-867`), оценок 4 915; `manage.py test catalog` 314 OK / 1 skip;
  release history PASS; браузер (отдельный порт 18813, та же БД): RU/EN, карточки text/image/
  video/audio/other, MTEB — 3 результата + «Показать все (+123)», светлая/тёмная тема, 375 px без
  горизонтальной прокрутки, селектор теста без developer-бенчмарков, ошибок сервера нет.
- **Local / GitHub / Production:** рабочий Local синхронизирован и перезапущен с новым кодом;
  GitHub — без commit/push; Production не менялась (#011 / v0.11.0, `9ddba83`).
- **Что смотреть владельцу (вкладка «Проверки»):** Qwen3-Embedding-8B (MTEB сгруппирован),
  GPT-5.6 Sol (независимые + ECI), GigaChat 3.5 Reasoning / EXAONE 4.5 (только разработчик),
  Scribe v2 (research-only + конкурент + разработчик), AlphaFold 3 (research-only без баллов),
  Lyria 3.5 («Опубликованных тестов точной версии не найдено»), Kimi K3 (max) (конфигурация).
- **Не завершено:** приёмка владельцем (`done` только после неё); решение по предложению
  `D-2026-09-27-independent-evaluation-evidence-policy` (дополнено этапом 2); вручную: PDF
  технического отчёта Nova 2 (404 для автоматической загрузки) и значения графиков OpenAI audio
  (в тексте только относительные улучшения); подписи новых строк на 20 других языках интерфейса — пока
  английский fallback.
- **Следующим выполнить:** владелец смотрит Local; при приёмке — карточка `done`; затем, по
  отдельной команде, выпуск по `docs/RELEASE.md` (новый Release #, карточка) или правки по замечаниям.

## Независимые оценки моделей и evidence-база AIpediya Rating — этап 1 выполнен (Local, master), 2026-09-27

- Карточка Timeline `EVAL-EVIDENCE-AUDIT-2026-09-27` создана первым действием
  (`in_progress`), по завершении переведена в `review` (Local ✓, Owner —,
  Production —). Новый Release # не резервировался: изменён только master.
- Изменено: master `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` (backup
  `backups/catalog-master-eval-audit-20260927/`, SHA до `9e0c7659…`, после
  `a6765737…`): Evaluations 906 → 5 031 (+4 125 наблюдений этого прогона),
  `independent_evaluation_status` у всех 799 моделей (11 прежних фактов обновлены,
  788 добавлены), 889 прежним строкам добавлены только поля готовности к рейтингу
  в `Conditions Extra (JSON)`; всё — в Changelog. Источники: Epoch AI hub 2026-09-27
  (own + внешние лидерборды), `lmarena-ai/leaderboard-dataset` (CC BY 4.0), Aider
  (Apache-2.0), ForecastBench (CC BY-SA), MTEB results (CC0), Open ASR и TTS Arena
  (без лицензии → Public=NO). Точные версии — ручная карта
  `tools/eval_audit_2026_09_27_map.py`; импорт — `tools/master_eval_audit_2026_09_27.py`
  (идемпотентен); отчёт — `tools/eval_audit_2026_09_27_report.py`.
- Baseline (пересчитан из XLSX; поручение называло 795/321): Models 799, PUBLISHED 325,
  NEEDS_REVIEW 474; публичная независимая оценка у 69/325; evaluator'ов 1.
- BEFORE → AFTER (PUBLISHED): исследовано 11 → 325 (100%); ≥1 публичная независимая
  оценка 69 (21.2%) → 159 (48.9%); ≥2 публичных evaluator'а 0 → 102 (31.4%), ≥3 0 → 60,
  ≥4 0 → 29; с независимыми данными вкл. Public=NO 77 → 175. Публичных независимых
  evaluator-организаций 1 → 7, всех независимых 2 → 61 (41 нейтральная); публичных
  семейств бенчмарков 11 → 26; публичных наблюдений 777 → 2 096; Public=NO 50 → 2 495;
  developer-reported 0 → 361. По категориям: text 31.2% → 54.3%, image 19.2% → 67.7%,
  video 19.4% → 47.2%, audio 0 → 0, other 0 → 0. NEEDS_REVIEW: 59 моделей получили
  публичные независимые оценки. Подробно — `artifacts/eval-audit-2026-09-27/REPORT.md`
  и `BEFORE_AFTER.md` (пробел по каждой оставшейся модели).
- Проверки: `catalog_master refresh` renumbered=0; `check: OK` (дрейф Models/Tools/
  Offers/Access совпадает с исходной книгой); `qa` на изолированной копии Local после
  пробного `sync-local --apply` (3 289 evaluation_new) + `import` — PASS, повторный план
  0; повторный прогон скрипта — 0 изменений; 1 812 строк Epoch перечитаны из CSV —
  0 расхождений; `manage.py test catalog` 313 OK / 1 skip; release validator PASS.
- Local / GitHub / Production: рабочий Local SQLite **не** синхронизировался, поэтому
  `catalog_master qa` на рабочем Local блокирует только «master → Local: 3289 changes
  not synced (evaluation_new)» — это ожидаемый gate до решения владельца, данные ради
  PASS не удалялись. GitHub без commit/push; Production не менялась
  (#011 / v0.11.0, `9ddba83`). Изменены также `docs/timeline.json`, тесты истории,
  `docs/DECISIONS.md` (предложение), этот статус, `timeline.html`, AI_CONTEXT.
- Не завершено: приёмка владельцем; решение о синхронизации Local (до неё — решить
  отображение 402 task-level строк MTEB и Arena-строк на карточке); предложение
  `D-2026-09-27-independent-evaluation-evidence-policy` (в т.ч. LMArena CC BY 4.0
  вместо прежнего «Arena запрещает») ждёт подтверждения; audio 0/44 и other 0/8
  публичных — нет открытых лицензий на результаты; `catalog_qa.GAP` учитывает только
  статус `gap` (предложено расширить); 2 прежние строки `promax` и ECI `evaluation-867`
  отмечены для проверки владельцем.
- Следующим выполнить: владелец просматривает отчёт и принимает/отклоняет политику;
  затем `sync-local` на копии → diff владельцу → рабочий Local по
  `docs/CATALOG_MASTER.md`; параллельно запросить лицензии ARC Prize, METR, Scale,
  Terminal-Bench, HF Open ASR, TTS Arena. Production — только по `docs/RELEASE.md`.

## Полный аудит автономной истории и social preview — Local, 2026-09-27

- Изменено: сверены все 15 карточек с release reports, `RELEASE.md`, решениями,
  статусом и публичным `/healthz`. Карточка версий переведена из `review` в
  `done` с Local ✓ / Owner ✓ / Production — по явной приёмке владельца.
  Существующая карточка AIpediya Cloudflare Web Analytics теперь связывается
  с выпуском Tools/CSP `cf4ac9a` и публичным beacon 200 / RUM 204:
  Local ✓ / Owner ✓ / Production ✓. Новый deploy не выполнялся. Исправлены
  устаревшие пояснения Adaptive UI, истории и master; даты, номера Release
  #001–#011 и текущий Production baseline не менялись. Подробная матрица —
  `docs/history/2026-09-27-timeline-status-audit.md`.
- Social preview: сырой HTML всех 22 языковых корней для
  `facebookexternalhit/1.1` имеет валидные OG-поля и Twitter Card;
  `/` и `/ru/` HTTP 200, `cf-cache-status: DYNAMIC`. Share-card PNG 1200×630
  HTTP 200 для Facebook, Twitter и LinkedIn crawler User-Agent, SHA-256
  одинаковый. `/healthz` подтвердил `9ddba83c176aa3f6793362d6345b797c76ddf987`.
  Дефекта сайта или устаревшего ответа Cloudflare не найдено; cache purge
  не выполнялся. Если конкретная сеть всё ещё показывает старый preview,
  возможен её URL-specific cache, но её сбой здесь не воспроизведён.
- Local / GitHub / Production: изменены только Local реестр, шаблоны,
  тесты, документы и производные `timeline.html`/AI_CONTEXT. GitHub и
  Production не менялись; текущие указатели — Release #011 · v0.11.0.
  Файлы этого аудита: `docs/timeline.json`, `catalog/tests/test_product_history.py`,
  `templates/product_history.html`, `templates/product_history_standalone.html`,
  `docs/PRODUCT_HISTORY.md`, `docs/DECISIONS.md`, этот статус,
  `docs/history/2026-09-27-timeline-status-audit.md`, `timeline.html` и
  производный пакет `AI_CONTEXT`.
- Проверки: 15/15 карточек имеют уникальные ID; `review=0`, `in_progress=0`,
  `planned=1`; release validator PASS, 11/11 прицельных тестов истории и версий,
  полный catalog suite 313 OK / 1 skip, Django check и `git diff --check`
  PASS. Ярлык направляет на существующий `timeline.html`; локальный и
  публичный share-card имеют одинаковый SHA-256. Не завершено: только
  внешний визуальный просмотр вновь собранного автономного файла и будущая
  конкретная карточка #012. Следующим выполнить: владелец открывает ярлык
  истории и проверяет обновлённые статусы; отдельный Production выпуск
  возможен лишь по `docs/RELEASE.md`.

## Система версий и обязательная история выпуска — Local DONE / Owner PASS, 2026-09-27

- Изменено: 11 подтверждённых Production-вех получили Release #001–#011 и
  SemVer; существующая карточка каталога 325/147 стала Release #011 · v0.11.0.
  В `docs/timeline.json` появились независимые `current_local` и
  `current_production`. Автономный `timeline.html` показывает оба указателя,
  версии карточек и состояние Local / Owner / Production. Добавлены
  `tools/release_history.py` и post-production closure для той же карточки.
- Local / GitHub / Production: изменения только в Local working tree;
  GitHub не отправлен, Production не менялась. Последний подтверждённый
  Production commit `9ddba83`; 325 Models / 147 Tools. Текущая версия в
  обоих указателях #011 / v0.11.0. Открытые Local-задачи не получили номер #012.
- Проверки: release history validator PASS; 312 catalog tests OK, 1 skipped;
  `manage.py check` PASS; `git diff --check` PASS; сборка старого архива без
  новой карточки заблокирована release gate. Ярлык истории проверен: target
  `C:\Users\dimon\Documents\AIpedia\timeline.html`. Автономный HTML
  пересобран. Edge заблокировал открытие `file://` политикой браузера;
  владелец в поручении на аудит 27.09.2026 явно сообщил, что визуально
  проверил результат и подтвердил завершение этапа.
- Не завершено: будущий реальный Release #012 ещё не проходил полный
  release workflow; отдельного deploy самой системы версий не было.
  Следующим выполнить: для конкретного следующего пакета зарезервировать
  #012 с точным составом и провести Local QA до отдельного разрешения на
  Production. Указатели Local и Production остаются #011 / v0.11.0.

## Каталог 325 Models / 147 Tools — Production VERIFIED, 2026-09-27

- Изменено: проверенное владельцем Local-состояние опубликовано штатным
  `tools/server.py deploy` через `aipediya-prod`. Публичный commit
  `9ddba83c176aa3f6793362d6345b797c76ddf987`; tag
  `release-2026-09-27-catalog-325-147`. Добавлены 4 модели и 4 инструмента,
  обновлены 7 записей и пересчитаны номера. Local SQLite не копировалась.
- Проверки: серверные preflight, dry-run, deploy, health, catalog,
  verify-release и `catalog_master qa --production` — PASS. Production SQLite:
  325/325 Models и 147/147 Tools пронумерованы, integrity OK, FK 0.
  Публичный GSD check 34/34, полный Production QA 1657/1657. Тесты
  истории после обновления текущего release tag: 7/7. Браузер RU/EN:
  счётчики 325/147, LongCat #325 и новые инструменты видны.
  Backup до и после выпуска, SHA архива и детали —
  `docs/history/2026-09-27-catalog-325-147-release.md`.
- Local / GitHub / Production: Local PASS и утверждён владельцем; release
  commit `9ddba83`, docs/test commits `c4c9422`, `b3abb24`, `2fd442c`, tag
  `release-2026-09-27-catalog-325-147` отправлены в `origin/main`;
  Production опубликована и проверена. Исходные посторонние dirty/untracked
  файлы сохранены.
- Не завершено: 35 известных неполных фактов master остаются в очереди
  качества; прямой тариф LongCat 2.5 API не подтверждён, показанная цена —
  Vercel AI Gateway. Следующим выполнить исследование этих фактов сначала
  в master и Local; новый Production выпуск — только по отдельной команде.

## Каталог 25–27 сентября — Local до выпуска, снимок 2026-09-27

- Изменено: canonical master пополнен 4 моделями (LongCat-2.5-Preview,
  Qwen3Guard-Stream 0.6B/4B/8B) и 4 инструментами (GPT Researcher,
  KoboldCpp, Darkbloom, vMLX). Обновлены существующие Codex, llama.cpp,
  GPT-6 Sol/Luna, Replit Agent, Qwen Code и Cline. Qwen Code Version =
  0.24.6; Codex stable 0.157.1 сохранён. Записей ARCHIVE и отдельных
  карточек для Luna Fast, сборок llama.cpp или alpha Codex нет. Временные
  цены LongCat отмечены акционными и исключены из сравнения стандартных
  тарифов. В master записаны лицензии, факты, источники, доступ к весам
  Qwen3Guard и code update KV-cache только для 0.6B/4B. Номера пересчитаны
  штатным refresh и синхронизированы, старые Record ID/URL сохранены.
- Проверки: пробная SQLite-копия и рабочий Local прошли `catalog_master
  check: OK` и `qa: PASS`; 325/325 Models и 147/147 Tools пронумерованы.
  Полный `manage.py test catalog` — 309 тестов, OK, 1 skip. Браузер Local:
  RU/EN LongCat (цены, ограничения, источники), EN Qwen3Guard (лицензия,
  открытые веса, ссылка Download), EN GPT Researcher и RU Tools/Qwen Code;
  даты, номера, списки и панели проверены. `sync-local` после применения
  не планирует поддерживаемых изменений.
- Local / GitHub / Production: master XLSX, Local SQLite, код распознавания
  временной цены и синхронизации строк Offers изменены; GitHub без commit/push.
  Production не изменялась и не проверялась как выпуск этого пакета.
  Исходные посторонние dirty/untracked файлы, включая traffic audit,
  `catalog/tests/test_product_history.py`, `data/release/v013/`,
  `data/research/`, `.claude/`, `%SystemDrive%/`, ярлык и `timeline.html`,
  сохранены.
- Не завершено: визуальная приёмка владельца и отдельное разрешение на
  конкретный Production выпуск. В очереди качества `qa` — 35 известных
  неполных фактов (включая неподтверждённые страны GPT Researcher,
  KoboldCpp и vMLX и официальную hosted-цену Darkbloom); проверки проходят
  за счёт явных `*_status`. У прямого LongCat API тариф для 2.5 отдельно
  не подтверждён: опубликованные в Local цены относятся к Vercel AI Gateway.
  `sync-local` сообщает о 112 неподдерживаемых расхождениях опубликованных
  записей (16 публичных, 96 служебных), они не входят в применённый план;
  до публикации каталога нужен отдельный разбор этих расхождений.
  Следующим выполнить визуальную приёмку Local владельцем, разобрать
  расхождения, затем при отдельной команде на конкретный выпуск следовать
  `docs/RELEASE.md`.

## Аудит пассивного трафика двух проектов — 2026-09-27

- Уточнение состояния Timeline: карточка Cloudflare Web Analytics AIpediya
  завершена и имеет Production ✓ **по ранее выполненному выпуску**
  `release-2026-09-27-tools-chronology-csp` (`cf4ac9a`): публичный браузер
  получил beacon 200 и `/cdn-cgi/rum` 204 без CSP load failure. Аудит ниже
  не был новым deploy. Отдельная проблема StratForge остаётся за пределами
  этой карточки и этого проекта.

- Изменено: выполнен Production browser/Cloudflare аудит AIpediya и
  StratForge; факты и точное место блокировки —
  `docs/history/2026-09-27-traffic-analytics-audit.md`. На AIpediya
  Automatic Web Analytics уже работает: beacon 200, RUM POST 204,
  15 page views / 11 visits в панели. На StratForge пробное Automatic
  Setup обнаружило CSP-отказ, поэтому Cloudflare RUM возвращён в OFF.
- Проверки: браузер desktop и Network на обоих Production UI; HTTP Traffic,
  Security Analytics, AI Crawl Control, GSC/Bing просмотрены. У StratForge
  ≈27,17 тыс. `/api/` и ≈1,4 тыс. `/ws/` из ≈29,65 тыс. запросов
  `app.stratforges.com` за 24 часа — не число посетителей. Local код и
  Production приложения не менялись; повторный browser reload после
  отката RUM без CSP-ошибок. Финальный Local `manage.py test catalog` —
  308 OK, 1 skip; targeted `catalog.tests.test_product_history` — 7 OK;
  `git diff --check` PASS; история и AI_CONTEXT собраны. Прямое
  browser-открытие `file://` автономной истории отклонено политикой
  браузера; её визуальная Local-проверка не подтверждена.
- Local / GitHub / Production: Local — отчёт, статус, реестр истории и
  ожидаемые счётчики её тестов;
  GitHub — без commit/push; Production код и БД — без изменений. Cloudflare
  AIpediya — без изменений, StratForge — исходное Disable восстановлено.
  Существующие untracked файлы сохранены.
- Не завершено: реальный RUM StratForge и проверка soft navigations
  заблокированы CSP. Следующим выполнить узкую правку `script-src` в
  `app/server.py` и `app/static/aurora/*.html` в StratForge, провести
  Local/Canary QA и получить отдельное разрешение на конкретный
  Production выпуск; затем включить Automatic Setup и подтвердить
  beacon 200, RUM 204 и данные в панели. Никакого такого выпуска
  текущий аудит не санкционирует.

## Tools chronology + Cloudflare CSP — Production VERIFIED, 2026-09-27

- Изменено: Production выпуска `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`
  развёрнута по утверждённому плану; предыдущий публичный commit `aa48e11`.
  Canonical Production access: `python tools/server.py preflight` через
  `aipediya-prod`; текущий preflight PASS. Отдельный server trial на online
  backup подтвердил ровно 27 дат и 140 номеров без других фактических
  изменений. Backup перед deploy и после него есть; Local SQLite не копировалась.
- Фактическая Production SQLite: Tools 143/143, номера 1–143 без дыр/дублей,
  60 exact, 83 approximate, 0 без даты; Models 321. Integrity OK, FK 0,
  publication flags 0 изменений; служба `aipedia` RUNNING, `/healthz` =
  `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`.
- Проверки: Local/Production catalog master check OK и QA PASS; полный
  catalog suite 308 OK / 1 skip; `manage.py check` PASS; GSD public 34/34,
  полный GSD Production QA 1657/1657. Read-only сравнение живой БД с backup:
  только `catalog_tool` (140 номеров, 4 exact, 23 approximate/precision);
  Models, цены, оценки, описания не изменились.
  Публичный браузер RU/EN Tools oldest/newest и Models PASS. CSP строго
  ограничена; browser network: Cloudflare beacon 200, `/cdn-cgi/rum` 204,
  console errors 0. Детали —
  `docs/history/2026-09-27-tools-chronology-csp-release.md`.
- Local / GitHub / Production: Local PASS; release commit `cf4ac9a` и
  docs/access commit `c9ebe7b` отправлены в `origin/main`; tag
  `release-2026-09-27-tools-chronology-csp` отправлен и указывает на
  фактический Production commit `cf4ac9a`. Production VERIFIED.
  Посторонние untracked файлы (`%SystemDrive%/`, `.claude/`, `data/release/v013/`,
  `data/research/`, старый Claude task, history shortcut, производный
  `timeline.html`) сохранены и не входят в release docs commit.
- Не завершено: работ по этому выпуску нет. Следующим выполнять только новые
  задачи по отдельному поручению; новая публикация Production не требуется.

## Предыдущий checkpoint: owner approved Production release, server phase pending, 2026-09-27

- Изменено: владелец утвердил проверенное Local-состояние и отдельно разрешил
  его выпуск по `docs/RELEASE.md`. Текущая Production до выпуска подтверждена
  публичным `/healthz`: `aa48e11bad7326340463654e33ba5e89769042b9`;
  публичная `/tools/?sort=number_asc` отвечает 200. Production не менялась.
- Для release candidate построен `data/release/tools-chronology-csp-20260927/catalog_plan.json`
  из pre-apply online-копии Local: ровно 27 Tool date updates и 140 Tool
  number updates, ноль других видов записей; план содержит expected-before
  значения по Record ID. Манифест `data/release_state.json` обновлён с
  Local: 321/143 публичных, 0 изменений флагов публикации, 0 Models, 140 Tool
  numbers. На отдельной SQLite-копии apply-plan сделал 167 writes; все
  фактические catalog-таблицы после применения побайтно равны утверждённой
  рабочей Local. Различаются только временные данные журнала и outbox.
- Финальный Local QA кандидата: `catalog_master check` OK, `qa` PASS,
  `manage.py check` 0 issues, полный catalog suite 305 OK / 1 expected skip;
  SQLite integrity OK и FK 0 на утверждённой Local и trial. Браузер Local
  показывает Tools 143, сортировку 1…143, точные и `≈` даты. CSP regression
  входит в полный suite. Другие незакоммиченные/untracked файлы сохраняются;
  в выпуск попадут только точные файлы этапа.
- Server access: штатный SSH через указанный в `docs/RELEASE.md` Cloudflare
  transport отверг аутентификацию `Permission denied (publickey)`; секреты и
  альтернативные credentials не исследовались. Запрошен путь к уже настроенной
  identity или host alias. Серверный read-only baseline, server DB preflight,
  backup, deploy и Production QA ещё **не выполнены**; серверный план нельзя
  считать подтверждённым до проверки against Production SQLite.
- Release commit: `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`, ровно 17
  точных файлов; архив `artifacts/code-release/aipedia-code-cf4ac9a33f8d.zip`,
  SHA-256 `8af0a16c7044a8208e5ac38aa1d6a156621c670ccbaeb17640895c7f6e46c7a0`,
  333 файла, нет SQLite/секретов; deploy `--dry-run` PASS с catalog plan и
  publication manifest. Из распакованного архива: 305 тестов OK, 1 skip,
  `manage.py check` PASS. GitHub push и tag оставлены до полного Production PASS.
- Read-only публичная baseline: `/healthz` = `aa48e11bad7326340463654e33ba5e89769042b9`,
  143 Tool Record ID, 116 с номером; Models 321 на публичном каталоге;
  фактическая старая CSP `script-src 'self'`, Cloudflare beacon injected.
  Локальный отчёт: `artifacts/tools-chronology-csp-release/public-baseline.json`.
- Local / GitHub / Production: Local PASS и утверждён; release commit сохранён
  локально, не push; Production по-прежнему `aa48e11` и прежняя CSP.
- Не завершено: серверный read-only baseline, trial на копии Production DB,
  backup, deploy и все публичные проверки. Следующим выполнить: при получении
  точного пути к существующей настроенной SSH identity или host alias повторить
  штатную read-only проверку; затем подтвердить план на серверной копии,
  безопасный backup, штатный deploy и публичный QA. Если SSH остаётся недоступен,
  остановить только серверную фазу и сохранить готовый release candidate.


## Tools numbering and Cloudflare CSP — READY FOR OWNER REVIEW in Local, 2026-09-27

- Изменено: владелец утвердил точный план canonical master → рабочая Local.
  Перед записью план ещё раз совпал с принятой пробой: 167 поддерживаемых
  изменений (27 дат, 140 номеров), без Record ID, названий, цен, оценок,
  описаний, статуса публикации и других фактических полей. Перед применением
  сделан online backup `backups/catalog-count-csp-20260927/aipedia-working-before-approved-143.sqlite3`.
  Штатный `catalog_master sync-local --apply --max-changes 200` применил 167.
- Рабочая Local SQLite: **143 опубликованных Tools; 143 с номером; 60 exact;
  83 approximate; 0 без даты; номера 1–143 непрерывно, без дублей и дыр**.
  Сравнение всех таблиц с backup: только `catalog_tool` изменил фактические
  поля (140 `public_number`, 23 `approx_released`/`approx_precision`, 4 `released`);
  Models и прочие данные карточек не изменились. Штатный путь также дописал
  журнал публикаций Tools и pending discovery events; передача событий не
  запускалась. `catalog_master import` — 0 новых строк, 0 пересчётов;
  `catalog_master check` — OK; `catalog_master qa` — PASS для 321 Models и
  143 Tools; повторный план — 0 применимых изменений.
- Ревизии и outbox штатной синхронизации: 194 новых Tool publication revisions;
  450 discovery events имеют `pending`, `attempts=0` — отправки не было.
- Проверено: `PRAGMA integrity_check=ok`, FK ошибок 0; полный `manage.py test
  catalog --settings=aipedia.test_settings` — 305 OK, 1 skip; `manage.py check`
  — 0 issues. В настоящем браузере на рабочей SQLite RU/EN Tools: 143 строки,
  oldest №1…143, newest №143…1, `≈` виден у approximate dates; RU/EN Models
  показывают 321. Выявленный при browser QA дефект подписи «0 с номером» при
  быстрой сортировке исправлен в `catalog/views.py` для Models и Tools;
  регрессионный тест добавлен. Cloudflare CSP fix в `catalog/middleware.py`
  и его тест сохранены без изменения.
- Local / GitHub / Production:

  | Слой | Фактическое состояние |
  |---|---|
  | Local | даты и номера Tools из canonical master применены в рабочую SQLite; Tools 143/143, 60 exact + 83 approximate; QA PASS; Timeline READY FOR OWNER REVIEW |
  | GitHub | этот пакет не commit/push; текущие изменения остаются только в рабочем каталоге |
  | Production | публичный release `aa48e11`, 143 Tools и 116 номеров, прежняя CSP; не изменялась |

- Точный видимый Production diff относительно проверенной Local: 143 тех же
  Record ID и названия; **140 изменений Public Number и 27 отображаемых дат**
  (4 exact, 23 approximate), перечислены в
  `artifacts/tool-count-csp-production-public-diff.md` и JSON. Это сравнение
  публичной страницы с Local, не серверный DB preflight. Read-only SSH через
  существующий транспорт завершился `Permission denied (publickey)`; ключи
  не читались и сервер не менялся. DB-level diff и release dry-run потребуются
  при разрешённом выпуске по `docs/RELEASE.md`.
- Ранее существовавшие неподдерживаемые master↔Local различия остались вне
  узкого sync (110 в JSON-плане; `check` сообщает более широкий drift по всем
  листам). Их не применяли и не включали в 167 утверждённых изменений.
- Файлы этапа: canonical XLSX, `catalog/catalog_master.py`, `catalog/views.py`,
  `catalog/middleware.py`, тесты master/numbering/CSP/history,
  `docs/timeline.json`, этот статус, отчёт истории и локальные evidence/plan/diff
  в `artifacts/`; рядом остаются ранее существовавшие незакоммиченные файлы,
  которые не очищались и не staging-ились.
- Не завершено: визуальная приёмка Local владельцем и отдельное решение о
  конкретном Production-выпуске. Следующим выполнить: владелец просматривает
  Local и точный публичный diff; после отдельной команды на выпуск выполнить
  серверный read-only preflight, backup, dry-run, штатный release и public QA.
- `tools/pack_ai_context.py` пересобрал `timeline.html`, `AI_CONTEXT.md` и ZIP;
  два предупреждения относятся к незакоммиченным изменениям и отсутствию
  публикации. `git diff --check` — без ошибок.

## Historical trial before owner-approved Local application, 2026-09-27

- Изменено: владелец уточнил единое правило для опубликованных Models и Tools:
  существующая публичная сущность должна иметь доказанную хронологическую
  позицию, точную дату либо `≈` дату первого подтверждённого публичного
  существования. Цель 143/143/0. Для оставшихся 21 Tools проведена адресная
  проверка по датированным источникам; причины и URL сохранены в
  `artifacts/tool-count-csp-date-evidence-20260927.json` и полях evidence
  canonical master. Старый план на 115 изменений и пробная копия 122/21 ниже —
  промежуточный результат, теперь заменён новым планом.
- Canonical master: 143 опубликованы, 60 exact dates, 83 approximate dates,
  0 без даты; Public Number 1–143 непрерывно без дублей. Пересчёт дописал
  140 изменений номеров в Changelog. `catalog_master check` — OK. Копия master
  до этого этапа: `backups/catalog-count-csp-20260927/AIpediya_Model_Verification_Master_before_21.xlsx`.
- Trial Local: свежая online-копия исходной рабочей SQLite;
  `artifacts/tool-count-csp-full-trial-plan.json` фиксирует exact diff:
  27 дат + 140 номеров = 167 поддерживаемых изменений, 0 изменения публикации,
  Record ID и иных полей. Читаемая владельцем таблица: `artifacts/tool-count-csp-full-trial-diff.md`.
  Повторный read-only план против рабочей Local после обновления книги побайтно
  совпал по JSON-данным с пробным планом.
  Пробное применение: SQLite 143/143/0, `integrity_check=ok`, foreign key
  errors=0. Штатные import/check/qa на отдельной копии master: OK/OK/PASS;
  повторный план — 0 поддерживаемых изменений. RU/EN HTML выдал 143 строки,
  oldest 1…143, newest 143…1; маркеры `≈` присутствуют. Рабочая Local SQLite остаётся
  143/116/27 до приёмки владельцем нового diff.
- CSP fix в `catalog/middleware.py` и его тест сохранены без изменений.
  GitHub и Production в этом этапе не менялись. Production остаётся
  `aa48e11`, 143/116/27 и прежняя CSP.
- Файлы коррекции: `AGENTS.md`, `docs/DECISIONS.md`,
  `catalog/catalog_master.py`, `catalog/tests/test_catalog_master.py`,
  `catalog/tests/test_catalog_master_sync.py`, canonical XLSX,
  `artifacts/complete_tool_dates.py`, дата/source ledger, новый план и diff,
  `docs/timeline.json`, отчёт истории и этот статус. Существующие изменения
  CSP не переписывались.
- Проверено: `manage.py test catalog --settings=aipedia.test_settings` —
  304 OK (1 skip); `catalog_master check` — OK; `catalog_master qa` на
  пробной SQLite и пробной книге — PASS; повторный sync plan — 0 применимых
  изменений; RU/EN oldest/newest HTML — 143/143 в правильном порядке.
- Не завершено: приёмка владельцем нового полного diff для рабочей Local и
  отдельное разрешение конкретного выпуска для Production. Следующим выполнить:
  завершить QA пробной копии и сортировку, показать diff владельцу; после
  приёмки сделать backup рабочей Local, выполнить штатный sync/import/check/qa.

## Tools numbering and Cloudflare Analytics CSP — earlier 122/21 trial, superseded by owner correction

- Изменено: аудит 143 Tools по master, рабочей Local SQLite, Production SQLite
  (read-only) и публичной таблице. Исходно 116 с номером, 27 без даты/номера,
  max №116; опубликованные Record ID и номера совпали. В master шесть дат
  подтверждены официальными источниками (две приблизительные по месяцу),
  хронология пересчитана с записью в Changelog: 122 с №, 21 без №, max №122.
  Новых доказанных дублей или ошибочных Tool-записей не установлено; состав
  публикации и 143 в счётчике сохраняются. Полный список 27, причины, источники
  и 115 изменений пробного diff —
  `docs/history/2026-09-27-tools-count-cloudflare-csp-local.md` и
  `artifacts/tool-count-csp-trial-plan.json`.
- Пробная Local-копия: `catalog_master check` OK; `sync-local` применил только
  шесть дат и 109 номеров, повторный план — 0 поддерживаемых изменений;
  `catalog_master qa` PASS. В браузере 127.0.0.1:18813 EN Models = 321,
  EN/RU Tools = 143, из них 122 с № и 21 без №. Рабочая Local SQLite ещё
  показывает 143/116/27: правило `AGENTS.md` требует приёмки diff владельцем
  перед `sync-local --apply`. Поэтому QA против рабочей Local пока FAIL на
  115 ожидаемых расхождениях. Пробная SQLite и резервная копия master находятся
  в `backups/catalog-count-csp-20260927/`.
- CSP: Production header `script-src 'self'` блокирует автоматически вставленный
  Cloudflare `beacon.min.js/v31…`. В `catalog/middleware.py` добавлены только
  точный и версионный URL beacon в `script-src` и `connect-src 'self'` для
  same-origin `/cdn-cgi/rum`; добавлен `catalog/tests/test_csp.py`.
  Cloudflare Dashboard не менялся; реальный telemetry POST проверяется после
  отдельного разрешённого выпуска, не по Local. Существующие директивы CSP
  оставлены строгими.
- Local / GitHub / Production: код CSP, canonical XLSX, отчёт и Timeline только
  в рабочем каталоге `main`; Local рабочая SQLite не изменена, временная копия
  проверена; GitHub не обновлялся; Production `aa48e11` и серверная SQLite
  не изменялись. Read-only публичный каталог остаётся 143/116/27.

  | Слой | Состояние этой задачи |
  |---|---|
  | Local | master 143/122/21; пробная SQLite и браузер PASS; рабочая SQLite 143/116/27 до приёмки diff |
  | GitHub | `origin/main` без этого maintenance этапа; локальный `main` с незакоммиченными файлами |
  | Production | `aa48e11`, 143/116/27 и прежняя CSP; read-only аудит, без выпуска |

- Файлы этого этапа: `catalog/middleware.py`, `catalog/tests/test_csp.py`,
  `catalog/product_history.py`, `catalog/tests/test_product_history.py`,
  `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` (локальный untracked
  canonical master), `docs/timeline.json`, этот статус и
  `docs/history/2026-09-27-tools-count-cloudflare-csp-local.md`. До этапа уже
  были untracked `%SystemDrive%/`, `.claude/`, ярлык истории, master XLSX,
  `AIpediya_GSD_1_0_Claude_Task.md`, `data/release/v013/`, `data/research/`,
  `timeline.html`; чужие файлы не очищались и не staging-ились.
- Проверено: `manage.py test catalog --settings=aipedia.test_settings` —
  303 теста, OK (1 skip); `manage.py check` — 0 issues;
  `git diff --check` — 0 ошибок. EN Models и EN/RU Tools открывались в
  настоящем браузере на пробной Local SQLite; консоль EN Models/Tools без
  ошибок. История Local показала новую карточку in_progress и её источник
  ответил HTTP 200; её тесты PASS. `tools/pack_ai_context.py` собрал
  `AI_CONTEXT.md`, ZIP и автономный `timeline.html` (2 предупреждения о
  незакоммиченном/непубличном состоянии, см. пакет).
- Не завершено: приёмка владельцем diff для рабочей Local; проверка
  Cloudflare beacon/telemetry на Production возможна лишь после конкретного
  разрешённого выпуска. Следующим выполнить: после приёмки diff сделать backup
  рабочей Local SQLite, штатный `sync-local --apply`, import/check/qa и UI QA;
  затем отдельное решение владельца о Production-выпуске по `docs/RELEASE.md`.

## Выпуск aa48e11 (Adaptive UI) — опубликовано и проверено, 2026-09-27 16:30 UTC

- Итог: Local PASS → Owner PASS → Production PASS → Public PASS. Production = `aa48e11`
  (tag `release-2026-09-27-adaptive-ui`), предыдущий — `a51c0a1`. Отчёт —
  `docs/history/2026-09-27-adaptive-ui-release.md`; `docs/RELEASE.md` и Timeline (Production ✓
  у `ADAPTIVE-UI-2026-09-26`, `current_production`) обновлены после публичной проверки.
- Серверная фаза — Claude Code в Manual по `D-2026-09-27-claude-server-permission-mode`
  (первая попытка в `Auto` ожидаемо заблокирована; сервер тогда не затрагивался).
- Сервер (только контур AIpedia): read-only PASS (`/healthz` и `BUILD.json` = `a51c0a1`,
  `aipedia` RUNNING); архив SHA-256 `51d7a452…b453` совпал; preflight на онлайн-копии
  `/srv/aipedia/backups/aipedia-preflight-adaptive-ui-20260927T161617Z.sqlite3` — integrity ok,
  FK 0, 321/143, миграций нет, манифест 0 изменений; серверный `--dry-run` PASS; deploy
  16:16:46Z — backup `/srv/aipedia/backups/aipedia-before-code-20260927T161646Z.sqlite3`,
  `deployed-origin-verified`, `copied_sqlite=false`, предыдущий код
  `/srv/aipedia/releases/before-code-20260927T161646Z`; после — integrity ok, FK 0, отпечаток
  данных (номера, цены, оценки, переводы) идентичен backup до выпуска.
- Публично: `/healthz` = `aa48e11`; `final_check.py` 207/207; `gsd_production_qa` 1657/1657;
  `gsd_public_check` 34/34; `catalog_master qa --production` PASS; responsive 89 сценариев
  320×568…5120×1440 (EN/RU/DE/AR/FA/JA/ZH, тёмная/светлая) — page overflow 0; взаимодействия
  15/15 функциональных PASS (подгрузка 321/321 и 143/143, панель, X, Escape, клик вне,
  back/forward, прямые URL, Filter, Sort, поиск); обычный браузер — RU телефон, Sort, светлая
  тема, панель — PASS. Доказательства: `artifacts/adaptive-ui/release/`, `…/production/`.
- Известное, не связано с выпуском: Cloudflare на краю вставляет Web Analytics
  `beacon.min.js`, CSP приложения (`script-src 'self'`, не менялась с `a51c0a1`) его блокирует —
  одно сообщение в консоли на каждой странице; остальные известные ограничения — в блоке этапа
  ниже.
- Local / GitHub / Production: `main` содержит выпуск и документы; tag и документный commit
  отправлены в GitHub после Public PASS; Production = `aa48e11`. Рабочий Local 18810 владелец
  перезапускает ярлыками, чтобы увидеть итоговый код.
- Не завершено: ничего по выпуску. Следующим выполнить: новая задача только по поручению
  владельца; при желании — решение о Cloudflare Web Analytics (выключить вставку beacon или
  явно разрешить её в CSP — отдельная задача и отдельный выпуск).

## Adaptive Interface / Mobile & Tablet UX — утверждено владельцем, объединено с main, 2026-09-27

- Итог: владелец 27.09.2026 проверил Local `http://127.0.0.1:18811/` — «Adaptive Interface /
  Mobile & Tablet UX утверждаю. Визуальная приёмка владельца PASS»
  (`D-2026-09-27-owner-acceptance-adaptive-ui`). Карточка Timeline `ADAPTIVE-UI-2026-09-26` —
  `progress: done` («Готово в Local», Production «—»); решения `D-2026-09-26-adaptive-layout` и
  `D-2026-09-26-timeline-owner-review-state` — подтверждено владельцем. Это не разрешение на
  выпуск Production.
- Git: код этапа — commit `e08112c` в ветке `feature/adaptive-ui`, `main` переведён на него
  fast-forward (ветки не расходились: база `4f0c26f` = `origin/main`, файлы ветки и
  незакоммиченные документы `main` не пересекались); документы/история этапа — следующий
  документный commit в `main`. Не включены: `artifacts/` (git-ignored: скриншоты, отчёты QA,
  харнесс), Local SQLite, секреты, `.env`, `timeline.html`, `.claude/`, давние untracked-файлы
  (`%SystemDrive%/`, xlsx, ярлык, `AIpediya_GSD_1_0_Claude_Task.md`, `data/release/v013/`,
  `data/research/`) — не трогались.
- Сверка итогового `main` с утверждённым Local: 6 файлов кода и тестов идентичны утверждённой
  ветке (sha256 без учёта CRLF, `artifacts/adaptive-ui/approved-branch-files.sha256`); код `main`
  запущен отдельным Local 18812 на копии Local SQLite — 89/89 снимков матрицы совпадают с
  утверждённым 18811 (единственное расхождение в первом прогоне 768×1024 — растеризация; повтор на
  обоих серверах побайтно одинаков).
- Проверено на итоговом `main`: `manage.py test catalog` — 302 теста, 301 OK + 1 skip (`fcntl`);
  `manage.py check` чист; `node --check` для `site.js` и `product-history.js`; `git diff --check`;
  матрица 89 сценариев 320×568…5120×1440 — page overflow 0, вертикальный overflow app-shell 0,
  ошибок консоли 0 (`artifacts/adaptive-ui/final-main/`); smoke 16/16
  (`final-main/interactions.json`): Models 321/321 (телефон, планшет RU, desktop, ultrawide DE),
  Tools 143/143, панель (телефон / drawer / desktop: строка, X, Escape, клик вне, меню языка над
  панелью, back/forward, прямые URL EN/AR/JA), Filter-sheet, Sort-sheet, поиск.
- Изменения этапа (итог): `templates/catalog.html`, `static/site.css`, `static/table-layout.css`,
  `static/site.js`, `catalog/tests/test_responsive_layout.py` (12 тестов),
  `catalog/tests/test_number_order.py`; история: `catalog/product_history.py`,
  `templates/product_history*.html`, `static/product-history*.css` (состояние `review`, иконка),
  `catalog/tests/test_product_history.py`, `docs/timeline.json`, `docs/DECISIONS.md`,
  `docs/PRODUCT_HISTORY.md`, этот статус. Данные каталога, master XLSX, номера, цены, даты,
  оценки и publication state не менялись.
- Исправлены попутно (существовали до этапа): подгрузка на телефоне останавливалась на 200 из 321;
  меню языка после открытия другой записи вело на первую; «назад» к `?tab=` открывал Overview;
  скрытые подписи цены растягивали документ app-shell; центрирование названия в строке; крошки
  панели у края; одноимённые фильтры `status` могли отправить устаревшее значение.
- Известные ограничения (не блокируют): на touch-планшете иконки фильтров заголовка 32 px и ссылка
  «№» 24×40 (основной путь — кнопки Фильтр/Сортировка 40–44 px); Tools 143 ≤ первой порции 150 —
  догрузка Tools проверена как полная выдача; проверка — эмуляция в Chrome, не физические
  устройства, Safari/iOS не проверялись. Вне этапа, существовали раньше: CSP-ошибки inline-стиля на
  Local `/history/` и в отладочной 404 Django (DEBUG); `form-action ''none'` в `timeline.html`.
- Local / GitHub / Production: `main` содержит утверждённый код; рабочий Local 18810 запущен до
  этапа и держит в памяти старые шаблоны — для просмотра итогового `main` перезапустить его
  ярлыками «AIpedia — Stop Local» / «AIpedia — Local» (исполнитель 18810 не перезапускал);
  изолированные 18811 (ветка) и 18812 (проверка `main`) — временные. GitHub — push `main` (см.
  итоговый commit в сообщении выпуска документации). Production не затрагивался: `/healthz` по
  `docs/RELEASE.md` — `a51c0a1`.
- Не завершено: ничего по этапу. Следующим выполнить: выпуск Production только по отдельной команде
  владельца на конкретный commit по `docs/RELEASE.md`. Worktree
  `C:/Users/dimon/.claude/worktrees/aipedia-adaptive-ui` и ветку `feature/adaptive-ui` можно удалить
  после этого (ветка полностью в `main`).

## catalog-master-v015 final — опубликовано и проверено, 2026-09-27 03:23 UTC

- Итог этапа (Local): «116 Tools» — это № первой строки (116 инструментов с датой, 27 без
  даты), а не количество: вкладка = счётчик = строки после полной загрузки = база = 143;
  у счётчика добавлено пояснение (22 языка). Страны с источниками — 11 моделей,
  15 инструментов (3 в очереди: Aider, llama.cpp, Roo Code). +70 цен, +19 доступов,
  +25 независимых оценок Epoch AI; 20 проверенных пробелов цен и 9 пробелов оценок в
  master (`*_status`). Отчёт — `docs/history/2026-09-27-catalog-master-v015-final.md`.
- Изменено (не закоммичено на момент записи): `catalog/master_sync.py`,
  `catalog/catalog_master.py` (NATURAL_KEYS), новый `catalog/catalog_qa.py` + команда
  `catalog_master qa`, валюта цен (`catalog_tags.price`, `comparison.price_matches`),
  пояснение счётчика (`views`, `catalog.html`, UI-строки), нейтральная подпись «Цена»,
  controlled terms единиц, `data/evaluation_gap_notes.json`, тесты, документы,
  `tools/master_v015_final_2026_09_27.py`; master v015 и рабочий Local.
- Git: `main` fast-forward до опубликованной линии `00cb8f4`; прежняя незакоммиченная
  работа истории сайта сохранена (`backups/main-wip-20260927/`), конфликты поискового
  кода — в пользу проверенного на Production. Local 18810 перезапущен на текущем коде.
- Проверено: 290 тестов (289 OK, 1 skip); `catalog_master qa` PASS; HTTP 207/207;
  сохранность дат/номеров/ID PASS; браузер: счётчик Tools, флаги, цены ₹.
- Local / GitHub / Production: Local 18810 и `main` на `a51c0a1` (+ документный
  commit результатов); GitHub `main` синхронизирован; Production `/healthz` =
  `a51c0a1aed2f…` (tag `release-2026-09-27-catalog-master-v015-final`), 321/143,
  backup до/после, `copied_sqlite=false`.
- Public PASS: `final_check` 207/207, `catalog_master qa --production` PASS,
  GSD 34/34, 45/45 старых URL; `/history/` на Production — 404.
- Итог: Local PASS → Timeline PASS → GitHub synced → Production PASS → Public PASS.
- Не завершено (очередь качества данных, не блокирует): страны Aider, llama.cpp,
  Roo Code; 20 проверенных пробелов цен (в т.ч. MiniMax — валюта не подтверждена;
  SourceCraft — активировать тарифы 2026-10-01); 9 пробелов независимых оценок;
  17 старых моделей с датой без ссылки на доказательство. Следующим выполнить:
  2026-10-01 проверить и активировать цены SourceCraft через master; при новых
  снимках Epoch повторить сопоставление точных версий.

## catalog-master-v015 — опубликовано и проверено, 2026-09-27 01:35 UTC

- Итог: Local PASS → Timeline обновлён → Production опубликован → Public PASS.
  11 новых моделей (Claude Opus 5.5, GPT-6 Sol, GPT-6 Luna, Gemini 3.8 Flash TTS,
  Gemini 3.8 Flash-Lite TTS, Nemotron 3 Diarization, Speech TTS Live, Sarvam Vision 2.1,
  GLiNER2.5-Decide, FLUX 3 Action DROID, FLUX 3 Action SO-101) — №311–321 по дате
  22–24.09.2026; +4 инструмента, 9 исправлений; 321 Models / 143 Tools. NEEDS_REVIEW
  (Speech Realtime Max TTS Live, CLM-v0.1-8B, AX) не опубликованы. Отчёт —
  `docs/history/2026-09-26-catalog-master-v015.md`.
- Изменено в `main` (не закоммичено): канонический master v015 (+ резервные копии в
  `backups/catalog-master-v015-20260926/`), `catalog/catalog_master.py`,
  `catalog/master_sync.py` (новая модель приходит со своими ценами/доступом; проверка
  итогового состояния для черновиков), тесты, `tools/master_v015_import_2026_09_26.py`,
  `docs/CATALOG_MASTER.md`, `docs/RELEASE.md`, `docs/timeline.json` (веха v015),
  `catalog/product_history.py` (источник отчёта), тесты истории (счётчики вех).
  Рабочий Local: sync 56 изменений, переводы 440, `check: OK`, повтор 0.
- Выпуск: ветка `release/catalog-master-v015` от опубликованной линии `0702405`
  (не от `main`), commit `e36acfa`, tag `release-2026-09-26-catalog-master-v015`,
  документы после выпуска — `00cb8f4`; worktree
  `C:/Users/dimon/.codex/worktrees/catalog-master-v015/AIpedia`. `/healthz` =
  `e36acfa…`; backup до/после на сервере; `copied_sqlite=false`.
- Проверено: 272 теста в `main` (271 OK + 1 skip), 274 в кандидате и в распакованном
  архиве; Local HTTP 144/144; пробный перенос = рабочий Local; серверный preflight на
  онлайн-копии; Public 144/144, GSD 34/34, 45/45 старых URL.
- Расхождения, найденные в начале: в `AI_CONTEXT/` не было канонического
  `AIpediya_Model_Verification_Master.xlsx` (был только `…_updated_2026-09-26.xlsx` =
  v015); порт 8765 занят другим приложением (`app.server`, не AIpedia) — не трогался;
  Local AIpedia на 18810 запущен в 10:39 и обслуживает код до правок рабочего дерева
  (QA делался отдельным сервером 18811 с текущим кодом на той же базе); Production
  работал на `61adedd` из ветки `codex/search-visibility-update`, которой нет в `main`.
- Не завершено: push ветки `release/catalog-master-v015` и tag в GitHub (не
  выполнялся — ждёт команды владельца); сведение `main` с линией выпуска
  (`0702405`/`00cb8f4`); перезапуск Local 18810 для текущего кода — на усмотрение
  владельца (ярлыки Stop/Start Local). Следующим выполнить: push по команде, затем
  слить линию выпуска в `main` без потери незакоммиченной работы истории сайта.

## Маркеры автономной истории — Local, 2026-09-26

- Уточнение владельца: «Автономная история» — это локальный автономный
  `timeline.html`, лента изменений проекта, не каталог моделей. После
  визуальной проверки владельца этап завершён в Local, хотя сам просмотрщик
  не публиковался на Production. Прежний жёлтый кружок ошибочно связывал
  `open=true` (не опубликовано) с «работа ещё идёт».
- Изменено: в `docs/timeline.json` готовность (`progress`) отделена от
  публикации. Для автономной истории — `done`, для Paid Search — `planned`;
  опубликованные вехи считаются `done`. В автономном HTML и Local-маршруте
  синий кружок с галочкой означает выполнение, жёлтый с многоточием — работу
  в процессе, жёлтый пунктирный — план. Запланированная карточка также
  выделена жёлтой рамкой. Добавлена краткая легенда, а
  автономная история подписана «Готово в Local» с Local ✓ / Production —.
- Local / GitHub / Production: изменены только локальный реестр, вывод
  истории и стили; опубликованный сайт и каталог не менялись. Не завершено:
  визуальное подтверждение нового оформления кружков владельцем; агентский
  просмотр `file://` остаётся недоступен по политике браузера. Проверено:
  `catalog` 266 тестов — OK (1 skipped), `git diff --check` — PASS;
  `timeline.html` и AI_CONTEXT пересобраны. Следующим выполнить: принять
  замечания владельца по новому виду маркеров, если появятся.

## Автономная история — визуальная проверка владельца завершена, 2026-09-26

- Владелец сообщил о текущем `timeline.html`: «готово я проверил». В
  `docs/timeline.json` снята пометка «Визуальная проверка ожидается» и
  записано завершение визуальной проверки без новых замечаний. Старое
  ожидание в отчёте доводки сохранено как датированный снимок с дополнением.
- Local: автономная история и её ярлык остаются локальными. Агентская
  визуальная проверка `file://` по-прежнему недоступна из-за политики
  браузера; сообщение владельца не выдаётся за агентский скриншот или
  разрешение на Production. Опубликованный Search Visibility Optimization
  и отдельный план Paid Search не менялись.
- Не завершено: отдельных новых замечаний нет; Production-публикация истории
  не запрашивалась и не требуется. Следующим выполнить: учитывать только
  конкретные последующие замечания владельца. После обновления реестра
  проверить Local и пересобрать `timeline.html`/AI_CONTEXT.

## Paid Search Experiment / Google Ads — PLANNED, 2026-09-26

- Изменено: в `docs/timeline.json` добавлена отдельная открытая карточка
  `PLANNED` для paid acquisition. Органические GSD-1.0 и Search Visibility
  Optimization уже опубликованы; платный трафик не относится к росту
  органического ranking и не смешивается с Search Console metrics.
- Следующий этап **после контрольного замера 30.09.2026**: через Google
  Keyword Planner собрать большой многоязычный master запросов по выбранным
  странам с volume, competition и CPC, кластеризовать и выбрать небольшой
  первый набор Exact/Phrase для Search-кампании. Общий жёсткий бюджет — не
  более $10–15 в месяц (верхний предел $15), а не бюджет на каждую группу.
- Local / GitHub / Production: пока изменены только локальные реестр и история;
  рекламная кампания не создана, не запущена и ничего не потратила.
  После фактического запуска нужно обновить Timeline реальными настройками,
  расходом, показами, paid clicks и результатами отдельно от органических
  GSC impressions/clicks/positions.
- Проверено: 9 целевых тестов истории/упаковки PASS, JSON и Django-шаблоны
  валидны; `timeline.html` и AI_CONTEXT пересобраны. Автономный `file://`
  HTML не удалось визуально открыть инструментом браузера: политика разрешает
  только `http:` и `https:`; обход ограничения не выполнялся.
- Не завершено: контрольный замер 30.09, Keyword Planner master, выбор стран
  и ключей, создание кампании. Следующим выполнить: сначала контрольный
  органический замер, затем исследование спроса и небольшой проверяемый
  план Search-кампании; не отмечать `LAUNCHED` до реального запуска.

## Search Visibility Optimization — опубликовано, 2026-09-26 21:47 UTC

- Изменено: на основе аудита и описанного ниже Local P0 выпущен конечный
  поисковый пакет: 45 URL GSC (25 одношаговых 301, 19 корректных 404,
  один фрагмент 200/noindex), точечные robots-исключения без широкого
  card `?page=` Allow, чистые SSR-ссылки, исправление IndexNow для 301/302,
  две обоснованные EN/RU страницы сравнения контекста и официальных API-цен.
  Данные каталога и публикация 310 Models / 139 Tools не менялись.
- Local: изолированный worktree `codex/search-visibility-update`, финальный
  commit `61adedd6ea5e6a0955d51d87374fa2fa9bcc7799`, tag
  `release-2026-09-26-search-visibility-optimization-v2` опубликованы в GitHub.
  268 тестов: 267 PASS + 1 ожидаемый skip; `seo_report` 10 193 Local sitemap
  URL, 359 HTML и 320 обходных ответов без проблем (обход ограничен лимитом);
  45/45 legacy URL и браузерный переход с `?page=2` проверены.
- Production: штатный code-only deploy завершён, `/healthz` вернул финальный
  commit и `environment=production`; серверная SQLite сохранена, backup
  до/после и rollback указаны в
  `docs/history/2026-09-26-search-visibility-release.md`. На публичном сайте
  10 190 sitemap URL в 22 картах, 45/45 legacy URL и 1657/1657 Search QA
  PASS; Cloudflare cache только `/robots.txt` очищен и актуальные правила
  перепроверены. GSD public check 34/34 PASS.
- Поисковые системы: существующий IndexNow scheduler принял 330 уведомлений
  о старых 301 URL и четыре новых индексируемых URL; `active_pending=0`,
  `failed_unresolved=0`. GSC по-прежнему показывает за 24.09 только 41
  impression, 0 clicks, average position 8.5; отчёт индексации обрабатывается.
  Bing performance также ещё готовится. Google по бренд-запросу пока выводит
  старый `/?lang=en`: нового обхода и роста ranking этим не доказано.
- Local / GitHub / Production: поисковый код проверен Local, сохранён в GitHub
  и подтверждён на Production; первоначальный `main` сохраняет отдельные
  незавершённые изменения истории/master. Этот статус и AI_CONTEXT обновляются
  в `main` без смешивания с выпуском. Не завершено: подтверждение нового
  canonical/indexed pages и поисковых показов после recrawl, доступ к Naver
  после восстановления аккаунта. Следующим выполнить: через несколько дней
  снять GSC/Bing indexing, queries, страны и SERP повторно; не считать
  принятие IndexNow доказательством индексации.

## P0 Search/Indexing URL cleanup — исторический Local QA, позднее опубликовано

Следующие строки фиксируют состояние на 20:13 UTC **до** разрешённого выпуска;
их формулировки «Local-only», «Production не менялась» и «ожидается выпуск»
исторические. Актуальный статус — в разделе Search Visibility Optimization выше.

- Изменено: `catalog/locale_urls.py`, `catalog/middleware.py`, `catalog/views.py`,
  новый конечный список `catalog/legacy_search_urls.py` (ровно 45 URL из GSC
  Pages), регрессионные тесты в `catalog/tests/test_global_search_discovery.py`,
  раздел Local P0 в `docs/SEARCH_DISCOVERY.md`. Старые полные карточки с
  `?lang=`, `page`, `sort`, `kind`, `tab` переходят одним 301 на чистую карточку
  соответствующего языка; подтверждённые alias — сразу на опубликованный
  Record ID. Непубличные записи остаются 404; старый AJAX `partial=rows`
  остаётся фрагментом с `noindex`. Фильтры/сортировка старых **каталогов**
  сохранены ради их смысла и работы приложения; их назначения по-прежнему
  robots-blocked/noindex. В robots добавлены только точные GSC-исключения с
  `$`, без широкого `Allow` для `?lang` или любых фасетов.
- Local факты: 45/45 GSC URL разрешаются будущими robots-правилами,
  добавление параметра к любому из них остаётся запрещённым. По существующей
  Local DB — 25 полных карточек → 301 → конечный 200/self-canonical, 19
  снятых URL → 404, 1 публичный HTML-фрагмент → 200/noindex (два других
  фрагмента входят в 19 ответов 404). Через настоящий локальный WSGI/HTTP
  проверены 301→200 EN/RU, `/robots.txt` и `/sitemap.xml`; отдельный
  тестовый порт завершён, чужие процессы не остановлены. Local robots
  остаётся `Disallow: /`; Production-подобные правила проверены только через
  `override_settings`, Production не менялась.
- Проверки: `manage.py test catalog --settings=aipedia.test_settings` —
  **264 запущено: 263 PASS, 1 skip**. Проверены чистые canonical/hreflang на EN/RU/zh-Hans
  карточках и корнях; 22 чистых sitemap child URL, 3 языковые карты без query
  в `<loc>`/alternates, 4 локальных страницы и их внутренние ссылки без
  `lang/kind/partial`; `git diff --check` чистый. Сверено с официальными
  Google robots/redirect/facet и Bing Webmaster Guidelines (ссылки в
  `docs/SEARCH_DISCOVERY.md`). Дополнительно после локального
  `collectstatic --noinput` штатный read-only `seo_report --html 2 --crawl
  --crawl-limit 500` проверил 10 189 sitemap URL (0 проблем), 355 HTML
  страниц (0 проблем), 500 обходных ответов (все 200, скрытых карточек в
  ссылках 0). Лимит остановил очередь до полного обхода: достигнуты 339/449
  карточек, `queue_left=21697`; это не отчёт о недостижимости остальных.
  Отдельный обход всех шести страниц пагинации в каждом из EN/RU нашёл
  ссылки на **449/449** публичных карточек в обоих языках, 0 закрытых robots
  ссылок и 0 пропусков. JSON отчёта в ignored
  `outputs/01a0df19-0f44-7c40-8d47-280b013f5d84/p0_local_seo_report.json`.
- Local / GitHub / Production: P0-правка в Local незакоммичена;
  GitHub не менялся; Production остаётся на v014 без этой правки. Существующие
  незавершённые файлы истории, master и аудита сохранены как были; эта работа
  к ним не относится. Расхождение с прежним статусом: прежний план предполагал
  отдельную Local-итерацию `?lang=`, она выполнена здесь; новый релиз и
  фактический recrawl поисковиками не подтверждены.
- Не завершено: реальная переиндексация GSC/Bing после будущего утверждённого
  выпуска, owner approval и сам выпуск. Следующим выполнить: владельцу
  проверить эту Local-правку; только по отдельной команде на конкретный пакет
  провести выпуск по `docs/RELEASE.md`, затем проверить URL Inspection и
  динамику старых URL в GSC. Новые comparison/pricing/SEO landing pages в
  этой итерации не создавались.

## Аудит поисковой видимости — Local, 2026-09-26 19:30 UTC

- Изменено: создан один итоговый файл
  `outputs/01a0df19-0f44-7c40-8d47-280b013f5d84/AIpediya_Search_Visibility_Audit_2026-09-26.xlsx`
  (4 листа: вывод/приоритеты, поисковики и метрики, 52 замера выдачи, технический
  аудит). Выполнены только публичные GET и read-only просмотры поисковой выдачи,
  Google Search Console, Bing Webmaster и Cloudflare. Production, каталог, master,
  DNS, роботы, IndexNow и настройки кабинетов не изменялись; GitHub не менялся.
- Проверено: 22/22 языковые карты HTTP 200, 10 186 URL суммарно; 9
  индексируемых подборок, self-canonical и 23 hreflang на выбранных страницах.
  GSC Domain property показывает 41 показ, 0 кликов, среднюю позицию 8,5
  за фактически доступный день 24.09; sitemap Successful и 10 032 discovered.
  Отчёт индексирования ещё обрабатывается. Bing: sitemap Success, примерно
  1,4K discovered и без ошибок; Search Performance ещё готовится. Явные
  позиции/глубина и URL зафиксированы по 52 запросам в 8 системах.
- Подтверждённый риск: robots.txt закрывает старые параметры `?lang=` на
  карточках, тогда как GSC ещё показывает эти адреса; для опубликованных карточек
  они отвечают 301, для некоторых снятых/несуществующих — 404. Исправление
  требует отдельной Local-правки с узким исключением и проверкой, что фасеты
  останутся закрыты. Нет доказательства, что именно это вызвало низкие позиции.
- Границы: браузерный IP США, параметр страны не имитирует местного пользователя;
  это разовые SERP-снимки. Yandex Webmaster в текущем браузере требует вход;
  Naver Search Advisor всё ещё без подтверждённого восстановления; Baidu
  Webmaster не подключён. Число индексированных URL, backlinks и метрики этих
  кабинетов не выдумывались. Cloudflare Web Analytics имеет лишь один визит/один
  образец LCP, недостаточно для оценки Core Web Vitals. Публичный запрос с
  браузерным User-Agent вернул 200, а стандартный Python urllib UA получил
  Cloudflare 403 code 1010; это не доказательство блокировки поисковых роботов,
  потому что Cloudflare отдельно показывает успешные запросы Google/Bing.
- Расхождение прежнего статуса: предыдущий блок ниже называл GSC/Bing/Cloudflare
  недоступными из-за Browser Use; в этой сессии доступ к ним восстановился и
  метрики сняты. `docs/timeline.json` всё ещё указывал старый Production
  revision `634778…`; текущий выпуск v014 подтверждён верхним блоком статуса и
  `/healthz`, реестр обновлён без изменения истории старых выпусков.
- Не завершено: фактический индекс/причины исключения после формирования GSC
  coverage, текущая очередь IndexNow, статистика Yandex/Naver/Baidu, Local QA
  возможных SEO-правок. Следующим выполнить: после обработки Search Console
  проверить выборку URL Inspection; затем в отдельной Local-итерации исправить
  миграцию `?lang=` и подготовить проверенные страницы сравнения/цен из master.
  Любой Production выпуск — только по отдельной команде владельца.

## Catalog master v014 — опубликовано и проверено; этап закрыт — 2026-09-26 18:55 UTC

- Статус: **опубликовано и проверено** (выпуск catalog-master-v014, отчёт
  `docs/history/2026-09-26-catalog-master-v014-release.md`). Приёмка и разрешение
  владельца — `D-2026-09-26-owner-acceptance-v014`.
- Production: release_id пакета `1a10421d9d7bcd68b2b1224ce74843bebd932e2c` (не git-commit; архив
  `aipedia-code-1a10421d9d7b.zip`, SHA-256
  `c80469b298a8221655030c735475fef2c945524a81c6d4466e2eaa74e4ec4377`), deploy
  2026-09-26 18:18Z, `deployed-origin-verified`, backup
  `/srv/aipedia/backups/aipedia-before-code-20260926T181857Z.sqlite3`. Публично
  310 Models / 139 Tools; публичная проверка — `artifacts/catalog-master-v014/public_check.json`.
  Git-коммит с изменениями выпуска — `20807cd542ec…` (tag ниже); код архива с ним совпадает.
- Серверная база обновлена штатно с резервными копиями и сохранением истории;
  локальная SQLite поверх серверной не копировалась.
- Что получает посетитель (`artifacts/catalog-master-v014/visitor_check.json`,
  2026-09-26 18:48:27Z): `/healthz` → release `1a10421d9d7b…`, production; `/` и `/ru/`
  (и с параметром против кэша) — Models 310, Tools 139, «150 / 310», первые номера
  310, 309, 308; `cf-cache-status: DYNAMIC` — Cloudflare HTML не кэширует, старой копии
  на краю нет. Веб-инструмент этой сессии (WebFetch) в 18:49Z тоже получил 310/139.
  Значение 304/138 во внешнем инструменте — его сохранённая копия страницы до выпуска
  18:18Z, а не выдача сайта; повторный deploy и правки Cloudflare не нужны и не делались.
- Ограничение сборщика AI_CONTEXT (до исправления извлечения): `tools/pack_ai_context.py`
  извлекает из `docs/RELEASE.md` только Git-коммит (`production_commit_from_docs`),
  release_id опубликованного пакета не извлекает. Запрос исполнителю сборщика (его
  незакоммиченные правки в этом файле не трогались): добавить извлечение строки
  «release_id опубликованного пакета: `…`» в MANIFEST/AI_CONTEXT.md и тест к ней; до
  этого сверять выпуск по `docs/RELEASE.md` и `/healthz`.
- Исправлено по приёмке: порядок номеров (`D-2026-09-26-number-order`), GPT-Live 1
  (`D-2026-09-26-gpt-live-1-classification`). Первый серверный preflight остановил
  выпуск на расхождении pk цен (`offer-552…555`); план переведён на стабильные ключи
  строк, второй preflight и выпуск прошли.
- Master: `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` v014 (v013 — резервная
  копия в `backups/catalog-master-finalize-20260925/`); после `import --production`
  SHA-256 `94054b1392cbbee0140230883b2b557a106c6101ad23119e7ddf9542c2dba950`,
  Status PUBLISHED = On Production у 310 + 139 записей, расхождений 0.
- Git: commit `20807cd` (только файлы этой задачи; параллельная работа над
  историей сайта не включена), tag `release-2026-09-26-catalog-master-v014`, push
  в `origin/main` выполнен; последующие коммиты — только документы статуса.
- Local: 310 / 139, совпадает с Production по выдаче (списки EN/DE, 1 248 карточек,
  20 редиректов).
- Тесты: рабочее дерево 260 OK (1 skip); архив выпуска в чистом окружении 258: 257 OK,
  1 skip (`fcntl`, POSIX-only), 0 failed.
- Изменено: master v014, Local и Production (310/139), документы выпуска. Не завершено:
  извлечение release_id сборщиком (за исполнителем сборщика). Следующим выполнить:
  новая задача только по поручению владельца; этап базы закрыт. Отложенная очередь
  (не возвращаться без поручения): 441 модель резерва, 30 публичных
  дополнений доступа/цен, 94 служебных расхождения, Kimi K3 (max), Grok Voice API,
  основание показа оценок AA, вычитка машинных переводов.

## Catalog master v013 — кандидат (заменён выпуском v014) — 2026-09-26 17:00 UTC

- Статус на тот момент: основной этап базы завершён; кандидат проверен; ожидалась
  приёмка. Заменён выпуском v014 (см. блок выше).
- Окончательный кандидат (полные SHA-256; сводка — `artifacts/catalog-master-v013-final/FINAL_CANDIDATE.json`):
  - код: `artifacts/code-release/aipedia-code-954db5a4586b.zip`,
    `c623be31641c4ad1175ac911599555ddab9646ceba8e5333e71ee0d5cc8c7618`; id выпуска
    `954db5a4586bf1d2b36fabb5ba0647b112bf17b3` = digest файлов из
    `data/release/v013/CANDIDATE_FILES.txt` поверх базового commit
    `b3116cf6dc563ccbd3c7e12eff8b428e40967547`; 304 файла, без SQLite/секретов;
  - план каталога `data/release/v013/catalog_plan.json`:
    `fd6281a04eb0962381cc9651374a90f3d69f99fc5276be6257e0b78cdace1c13`;
  - переводы `data/release/v013/translations.json`:
    `4c8f3c1354741cc6a12fddb40f450e2012b46d7ccc6cdd0a97074e513f58d075`;
  - манифест публикации `data/release_state.json` (309/140):
    `c13563fd4e9ff1d010c3ff0ca6b5b68e8996dfd9560361ada15264bcc70a2c33`;
  - master `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` (v013):
    `7e0081324012706d5e2ac06debe1eefc4929b2785fbbdaada0ec91607626203c`.
  Если после commit/tag пакет изменится — сверить с этими суммами и проверить
  заново; прежний PASS не переносится.
- Тесты архива (распакован вне проекта, чистое окружение: системный PATH + git,
  без `AIPEDIA_*`/`PYTHON*`, `.env.local` и рабочего дерева; `.venv` только с
  библиотеками; `python -E -s manage.py test catalog --settings=aipedia.test_settings -v 2`):
  найдено 246, успешно 245, пропущено 1 (`fcntl` только POSIX — проверяется на
  Linux-хосте), упало 0. Рабочее дерево: 248, OK (1 skip) — на 2 теста больше
  из-за незакоммиченных тестов параллельной работы над историей сайта.
  `test_import_research` больше не читает незакоммиченный `data/research/…json`:
  контролируемый архив создаётся в тесте, проверки сохранены и дополнены.
- Восстановление: внутри `apply-plan` (подделанный план → отказ без записи; сбой
  посреди записи → откат); весь выпуск (сценарий
  `artifacts/catalog-master-v013-final/release_process_recovery_script.py` на
  окончательном архиве: сбой на переводах после успешного `apply-plan` и сбой
  после переключения приложения → код побайтно = предыдущее приложение
  (`634778807b2e`), БД = исходная: схема 0018, та же сумма каталога, 304
  публичных; `migrate --check` предыдущего кода OK). supervisor/права Linux не
  воспроизводились.
- Граница Production: испытан исходный снимок Local, сверенный с публичными
  данными Production построчно (304 + 138), — не копия серверной БД. Серверный
  preflight `apply-plan` обязателен; при несовпадении — остановка без
  принудительного применения и без перестроения плана на сервере.
- Рабочий Local (для визуальной приёмки, `127.0.0.1:18810`): 309/140, состав —
  `local_final_composition.json` (`a1e91589839cd280ca7468d16b682528abc4aa60b392bbd41648f651e63e79e3`),
  база `2fd2aa6350224b37f467e5371128032c2219b3107142010560764c66db6611ba`; в этом
  шаге не менялась. Проверка выдачи — текст/DOM/HTTP, не визуальная приёмка.
- Отложено (очередь, не блокирует): 441 модель резерва; 30 публичных дополнений
  доступа/цен; 94 служебных расхождения; Kimi K3 (max), Grok Voice API; основание
  показа оценок AA; вычитка машинных переводов.
- Реальных технических блокеров не осталось. Следующим выполнить: владельцу —
  визуальная приёмка Local; выпуск — только после отдельного разрешения на этот
  кандидат, по `docs/RELEASE.md`.

## Автономная история и финальная сверка поиска — 2026-09-26

### Последняя Local-only редакция истории — 2026-09-26

- Интерфейс автономной истории доведён по исходникам и поведению локального
  `timeline.html` StratForge AI без изменения его файлов: широкая область, две
  среды AIpediya, лента дат с узлами, короткие change chips и правая панель 510 px.
  Основная карточка целиком открывает свои подробности; добавлены Enter/Space,
  Escape, закрытие крестиком/фоном, удержание фокуса и восстановление фокуса.
  В карточках сред функции GSD-01…GSD-10 отображаются простыми номерами 01…10;
  внутренние идентификаторы реестра сохранены. В открытой панели каждое изменение
  выводится отдельной карточкой; GSD-1.0 раскрывает 10 нумерованных карточек
  критериев, прочие вехи — по одной карточке на записанное изменение.
  Данные остаются из `docs/timeline.json` и разрешённых документов.
- `timeline.html` и ярлык оставлены автономными; Production не менялся. Новая
  запись — `docs/history/2026-09-26-offline-history-reference-match.md`.
- Проверено: после разделения изменений целевые тесты истории 5/5, Django system check чистый, JS `node
  --check` проходит. Визуальное окно и реальное поведение не удалось проверить:
  Computer Use отказался до захвата с сообщением `could not determine the current
  browser URL on Windows with enough confidence to enforce policy`. Снимки экрана
  результата не получены; не обходить ограничение через другой браузер или CDP.
- Полный `manage.py test catalog`: 238 тестов — 235 PASS, 2 FAIL, 1 skip. Два
  отказа только в `catalog.tests.test_chronology` (тесты
  `test_manifest_dry_run_idempotency_coverage_and_rollback` и
  `test_same_day_uses_name_and_unknown_stays_last_both_directions`); файлы хронологии
  уже были изменены до этой задачи и здесь не редактировались.
- Не завершено: визуальная и интерактивная проверка исполнителем и приёмка владельца;
  Owner Approved не выставлен. Следующим выполнить: владелец проверяет собранную
  страницу через существующий ярлык и передаёт замечания либо принимает вид.

- Причина переделки: владелец не принял прежнюю страницу — её сгенерировали из
  публичного `base.html` и общих стилей, поэтому она сохраняла оболочку каталога и
  не соответствовала компактному макету. Нынешняя редакция — отдельный минимальный
  шаблон `templates/product_history_standalone.html` и CSS
  `static/product-history-offline.css`; только две среды, устойчивые ID функций
  GSD-01…GSD-10, горизонтальная лента и подробности в этом же файле. Тёмная тема
  включена по умолчанию; язык и тема страницы переключаются независимо от сайта.
- Статусы истории разделены: GSD-1.0 и последующая Naver/IndexNow activation —
  опубликованные Production milestones. Исправление автономной истории — отдельная
  Local-only карточка без Production deploy. Текущий Production сверён live:
  `https://aipediya.com/healthz` вернул `status=ok`, release
  `634778807b2e82ca52dea1de150ea0810950d644`, совпадающий с `docs/RELEASE.md`.
  Старый `ed103a3` остаётся доказательством выпуска от 25.09, не текущим состоянием.
- Ярлык `AI_CONTEXT/AIpedia — История сайта.lnk` всё ещё указывает на
  `C:\Users\dimon\Documents\AIpedia\timeline.html`, без аргументов; порт
  Local `127.0.0.1:18810` сейчас не слушает. Просмотр не требует Local, сети,
  PowerShell или запуска сборщика. `tools/pack_ai_context.py` сначала пересобирает
  HTML из `docs/timeline.json` и разрешённых источников. Владелец при открытии ничего
  не запускает.
- Проверки этого изменения: `manage.py test catalog --settings=aipedia.test_settings`
  — **237 PASS, 1 skip**, System check чистый; тест автономной истории 4/4.
  `timeline.html` — около 318 KB, 6 карточек в каждой edition, 12 встроенных
  шаблонов источников, 0 внешних asset requests; два встроенных JS скрипта прошли
  `node --check`. В HTML нет email или browser tab/session id; значение ключа
  IndexNow в документы/HTML не добавлялось. Shortcut target и отсутствие Local
  процесса проверены read-only. Проверка ZIP обнаружила посторонние Windows cache
  файлы `.db` в рабочем слое архива; фильтр `pack_ai_context.py` теперь исключает
  SQLite/DB семейства, тест проверяет их отсутствие. Cache-файлы на компьютере
  сохранены и не изменялись.
- Визуальную/интерактивную проверку этой новой редакции и время полной отрисовки
  подтвердить не удалось: Browser Use для `file://` в прежнем отказе разрешает только
  HTTP/HTTPS и запрещает альтернативные способы доступа. Не обходить это ограничение;
  новая визуальная приёмка владельцем остаётся открытой. Наличие Local CSS/template
  не считать Owner Approved.
- Production smoke, только HTTP read-only 2026-09-26: `/`, `/robots.txt`,
  `/sitemap.xml`, `/healthz`, `/ru/`, `/ar/`, страница модели GPT-5.3-Codex,
  карточки инструментов Codex и Claude Code — HTTP 200. В sitemap index 22 child
  maps; проверенные RU/AR/EN maps содержали по 456 URL. Проверенные HTML содержат
  canonical, 23 hreflang и x-default; AR — `lang=ar`, `dir=rtl`; Naver verification
  meta-tag присутствует в серверном HTML. Это ограниченный sample, не полный crawl.
- Текущие кабинеты GSC, Bing и Cloudflare не открылись: Browser Use вызовы к каждой
  из видимых вкладок прямо отказали по `saved user permission`, несмотря на прежние
  разрешающие настройки интерфейса. Причина несоответствия не установлена; обход
  запрещён. Yandex Browser не был в списке подключённых браузеров. Их прошлые
  статусы остаются сведениями прежних отчётов/владельца, текущие ошибки, статистика,
  sitemap processing и UI записи Cloudflare недоступны. Публичная DNS TXT-проверка
  сейчас вернула ожидаемые Google и Yandex значения; дубликаты и другие DNS типы
  через панель не аудированы.
- Naver: ownership/sitemap — ранее подтверждены скриншотами владельца; meta-tag
  дополнительно найден live в Production HTML. Запрос recovery по сообщению владельца
  принят Naver, номер не показан, ожидается email; account recovery не подтверждено.
  После restriction Search Advisor status не перепроверен; повторных действий нет.
  Browser Use incident остаётся отдельным открытым внешним инцидентом. IndexNow и
  Brave статусы остаются из отчёта/сообщения владельца: 10 032 URL были приняты,
  scheduler/lock работают по release report, Brave re-fetch принят; индексация не
  подтверждена. Текущий pending outbox и ключевой URL без доступного read-only канала
  не перепроверены.
- Контентное покрытие осмотрено в существующих страницах; реестр направлений и
  подтверждённых пробелов — `docs/SEARCH_DISCOVERY.md`. Новые страницы и массовый
  контент не создавались. Лицензия datasets, качество данных и переводов остаются
  отдельными незавершёнными вопросами.
- Не завершено: владельцу визуально проверить новую автономную страницу и работу
  языка/темы/ленты/подробностей после открытия ярлыка; Search Console metrics и
  актуальные UI статусы взять из кабинетов, когда устранится Browser Use доступ.
  Naver — ожидать email. Следующим рабочим этапом после поискового snapshot остаётся
  отдельный эпизод Baidu / Китай; в этой задаче он не начинался.
- Изменено только Local history viewer, его тесты, история/правила и AI_CONTEXT.
  Production, DNS, каталожная база, поисковые registrations и StratForge не менялись;
  deploy не выполнялся. Параллельные catalog master правки сохранены отдельно.

## Автономная история сайта — первая редакция, заменена визуальной правкой 2026-09-26

- Причина задержки: ярлык `AI_CONTEXT/AIpedia — История сайта.lnk` раньше
  запускал PowerShell → `tools/local/start-local.ps1 -OpenPath /ru/history/`;
  launcher подготавливал каталог, запускал migrate/check, поднимал Waitress и
  только затем открывал маршрут.
- Изменено: корневой файл проекта
  `C:\Users\dimon\Documents\AIpedia\timeline.html` генерируется из
  `docs/timeline.json`, той же Django history view и allowlist source-документов.
  HTML содержит RU/EN editions, 4 milestone cards, package details, все разрешённые
  документы-источники, CSS/JS/SVG assets и видимое время генерации, которое
  обновляется при каждой штатной пересборке.
  Сетевые resource-загрузки запрещены CSP; email и session ID редактируются при
  экспорте. Сборка автоматически выполняется перед `tools/pack_ai_context.py`;
  при открытии HTML ничего не запускается/собирается.
- Изменено: существующий ярлык внутри `AI_CONTEXT` теперь имеет TargetPath на
  корневой `timeline.html` без аргументов. Windows default association — Edge
  (`MSEdgeHTM`); запуск через `.lnk` создал вкладку Edge `file:///.../timeline.html`.
  Ярлык не запускает PowerShell. Local был остановлен штатно, порт 18810 не
  слушал; он после открытия не запускался. Маршрут Local `/ru/history/` и source
  routes сохранены.
- Проверки: `manage.py test catalog --settings=aipedia.test_settings` —
  **224 PASS, 1 skip**; история Local отрисовалась в тестовом клиенте.
  Автономный HTML: 4 milestones в RU и EN, 10 embedded source templates, 0 внешних
  script/style/image resources, `connect-src 'none'`; три inline scripts проходят
  `node --check`. Новое Naver-состояние присутствует в output.
- Browser Use limitation: чтение вкладки `file:///` отклонено политикой браузера;
  инструмент указал, что разрешены только `http:`/`https:` и запрещает обход этой
  операции через CDP/другие браузеры/команды. Поэтому DOM/click/visual проверку,
  фактическое время полной отрисовки и работу элементов в браузере подтвердить не
  удалось. Вызов Shell для открытия ярлыка вернулся за 196 ms — это время запуска
  ассоциации файла, не измерение полной отрисовки.
- Naver: по сообщению владельца recovery request отправлен и принят; номер не
  показан, ожидается email, восстановление доступа не подтверждено. Отказ Browser
  Use остаётся отдельным открытым инцидентом.
- Не завершено: визуальная/интерактивная проверка владельцем. Owner approval
  этому результату не присваивался; Production не изменялся и deploy не выполнялся.
  Следующим выполнить: владельцу заново открыть ярлык после последней сборки и
  проверить страницу и элементы в Edge; Browser Use block оставлен без обхода.
- Незакоммиченные документы и untracked `timeline.html` сохранены; существующие
  параллельные файлы не удалялись и не откатывались.

## Поисковый запуск и открытые внешние блокеры — 2026-09-26 02:28 UTC

- Naver recovery update (сообщение владельца от 2026-09-26): «Запрос на снятие
  ограничения входа отправлен и принят Naver. Номер обращения на экране не показан.
  Ожидается ответ по email. Восстановление доступа ещё не подтверждено».
  Другой браузерный помощник открыл официальную форму для зарубежных пользователей.
  Эта запись содержит только статус со слов владельца; фото, реквизиты документа и
  личные поля формы не сохранялись. Отдельный Browser Use incident в этой сессии
  остаётся открытым; приём обращения не означает, что доступ к аккаунту восстановлен.

- Завершено по имеющимся свидетельствам: Google Domain property подтверждён и
  основной sitemap Successful; Bing импортирован из GSC, sitemap принят в
  обработку; Yandex ownership подтверждён по сообщению владельца и sitemap
  добавлен. Статусы и источники приведены в `docs/SEARCH_DISCOVERY.md`; это не
  новая кабинетная проверка.
- DNS: Google и Yandex TXT на корне публично проверялись 2026-09-25 через DNS
  resolver 1.1.1.1; прежний отчёт фиксирует ожидаемые значения. Cloudflare UI
  и полный аудит остальных DNS-записей в этом этапе не выполнялись.
- IndexNow: `docs/history/2026-09-25-naver-indexnow-activation.md` фиксирует
  ключевую URL HTTP 200, 10 032 принятых URL, scheduler `aipedia-indexnow`
  каждые 300 секунд, защиту dispatcher/deploy общей блокировкой и последний
  Production status 22:54Z (active_pending 0, active_retry 0,
  failed_unresolved 0; 5 016 failed_resolved_historical). Это доказательства
  отчёта от 2026-09-25, не текущий запрос к серверу. Принятие не означает
  индексацию. Brave re-fetch request принят по сообщению владельца от
  2026-09-26; фактическая индексация неизвестна.
- Naver account restriction: владелец ранее подтвердил ownership HTML meta tag
  и отправку sitemap; доказательства — предоставленные владельцем скриншоты,
  дата скриншота в доступной записи не указана. Activation report отдельно
  подтверждает Production meta tag curl-проверкой 2026-09-25 22:02Z.
  Позднее владелец сообщил об ограничении входа `abnormal registration /
  mass-created ID`. Точная причина неизвестна. Текущие права и sitemap после
  ограничения не перепроверены; на момент этого снимка запрос восстановления ещё
  не был отправлен. Последующее сообщение владельца ниже фиксирует, что запрос
  отправлен и принят Naver.
- Browser Use incident в этой сессии остаётся открытым: при разрешающих настройках интерфейса вызов
  `mcp__cua_repl.js` отказал для `help.naver.com` с прямой ссылкой на saved user
  permission. Точный отказ зафиксирован в переписке 2026-09-26; причина
  расхождения с интерфейсом не установлена. Диагностика подготовлена; владелец
  сообщил об отправке отзыва OpenAI. Номер обращения и подтверждение принятия
  поддержки в работу не представлены. Полные диагностические идентификаторы
  в эту документацию не включать.
- Не завершено: дождаться ответа Naver по email и подтверждения восстановления
  доступа; состояние прав и sitemap после ограничения не перепроверено. Отказ
  Browser Use в этой сессии не устранён; Baidu отложен и в этой работе не начинался.
- Следующим выполнить: дождаться Naver email/решения и отдельно снять первый
  фактический snapshot индексации и поисковых показателей в доступных Google/Bing/
  Yandex кабинетах, без повторной настройки интеграций. Naver не регистрировать и
  sitemap повторно не отправлять.
- Изменено: согласованы `docs/EXECUTION_STATE.md`, `docs/SEARCH_DISCOVERY.md`,
  `docs/history/2026-09-25-naver-indexnow-activation.md` и статус GSD-08 в
  `docs/timeline.json`; чужие параллельные изменения сохранены. Не завершено:
  два внешних инцидента выше и первый фактический index-performance snapshot.
  Следующим выполнить этот snapshot, когда кабинеты доступны.
- Внепроектные untracked cache-файлы, не удалять: `%SystemDrive%/ProgramData/Microsoft/Windows/Caches/*`.

## Исторический снимок подготовки Naver release candidate — до deploy, 2026-09-25

Следующие сведения были актуальны до выпуска Naver-кода; итог выпуска и внешней
активации приведён в текущем статусе выше и в release report.

- Изменено: штатный SEO/config путь теперь передаёт `NAVER_SITE_VERIFICATION` в
  серверный `<head>`; только Production получает публичный токен по умолчанию.
  Создан commit `160be0f37037e34845edc1dae1e38eead4460a60` и tag
  `release-2026-09-25-naver-verification`. Code-only архив:
  `artifacts/code-release/aipedia-code-160be0f37037.zip`, SHA256
  `fcdda4a43d4763883ce8a636a105328cc16cdaa259f88f07a7e974dcf678705d`, 292 файла.
- Слои: Local-код/тесты сохранены в Git и tag; тестовый запуск не менял Local
  SQLite. Production по-прежнему на ранее опубликованном `ba93f7ddf690`;
  release candidate не опубликован, GitHub push не выполнялся. Предыдущие
  незакоммиченные документы `docs/EXECUTION_STATE.md`, `docs/SEARCH_DISCOVERY.md`
  и `docs/timeline.json`, а также исходные untracked ярлык/XLSX/задание и
  `data/research/` сохранены вне release commit.
- Проверки: `manage.py test catalog --settings=aipedia.test_settings` —
  **217/217 PASS**; Local browser homepage 200; сырой Local HTML сохранил title,
  description, canonical и 23 hreflang и не содержит production Naver token;
  тест с Production verification override подтвердил, что единственный Naver
  meta-tag находится в серверном `<head>`. `git diff --check` PASS; штатный
  `deploy_code_release.py … --dry-run` PASS, архив без SQLite (`copies_sqlite=false`).
- Не завершено: Production deploy и HTTP/view-source проверка ещё не выполнены.
  Deploy script предназначен для Linux `/srv/aipedia`, но сессия не имеет
  настроенного SSH host/config или удалённого терминала; ничего на Production
  не запускалось. Naver Verify не нажимался.
- Следующим выполнить на тот момент: доставить этот архив на существующий AIpedia host и
  запустить `python3 tools/deploy_code_release.py` с тем же SHA256, затем
  проверить `/healthz` и сырой `https://aipediya.com/` HTML. После этого владелец
  сможет нажать Verify в Search Advisor. Не использовать StratForge host/tunnel.

## Исторический снимок первоначального подключения поисковых консолей — 2026-09-25

Статусы Naver/Yandex/IndexNow ниже относятся к первому этапу подключения до
последующих подтверждений владельца и release `2026-09-25-naver-indexnow-activation`.

- Изменено: в Google Search Console создан и подтверждён Domain property
  `aipediya.com` через Cloudflare DNS TXT; основной sitemap отправлен, статус
  **Successful**. В Cloudflare добавлена только TXT-запись
  `google-site-verification=5xX-QJunG73VRNA5s43y706xYMQzkKtiRq0Q9j31Vmk`.
  Bing Webmaster Tools связал read-only импорт с GSC аккаунтом
  `[email скрыт]`, импортировал `https://aipediya.com/`; sitemap
  отправлен отдельно, статус **Submitted / Processing**, errors 0, warnings 0.
- Слои: это изменения только во внешних сервисах и в этой документации; код,
  Production-сайт, сервер и DNS записи кроме одного Google TXT не менялись.
  Сохранены ранее существовавшие незакоммиченные файлы: ярлык
  `AI_CONTEXT/AIpedia — История сайта.lnk`, канонический файл
  `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx`,
  `AIpediya_GSD_1_0_Claude_Task.md` и `data/research/`; их содержимое не менялось.
  Chrome-вкладки идентифицированы по URL и содержимому: Google Search Console,
  Bing Webmaster Tools (две вкладки одного сервиса), Naver Search Advisor и
  Cloudflare Dashboard/Cloudflare One. Отдельный Yandex Browser не доступен
  через подключённое управление браузерами этой сессии; вкладки Baidu нет.
- Проверки / незавершено: Naver account `dim` авторизован, но предлагает только
  HTML-файл `naver9a3b428465e5fc6466aac0d50359f968.html` или meta-tag
  `<meta name="naver-site-verification" content="9c99ee04834598097c2ba9b6a809819418e5d74d" />`;
  Production не менялся по заданному ограничению, поэтому права не подтверждены
  и sitemap туда не отправлен. Yandex пока не проверен. Baidu среди открытых
  вкладок не найден, действие не предпринималось. Google показывает 0 найденных
  URL на момент отправки; принятие sitemap не означает индексацию.
- Следующим выполнить: продолжить Yandex Webmaster в авторизованном Yandex
  Browser; владелец/отдельно утверждённый выпуск должен добавить один из
  вариантов Naver verification в Production, после чего исполнитель завершит
  Naver и sitemap. Baidu — только если станет доступен авторизованный аккаунт.
  Независимые шаги IndexNow, лицензия датасетов и другие пункты GSD сохраняют
  свои прежние статусы. Production deploy не выполнялся.

## История сайта: две среды и ярлык — Local, 2026-09-25 15:42 UTC

- Изменено: по указанию владельца верх страницы `/ru/history/` содержит только
  Local и Production; Git HEAD и состояние рабочего дерева находятся в панели
  последней открытой карточки таймлайна. В `AI_CONTEXT` создан ярлык
  `AIpedia — История сайта.lnk`; он указывает на штатный
  `tools/local/start-local.ps1 -OpenPath /ru/history/`. Восстановление ярлыка —
  `tools/local/install-history-shortcut.ps1`. Для следующих агентов обновлены
  `docs/PRODUCT_HISTORY.md`, `AI_CONTEXT/README.md`, `AGENTS.md`,
  `docs/timeline.json`; решение о композиции записано в `docs/DECISIONS.md`.
  Сборщик AI_CONTEXT теперь включает порядок истории, реестр и установщик;
  Git-список в сборке читает Unicode-имя ярлыка без escape-последовательностей.
- Слои: текущий Local работает на `127.0.0.1:18810`; состояние сохранённого
  кода видно в последней панели. Production не менялся; по отчёту последний
  подтверждённый выпуск — `ed103a3`, текущий онлайн-ответ не проверен.
  Предшествующие незакоммиченные файлы сохранены, включая
  `AIpediya_GSD_1_0_Claude_Task.md`.
- Проверки: полный `manage.py test catalog --settings=aipedia.test_settings`
  **216/216 PASS**; PowerShell parser для двух launcher-скриптов — 0 ошибок;
  `.lnk` указывает на ожидаемый script/аргумент; `start-local.ps1 -OpenPath`
  на работающем Local вернул нужный адрес; `git diff --check` PASS. В браузере
  Local: две карточки, Git только в последней панели; mobile viewport 390 px
  — две карточки в колонку, без горизонтального переполнения. Физический
  телефон не проверялся. Автоматическое открытие браузера из ограниченного
  shell получило Access denied; скрипт корректно оставил Local работающим и
  вывел адрес. Двойной клик по `.lnk` вне sandbox отдельно не проверен.
- Не завершено: личный просмотр владельцем новой композиции; другие открытые
  задачи GSD-1.0 и master сохраняют прежний статус. Production не публиковался.
- Следующим выполнить: владельцу посмотреть страницу и ярлык; следующему
  исполнителю перед новой работой прочитать открытый пакет и замечания,
  обновлять `docs/timeline.json` только при изменении фактического состояния.

## История развития сайта — Local, 2026-09-25 08:09 UTC

- Изменено: в существующий `docs/timeline.json` добавлен слой истории продукта
  с тремя подтверждёнными этапами (20.09, 22.09, 25.09) и открытым пакетом;
  GSD-1.0 берёт 10 задач и их критерии из прежней записи реестра. Отдельно
  показаны master и эта страница, не смешанные с уже опубликованной базой.
  Созданы Local-only `/history/` и allowlist `/history/source/<id>`, шаблон,
  стили, JS боковой панели и тесты; ссылка добавлена в Local footer. Процесс
  сопровождения — `docs/PRODUCT_HISTORY.md`, краткая ссылка в `AGENTS.md`.
- Слои: Local HEAD `791e4ac5bf7469de243464c640c4af05b7304b26`, рабочее
  дерево грязное (включая прежние чужие изменения и не затронутый этой задачей
  `AIpediya_GSD_1_0_Claude_Task.md`); GitHub по более ранней
  проверке GSD-1.0 совпадал с HEAD, сейчас повторно не проверялся. Production
  по `docs/RELEASE.md` и отчёту выпуска — commit `ed103a3ff163`, tag
  `release-2026-09-25-local-approved`; доступ к публичному `/healthz` из этого
  окружения отклонён сетевыми правами, поэтому онлайн-состояние на текущий
  момент не подтверждено. Production не менялся.
- Проверки: `manage.py check` PASS; полный `manage.py test catalog
  --settings=aipedia.test_settings` **213/213 PASS**; JS syntax PASS;
  `git diff --check` PASS. Local browser: 1920, 1440, 2560, mobile 390;
  горизонтальная/вертикальная композиция, RU/EN/AR RTL, Light/Dark,
  панель/кнопка/Escape/клик вне/возврат фокуса — PASS. Эти mobile-проверки
  выполнены эмуляцией viewport, не физическим устройством. Существующий
  сервер 18810 держал старый шаблон в памяти; точная финальная версия
  запущена отдельным Local-процессом на `127.0.0.1:18811` и открыта в браузере.
- Не завершено: личная приёмка страницы владельцем; выпуск GSD-1.0 и master
  sync-local остаются открытыми; опубликованный сайт не получил страницу.
  Подтверждённый публичный статус после 03:21 UTC не получен из-за сетевого
  ограничения. Для не-RU/EN локалей текст истории показан с пометкой `lang=en`
  внутри правильного направления страницы; перевод истории на 20 языков не
  утверждён и не заявлен.
- Следующим выполнить: владельцу просмотреть Local-страницу и дать замечания;
  исполнителю обновить реестр по решению, а перед выпуском подтвердить
  конкретный commit/tag по `docs/RELEASE.md` и после него проверить public
  runtime. Никаких публикаций в этом этапе не выполнялось.

- Выпуск GSD-1.0: **DEPLOYED AND VERIFIED** 2026-09-25 16:08Z. Production =
  `ba93f7ddf690` / `release-2026-09-25-gsd-1-0` (отчёт
  `docs/history/2026-09-25-gsd-1-0-release.md`). Backup
  `aipedia-before-release-2026-09-25-gsd-1-0-20260925T160739Z.sqlite3`;
  migrate 0018; publication state без изменений (304/138); integrity ok, FK 0,
  счётчики = baseline; Production GSD QA 1596/1596; public check 34/34; public
  sitemap 10 032 `<loc>`. Внешне: Brave re-fetch принят; остальное — действия
  владельца (`docs/SEARCH_DISCOVERY.md` §10). Следующим выполнить: владельцу —
  консоли Google/Bing/Yandex и ключ IndexNow; исполнителю после ключа —
  `notify_indexnow --all` + `indexnow_dispatch --send` на Production.
- История подготовки выпуска (до deploy):
  - Commit `ba93f7ddf690f4a958405fbabfc65a59d3a9cfbf`, tag
    `release-2026-09-25-gsd-1-0`, push в GitHub выполнен (push не деплоит).
    Включены: GSD-1.0, код catalog master, Local-only «История сайта».
    Не включены (публичный репозиторий): master XLSX, `data/research/`,
    ярлык `.lnk`, файл задания.
  - Gate: 216 тестов PASS (история 3/3, catalog master 10/10), `check` OK,
    `makemigrations --check` — нет изменений. Манифест
    `data/release_state.json` переэкспортирован: изменилась только метка
    release; 304 Models / 138 Tools, как на Production.
  - Архив `artifacts/code-release/aipedia-code-ba93f7ddf690.zip`, sha256
    `5ed63075cb59e6bc97b05fe4e290c53b3a31202a043056aebb069dad8f8facc4`,
    290 файлов, без SQLite/секретов; dry-run `deploy_code_release.py` OK.
  - Блокер: удалённое выполнение через существующий SSH-канал общей машины
    отклонено автоматическим классификатором разрешений этой сессии (ключ
    StratForge). Обход не выполнялся. Production по-прежнему `ed103a3`.
  - Следующим выполнить: владельцу — либо разрешить этот SSH-канал для сессии,
    либо выполнить серверные шаги (backup → dry-run → deploy с
    `--publication-state data/release_state.json`); затем исполнителю —
    `tools/gsd_production_qa.py https://aipediya.com --commit ba93f7ddf690f4a958405fbabfc65a59d3a9cfbf`
    и запись выпуска в `docs/history/`.
- Обновлено (UTC): 2026-09-25 (GSD-1.0, Local)
- Задача 2026-09-25 **GSD-1.0 «Глобальная поисковая доступность»** (Local-only):
  реализация и Local QA; Production **не менялся**, ничего не отправлялось,
  push/tag/deploy не выполнялись. Паспорт и критерии — `docs/timeline.json`
  (прогресс: `.venv\Scripts\python.exe tools/gsd_progress.py`), контракт —
  `docs/SEARCH_DISCOVERY.md`, решения — `D-2026-09-25-locale-paths`,
  `…-seo-readiness`, `…-facets-pagination`, `…-datasets-license-gate`,
  `…-discovery-outbox`; evidence — `artifacts/global-search-discovery/GSD-1.0/`.
  - Слои (проверено 2026-09-25 04:08Z): Local HEAD = GitHub `origin/main` =
    `791e4ac` (свежий `git ls-remote`); Production `/healthz` = `ed103a3ff163`,
    sitemap 443 `?lang=en` URL (1 + 304 + 138). Local рабочее дерево = HEAD +
    незакоммиченные изменения (ниже).
  - Существующие незакоммиченные изменения другого исполнителя (не трогались,
    снимок `artifacts/…/baseline/`): `AGENTS.md`, `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (разделы master), `docs/EXECUTION_STATE.md`,
    `catalog/catalog_master.py`, команды `catalog_master`, `reconcile_catalog`,
    `restore_core_catalog`, `catalog/tests/test_catalog_master.py`, XLSX,
    `data/research/`, `requirements-dev.txt`.
  - Изменено этой задачей: URL `/<locale>/…` (English на корне) + 301 для
    `?lang=`; `catalog/locale_urls.py`, `middleware.py`, `readiness.py`,
    `seo.py`, `hubs.py`, `datasets.py`, `discovery.py`, `discovery_content.py`,
    `aggregates.py`, `views.py`, `context.py`, `static_pages.py`, `signals.py`,
    `comparison.py` (скрытые модели не связываются с инструментами),
    `templatetags/catalog_tags.py`, `models.py` + миграция
    `0018_discovery_outbox`; команды `seo_report`, `indexnow_dispatch`,
    `export_datasets`, `catalog_stats`, `notify_indexnow` (теперь только
    ставит в журнал); шаблоны base/catalog/panel/tool_panel/rows/header/footer/
    methodology/404/report + новые `collections.html`, `datasets.html`;
    `static/site.js`, `site.css`, `share-card.png`, `brand-512.png`;
    `data/discovery_translations.json` (переводы новых строк на 20 языков —
    черновик агента, не проверен человеком); `aipedia/settings.py`,
    `test_settings.py`, `urls.py`; `tools/gsd_progress.py`,
    `tools/gsd_public_check.py`, `tools/local/start-local.ps1` (URL `/ru/`);
    тесты: новый `test_global_search_discovery.py` (38), переписаны тесты
    старого URL-контракта (`test_i18n`, `test_search_discovery`, частично
    `test_catalog`, `test_environments`, `test_redesign`, `test_split_catalog`;
    остальные вызовы `?lang=` идут через 301 с `follow=True`).
  - Исправленные по ходу дефекты: ссылки строк в подгружаемых чанках несли
    `partial=rows` (пред-существующий); заголовок `X-Aipedia-Title` для
    нелатинских названий приходил в RFC 2047 (`=?utf-8?b?…`); `rel=prev` на
    второй странице; HEAD отвечал 405; заголовок вкладки не возвращался после
    закрытия панели; `notify_indexnow --all` был сломан; собственный crawler
    не разрешал относительные ссылки (исправлено до финального прогона).
  - Reconciliation 2026-09-25 (по запросу владельца): в sitemap добавлена
    индексируемая `/privacy` (×22) и правила sitemap выровнены с правилами
    страниц (двусторонняя проверка 396/396 без расхождений); итог 10 035
    `<loc>`; BreadcrumbList теперь всегда сопровождается видимой цепочкой;
    тесты матрицы structured data (Organization, BreadcrumbList, Dataset,
    DataCatalog, DataDownload); §8 `SEARCH_DISCOVERY.md` — только официальные
    первоисточники (Naver и способы верификации Baidu — «не подтверждено»);
    Brave: исправлено — отправка URL существует; политика training-краулеров
    записана как не определённая владельцем (`D-2026-09-25-training-crawlers-undefined`).
  - Проверки: `catalog` **216 тестов PASS, 0 FAIL, 0 SKIP** (было 174);
    полный rendered-аудит `seo_report --html all`: 10 013 страниц × 22 локали,
    0 проблем (canonical/hreflang/noindex/lang/dir/H1/title/description vs
    sitemap); sitemap = реестр (9 724 entity-URL, 0 утечек скрытых);
    robots-crawler завершился на 2 142 страницах, 442/442 публичных записи
    достижимы обычными ссылками без JS; `check` OK;
    `makemigrations --check` — нет изменений; `export_datasets --check`
    (детерминизм) PASS; `gsd_public_check` Local 33/33; браузер (desktop/mobile,
    тёмная/светлая, RU/UK/PL/ZH/AR/FA/DE/JA/ES/FR/EN) — PASS; сохранность данных:
    счётчики всех ключевых таблиц = baseline, ContentTranslation 42 260 current,
    XLSX sha256 без изменений, `release_state.json` ↔ БД 0 расхождений.
    Local SQLite изменена только миграцией 0018 (новая пустая таблица).
  - Не завершено / вне Local: выпуск GSD-1.0 на Production (нужно отдельное
    утверждение); лицензия датасетов (решение владельца); регистрация в
    консолях и ключ IndexNow (владелец); проверка переводов-черновиков;
    отложенный eval-gap (412,820 billable chars; ранее записанный дефицит F0
    108,605) — отдельно; пред-существующее: карточка AR на мобильном обрезана
    по горизонтали так же, как на Production.
  - Следующим выполнить: владельцу — утвердить scope GSD-1.0
    (`docs/history/GSD-1.0-release-scope.md`) и решить лицензию данных;
    исполнителю после утверждения — commit/tag и выпуск по `docs/RELEASE.md`,
    затем `tools/gsd_public_check.py https://aipediya.com`.
- Обновлено ранее (UTC): 2026-09-25T01:46:36Z
- Follow-up (master finalize): `catalog_master import` (added 0, renumbered 0) и `catalog_master check` = OK подтверждены повторно; исправлены тесты `catalog/tests/test_catalog_master.py` под обязательное поле `Publication Decision`; `manage.py test catalog --settings=aipedia.test_settings` снова PASS (170/170). Production не трогался.
- Задача 2026-09-25 (выпуск утверждённого Local-состояния): **DEPLOYED AND
  VERIFIED**. Production = commit `ed103a3ff163` / tag
  `release-2026-09-25-local-approved` (отчёт
  `docs/history/2026-09-25-local-approved-release.md`, процесс
  `D-2026-09-25-release-process`).
  - Слои: Local = GitHub (`origin/main` + tag) = Production для кода выпуска;
    Production: 304 Models / 138 Tools публично, 459 research-моделей скрыты
    (№305–763, данные/переводы/история сохранены), `/healthz` = `ed103a3ff163`.
  - Проверки: тесты 174 PASS; Local и public HTTPS аудит — 0 fails (22 локали,
    sitemap 304/138, 459 скрытых = 404); строки каталога Production и Local
    совпадают побайтно; браузер AR/RU/UK, desktop/mobile.
  - Вне выпуска (остались незакоммиченными в рабочей копии, работа другого
    исполнителя): `catalog_master*`, XLSX, `AI_CONTEXT/README.md`,
    `requirements-dev.txt`, `data/research/`, разделы catalog master в
    `AGENTS.md`/`DECISIONS.md`/этом файле; а также `restore_core_catalog`,
    `reconcile_catalog`.
  - Следующим выполнить: отдельная Local-итерация Global Search / SEO /
    discoverability (в т.ч. локализованный `<title>`); Production — только по
    новому утверждению владельца.
- Задача 2026-09-24 (catalog master — единая каноническая база, Local-only):
  **COMPLETE, Local PASS**. Production **не менялся**; ничего не публиковалось;
  Local SQLite не изменялась (sha256 до/после import/check совпадает).
  - Слои: Local — изменения не закоммичены. GitHub — `origin/main` = `6ce09b2`
    (без этой задачи). Production — не трогался; `/healthz` (только чтение)
    release `e8a4df761a87`, sitemap 763 модели / 138 инструментов.
  - Изменено: `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx` пересобран как
    catalog master (схема `aipediya-catalog-master/2`): листы Models (763 =
    304 PUBLISHED + 459 NEEDS_REVIEW, 54 колонки), Tools (138 PUBLISHED, 44
    колонки), Offers 555, Evaluations 881, Access 1205, Facts 10, Origins 812,
    Tool Platforms 224, Changelog, Meta, Rules, Lists. Код:
    `catalog/catalog_master.py`, `catalog/management/commands/catalog_master.py`
    (`import [--production] [--rebuild]`, `check [--production]`),
    `catalog/tests/test_catalog_master.py`. Удалены созданные ранее этой же
    задачей и не закоммиченные `catalog/verification_master.py`,
    команда `verification_master` и её тест (старый XLSX: копия в
    `%TEMP%\old_registry_backup.xlsx`, ручных правок в нём не было). Правила:
    `AGENTS.md` («Каноническая база каталога (master)»), `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (`D-2026-09-24-catalog-master`; прежние
    `…-model-verification-registry` и нумерация из
    `…-permanent-catalog-numbers` — «заменено»; два открытых вопроса).
  - Результат импорта: drift master↔Local = 0 во всех листах; Public Number
    master (хронология) совпал с Local у всех 304 моделей и 17 датированных
    инструментов. Предупреждения `check` (ожидаемые): 580 записей имеют номер
    в Local без Public Number в master (459 NEEDS_REVIEW с 305–763 и 121
    инструмент без даты с 18–138); 459 NEEDS_REVIEW опубликованы на Production;
    121 PUBLISHED инструмент без verified date.
  - Проверки: `catalog_master import` повторно — added 0, renumbered 0;
    `check --production` — OK; Excel (COM) открывает все 12 листов, списки и
    подсветка (NEEDS_REVIEW + On Production=YES — красным) работают;
    `catalog` **170 тестов PASS**.
  - Не завершено: синхронизация master → Local (и затем Production) не
    реализована; Local-код (незакоммиченный) ещё выдаёт постоянные номера;
    верификация 459 кандидатов не выполнялась; открытые вопросы владельцу —
    номера 121 инструмента без даты и снятие 459 NEEDS_REVIEW с Production.
  - Следующим выполнить: владельцу — ответить на два открытых вопроса в
    `docs/DECISIONS.md`; исполнителю — реализовать `catalog_master sync-local`
    (master → Local, с журналом, без `QuerySet.update`), затем верифицировать
    кандидатов пачками (`import` + `check` после каждой).
- Ранее в этот день (реестр верификации, заменён catalog master): ниже — его
  исходная запись для истории.
  - Слои: Local — изменения ниже, не закоммичены. GitHub — `origin/main` =
    `6ce09b2` (без этой задачи). Production — этой задачей не трогался (текущий
    по этому файлу — `e8a4df761a87`; строка `docs/RELEASE.md` «публичный сайт
    работает на commit `43e2d3f…`» устарела — расхождение, не исправлялось).
  - Параллельно: в 00:27 UTC другой исполнитель записал ниже блок о выпускном
    прогоне (архив `artifacts/code-release/aipedia-code-6ce09b289d3f.zip`, deploy
    заблокирован). Имя архива указывает на commit `6ce09b2`, в который файлы
    этой задачи не входят; блок не изменялся, кроме пометки «Обновлено ранее».
  - Изменено: создан `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx`
    (листы Models / Rules / Lists; 459 строк = все скрытые модели Local, все
    `TO_VERIFY`; 15 колонок владельца + служебные Slug, Research Entity ID,
    Category, Catalog Status (DB), Reserved Number (Local DB), Research Date Hint,
    Import Sources (unverified), DB Checked, Import Batch, Missing Count;
    выпадающие списки, условная подсветка недостающего, закреплённая шапка,
    автофильтр). Код: `catalog/verification_master.py`,
    `catalog/management/commands/verification_master.py` (`sync|check`),
    `catalog/tests/test_verification_master.py`, `requirements-dev.txt`
    (`openpyxl`, только Local; установлен в `.venv`). Правила: `AGENTS.md`
    (раздел «Реестр верификации моделей»), `AI_CONTEXT/README.md`,
    `docs/DECISIONS.md` (`D-2026-09-24-model-verification-registry` + открытый
    вопрос о номерах).
  - Данные в реестре: Official/Secondary Source, даты, Exists, Release Stage,
    Last Verified **пустые** у всех 459 (ничего не верифицировано); Missing Data
    у всех = `exists; date (exact or ≈); release_stage; official_source;
    last_verified`. Подсказки импорта: дата у 412, ссылки у 459 (служебные
    колонки, не доказательство). У 29 записей импортный источник — заглушка
    Smithsonian Mark I Perceptron.
  - Расхождения, найденные при сверке: (1) 459 моделей скрыты 2026-09-24 в
    23:37 UTC незакоммиченной командой `restore_core_catalog --apply` (журнал
    `move_to_research_layer`); блок ниже про «опубликованные 763» устарел —
    сейчас в Local опубликовано 304 модели (№1–304), скрытые 459 держат
    предварительные номера 305–763. (2) `restore_core_catalog` снимает
    публикацию через `QuerySet.update` (журнал пишется отдельно), а
    незакоммиченный `reconcile_catalog` описывает «clear all model numbers and
    assign fresh 1..N» — противоречит `D-2026-09-24-permanent-catalog-numbers`;
    не запускать без решения владельца.
  - Проверки: `verification_master sync` (повторный — added=0) и `check: OK`;
    `openpyxl` round-trip (правка агентом сохраняется, Missing Data
    пересчитывается, кандидат без slug сохраняется); негативный `check` ловит
    7/7 нарушений; Excel (COM) открывает файл без восстановления, списки и
    подсветка работают, введённая дата остаётся текстом; сохранить из Excel на
    этой машине нельзя — истекла лицензия Office. `catalog` **169 тестов PASS**.
  - Не завершено: сама верификация 459 кандидатов (источники/даты) не
    выполнялась; публикация кандидатов — только после `VERIFIED` →
    `READY_FOR_SITE` и отдельного решения владельца; вопрос о номере
    публикуемого кандидата (предварительный 305–763 или следующий свободный)
    открыт.
  - Следующим выполнить: владельцу — решить вопрос о номерах и при желании
    закоммитить; исполнителю — верифицировать кандидатов пачками, после каждой
    `verification_master sync` + `check`.

- Обновлено ранее (UTC): 2026-09-25T00:27:23Z
- Текущий выпускной прогон: `catalog --settings=aipedia.test_settings` PASS; Local smoke PASS (`127.0.0.1:18810`, `healthz`, каталог 304/138, newest-first, row-click проверен частично); isolated release verify FAIL по fingerprint базы (`publication_revisions`/`tool_publication_revisions` расходятся с ожиданием на Local-данных); code-only deploy из этого Windows окружения заблокирован, потому что серверный шаг выполняется на хосте `/srv/aipedia`, а здесь нет SSH-доступа к нему.
- Изменено: рабочее дерево содержит локальные правки каталога/вёрстки/документации и неотслеживаемые `data/research/`; архив кода собран как `artifacts/code-release/aipedia-code-6ce09b289d3f.zip`.
- Не завершено: публикация текущего Local-состояния в Production.
- Следующим выполнить: на серверном хосте AIpedia запустить по `docs/RELEASE.md` `python3 tools/deploy_code_release.py /path/aipedia-code-6ce09b289d3f.zip --sha256 6054b382624c31d00dd437e60245bfa921067089f34a5109fd7ed2600da88459` после отдельной проверки того, как должны трактоваться локальные revision counts для скрытых research-строк.

- Задача 2026-09-24 (три UX/data-нюанса, Local-only): **IMPLEMENTATION COMPLETE,
  Local PASS**. Production **не менялся** (нет применимого разрешения на выпуск).
  - Изменено:
    - (1) Чистый `/` открывает каталог по дате выпуска убыв. (newest-first) для
      Моделей и Инструментов; явные `?sort=…` переопределяют; детерминизм после
      перезагрузки (`catalog/views.py` default `release_desc`).
    - (2) Клик по всей строке открывает нужную панель; ссылки/кнопки/поля/фильтры
      и выделение текста не перехватываются; клик по строке не закрывает панель
      (`static/site.js`, `static/site.css` cursor).
    - (3) `catalog/public number` — постоянный ID (одна простановка, не
      пересчитывается на дате/цене/оценке/сортировке; существующие сохранены;
      остальные опубликованные проставлены один раз детерминированно; новая
      запись получает следующий свободный). Отдельная приблизительная дата
      `approx_released`/`approx_precision`/`approx_evidence` (рендер `≈`, никогда
      не выдаётся за точную). Сортировка по выпуску: точная → приблизительная →
      неизвестные в конце. Файлы: `catalog/models.py`, `catalog/chronology.py`,
      `catalog/comparison.py`, `catalog/templatetags/catalog_tags.py`, шаблоны
      строк/панелей, миграция `0016_approx_dates_and_permanent_numbers`.
  - Данные Local после миграции: модели опубликованные 763 → пронумерованы 763
    (0 null); инструменты 138 → 138 (0 null); номера уникальны и непрерывны
    (1..763 / 1..138); существующие 1..304 / 1..17 сохранены (первый `#1`
    jurassic-1-jumbo / github-copilot).
  - Проверки: `catalog` **160 тестов PASS** (5 старых тестов правила «номер по
    дате» переписаны на постоянные номера; добавлен `test_permanent_numbers.py`).
    Local-браузер: чистый `/` newest-first, `?sort=number_asc` даёт 1..5,
    `release_asc` oldest-first, клик по ячейке строки открывает панель, клик вне
    закрывает; Tools newest-first.
  - Решения: добавлено `D-2026-09-24-permanent-catalog-numbers`;
    `D-2026-09-20-chronology-numbers` и `D-2026-09-20-undated-last` помечены
    «заменено новым решением»; обновлён numbering-абзац
    `D-2026-09-21-model-tool-catalog-split`.
  - Не завершено: приблизительные даты как инфраструктура — конкретные `approx_*`
    значения для 459 недатированных моделей владельцем не вносились (по замыслу).
    Публикация на Production не выполнялась.
  - Следующим выполнить: дождаться явного разрешения владельца на выпуск этого
    состояния по `docs/RELEASE.md`; при желании — наполнить `approx_*` доказанными
    приблизительными датами.
- Обновлено ранее (UTC): 2026-09-24T00:20:00Z

- Документация имён: правило «бренд AIpediya / техкод aipedia» закреплено в
  `AGENTS.md` и `D-2026-09-23-brand-vs-tech-name` (`docs/DECISIONS.md`). Код,
  сервер и Production не менялись.
- Задача владельца: опубликовать на `https://aipediya.com/` точное текущее
  состояние Local и проверить полноту данных и актуальность версии.
- Реализация Local: **IMPLEMENTATION COMPLETE** (i18n 22 языка + UI-исправления
  правой панели и языкового меню).
- Автоматическая проверка: **PASS** — `catalog` 140 тестов.
- Local-браузерная проверка исправлений: **PASS** — панель закрывается по клику
  вне/Escape/крестику, клики внутри не закрывают, меню языков над панелью,
  смена языка сохраняет открытую карточку; desktop и mobile; EN/UK/AR(RTL).
- Разрешение на Production: **ПОЛУЧЕНО** (явный мандат владельца на выпуск
  итоговой исправленной версии по `docs/RELEASE.md`).
- Предыдущий Production: commit `43e2d3feba57cf67084cc2e3774c86a72ce361b5`.
- Production: **DEPLOYED AND VERIFIED** на commit
  `289d01b30c865a66adf674d5329b1133ee4c3e75` (tag `release-2026-09-23-i18n-ui`),
  2026-09-23. Деплой по `docs/RELEASE.md` через существующий SSH-доступ к общей
  машине (владелец подтвердил: AIpedia и StratForge — один сервер; тронуты только
  пути/службы AIpedia). Серверный online-backup боевой БД
  `aipedia-before-code-20260923T194848Z.sqlite3`; миграция `0015_contenttranslation`
  применена; перезапущена только программа `aipedia`; `/healthz` release совпал.
- Перенос переводов: 42 260 локализаций импортированы в боевую БД идемпотентной
  командой `import_translations` (по slug+поле+язык+sha256 английского источника,
  без провайдера, без копирования Local SQLite). Повторный запуск — 0 применённых.
  Боевые данные после: ContentTranslation 42 260; ядро без изменений
  (901/138/555/881/343, revisions 4354, integrity ok).
- Публичная проверка `https://aipediya.com/`: **PASS** — release 289d01b,
  EN/UK/AR(RTL)/FA, модель и инструмент, локализация и страны, панель (клик вне/
  Escape/крестик), меню языков над панелью, смена языка при открытой карточке,
  mobile, защита токена `1M`; секретов в развёрнутом коде нет.
- Локализация контролируемых меток (после публичного QA нашлись русские слова в
  нерусских локалях, например «Модель» на корейской странице). Два code-only
  выпуска по `docs/RELEASE.md`, без изменения БД и без Azure:
  - `bababd103ff0` (`release-2026-09-23-locale-fix`): метки конфигурации/
    протокола оценок локализуются (`catalog/evaluation_labels.py`); `public_text`
    даёт английский fallback вместо русского для остальных контролируемых меток.
  - `e8a4df761a87` (`release-2026-09-23-controlled-i18n`, **текущий Production**):
    полноценная детерминированная локализация контролируемых меток на все 22
    локали (`catalog/controlled_terms.py`); английский — только аварийный
    fallback. Бренды/ID/тарифы/API/разрешения/URL не переводятся.
  Оба задеплоены через существующий SSH к общей машине (только пути/службы
  AIpedia); боевой online-backup перед каждым; `copied_sqlite=false`; миграций
  нет. Аудит всех 22 локалей (Local и Production): 0 русских утечек, 0
  английского fallback на поддерживаемых локалях. Тесты: 155 PASS.
- Поверх выпуска `43e2d3f` реализованы мультиязычность интерфейса на 22 языка,
  provider-agnostic translation pipeline и исправления UI. Подробности —
  раздел «Мультиязычность 22 языка и translation pipeline» ниже.

## Три слоя

Последний **подтверждённый** Production: commit
`289d01b30c865a66adf674d5329b1133ee4c3e75` (tag `release-2026-09-23-i18n-ui`),
2026-09-23, способ: code-only выпуск по `docs/RELEASE.md` через существующий
SSH-доступ к общей машине + идемпотентный импорт переводов (`import_translations`).
Предыдущий Production `43e2d3feba57cf67084cc2e3774c86a72ce361b5` (2026-09-22),
отчёт: `docs/history/2026-09-22-global-catalog-release.md`.

| Слой | Указатель | Примечание |
| --- | --- | --- |
| Local | post-release audit поверх `43e2d3f` + только локальные research/output файлы | runtime-код и каталог равны выпуску; Local работает на 127.0.0.1:18810 |
| GitHub | `origin/main` содержит `43e2d3f` и последующий audit-отчёт | runtime-код выпуска не менялся |
| Production | `43e2d3f` | `/healthz` и серверная БД проверены после deploy |

| Изменение | Local | GitHub | Production |
| --- | --- | --- | --- |
| Хронологические номера и даты выпуска | В коде и в Local-каталоге | Есть (с `6e901dc`) | Опубликовано как `6e901dc` |
| Local/Production, ярлыки, code-only выпуск | Реализовано | `901eb47` | Не опубликовано |
| `AGENTS.md` и правило Cursor | Реализовано | `7e66da2` | Не опубликовано |
| Живой статус, решения, сборщик `AI_CONTEXT` | Есть | Есть | Код есть; пакет остаётся локальным |
| Редизайн таблицы и правой панели | PASS | Есть | PASS |
| Финальная визуальная доводка по утверждённому PNG | PASS | Есть | PASS |
| Знаки разработчиков у моделей | PASS | Есть | PASS |
| Подгрузка строк при прокрутке (150 → 50…) | PASS | Есть | PASS |
| Дата релиза с днём и месяцем (RU/EN) | PASS | Есть | PASS |
| Раздельные каталоги моделей и инструментов | 763 / 138 | Есть | 763 / 138, PASS |
| Reconciliation Local + applicability-fixed research master | Импортировано; XLSX собран | Payload в Git | Импортировано |
| Визуальная проверка после reconciliation | PASS | Есть | PASS |
| Видимый бренд `AIpediya` и палитры Midnight/Day | PASS | Есть | PASS |
| Правило имён бренд vs техкод в AGENTS/DECISIONS | Закреплено Local | Нет (ещё не commit) | Не требуется (docs) |
| Полный выпуск Local на Production | Завершён | `43e2d3f` | DEPLOYED AND VERIFIED |
| Ярлыки через `DesktopDirectory` | `install-shortcuts.ps1` изменён ранее, не этой задачей | Нет | Нет |
| Неотслеживаемые дампы `data/research/` | Только на диске | Нет | Нет |

## Мультиязычность 22 языка и translation pipeline (2026-09-23, Local, не опубликовано)

Реализовано поверх выпуска `43e2d3f` в рабочем дереве Local. Не закоммичено,
Production без изменений, серверная SQLite не трогалась. Существующая RU/EN
логика расширена, а не заменена.

- 22 языка интерфейса: `en, ru, zh-Hans, es, fr, ar, pt-BR, de, ja, ko, hi, id,
  tr, vi, it, pl, uk, fa, th, nl, bn, zh-Hant`. English — канонический,
  `x-default` и итоговый fallback.
- Определение языка: URL `?lang=` → cookie `aipedia_lang` → `Accept-Language` →
  слабый хинт `CF-IPCountry` → English. Ручной выбор пишется в cookie и не
  переопределяется гео (`catalog/i18n.py`, `catalog/middleware.py`).
- URL не менялись: локаль остаётся в query-параметре `?lang=`. `canonical`,
  полный набор `hreflang` для 22 локалей и `hreflang="x-default"` (English),
  `<html lang dir>`, sitemap с `xhtml:link` alternates
  (`catalog/seo.py`, `templates/base.html`, `catalog/views.py`).
- Переключатель на 22 языка (родные названия, `<details>`-меню), сохраняет
  текущую страницу/карточку (`templates/includes/site_header.html`).
- RTL для `ar` и `fa` через логические CSS-свойства и точечный блок `[dir=rtl]`;
  бренд остаётся LTR (`static/site.css`, `static/table-layout.css`, `static/site.js`).
- Статические переводы UI (~299 ключей × 20 языков) и таксономии категорий
  (24 кода × 20 языков) хранятся в коде `catalog/ui_translations.py`;
  резолверы `catalog/context.t` и `category_label`. Отсутствующий перевод →
  English fallback, техно-ключи не показываются. Локализованные даты/месяцы для
  всех локалей (`catalog/templatetags/catalog_tags.py`).
- Фактические поля (названия, компании, URL, цены, числа, рейтинги, даты, API
  identifiers) не переводятся и общие для всех языков.
- Translation pipeline для будущих динамических данных: модель
  `ContentTranslation` (состояния `current`/`outdated`/`missing`/`reviewed`,
  привязка к sha-256 hash английского источника), провайдеры
  `catalog/translation_providers.py` (offline mock по умолчанию, adapter Azure
  Translator, null), сервис `catalog/translation_pipeline.py`, команда
  `translate_catalog` (status/dry-run/backfill/повторный перевод только
  missing/outdated), сигнал `pre_save` делает перевод устаревшим при изменении
  источника без вызова API. Ключ провайдера — только из env
  `AIPEDIA_AZURE_TRANSLATOR_KEY`; реальный внешний API в тестах не вызывается.
  Миграция `0015_contenttranslation` (только схема).

Проверки: **все автоматические тесты PASS** (`manage.py test catalog
--settings=aipedia.test_settings`). Включают `test_i18n` (20), `test_translation_pipeline`
(14), `test_translation_finalization` (9: auto-translate on-commit+рендер,
отключён по умолчанию, bulk-suppression, dedup translation memory, URL-agnostic
retrieval, country_label, семантика `missing`/`not_applicable`, GET не вызывает
Translator). Ранее единственный FAIL `test_pack_ai_context…install-shortcuts.ps1`
исправлен выравниванием `SOURCE_FILES` в `tools/pack_ai_context.py` (файл существует
и в Git; тест ожидал его в пакете — это pre-existing рассинхрон packer↔тест, не
связан с i18n). `manage.py check` PASS. Данные Local без потерь:
763 модели, 138 инструментов, 555 offers, 1205 accesses, 881 evaluations,
343 sources, 2900 research, 901 ModelVersion; **revisions = 4354 (baseline
восстановлен)**; **ContentTranslation = 42260 (state=current, provider=azure)**.

Реальный Azure backfill выполнен (провайдер F0, region eastus2, endpoint
глобальный): 901 объект, **360 запросов**, **1 680 285 биллинг-символов**
(< 2 000 000 бесплатного месячного лимита F0), 42 254 перевода, 42 254 reused
через translation memory (dedup по sha-256), 0 failed. Состояния переводов
(семантика исправлена: `missing` = «источник есть, актуального перевода нет»,
`not_applicable` = «английского источника нет»):
`current=42260, outdated=0, reviewed=0, missing=0, not_applicable=36800`. Все
36800 `not_applicable` — слоты полей с пустым английским источником (1840 полей
× 20 языков), переводить нечего; поля с содержимым переведены на 100%
(2113 × 20 = 42260). **Реальных недостающих переводов нет (missing=0).**
Аудит остаточной локализации `manage.py audit_localization` по всем 22 локалям:
`static_gaps=0`, `untranslated_with_source=0`, `ui_missing/category_missing/
country_missing = []` для каждого языка (allowlist универсальных ключей
api/cli/ide/github/ocr/3d/no_rating_yet).

Финализирующий QA-слой (без повторного вызова Azure):
- Семантическое качество: команда `audit_translation_quality` (offline) сверяет
  42 260 переводов с английским источником. После нормализации ложных срабатываний
  (персидские/арабские цифры ۱۲۳, десятичная запятая 1,05, компактность CJK):
  `empty=0, escape_artifact=0, no_target_script=0, length_extreme=0`;
  числа сохранены; идентификаторы для латинских локалей сохранены (62 остатка —
  косметическая нормализация регистра избыточного `exact version: gpt-5-pro` →
  `GPT-5-Pro`, имя модели сохранено); в индийских/CJK письменностях 1367
  транслитераций имён собственных (естественно; slug/ID/заголовки — латиница).
  Системных дефектов, требующих повторного перевода, нет.
- **Систематический rendered QA 22/22** (автоматический аудит через Django test
  client по реальной БД, не ручной браузер): для каждой из 22 локалей отрендерены
  карточка Model (Claude 3 Haiku) и Tool (GitHub Copilot) — HTTP 200,
  локализованные описание/страна в целевом письме, направление (`ar`/`fa` RTL),
  бренды/ID (Anthropic, claude-3-haiku, GitHub) сохранены: **0 fails**. Mobile:
  `<meta viewport>` + 8 `@media` брейкпоинтов; RTL: 39 логических CSS-свойств,
  бренд `direction: ltr`.
- **Targeted visual QA** (реальный браузер) для критичных представительных локалей
  и RTL: ar (карточка + privacy, зеркальная раскладка), плюс проверка контента
  в uk/de/ja/fa/zh-Hant. Не для всех 22 локалей визуально — это targeted, а 22/22
  выше — систематический rendered-аудит.
- Авто-перевод доказан end-to-end (mock): новый/изменённый English → авто-перевод
  на commit → сохранение (`ContentTranslation` + JSON) → рендер в целевой локали;
  и доказано, что GET/просмотр страниц **никогда** не вызывает Translator
  (тесты `test_saving_model_autotranslates_on_commit_and_renders`,
  `test_get_requests_never_call_the_translator`).

Локализация карточек (root-cause фиксы поверх статики UI):
- Страны — детерминированный код-слой `catalog/countries.py`
  (`COUNTRY_TRANSLATIONS` ISO2 × 22 языка, `country_label()`), фильтр
  `country_name`, подключён в `templates/panel.html` и
  `templates/includes/country_flag.html`. RU/EN — из БД (`name_ru/name_en`),
  прочие — из карты, fallback English.
- Модальности (text/image/video/audio), open weights, yes/no — уже
  локализованы через `t()`/`label:lang`; факты — только `service_price`
  (цены, не переводятся).
- Прозаические поля модели (`description/suitable/limitations/origin/philosophy`)
  и инструмента (`description`) переводятся pipeline и рендерятся `local:lang`.
  `ecosystem` инструментов исключён (бренд-названия, ru==en).

Автоматический перевод новых/изменённых данных (штатный путь):
- `pre_save` помечает переводы устаревшими при изменении английского источника
  (без вызова API).
- `post_save` хук `auto_translate` (`catalog/signals.py`) переводит новый/
  изменённый объект после commit (`transaction.on_commit`), пакетно и
  безопасно; включается `AIPEDIA_AUTO_TRANSLATE` (по умолчанию off в коде для
  тестов/миграций; включён в `deploy/aipedia.env.example` и в Local `.env.local`).
- Массовые импорты используют `suppress_auto_translation()` (подключено в
  `promote_research`) и один пакетный `translate_catalog` после загрузки.
- Провайдер батчит `translate_batch` с retry на 429/5xx (Retry-After), dedup
  через translation memory; `translate_catalog` умеет `--dry-run` с оценкой
  биллинг-символов, `--status`, `--batch-size`.

Публичные не-карточные страницы:
- `privacy.html` локализована на 22 языка (`catalog/static_pages.py` +
  overlay `data/static_page_translations.json`, команда `translate_static_pages`;
  15 500 символов, 20 запросов). Рендер из локализованных блоков.
- `methodology.html` — сейчас осиротевший шаблон без маршрута/навигации/рендера
  (`/methodology` → 404). **Не удалять**: следующая задача Global Search &
  Discovery отдельно решит публичную локализованную Methodology page (маршрут,
  контент, hreflang/sitemap для неё).
- Панельные заметки покрытия оценок (`evaluation_gap`). Классификация содержимого:
  (а) AIpediya-авторская проза — 105 уникальных `reason` (20 550 символов) +
  4 generic label («Checked source» и др., 91 символ) → **должно локализоваться**;
  (б) сторонние имена бенчмарков/источников/URL/ID (7 label: BFCL, Open ASR,
  AVGen-Bench, EvalPlus, репозитории, URL, а также имена моделей/бенчмарков внутри
  reason) → **сохраняются в оригинале**. Пересчёт уникальных биллинг-символов
  после классификации и dedup: **412 820 символов** (× 20 языков). В месячном
  лимите F0 осталось **304 215** → **не помещается, дефицит 108 605 символов**.
  Платные расходы запрещены, поэтому эта часть **не переведена и НЕ считается
  завершённой** — единственный quota-blocker. Переводимо при сбросе месячного
  лимита F0 тем же pipeline; template-level dedup (27 шаблонов ≈ 105 000 символов)
  влез бы, но требует реконструкции имён собственных по 20 разно-типологическим
  языкам — риск неестественности (QA качества), не выполняется без решения владельца.
  Окружающий UI секции (заголовок, «почему нет оценки», дата) локализован.
  Очередь на следующий доступный период F0 quota (не обходить template-хаком,
  платных расходов не создавать):
  `AIpediya-authored eval-gap remaining: 412,820 billable chars; current shortfall: 108,605`.

Защита технических токенов (реальный дефект «1M → ۱ متر» и класс риска):
- `catalog/token_guard.py` — оборачивает машиночитаемые токены (`1M`, `128K`,
  `32K`, `7B`, `70B`, `405B`, версии/ID `gpt-5-pro`, `GPT-5.2`, акронимы `API`/
  `OCR`, URL) в `<span translate="no">`; провайдер Azure шлёт `textType=html`,
  затем markup снимается — Azure не может превратить токен в слово/единицу.
  Подтверждено реальным минимальным запросом: fa «Context: 1M» → «زمینه: 1M»
  (без «متر»).
- Уже сохранённые переводы проверены `token_guard`: семантический класс
  «число+единица» (`1M`/`128K`/`7B`) — **328 строк / 232 уникальных (source,lang)
  пар** искажены. Точечный ремонт `manage.py repair_token_distortions --provider
  azure` (только этот класс, защищённый повторный перевод, dedup): 244 пары,
  **17 запросов, 23 396 символов**, 340 обновлений полей, 0 failed. После ремонта
  искажений класса «число+единица» = **0**. Записи ревизий не создаются
  (`_aipedia_translation_write`), revisions = 4354. Резервная копия БД:
  `backups/aipedia-before-token-repair-*.sqlite3`.
- Оставшиеся 6 262 «any-token» расхождения — это транслитерация имён собственных
  в индийских/CJK письменностях (не семантическое искажение, а смена письма;
  slug/ID/заголовки — латиница). Полный ремонт стоил бы ~376 500 символов (за
  остатком F0), поэтому не выполняется; защита `token_guard` предотвращает такие
  случаи во всех будущих переводах.

Ревизии: старый процесс backfill (до добавления guard) создал 765 технических
translation-ревизий (`ModelVersion`, `updated`, снимок прозы получил ключи
машинных языков). Идентифицированы точно по контент-сигнатуре (ни одна
до-backfill ревизия не могла содержать эти ключи; id 4355–5119, contiguous),
доказано: `distinct_models=763`, ни одна модель не теряет историю, non-artificial
= 4354 (baseline). Перед удалением снята полная резервная копия БД
(`backups/aipedia-before-translation-revision-cleanup-*.sqlite3`). Удалены только
765 искусственных ревизий в транзакции с assert-проверками; переводы сохранены
в `ContentTranslation` (42260) и в JSON моделей. Далее guard
(`_aipedia_translation_write` в `translation_pipeline`/`signals`) исключает
машинные записи перевода из журнала ревизий.

Безопасность секрета Azure: ключ читается только из env
`AIPEDIA_AZURE_TRANSLATOR_KEY` (в коде/Git/тестах/логах/AI_CONTEXT отсутствует).
На Local settings.py авто-загружает несекретную/секретную конфигурацию из
неотслеживаемого `.env.local` рядом с `manage.py` (реальное значение env
побеждает; **пустое** значение env трактуется как отсутствующее, чтобы
`.env.local` мог его заполнить). Endpoint и region — несекретные defaults
(`…microsofttranslator.com`, `eastus2`). `.gitignore` исключает `.env`/`.env.*`
(кроме `.env.example`), `secret.key`, `data/local/`; `git check-ignore .env.local`
→ ignored; в отслеживаемых файлах значения ключа нет. `check_translator`
(default azure) делает один минимальный запрос и печатает только PASS/FAIL,
provider, region; ключ/части/длину не печатает.

Targeted visual QA после backfill (реальный браузер, 127.0.0.1:18815, отдельный
dev-сервер; чужой Local на 18810 не трогался) — критичные представительные локали
и RTL: карточка модели (Claude 3 Haiku) и панель инструмента (GitHub Copilot) в
uk/de/ja/ar/fa/zh-Hant — описание, ограничения, страна, модальности, статусы,
ярлыки, yes/no локализованы; бренды (Anthropic, GitHub, Microsoft, AI21 Labs,
DeepMind, Meta AI, OpenAI), model IDs, `API`, `Cloudflare`, `IP`, URL остаются
оригинальными; ar/fa `dir=rtl` с зеркальной раскладкой и LTR-брендом; privacy
(визуально ar RTL). Полное покрытие всех 22 локалей обеспечено систематическим
rendered-аудитом выше (0 fails), а не ручным браузером по каждой локали.

Хранилище переводов не привязано к конкретной URL-схеме. Переводы адресуются
исключительно по коду локали (`ContentTranslation`, JSON-поля моделей,
`TRANSLATIONS`, страны/категории, overlay статических страниц); текущее
согласование языка (`resolve_language()`) читает `?lang=` лишь как один из
сигналов и возвращает код. Поэтому **сами данные и pipeline перевода переживут
смену URL-схемы без миграции переводов** (доказано тестом
`UrlAgnosticContentTests`). Отдельный будущий этап Global Search & Discovery,
если переведёт локали в путь (`/uk/…`, `/de/…`, `/ar/…`), изменит именно слой
маршрутизации: routing, обратное построение URL (reverse), `canonical`,
`hreflang`, `sitemap`, переключатель языка и редиректы — это работа того этапа,
а не translation pipeline.

Изменено/добавлено (Local, не закоммичено): `aipedia/settings.py`,
`aipedia/test_settings.py`, `catalog/{i18n,middleware,context,seo,comparison,
views,signals,models,ui_translations,translation_providers,translation_pipeline,
countries,static_pages,token_guard}.py`, `catalog/templatetags/catalog_tags.py`,
`catalog/management/commands/{translate_catalog,check_translator,audit_localization,
audit_translation_quality,translate_static_pages,repair_token_distortions,
promote_research}.py`,
`catalog/migrations/0015_contenttranslation.py`, `contributions/views.py`,
`tools/pack_ai_context.py`, `templates/{base,catalog,privacy,panel,
includes/site_header,includes/country_flag}.html`,
`static/{site.css,table-layout.css,site.js}`, `.env.example`,
`deploy/aipedia.env.example`, `data/static_page_translations.json`, тесты
`test_i18n.py`, `test_translation_pipeline.py`, `test_translation_finalization.py`,
`test_token_guard.py`.
Данные Local: `data/local/aipedia.sqlite3` получила 42260 ContentTranslation и
переводы в JSON моделей/инструментов; класс «число+единица» отремонтирован
защищёнными переводами; резервные копии до чистки ревизий и до ремонта токенов в
`backups/`. Не завершено: ручная приёмка владельцем; commit/push/Production —
только по отдельной команде владельца. Production без изменений, серверная SQLite
не трогалась.

## Текущая работа: полный выпуск Local на Production (2026-09-22)

- Перед любыми изменениями серверная SQLite проверена: `integrity_check=ok`,
  `foreign_key_check=0`, 255 published legacy `ModelVersion`, 503 offers,
  280 accesses, 854 evaluations, 63 sources, 2163 research records.
- Создан отдельный online-backup без остановки и без копирования Local SQLite:
  `/srv/aipedia/backups/aipedia-before-global-catalog-20260922T062133Z.sqlite3`,
  SHA-256 `b40fe0d0baeb05c941a2afbf5d10e7b02b12d24009eb09f7608f54ac7503b47d`.
- Production baseline до миграции подтверждён как точная копия сохранённого
  локального snapshot `backups/chronology-production-after.sqlite3` по SHA-256.
- Подготовлена атомарная natural-key миграция `0014_global_catalog_20260922`.
  Она сначала сверяет точное исходное состояние Production, не удаляет записи,
  сохраняет существующую историю и импортирует переносимый payload без SQLite.
- Payload: `catalog/migrations/data/global_catalog_20260922.json`, SHA-256
  `5ad37f33608e3e216e4babf0983a709e050bdc37fd7c93ddd763292db8bad0d2`;
  персональных путей, секретов и Local SQLite в нём нет.
- На изолированной копии точного Production baseline миграции `0011`–`0014`
  применились успешно. Итоговые таблицы семантически совпали с Local по всему
  переносимому payload; `integrity_check=ok`, внешних ключей с ошибками — 0.
- Local после регистрации миграции сохранил 763 модели, 138 инструментов,
  555 offers, 1205 accesses, 881 evaluations, 343 sources, 2900 research
  records, 4354 revisions, 3049 model publication revisions и 158 tool
  publication revisions.

Проверки кандидата: **82 Django tests PASS**; `manage.py check` PASS;
`makemigrations --check --dry-run` — изменений нет; `node --check` PASS;
`git diff --check` PASS. Точный архив commit `43e2d3f…`, SHA-256
`33be8e0054f1909bcb2ad891caae8558f61c58fc03932a80b3542af6199c3625`,
прошёл изолированную миграцию и semantic comparison с Local.

Production после deploy: `/healthz` = `status: ok`, `environment: production`,
release `43e2d3f…`; SQLite `integrity_check=ok`, `foreign_key_check=0`; payload
SHA совпал; 763 published моделей, 138 published инструментов, 901 legacy
ModelVersion, 555 offers, 1205 accesses, 881 evaluations, 343 sources, 2900
research records, 3590 research revisions, 4354 revisions, 3049 model и 158
tool publication revisions. Номера моделей непрерывны 001–304, инструментов
001–017; записи без точной даты остаются без выдуманного номера.

Server deploy backups:
`/srv/aipedia/backups/aipedia-before-code-20260922T065139Z.sqlite3` и
`/srv/aipedia/backups/aipedia-after-code-20260922T065139Z.sqlite3`.
Предыдущий код сохранён в
`/srv/aipedia/releases/before-code-20260922T065139Z`.

Public Browser PASS: AIpediya; 763/138; номера 001–018 видны; флаги IL/GB/US
и другие отображаются; переключение из `status=retired&q=jurassic` в Tools
очищает фильтры и показывает 138/138; RU/EN, dark/light и карточка
Jurassic-1 Jumbo проверены; ошибок console warn/error — 0. HTTP: models 200,
TTFB 0.234 s, total 0.288 s; tools 200, TTFB 0.369 s, total 0.414 s.

Изменено: release commit опубликован на GitHub и Production, серверная SQLite
мигрирована на месте с сохранением истории, отчёт и audit verifier обновлены.
Не завершено: очередь качества данных остаётся 711 записей / 1376 Required
полей и 108 записей / 110 Needs verification; это явные пробелы источников,
не дефект выпуска. Следующим выполнить: дальнейшую независимую проверку этой
очереди отдельными пакетами; новый Production выпуск — только по новой команде.

## Документация: бренд vs техкод (2026-09-23)

Изменено: в `AGENTS.md` добавлен раздел «Имена: бренд и техкод»; в
`docs/DECISIONS.md` — `D-2026-09-23-brand-vs-tech-name` (подтверждено
владельцем). Публично **AIpediya** / aipediya.com; внутренний техкод
**aipedia** не переименовывать без поручения. Не завершено: commit этих
docs по желанию владельца. Следующим выполнить: ничего обязательного по
именам; runtime и сервер не трогать.

## Текущая работа: видимый бренд AIpediya и проверка дизайна (2026-09-22)

- Видимое имя в шапке, footer, SEO title, карточках, методологии,
  конфиденциальности и административных подписях изменено с `AIpedia` на
  `AIpediya`. Внутренние имена Python/Django, совместимые HTTP-заголовки,
  пути, база и исторические имена файлов намеренно не переименовывались
  (с 2026-09-23 то же зафиксировано в `AGENTS.md` и
  `D-2026-09-23-brand-vs-tech-name`).
- `static/brand.svg` заменён на аккуратный векторный ленточный знак по
  предоставленному логотипу; растр с тёмным фоном напрямую не использован,
  поэтому знак корректно работает и в светлой теме.
- Базовая тёмная палитра приведена к предоставленной теме «Полночь»
  (`#080F14`, `#0F1A21`, `#00E0C6`, `#22D9FF`, `#E6F7FF`), светлая — к теме
  «День» (`#F5F8FA`, `#FFFFFF`, `#00C2AC`, `#0B6E99`, `#0E1B22`). Новые
  переключатели тем не добавлялись: сохранено существующее поведение dark/light.
- При проверке на ширине встроенного браузера выявлено и исправлено сжатие
  колонки названия до одной иконки. До 1180 px таблица теперь сохраняет
  читаемую колонку 188 px и использует собственную горизонтальную прокрутку.
- Browser Local PASS: dark/light, RU/EN, модели и инструменты, переход на
  «Инструменты» при активном поисковом фильтре, номера с `001`, флаги и правая
  карточка `Jurassic-1 Jumbo`; document title — `Jurassic-1 Jumbo | AIpediya`.

Проверки: **79 Django tests PASS**; `manage.py check` PASS; `makemigrations
--check --dry-run` — изменений нет; `git diff --check` — без ошибок (только
предупреждения Git о нормализации окончаний строк). Local слушает только
`127.0.0.1:18810`.

Изменено: `static/brand.svg`, `static/site.css`, `static/table-layout.css`,
видимые шаблоны и тексты контекста/views/admin/apps, regression tests и этот
статус. Не завершено: ручная визуальная приёмка владельцем. Следующим выполнить:
владелец проверяет Local; commit/push/Production возможны только по отдельной
команде.

## Архив: визуальная проверка каталога после reconciliation (2026-09-22)

- Причина начала списка с 018 установлена: данные не были потеряны. Позиции
  001–017 сохранены в SQLite, но все они historical: 10 `retired` и 7
  `archived`; прежний неявный фильтр `status=active` скрывал их. Обычный вид
  теперь открывает `all` и показывает полную подтверждённую хронологию; явный
  фильтр `active` по-прежнему доступен и не перенумеровывает результаты.
- Счётчики вкладок приведены к фактически доступным published-записям:
  763 модели и 138 инструментов. В браузере первые 18 номеров проверены как
  непрерывная последовательность `001`–`018`.
- Переключатели «Модели» / «Инструменты» теперь ведут на чистый корень своего
  независимого каталога. Параметры, сортировка, выбранная карточка и маршрут
  другой таблицы не переносятся. Проверен переход из отфильтрованной карточки
  `/models/<slug>` на 138 инструментов и обратный переход после tool-фильтров.
- Исправлен неполный список значений status в двух фильтрах модели; `all`,
  `active`, `deprecated`, `retired`, `archived` отображаются согласованно.
- Локальный `flags.svg` дополнен `IL`, `JP`, `NL`, `SA`, `AU`, `CZ`, `SE`.
  Автопроверка: отсутствующих символов — 0 для всех 16 кодов стран моделей и
  всех 14 кодов, извлечённых из подтверждённого `Organization.country`
  инструментов. Составные значения (`USA/UK`, `India/USA`) показывают оба
  флага; `Open source` / `International` не получают выдуманный флаг.
- Высота строки 55 px сохранена. Внутри неё увеличены основной текст таблицы,
  названия, вторичные подписи, назначения, цена/доступ/дата, badges, флаги и
  знаки разработчика. Проверено в RU/EN и dark/light без наложений.
- Для сортировки по номеру SQLite теперь выбирает только нужный кусок
  150/50 строк, а не загружает и декорирует весь набор. Повторный Local-ответ
  обычного каталога моделей сократился примерно с 600–700 мс до 250–320 мс;
  проверенные сложные фильтры — примерно 110–200 мс. Набор и lazy loading не
  урезаны.
- `prepare_local_catalog.py` больше не отвергает уже существующую Local SQLite
  из-за устаревших фиксированных размеров исходного snapshot. Строгие старые
  числа проверяются только при первичном копировании snapshot; существующая
  база всё так же проходит integrity и проверку отсутствия users/sessions.

Проверки: **78 Django tests PASS**; `manage.py check` PASS; `makemigrations
--check --dry-run` — изменений нет; SQLite `integrity_check=ok`,
`foreign_key_check=0`; `git diff --check` — без ошибок. Browser Local PASS:
RU/EN, dark/light, полная хронология, active/retired/category/access/price
filters, tool platform/local/sort filters, обе вкладки, переход из правой
карточки и флаги. Local слушает только `127.0.0.1:18810`.

Изменено: `catalog/views.py`, `catalog/comparison.py`, `templates/catalog.html`,
`templates/tool_rows.html`, `static/site.css`, `static/flags.svg`,
`tools/local/prepare_local_catalog.py`, regression tests и этот статус. Не
завершено: ручная визуальная приёмка владельцем. Следующим выполнить: владелец
проверяет Local; commit/push/Production возможны только по отдельной команде.

## Архив: reconciliation Local + research master (2026-09-22)

- Новый источник:
  `C:/Users/dimon/Desktop/AIpedia_global_research_master_2026-09-21_applicability_fixed.xlsx`;
  SHA-256 и каждая исходная строка сохранены в provenance `ResearchRecord`.
- До импорта в Local было 234 модели и 21 инструмент. После reconciliation —
  763 модели и 138 инструментов: добавлены 529 моделей и 117 инструментов,
  уточнены 80 существующих моделей и 11 инструментов. `LM Studio` сопоставлен
  с существующей записью `LM Studio / Bionic`; созданных дубликатов — 0.
- Сохранены все исходные pk/slug/URL, даты существующих записей, 503 цены,
  280 доступов, 854 оценки, 89 источников и вся история ревизий; потерь и
  изменения прежних строк этих таблиц нет. Позиционные `public_number`
  пересчитаны только по подтверждённой хронологии после вставки более ранних
  дат; относительный порядок прежних моделей/инструментов сохранён, значения
  до reconciliation записаны в канонической книге и истории ревизий.
- Частичные даты не превращались в фиктивный день: они сохранены в evidence и
  XLSX, а `released` заполнен только для точной даты. Неизвестные значения
  остались пустыми. Рейтинг AIpedia не рассчитывался.
- Добавлены 52 подтверждённых ценовых предложения и 27 наблюдений benchmark;
  цена хранится с единицей/scope/источником/датой, оценка — с точной версией,
  evaluator/benchmark/score/snapshot/source. Всего Local: 555 offers,
  1205 accesses, 881 evaluations, 343 sources и 737 provenance-записей партии.
- Применимость исправлена для image/video/STT/TTS и historical/retired: modern
  LLM-поля не обязательны там, где они не применяются. Дополнительно очищены
  ошибочные требования контекста у 9 TTS/audio-записей источника.
- Канонический файл:
  `outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_catalog_master.xlsx`.
  В нём ровно две таблицы/вкладки: `Модели` (763 строки, 73 колонки) и
  `Инструменты` (138 строк, 53 колонки); provenance и verification находятся
  внутри этих таблиц, формульных ошибок не найдено, оба листа отрендерены и
  визуально проверены.
- Остаток очереди качества: Required — 711 записей / 1376 полей; Needs
  verification — 108 записей / 110 пунктов. Это явные пробелы, не нули и не
  догадки. Состав: модели 600/1265 Required и 103/104 Needs; инструменты
  111/111 Required и 5/6 Needs.
- Резервная копия до импорта:
  `backups/aipedia-before-global-master-reconcile-20260922T035236Z.sqlite3`,
  SHA-256 `7a0a0584e505ec4392eec4647752e280611b91862d6f1f1c65d0c00f974a1a8e`.
- Браузер Local PASS: RU/EN, вкладки моделей/инструментов, `status=all` (763),
  retired-поиск, сортировка, API-фильтр инструментов, правая карточка, а также
  historical McCulloch-Pitts, retired Jurassic-1 Jumbo, API GPT-6 Astra,
  open-weight Llama 3 70B, TTS Eleven v3, ChatGPT и Grok Voice API.
  Active-срез показывает 412 моделей и 137 инструментов; полный набор доступен
  в обычном виде и через явный статус `Все`.
- Автоматические проверки PASS: 75 Django tests; `manage.py check` без ошибок;
  `makemigrations --check --dry-run` — изменений нет; SQLite `integrity_check`
  — `ok`, `foreign_key_check` — 0; `git diff --check` — без ошибок.

Изменено: только Local SQLite, этот статус, свежий `AI_CONTEXT` и итоговый XLSX;
интерфейс, маршруты, модели Django и Production не менялись. Не завершено:
явно перечисленные Required/Needs verification требуют будущей проверки по
источникам; это не препятствует сохранению подтверждённой части. Следующим
выполнить: владелец проверяет канонический XLSX и задаёт приоритет очереди
Required/Needs verification; публикация возможна только отдельной командой на
конкретный commit/tag по `docs/RELEASE.md`.

## Доказательства для архива

- tools/pack_ai_context.py
- docs/EXECUTION_STATE.md
- outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_catalog_master.xlsx

## Архив: глобальный research master (2026-09-21)

- Сопоставлены `AIpedia_global_catalog_2026-09-21.xlsx`,
  `AIpedia_global_catalog_2026-09-21_pass2.xlsx` и
  `AIpedia_site_data_2026-09-21_pass3.xlsx`.
- Pass 3 выбран структурной основой: он содержит все названия из двух ранних
  книг, добавляет к pass 2 ещё 22 модели и 3 инструмента, а к первому проходу —
  94 модели и 10 инструментов; потерь по названиям не найдено.
- Создан
  `outputs/01a0c6f2-58a7-71d3-8dd5-e0f844e2e96d/AIpedia_global_research_master_2026-09-21.xlsx`:
  609 моделей/нейросистем, 128 инструментов, обзор, очередь проверки,
  аудит актуальных источников, происхождение данных и словарь полей.
- В очередь вынесена 621 запись с конкретным незакрытым вопросом. Неизвестные
  значения не заменялись нулями или догадками; хронологические номера сохранены.
- По официальным источникам точечно перепроверены GPT-6 Astra, Claude Fable 5.1,
  Grok 4.7, Qwen3.8-Flash, Gemini CLI, Antigravity CLI и Grok Voice API.
  Для GLM-5.3-Flash отдельно зафиксировано различие между первым публичным
  preview 2026-08-20 и официальным материалом Z.ai 2026-09-21.
- У Grok Voice API обнаружено расхождение официальных страниц: developer docs
  показывают `$0.08/min`, продуктовая страница — `$0.05/min`; в master оставлена
  цена developer docs и явное требование перепроверки.

Проверки: XLSX ZIP integrity PASS; 7 листов и 6 Excel tables открываются через
`openpyxl`; 609/128 строк сохранены; формулы протянуты до последних строк;
скан ошибок `#REF!/#VALUE!/#NAME?/#N/A/...` — 0; визуально проверены 9 рендеров
всех листов и обеих половин широких таблиц.

Изменено: создан только отдельный research workbook и обновлён этот статус;
код, Local SQLite, GitHub и Production не менялись. Не завершено: 621 пункт
очереди не прошёл независимую построчную web-проверку, данные не импортированы
в Local. Следующим выполнить: владелец подтверждает границы каталога и приоритет
очереди; затем отдельной задачей провести пакетную верификацию и подготовить
безопасный preview-импорт в Local без перенумерации и без перезаписи SQLite.

## Текущая работа: разделение моделей и инструментов (2026-09-22)

- В интерфейсе ровно две вкладки; смешанного режима «Все» нет.
- Используются разные query, view model, таблицы, фильтры, сортировки, URL и панели.
- Создана отдельная сущность `Tool`, связанная с исходной legacy-записью через
  `PROTECT`; все 255 исходных `ModelVersion` и связанные цены/доступ сохранены.
- Страны нормализованы через `Country` / `ModelOriginCountry`, платформы — через
  `Platform` / `ToolPlatform`. Неизвестное происхождение остаётся пустым.
- Независимая нумерация: модели №001 — Eleven Multilingual v2; инструменты
  №001 — GitHub Copilot. Фильтры и сортировки номера не меняют.
- Штатный Local launcher валидирует обе хронологии.

Фактические данные Local: 234 модели всего, 233 active, 1 archived; 21 active
инструмент; 198 пронумерованных моделей и 14 инструментов; страна указана у
230/234 моделей (229/233 active), 4 карточки `ai-sage` остаются пустыми.

Проверки: 75 тестов PASS; Django check PASS; migrations check PASS; `node --check`
PASS; SQLite quick_check `ok`, foreign_key_check 0; `git diff --check` PASS.

Браузер Local после явного разрешения владельца: desktop 1672×941 и mobile
390×844 PASS; RU/EN, dark/light, поиск, сортировка, обе панели и Escape PASS.
Панель инструмента не содержит модельных проверок, рейтинга или контекста.

Резервная копия до миграции:
`backups/aipedia-before-model-tool-split-20260921.sqlite3`.

## Архив предыдущей текущей работы (до разделения каталогов)

### Этап «дата релиза: день + месяц» (2026-09-21)

- Поручение: сокращённый месяц как раньше, плюс число дня; EN в американском порядке.
- Изменено: `catalog/templatetags/catalog_tags.py` (`month_year`), таблица и панель,
  `docs/visual-spec.md`, тест в `test_redesign.py`.
- Формат: RU `29 Июн 2021`, EN `Jun 29, 2021`.
- Проверено в Local; тест OK.
- Commit, push и публикация не выполнялись.

### Этап «дата релиза с числом» (2026-09-21) — заменён

- Кратко был `дд.мм.гггг`; заменён форматом выше по просьбе владельца.

### Этап «подгрузка при прокрутке» (2026-09-21)

- Поручение: убрать 12/25/50; сначала 150 строк, при долистывании вниз ещё по 50.
- Изменено: `catalog/views.py` (`CatalogPaginator` / `CatalogPage`, `INITIAL_PAGE_SIZE=150`,
  `CHUNK_SIZE=50`), `templates/catalog.html` (`#infinite-scroll`, счётчик `#shown-count`,
  без селектора строк), `static/site.js` (IntersectionObserver на `.table-scroll`, Retry),
  `static/site.css`, тесты пагинации/SEO.
- Проверено в Local: первая отрисовка 150; скролл → 200 → 250 → 254; счётчик обновляется;
  `partial=rows` отдаёт по 50 и `X-Aipedia-Next`.
- Тесты: `manage.py test catalog --settings=aipedia.test_settings` — после правки evidence.
- Commit, push и публикация на этом этапе не выполнялись.

### Предыдущий этап «знаки разработчиков» (2026-09-21)

- Знаки 34 разработчиков в таблице и правой панели; Local 34/34 published со знаком.
- Незакоммичено вместе с редизайном.

### Предыдущий этап «воспроизведение утверждённой оболочки»

- Спецификация и пиксельные измерения — `docs/visual-spec.md` §10.
- Орбита, бренд, палитра, геометрия таблицы/панели — в Local, незакоммичено.

### Архивная карта смешанной таблицы (элемент → источник → есть/нет → показ)

| Элемент | Источник | В Local сейчас | Показ |
| --- | --- | --- | --- |
| № | `public_number` | 212 из 255 | пусто, если нет |
| Название | `name`, `version`, знак разработчика | все | SVG/PNG из `static/marks/`; иначе инициал |
| Тип | `entry_type` | все | текущая классификация |
| Разработчик | `family.developer` | есть | как сохранено |
| Для чего | задачи / категории | есть | токены назначений |
| Стоимость | `Offer` | 503, не у всех карточек | вход и выход раздельно; без «Бесплатно» из макета |
| Доступ | `Access` / `Service` | есть | виды запуска |
| Независимые проверки | `Evaluation` independent | 752 | первичные/составные подписи сохранены |
| Составные индексы (ECI и т.п.) | `result_kind=composite` | 58 | вкладка «Проверки», не рейтинг AIpedia |
| Отчёты разработчика | `independent=False` | есть в БД | не в колонке независимых; во вкладке с подписью |
| Рейтинг AIpedia | нет утверждённого поля | 0 | пустая колонка и блок |
| Контекст | `ModelVersion.context` | 18 | иначе пусто |
| Релиз | `released` + источник | 212 | иначе пусто |
| Fact / аудит | `Fact`, `AuditReport` | 0 | блоки пустые |
| GitHub-кнопка | только реальный репозиторий | по ссылкам | не у каждой модели |
| Сохранить | кабинет | нет | неактивно, подсказка |

### Архивные проверки предыдущего этапа

| Что | Когда | Версия | Результат |
| --- | --- | --- | --- |
| Browser Local: scroll 150→200→250→254 | 2026-09-21T23:30Z | http://127.0.0.1:18810/?lang=ru | **PASS** |
| `partial=rows` page=2 → 50 строк + Next | 2026-09-21T23:30Z | Local | **PASS** |
| `manage.py test catalog --settings=aipedia.test_settings` | 2026-09-21T23:31Z | после infinite scroll | **PASS, 69 тестов** |
| Покрытие published → mark | 2026-09-21T23:25Z | Local SQLite | **34/34**, 0 без знака |
| Production | эта сессия | — | **не запускалось** |

### Архивные расхождения документов

- `docs/ACCEPTANCE.md` всё ещё пишет, что приёмка владельцем ожидается. Хронология 2026-09-20 опубликована; редизайн Local — к новой приёмке вида, не к публикации.
- `docs/VERIFICATION.md` старше текущего GitHub (`7e66da2`) и незакоммиченных файлов.
- Пустые рейтинг AIpedia, факты, аудиты и большинство контекстов — согласованное ограничение этого этапа, не дефект вёрстки.

### Архивные ограничения предыдущего этапа

- Рейтинг AIpedia не рассчитывается.
- «Сохранить» неактивна.
- 43 карточки без доказанной даты и номера остаются в конце хронологии.
- У части моделей нет офферов (пример: GPT-4.1) — вкладка стоимости пустая, не «Бесплатно».
- Знак — у разработчика, не у отдельной версии модели (так в эталоне и в `D-2026-09-21-developer-marks`).
- Адрес с хвостовым слэшем `/models/<slug>/` по-прежнему 404 (было до редизайна).
- Local слушает 127.0.0.1:18810; это не публичный сайт.
- Грязные незакоммиченные файлы: редизайн, знаки, infinite scroll, docs, artifacts, AI_CONTEXT, data/research.
- Без JS остаётся ссылка «Далее» на следующую порцию (полная перезагрузка страницы).

### Доказательства предыдущего этапа

Относительные пути; сборщик копирует их в zip, если файл есть и не секрет:

- docs/history/2026-09-20-chronology-release.md
- docs/RELEASE.md
- docs/DECISIONS.md
- docs/visual-spec.md
- tools/pack_ai_context.py
- artifacts/reference-plan-design.png
- artifacts/visual-rebuild/local-final-1672x941.png
- static/marks/

## Передача на Production (серверные шаги, выполняет владелец на хосте)

Развёртывание и перенос переводов запускаются **на самом сервере** `/srv/aipedia`
(в этом окружении нет SSH к хосту AIpedia; [ЗАМЕНЕНО 2026-09-26: правило «StratForge-ключи не используются» неверно — см. AGENTS.md, раздел «Общая серверная машина и SSH»: разрешено использовать настроенную SSH identity к общей машине строго в контуре AIpediya, ключи не читать и не раскрывать]).
Порядок строго по `docs/RELEASE.md`; Local SQLite на сервер не копируется;
туннель, секреты и StratForge не трогаются.

1. Локально собрать архив на релизном commit и сохранить SHA256:
   `.\.venv\Scripts\python.exe tools/build_code_release.py`
   (архив в `artifacts/code-release/aipedia-code-<commit12>.zip`, только
   tracked-файлы, без SQLite/секретов).
2. Локально проверить изолированно и dry-run:
   `.\.venv\Scripts\python.exe tools/verify_isolated_release.py`
   `.\.venv\Scripts\python.exe tools/deploy_code_release.py <archive> --sha256 <digest> --dry-run`
3. Скопировать на сервер **два** файла (без Local SQLite): архив кода и
   `artifacts/translation-data-release/translations-export.json` (42 260 записей,
   15.3 MB, только переводы, без секретов).
4. На сервере развернуть код:
   `python3 tools/deploy_code_release.py /path/aipedia-code-<commit12>.zip --sha256 <digest>`
   (останавливает только `aipedia`, online-backup серверной БД, перенос кода и
   статики, `migrate` существующей БД, старт `aipedia`, проверка `/healthz`).
5. На сервере перенести переводы в существующую серверную БД, идемпотентно и без
   провайдера, сначала dry-run:
   `python3 manage.py import_translations /path/translations-export.json --dry-run`
   затем боевой прогон без `--dry-run`. Импорт применяет перевод только там, где
   английский источник на сервере совпадает по sha256; несовпадения безопасно
   пропускаются (остаётся английский), повторный запуск ничего не меняет.
6. Публичная проверка `https://aipediya.com/`: `/healthz`, Модели и Инструменты,
   карточка модели и инструмента, EN/UK/AR(RTL), локализованные описания и
   страны, оригинальные бренды/ID/API/бенчмарки, правая панель (клик вне/Escape/
   крестик), меню языков над панелью, смена языка сохраняет карточку, desktop и
   mobile, защита числовых токенов (например «1M»).

Экспорт переводов проверен на Local: `import_translations --dry-run` против той
же базы даёт applied=0, unchanged=42 260 (полная идемпотентность).
