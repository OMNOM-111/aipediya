# AIpedia

Самостоятельная энциклопедия моделей ИИ. Существующий публичный сайт https://aipediya.com.
Django 5.2 LTS, SQLite, серверные HTML-страницы,
WhiteNoise, Waitress. Без Node.js во время работы, отдельного API-сервера,
Redis и фоновой очереди.

## Открыть

Локальный адрес: http://127.0.0.1:18810

```powershell
cd C:\Users\dimon\Documents\AIpedia
.\start.ps1
```

Если порт занят, `./start.ps1 -Port 18811`. Скрипт не завершает чужие процессы.

## Установка с нуля

Python 3.12+. Команды выполняются из корня проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_catalog
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\start.ps1
```

На Linux вместо `.venv\Scripts\python.exe` используется `.venv/bin/python`.
`requirements.lock` фиксирует установленные версии, `requirements.txt` задаёт
допустимые диапазоны для осознанного обновления с повторной проверкой.

## Редактирование

Создайте личного редактора, затем откройте `/admin/`:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Пароля по умолчанию и обхода входа нет. В редакторе доступны версии моделей,
источники, разработчики, сервисы, тарифы, проверки и дополнительные факты.
Поля текста двуязычные: `{"ru": "Текст", "en": "Text"}`.
У каждой версии есть встроенные таблицы доступа, цен, проверок и фактов.
Значимые сведения требуют источника и даты. Неизвестные значения оставляйте
пустыми, а не нулевыми. `primary` выделяет один согласованный набор тарифов
для каталога; подписка принадлежит сервису, цена API — поставщику.

Снимки изменений создаются при сохранении модели, тарифа, доступа, факта
или результата проверки. Редактор не может менять журнал. Для сохранения
истории не используйте SQL UPDATE, QuerySet.update или bulk_update.
Общие справочники имеют обычный журнал Django Admin. Модель лучше снять
с публикации (`published=False`), а не удалять вместе с её историей.

Повторный `seed_catalog` пропускает существующие модели и сохраняет правки.
Сообщения пользователей доступны в разделе Error reports.

## Начальная выборка

7 реальных моделей: Gemini 2.5 Flash, Pro, Flash-Lite, Qwen3-8B,
FLUX.1 [schnell], Voxtral Mini 3B 2507, Veo 3.1 Preview.
Источники проверены 18 сентября 2026 года; ссылки сохранены в базе.
Это не полный или автоматически обновляемый реестр.

- Цены Standard API Google: https://ai.google.dev/gemini-api/docs/pricing
- Цена FLUX у fal: https://fal.ai/models/fal-ai/flux/schnell
- GPQA/AIME: https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf
- Карточки открытых моделей: ссылки на официальные репозитории Hugging Face в паспортах.

Цены API, подписки, единицы для изображений и видео не складываются.
Тариф fal задан за мегапиксель с округлением вверх. Для Pro внесены оба
порога длины входа; Flash имеет отдельную цену аудиовхода. Batch, Priority,
кеширование, инструменты и все сторонние провайдеры пока не каталогизированы.
Подписки, страны организаций, точные даты выпуска, энергия и многие оценки
пока не подтверждены и явно обозначены как неизвестные.
GPQA взят из отчёта Google. AIME в отчёте атрибутирован MathArena; это
вторичная публикация независимой оценки, не собственный тест AIpedia.
Результаты относятся к версии отчёта 2025 года; актуальный API не тестировался.

## Проверка

### Текущая контрольная точка

Актуальные шаги и публичный статус: `docs/EXECUTION_STATE.md`; правила сравнения:
`docs/COMPARISON_RULES.md`. Исторические числа ниже не заменяют текущую приёмку.
Рабочая SQLite находится на сервере; локальная `data/aipedia.sqlite3` устарела
и никогда не должна заменять рабочую БД. Приёмка использует online-копию.

```powershell
.\.venv\Scripts\python.exe manage.py test catalog
.\.venv\Scripts\python.exe manage.py check
python tools/browser_check.py
```

Последняя команда требует Playwright и Chromium в используемом Python,
а также работающего сервера на 18810. Изображения сохраняются в `artifacts/`.
Приёмка владельцем описана в `docs/ACCEPTANCE.md`.

## Развёртывание

Существующая topology проверена: `/srv/aipedia/app`, БД `/srv/aipedia/data/aipedia.sqlite3`,
выделенный Supervisor. Для обновления — `tools/build_release.py` и
`tools/deploy_release.py`, свежая серверная копия и публичная приёмка.
Туннель, секреты и StratForge не менять. `deploy/README.md` содержит исторические
шаблоны начальной установки; не повторять уже выполненную инфраструктуру.

## Лицензии

Лицензия нового проекта пока не назначена владельцем. Lucide 0.468.0
в `static/lucide.min.js` распространяется по ISC, см. `static/LUCIDE-LICENSE`.
SVG-значок AIpedia создан для проекта; внешние логотипы не используются.
