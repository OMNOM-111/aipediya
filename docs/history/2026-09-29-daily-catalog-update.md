# Daily Catalog Update — Release #016 / v0.14.0

Карточка: `DAILY-CATALOG-UPDATE-2026-09-29`.
Исполнитель: GitHub Copilot. Старт карточки: 2026-09-29T20:42:02Z.

## Scope

Продолжен тот же Release #016. Новая карточка не создавалась. Внесён только
пакет данных из поручения владельца от 2026-09-29: новые модели, Cue, Manus 2.0
и проверка OpenAI shutdown records. SEO, производительность, переводы и старые
очереди не входили в scope.

## Master

Перед записью сделан backup master:
`backups/daily-catalog-20260929-20260929T210019Z/AIpediya_Model_Verification_Master.before.xlsx`.

Идемпотентный импорт: `tools/daily_catalog_update_2026_09_29.py`.

Добавлены PUBLISHED Models:

- Claude Sonnet 5.5 — `claude-sonnet-5-5-899c1979`, Anthropic, 2026-09-28.
- Eleven v4 — `eleven-v4-1cc3a926`, ElevenLabs, 2026-09-28.
- Eleven v4 Turbo — `eleven-v4-turbo-6a02a110`, ElevenLabs, 2026-09-28.
- Holo4-27B — `holo4-27b-62d1091f`, H Company, 2026-09-28.
- Holo4-35B-A3B — `holo4-35b-a3b-b9f93a3e`, H Company, 2026-09-28.
- Holotron4-30B-A3B — `holotron4-30b-a3b-c0c87f8d`, H Company, 2026-09-28.

Добавлены PUBLISHED Tools:

- Cue — `cue-77457549`, Manus, 2026-09-28.
- Manus — `manus-0214c7c8`, Manus 2.0, 2026-09-28. На старте master/Local
  существующей Manus Tool-card не было; дубль не создавался.

Не созданы публичные карточки:

- Meta Enterprise Platform — источник описывает направление/платформенную
  инициативу и будущие продукты/сервисы, без ясной standalone self-serve Tool-card.
- Claude Haiku 5.5 — Anthropic указал future availability “in the coming weeks”.

OpenAI shutdown records:

- Exact master/Local records для `gpt-3.5-turbo-instruct`, `babbage-002`,
  `davinci-002`, `gpt-3.5-turbo-1106` не найдены. Существующие семейные/другие
  записи не закрывались вместо отсутствующих exact records. `ft-babbage-002` и
  `ft-davinci-002` не изменялись.

## Local QA

- `catalog_master refresh` — PASS, renumbered=8.
- `catalog_master check` — OK.
- Trial sync на копии Local: 8 creates, integrity OK, FK 0.
- Post-import trial QA — PASS; повторный план содержит только прежние
  513 `intentional_master_only`.
- Working Local backup:
  `backups/daily-catalog-20260929-local-20260929T211835Z/aipedia-before-daily-catalog-016.sqlite3`.
- Working Local `sync-local --apply` — 8 creates.
- Working Local post-import `catalog_master check` — OK.
- Working Local `catalog_master qa --report artifacts/daily-catalog-20260929-local-qa.json` — PASS.
- Local counts: 331 Models / 149 Tools, SQLite integrity OK, FK 0.
- Browser Local touched-card QA: 8/8 direct URLs 200; #326–#331 Models and
  #148/#149 Tools visible in table and right panel; no console/network errors;
  no horizontal overflow. Screenshot evidence captured in the VS Code browser tool.

Release manifests prepared:

- `data/release/daily-catalog-20260929/catalog_plan.json` — 8 creates,
  SHA-256 `94057d16ca6cb18ee6bad303238d52bf74fc7f9805af99e74630fd856764532e`.
- `data/release_state.json` / `data/release/daily-catalog-20260929/release_state.json`
  — public state 331 Models / 149 Tools,
  SHA-256 `1cdc687eec079eb3783de282a3bde1011f866369d2743d9270e308f263dca99a`.

## Owner Authorization

Владелец в этом же поручении явно разрешил публикацию Release #016 после
успешной Local-проверки. Это считается owner authorization для #016 по
`docs/RELEASE.md`; повторное подтверждение не требуется.

## Production

Production опубликован штатным release process. Local SQLite не копировалась.

- Archive: `artifacts/code-release/aipedia-code-7c18e9f078f4.zip`.
- SHA-256: `4abb3c4bb76ee248902d0d459787a0bc6106555d952f89f463a73e1c8e145f6a`.
- Release id / `/healthz`: `7c18e9f078f457d313ef69b8c70de564c050e231`.
- Server preflight PASS; isolated release preflight PASS on backup
  `aipedia-preflight-016-20260929T213249Z.sqlite3`.
- Deploy backup: `aipedia-before-code-20260929T213309Z.sqlite3`.
- `verify-release` PASS: factual catalog tables changed only in the approved
  create scope; 325/147 → 331/149; evaluations stayed 5010 / public 2741;
  sources 999 → 1003; integrity OK, FK 0.
- `catalog_master qa --production --report artifacts/daily-catalog-20260929-production-qa.json` — PASS.
- `gsd_production_qa` — 1657/1657 PASS.
- `gsd_public_check` — 34/34 PASS.
- Public touched-card browser QA: 8/8 direct URLs 200, right panels visible,
  no console/network errors, no horizontal overflow; `/healthz` confirmed
  release `7c18e9f078f457d313ef69b8c70de564c050e231`.

Timeline #016 closed as `done`, Production ✓.