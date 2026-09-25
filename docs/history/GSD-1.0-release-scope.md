# GSD-1.0 «Глобальная поисковая доступность» — подготовленный scope выпуска

Статус: **подготовлено, НЕ выпущено.** Production = `ed103a3ff163`
(release-2026-09-25-local-approved). Выпуск — только после отдельной команды
владельца вида «опубликовать commit/tag … по `docs/RELEASE.md`».

## Что входит

Проверенное Local-состояние GSD-1.0 (см. `docs/SEARCH_DISCOVERY.md`,
`docs/timeline.json`): языковые пути и 301-карта, readiness-реестр, SSR-карточки,
локализованные сигналы, sitemap index + 22 дочерних sitemap, политика фасетов и
пагинации, методика, 10 подборок, выгрузки данных (выключены флагом), журнал
IndexNow и dispatcher (выключен), отчёты/проверки.

Не входит (отдельные решения/задачи): незакоммиченная работа другого исполнителя
по catalog master (`catalog_master*`, `reconcile_catalog`, `restore_core_catalog`,
XLSX, `data/research/`, `requirements-dev.txt`, соответствующие разделы
`AGENTS.md`/`DECISIONS.md`/`AI_CONTEXT/README.md`) — владелец решает, включать ли
её в тот же commit. Для GSD-1.0 она не нужна. Публикационное состояние каталога
не меняется (304/138, номера прежние) — манифест `data/release_state.json`
остаётся тем же.

## Зависимости

1. Commit только файлов GSD-1.0 (архив `build_code_release.py` берёт лишь
   tracked-файлы; новые файлы без commit в архив не попадут).
2. Миграция `catalog/0018_discovery_outbox` (новая таблица, данные не меняет).
3. `collectstatic` (новые `share-card.png`, `brand-512.png`, изменённые
   `site.js`, `site.css`) — выполняется `deploy_code_release.py`.
4. Переменные окружения Production (по умолчанию безопасны):
   `AIPEDIA_DATASETS_PUBLIC=0` (по умолчанию для production),
   `AIPEDIA_INDEXNOW_ENABLED` не задана (=выключено).
5. `tools/public_acceptance.mjs` и `browser_check.py` проверяют старый
   `?lang=`-контракт — для этого выпуска вместо них:
   `python tools/gsd_public_check.py https://aipediya.com` (ожидается 32/32
   после выпуска; до выпуска 8/32).

## Выпуск (по `docs/RELEASE.md`, без изменений процесса)

1. Полный `manage.py test catalog --settings=aipedia.test_settings` PASS (210).
2. Commit + tag `release-YYYY-MM-DD-gsd-1-0`; `build_code_release.py`.
3. `deploy_code_release.py <archive> --sha256 … --dry-run`, затем без `--dry-run`
   (с `--publication-state data/release_state.json`, если владелец требует
   повторного применения манифеста; изменений видимости нет).
4. Post-deploy: `/healthz` = новый commit; `gsd_public_check.py` 32/32;
   `/sitemap.xml` — index 22 дочерних; ограниченная ручная проверка
   RU/EN/AR карточек.

## Откат

Код — как в `docs/RELEASE.md` (вернуть `/srv/aipedia/releases/before-code-*`).
Миграция 0018 только добавляет таблицу; старый код её не читает, откат БД не
нужен. После отката старые `?lang=` URL снова отвечают 200, новые `/ru/…` — 404
(поисковики получат 404 на новых адресах до повторного выпуска; поэтому
IndexNow `--all` запускать только после подтверждения, что выпуск остаётся).

## Активация после выпуска (действия владельца)

См. `docs/SEARCH_DISCOVERY.md` §10: консоли Google/Bing/Yandex (+ по желанию
Naver/Baidu), sitemap, ключ IndexNow и одноразовый `notify_indexnow --all` +
`indexnow_dispatch --send`, решение о лицензии данных, проверка переводов.

## Числа (Local, 2026-09-25)

- Публичные записи: 304 модели, 138 инструментов (скрытые 459 — `not-public`).
- Потенциальные entity×locale URL: 442 × 22 = 9 724; indexable: 9 724
  (6 688 моделей + 3 036 инструментов); not-ready: 0 (все основные тексты
  текущие). Строк переводов ContentTranslation: 42 260 — это не число URL.
- Sitemap (после reconciliation): index + 22 дочерних; 10 035 `<loc>`:
  карточки 9 724 (модели 6 688 + инструменты 3 036), готовые подборки 198
  (9 × 22), индекс подборок 22, каталог моделей 22, каталог инструментов 22,
  методика 22, конфиденциальность 22, страницы данных 3 (только en);
  230 742 alternate-ссылки; крупнейший файл ≈ 1,15 МБ / 459 URL.
  На Production (датасеты выключены) ожидается 10 032 `<loc>`.
  На Production датасеты выключены → их 3 страницы (только `en`) не попадут в sitemap.
- Тесты: 216 PASS. Аудит HTML: 10 013 страниц (полный) + 575 после reconciliation, 0 проблем.
