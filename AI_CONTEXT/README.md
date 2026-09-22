# Пакет контекста для нового чата

Не редактировать `AI_CONTEXT.md` и `AI_CONTEXT.zip` вручную — это сборка.

1. Исполнитель обновляет `docs/EXECUTION_STATE.md` (и при необходимости `docs/DECISIONS.md`).
2. Из корня проекта: `.\.venv\Scripts\python.exe tools/pack_ai_context.py`
3. В новый чат прикрепить свежий `AI_CONTEXT.md`. Для разбора ошибки или вёрстки — ещё `AI_CONTEXT.zip`.

Правила работы: корневой `AGENTS.md`. Живой статус: `docs/EXECUTION_STATE.md`.
Секреты, `.env` и SQLite в пакет не входят. Сборка не публикует сайт.
