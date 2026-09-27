# catalog-master-v015 final — счётчики, страны и флаги, цены, независимые оценки, QA

Дата: 2026-09-27 (UTC). Основание: поручение владельца довести v015 до завершённого
состояния в master, Local, Timeline, GitHub и Production. Этот этап не меняет даты
выпуска моделей: номера 1–321 и все даты сохранены (проверка сохранности ниже).

## 1. «143 Tools» и «116»

Установлено на Local и Production (серверный HTML и состояние после JS): вкладка
Tools = 143, счётчик «143 результата», «Показано 143 / 143», в DOM 143 строки,
backend-total 143 — один и тот же набор опубликованных инструментов. «116» — не
количество, а **номер в колонке №** первой строки: хронологический номер получают
только 116 инструментов с подтверждённой датой выпуска, у 27 даты нет и номера нет.
Исправление: рядом со счётчиком (Models и Tools, 22 языка) показывается
«с датой выпуска (№): 116 · без подтверждённой даты, без №: 27», когда есть
записи без даты; QA сверяет вкладку, счётчик, «Показано x / y», строки после
загрузки всех страниц и базу (EN/RU).

## 2. Страны и флаги

- Модели: у 11 опубликованных моделей не было страны (10 новых v015 и GigaChat 3.5
  432B A28B Reasoning). Добавлены строки Origins с источником: США (Anthropic,
  OpenAI, Google, NVIDIA, Fastino — пресс-релиз «based in Palo Alto, California»),
  Германия (Black Forest Labs), Россия (Yandex, Sber — корпоративный блог).
- Инструменты: страна разработчика заполнена для 15 инструментов (Cursor, Ollama,
  LM Studio, Midjourney, Suno, ComfyUI, GitHub Copilot, 4 голосовых инструмента xAI,
  Cline — США; Qwen Intelligence — Китай; Alice AI Pro for Business, SourceCraft —
  Россия), источники — условия использования/страницы компаний (Facts `origin_status`).
- Не установлено и не выдумано (очередь качества данных): Aider (проект
  частного лица), llama.cpp (сообщество ggml-org), Roo Code (сайт перенаправляет на
  roomote.dev без юрлица).
- Правило (постоянное, `D-2026-09-27-release-qa-gate`): опубликованная запись с
  известным происхождением без страны/флага — блокирующая ошибка QA; флаг должен
  существовать в `static/flags.svg`.

## 3. Цены

Официальные страницы проверены 2026-09-27. Добавлено 70 строк цен (валюта, единица,
вход/выход, модальность, контекстный уровень, дата вступления, источник):
GPT-5 Pro, 5.1, 5.2, 5.2 Pro, 5.3-Codex, 5.4, 5.4 Pro, 5.4 mini, 5.4 nano, 5.5, 5.5 Pro
(Standard, <272K; длинный контекст на странице не опубликован — не выдумывался),
Gemini 3.1 Flash-Lite Image, Qwen3-Coder-480B (три уровня контекста),
Qwen3.8-LiveTranslate, Kimi K2.6 / K2.7 Code / K3, Solar Pro 2, Sarvam Vision 2.1
(₹ за страницу), Speech TTS Live ($ без НДС и ₽ с НДС за начатый блок 250 символов),
SourceCraft (тарифы с 2026-10-01 — сохранены как запланированные, неактивные),
Amazon Q Developer Pro и ElevenLabs burst (ранее собранные строки, добавлены RU-условия).
Четыре существующие строки $0 (Leanstral 1.5, Mistral Moderation 2, Cursor Hobby,
Suno Free) — подтверждённые бесплатные тарифы; условия теперь это явно говорят.
Сайт показывает валюту строки (₹, ₽, $), сравнения цен остаются только в USD.

Проверенные пробелы (факты `pricing_status`, не «$0»): Command A+ и North (цены по
договору), Jamba 1.5 и PLaMo 2.x (API продаёт уже новые версии), Qwen-Image-2.1,
PLaMo Translate, EXAONE 4.0, GLiNER2.5-Decide (нет официальной цены хостинга),
Nemotron 3 Diarization и FLUX 3 Action (открытые веса без API), Alice AI Pro for
Business, Qwen Intelligence (цена не публикуется), Yandex AI Studio (оплата по моделям),
MiniMax Speech Recognition (валюта не подтверждена — строка не опубликована).
Retired/archived модели не требуют текущей цены.

## 4. Независимые оценки

Источник с правом публикации — собственные прогоны Epoch AI (CC BY 4.0), снимок
2026-09-27 (`artifacts/epoch-ai-2026-09-27/`). Сопоставление только с точной версией:
добавлено 25 результатов — Claude Opus 5.5 (EBR-bench, Furniture Assembly, max),
GPT-6 Sol (те же, max), Qwen3.8-Max, Qwen3.8 Max (0902), DeepSeek V4 Flash 0731
(GPQA Diamond, FrontierMath, SimpleQA и др.). Artificial Analysis, Arena, LiveBench и
лидерборд SWE-bench не используются (условия запрещают републикацию); данные
разработчиков не считаются независимыми. Честные пробелы (9, показываются в
карточке): GPT-6 Luna, Gemini 3.8 Flash TTS / Flash-Lite TTS, Speech TTS Live,
Nemotron 3 Diarization, Sarvam Vision 2.1, GLiNER2.5-Decide, FLUX 3 Action DROID / SO-101.

