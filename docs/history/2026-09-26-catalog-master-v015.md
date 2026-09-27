# catalog-master-v015 — новые модели 22–24.09.2026 (Local → Production)

Дата: 2026-09-26 (UTC 2026-09-27). Основание: поручение владельца обновить AIpediya
по master v015, импортировать подтверждённые модели в Local, проверить, внести в
Timeline, затем опубликовать те же изменения на Production без копирования
Local SQLite. Статус «опубликовано и проверено» ставится только после реального
выпуска и публичной проверки (раздел 6).

## 1. Master v015

- Принятый файл `AI_CONTEXT/AIpediya_Model_Verification_Master_updated_2026-09-26.xlsx`
  (sha256 `cc431f94468d…`, копия — `backups/catalog-master-v015-20260926/`)
  установлен как канонический `AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx`.
  Расхождение: канонического файла v014 в `AI_CONTEXT/` на момент начала не было;
  v015 собран поверх `AIpediya_Model_Verification_Master(6).xlsx` (Meta `RUN_V015_*`).
- `check` отклонил два новых Record ID с точкой (`gemini-3.8-flash-tts`,
  `gemini-3.8-flash-lite-tts`). Записи ещё не были ни в Local, ни в Production;
  до первой синхронизации они приведены к `gemini-3-8-flash-tts` /
  `gemini-3-8-flash-lite-tts` вместе с 22 связанными строками
  (`tools/master_v015_import_2026_09_26.py`, всё в Changelog).
- Задачи и модальности новых записей были свободным текстом («speech synthesis»,
  «robot state»); приведены к словарю сайта (модальности text/image/audio/video/other,
  существующие ключи задач), подробности остаются в описаниях — 16 полей, Changelog.
- Итог: `check: OK`; Models 321 PUBLISHED / 474 NEEDS_REVIEW, Tools 143 / 2.

## 2. Состав изменений

Новые модели (номер — хронологическая позиция по подтверждённой дате выпуска):

| № | Модель | Разработчик | Дата выпуска | Источник даты |
|---|---|---|---|---|
| 311 | Claude Opus 5.5 | Anthropic | 2026-09-22 | platform.claude.com/docs/en/models/opus-5-5 |
| 312 | Gemini 3.8 Flash TTS | Google | 2026-09-22 | Gemini API changelog / model page |
| 313 | Gemini 3.8 Flash-Lite TTS | Google | 2026-09-22 | Gemini API changelog / model page |
| 314 | GPT-6 Luna | OpenAI | 2026-09-22 | OpenAI API changelog |
| 315 | GPT-6 Sol | OpenAI | 2026-09-22 | OpenAI API changelog |
| 316 | FLUX 3 Action DROID | Black Forest Labs | 2026-09-23 | Hugging Face model card / BFL blog |
| 317 | FLUX 3 Action SO-101 | Black Forest Labs | 2026-09-23 | Hugging Face model card / BFL blog |
| 318 | Nemotron 3 Diarization | NVIDIA | 2026-09-23 | Hugging Face model card |
| 319 | GLiNER2.5-Decide | Fastino AI | 2026-09-24 | Fastino launch post |
| 320 | Sarvam Vision 2.1 | Sarvam AI | 2026-09-24 | Sarvam blog |
| 321 | Speech TTS Live | Yandex | 2026-09-24 | Yandex AI Studio docs |

При одинаковой дате порядок — по имени, затем Record ID (правило master).
Существующие номера 1–310 не сдвинулись.

Также из master v015 (статус PUBLISHED): четыре новых инструмента — Alice AI Pro for
Business, Qwen Intelligence, Yandex AI Studio, SourceCraft (18 инструментов получили
новый хронологический номер из-за вставки SourceCraft ≈2025 и Yandex AI Studio
2025-09-24); исправления 9 существующих моделей (категория `image` → `text` у
GPT-5.6 Sol/Terra/Luna, GPT-6 Astra, Claude Opus 5, Claude Fable 5.1, Claude Sonnet 5,
Claude Haiku 4.5; задачи; контекст Claude Haiku 4.5 1M → 200K; alias `gpt-5.6`).

