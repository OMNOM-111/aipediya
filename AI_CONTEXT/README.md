# Пакет контекста для нового чата

Не редактировать `AI_CONTEXT.md` и `AI_CONTEXT.zip` вручную — это сборка.

1. Исполнитель обновляет `docs/EXECUTION_STATE.md` (и при необходимости `docs/DECISIONS.md`).
2. Из корня проекта: `.\.venv\Scripts\python.exe tools/pack_ai_context.py`
3. В новый чат прикрепить свежий `AI_CONTEXT.md`. Для разбора ошибки или вёрстки — ещё `AI_CONTEXT.zip`.

Правила работы: корневой `AGENTS.md`. Живой статус: `docs/EXECUTION_STATE.md`.
Секреты, `.env` и SQLite в пакет не входят. Сборка не публикует сайт.

Ярлык `AIpedia — История сайта.lnk` в этой папке запускает Local и открывает
`/ru/history/`. Если ярлык отсутствует, восстановить его командой
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/local/install-history-shortcut.ps1`
из корня проекта. Порядок ведения истории — `docs/PRODUCT_HISTORY.md`, единый
реестр — `docs/timeline.json`. Перед новой задачей читать открытый пакет и
замечания; после значимого этапа обновлять их вместе с фактическим статусом.

`AIpediya_Model_Verification_Master.xlsx` — **не сборка**, а единая
каноническая база каталога (все Models и Tools, раздел «Каноническая база
каталога (master)» в `AGENTS.md`). Её редактируют люди и агенты; импорт из
Local — `manage.py catalog_master import`, пересчёт — `catalog_master refresh`,
проверка — `manage.py catalog_master check`, план синхронизации в Local —
`catalog_master sync-local`. Инструкция владельцу — `docs/CATALOG_MASTER.md`.
Прежние версии книги (v001–v012) — неактивные копии в `backups/`.