## 5. Master, синхронизация и QA

- Все изменения — сначала в master v015 (`tools/master_v015_final_2026_09_27.py`,
  Changelog), затем `sync-local`. Резервные копии: master до этапа и Local до этапа —
  `backups/catalog-master-v015-20260926/`.
- `sync-local` / `release-plan` теперь переносят новые строки цен, доступа, стран и
  независимых оценок существующих записей, страну разработчика (только когда в Local
  её нет) и версию инструмента; у инструмента без legacy-строки создаётся контейнер
  цен и доступа. Строки узнаются по содержимому (Research Key, Observation Key,
  владелец + сервис, модель + страна) — повторный запуск и `import` дублей не дают.
- `catalog_master qa` — блокирующие проверки (счётчики, страна/флаг, цена
  коммерческого API, $0 без бесплатного тарифа, независимость и права источника
  оценок, источники, дубли, master ↔ Local ↔ Production) и очередь качества данных
  с применимостью по фактам `*_status`.

## 6. Local

- `sync-local`: 144 изменения (70 цен, 19 доступов, 25 оценок, 11 стран моделей,
  11 стран разработчиков, 4 версии инструментов, 4 условия); `import` ничего не
  добавил; `check: OK`; повтор 0 записей; переводы не требуются.
- Сохранность: ни одна дата, номер, ID или публикация модели/инструмента не
  изменились; прежние цены, оценки, доступы и страны не изменены и не удалены
  (кроме 4 уточнений условий бесплатных тарифов); журналы выросли.
- `catalog_master qa` — PASS (0 ошибок, очередь 29, предупреждений 17 — даты без
  ссылки на доказательство у старых моделей); HTTP `final_check.py` — 207/207;
  тесты — 290 (289 OK, 1 skip); браузер: счётчик Tools, флаги, цены ₹.

## 7. Git и Local 18810

`main` приведён к опубликованной линии: fast-forward до `00cb8f4`
(`release/catalog-master-v015`), незакоммиченная работа сохранена (резервная копия
`backups/main-wip-20260927/`), конфликты разрешены в пользу проверенного на
Production поискового кода. Local 18810 перезапущен штатными скриптами на
актуальном коде.

## 8. GitHub и Production

- GitHub: `main` = `a51c0a1aed2f63047b0203b208eccf8def458ae7` (push), ветка
  `release/catalog-master-v015` и tag `release-2026-09-26-catalog-master-v015`
  опубликованы; tag этого выпуска — `release-2026-09-27-catalog-master-v015-final`.
- Архив `aipedia-code-a51c0a1aed2f.zip`, SHA-256
  `e2f5485db53988bd7d66fd9fa5542665d2e232d157aa12071b1ae2446b3a92e1`, 327 файлов (без
  SQLite, секретов и XLSX); распакованный архив — 290 тестов (289 OK, 1 skip).
- Пробный перенос плана на исходный снимок Local совпал с рабочим Local по моделям,
  инструментам, организациям, ценам, доступу, оценкам и странам; QA на пробной базе PASS.
- Preflight на онлайн-копии боевой БД
  `/srv/aipedia/backups/aipedia-preflight-v015-final-20260927T032300Z.sqlite3`
  (integrity ok, 321/143, 590 цен): pending -> 144 записи, итог = план; манифест 0
  изменений; повтор «already applied»; стало 660 цен, 906 оценок, 844 страны, номера 1–321.
- `deploy_code_release.py` (2026-09-27 03:23:13Z): backup
  `/srv/aipedia/backups/aipedia-before-code-20260927T032313Z.sqlite3`; миграций нет;
  `apply-plan` 144 записи, итог = план; `sync_publication_state --apply` 0 изменений;
  `deployed-origin-verified`, `copied_sqlite=false`; предыдущий код —
  `/srv/aipedia/releases/before-code-20260927T032313Z`; после —
  `aipedia-after-code-20260927T032313Z.sqlite3`. StratForge и другие программы не
  затрагивались.

## 9. Публичная проверка https://aipediya.com

- `/healthz`: release `a51c0a1aed2f…`, production.
- `final_check.py` — 207/207 (`artifacts/catalog-master-v015-final/public_final_check.json`):
  все проверки v015 (144) + счётчики EN/RU после загрузки всех страниц (321 / 143),
  пояснение № Tools 116 / 27, флаги 21 карточки, цены (USD, INR, RUB), независимые
  оценки Opus 5.5 / GPT-6 Sol / Qwen3.8-Max / DeepSeek V4 Flash 0731, пробелы оценок.
- `catalog_master qa --production` — PASS: публичные наборы master = Local = Production.
- Поиск: `gsd_public_check` 34/34, `search_visibility_qa` 45/45 старых URL (25 × 301,
  19 × 404, 1 × 200 noindex); `/history/` на Production — 404 (только Local).
- Браузер: Tools 143 = счётчик = 143 строки, пояснение и флаги; оценки Claude Opus 5.5.

**Статус: Local PASS → Timeline PASS → GitHub synced → Production PASS → Public PASS. Этап закрыт.**
