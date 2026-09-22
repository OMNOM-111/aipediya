# Карта проекта AIpedia

Краткое устройство. Стек и установка — `README.md`. Правила — `AGENTS.md`.

## Стек

Django 5.2 LTS, SQLite, серверный HTML, WhiteNoise, Waitress.
Без Node.js в runtime, без отдельного API-сервера, Redis и очереди.

## Запуск Local

- Ярлык «AIpedia — Local», `start.ps1` или `tools/local/start-local.ps1`
- Обычно http://127.0.0.1:18810 (диапазон 18810–18819)
- Остановка только Local: «AIpedia — Stop Local» / `tools/local/stop-local.ps1`
- База: `data/local/aipedia.sqlite3` (не коммитить)

## Страницы

| Что | Где |
| --- | --- |
| Шапка, язык, тема, Local/Production | `templates/includes/site_header.html`, `catalog/context.py` |
| Каталог моделей | `templates/catalog.html`, `templates/model_rows.html` |
| Каталог инструментов | `templates/tool_table.html`, `templates/tool_rows.html` |
| Правая панель модели / инструмента | `templates/panel.html`, `templates/tool_panel.html`; `templates/detail.html` подключает каталог с открытой панелью |
| Стили и поведение панели | `static/site.css`, `static/table-layout.css`, `static/site.js` |
| Маршруты | `aipedia/urls.py`, `catalog/views.py` |
| Фильтры и сортировка | `catalog/comparison.py`, `catalog/views.py` |
| Независимые хронологические номера моделей и инструментов | `catalog/chronology.py`, команда `apply_release_chronology` |
| Импорт исследований | `catalog/management/commands/import_research.py` |
| Сообщения пользователей | `contributions/` |
| Выпуск | `docs/RELEASE.md`, `tools/build_code_release.py`, `tools/deploy_code_release.py` |

## Данные

Модели, инструменты, страны происхождения и платформы: `catalog/models.py`.
`ModelVersion` хранит модели и сохранённые legacy-записи; публичный каталог
инструментов читает отдельную сущность `Tool`, связанную с legacy-записью без
потери истории. Схема — миграции `catalog/migrations/` (актуальная 0013).
Модели и инструменты имеют независимые фильтры, сортировки, панели и
хронологические номера; смешанного публичного режима «Все» нет.
Production SQLite на сервере: `/srv/aipedia/data/aipedia.sqlite3`.
В пакет контекста базы не класть; достаточно этой карты, счётчиков в статусе и безопасных примеров в документах.