Не публикуются (NEEDS_REVIEW): Speech Realtime Max TTS Live, CLM-v0.1-8B (модели),
AX (инструмент) — на Local и Production отвечают 404 и не находятся поиском.

## 3. Код: новые модели приходят с ценами и доступом

`sync-local` / `release-plan` раньше создавали новую карточку без её строк Offers/Access
(они уходили в `unsupported`). Теперь запись `create` новой модели несёт её строки
master: 35 цен и 26 строк доступа 11 моделей, а также Suitable/Limitations EN/RU и
Release Evidence. Цена требует `Research Key` (по нему повторный запуск и `import`
узнают строку); сервис переиспользуется при полном совпадении, иначе создаётся;
единица проверяется по виду сервиса. `import`/`check` сопоставляют такие строки по
содержимому (`NATURAL_KEYS`: Research Key; владелец + сервис + ссылка). Строки
существующих записей и новых инструментов по-прежнему только в отчёте `unsupported`.

Найдено испытанием выпуска и исправлено: `final_state_problems` считал расхождением
номера черновиков master (NEEDS_REVIEW), которых нет в базе; `apply-plan` правильно
откатил пробный перенос. Теперь отсутствующая запись без планового номера — верное
состояние. Регрессионные тесты — `NewModelLinkedRowsTests`.

## 4. Local

- Резервная копия рабочей базы: `backups/catalog-master-v015-20260926/aipedia-local-before-v015.sqlite3`
  (sha256 `29d2c5dda826…`).
- Пробный прогон на копии: `sync-local --apply` 56 изменений → `import` (+3 связи
  платформ SourceCraft) → `check: OK` → повторный `sync-local` 0 записей.
- Рабочий Local: те же 56 изменений, `check: OK`, повтор 0; переводы
  `translate_catalog` (Azure, 41 580 символов, 440 переводов, 0 ошибок).
- Сохранность (сравнение с резервной копией): pk/slug всех 920 прежних записей без
  изменений; 0 изменённых или удалённых прежних строк цен, оценок, доступа, источников,
  сервисов; журналы только выросли (Revision 4867 → 4957, PublicationRevision
  4847 → 4879, ToolPublicationRevision 569 → 599).
- Каталог: 321 модель / 143 инструмента; номера моделей 1–321 без пропусков и
  повторов, по дате монотонны; дублей названий и алиасов среди публичных нет.
- HTTP-проверка (`artifacts/catalog-master-v015/v015_check.py`) на Local с текущим
  кодом: 144/144 PASS — карточки EN/RU 200, имя, номер, дата выпуска, цены
  Claude/GPT-6/Gemini TTS; поиск по имени и алиасам (`claude-opus-5-5`, `Opus 5.5`,
  `fastino/GLiNER2.5-Decide`, `nvidia/Nemotron-3-Diarization`,
  `speech-realtime-tts-live`); 3 записи NEEDS_REVIEW — 404 и нет в поиске; счётчики
  321/143; порядок по умолчанию 321 → 310; sitemap 321/143. Браузер: RU-поиск
  «GPT-6», карточка Claude Opus 5.5; переводы ja/de/ar.
- Тесты: `manage.py test catalog` — 272 (271 OK, 1 skip) в рабочем дереве.

## 5. Кандидат выпуска

Ветка `release/catalog-master-v015` от опубликованного `0702405` (код Production
`61adedd` + документы), только файлы из `data/release/v015/CANDIDATE_FILES.txt`;
незавершённая работа `main` (история сайта и др.) в выпуск не входит.

- `data/release/v015/catalog_plan.json` — `release-plan` на копии исходного снимка
  Local (310/139, сверен с публичным Production в v014; не копия серверной БД):
  create 15, update 9, number 18.
- `data/release/v015/translations.json` — 440 переводов 15 новых записей.
- `data/release_state.json` — 321 Models / 143 Tools.
- Пробный перенос (как на сервере): migrate → apply-plan 56 записей, итог = план →
  import_translations 440 → sync_publication_state 0 изменений → повтор apply-plan
  «already applied», повтор переводов 0. Результат совпал с рабочим Local по моделям,
  инструментам, ценам, доступу, оценкам, странам, платформам и текстам
  (`artifacts/catalog-master-v015/release_trial_vs_local.txt`).

## 6. Production

Ожидает выпуска.
