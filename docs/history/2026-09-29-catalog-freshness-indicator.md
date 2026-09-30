# Catalog Freshness Indicator — Local Review

Дата: 2026-09-29. Исполнитель: GitHub Copilot. Timeline: `CATALOG-FRESHNESS-INDICATOR-2026-09-29`, Release #018 / `v0.16.0`.

## Что изменено

- В toolbar каталога рядом со счетчиками Models / Tools и результатами добавлен индикатор последнего фактического catalog update: точное UTC-время, relative time и состояние свежести.
- Источник истины — `data/catalog_freshness.json`, seed из фактического #016 `data/release/daily-catalog-20260929/catalog_plan.json`.
- Future `catalog_plan` получает compact `catalog_update`; persisted snapshot пишется только при реальном `catalog_master apply-plan --apply`. Code-only release без `catalog_plan` эти данные не меняет.
- Desktop: hover/focus открывают popover. Mobile: tap/click. Пока popover открыт, уже загруженные строки последнего update слегка подсвечиваются; новые получают `NEW`, обновлённые — `UPD`.
- Каталог, master XLSX, Local SQLite и Production данные не менялись.

## Последний update

- Timestamp: `2026-09-29T21:39:59Z`.
- Added Models: 6 — Claude Sonnet 5.5; Eleven v4; Eleven v4 Turbo; Holo4-27B; Holo4-35B-A3B; Holotron4-30B-A3B.
- Added Tools: 2 — Cue; Manus.
- Updated Models: 0.
- Updated Tools: 0.

## Local QA

- `catalog.tests.test_catalog_freshness` + `CatalogTests.test_catalog_freshness_indicator` — 3 PASS.
- `manage.py check --settings=aipedia.test_settings` — PASS.
- `node --check static/site.js` — PASS.
- Local перезапущен штатно на `127.0.0.1:18810`; существующая SQLite сохранена, 331 Models / 149 Tools.
- Browser Local: RU desktop 1440 hover/focus PASS; RU 375 px tap/Escape/Enter PASS; EN smoke PASS; `/ru/tools/` visible-row `NEW` badges PASS; horizontal overflow false, console/page errors 0.

## Visual polish after owner feedback

- Long pill text was replaced with a small date/time block showing the visitor browser's local date and time. The clock updates once per second locally through standard browser APIs; no network, IP, geolocation or timezone API is used.
- User-facing exact catalog update time is localized in the browser from canonical UTC. The UI no longer shows `UTC` or `Свежие данные` in the compact block.
- Popover was simplified: no large stat cards; title `Последнее обновление`; compact sections `Модели · 6` / `Инструменты · 2`; each row shows `NEW` / `UPD`, name and the record's own release date from catalog data.
- Table badges remain visible but are smaller and lighter. Row highlight appears only while the freshness popover is open / target is hovered or focused, and disappears after close.
- Targeted QA for this visual slice: `node --check static/site.js` PASS; `manage.py check --settings=aipedia.test_settings` PASS; `CatalogTests.test_catalog_freshness_indicator` PASS; browser RU desktop, RU 375 px, EN smoke, ticking clock, hover/tap/focus, popover, release dates, NEW/UPD, row highlight close, overflow and JS errors PASS.

## Final Local handoff polish

- The compact date/time block is right-aligned directly above the result count. Date is muted, time is slightly stronger, and the relative update line is smaller; tabular numerals keep the clock width stable.
- Current date/time is always computed in the visitor browser local timezone via standard `Intl.DateTimeFormat`; no IP, geolocation or timezone API is used. The canonical catalog update timestamp remains UTC and is only converted for display.
- Table `NEW` / `UPD` badges are smaller and lighter and are shown only for the first 24 hours after the catalog update timestamp. A client-side visibility check hides them automatically after 24 hours without a new catalog release. The record release date shown in the popover remains separate and does not control badge lifetime.
- Final targeted QA: RU desktop, RU 375 px, EN smoke, ticking clock, browser timezone formatting, simulated +25h `NEW/UPD` hide, hover/tap/focus, popover, release dates, row highlight open/close, overflow and JS errors PASS. No broad audits or full catalog suite were run in this final visual step.

## Owner final remarks before Production

- The duplicate visible `331 результатов` text was removed from the UI; the counter remains present as `sr-only` so the existing mandatory catalog QA parser can still verify counts.
- `NEW` / `UPD` now means the model or tool itself is still newly released. Date-only records show badges only on the release calendar date in the visitor's browser-local timezone; exact datetimes use the first 24 hours; approximate dates never invent an exact window.
- The eight latest records' marks were checked only in scope: Anthropic and ElevenLabs resolve to existing SVG marks; H Company and Manus keep fallback initials because there is no existing official mark asset in `static/marks` and Simple Icons raw slugs `hcompany` / `manus` return 404. No invented or generated logos were added.
- Targeted QA after these final remarks: `node --check static/site.js` PASS; `manage.py check --settings=aipedia.test_settings` PASS; targeted freshness tests PASS; browser RU desktop, RU 375 px, EN smoke, ticking local clock, hidden duplicate result text, popover open/close, release dates, NEW expiry boundary, row highlight, overflow and JS errors PASS.
- Release tooling note: local `tools/server.py` now runs the current allowlisted `deploy_code_release.py` / `release_history.py` from a temporary remote directory during deploy, so #018 can be validated from Production #016 even though #017 was a Local-only reserved Release #. Targeted server wrapper test PASS.

## Next allowed paths

- **OWNER ACCEPTS:** the next agent does not change code; after a separate owner command, it publishes exactly the committed Release #018 / `v0.16.0` candidate by `docs/RELEASE.md`, runs only mandatory release gates and a short public smoke, then closes #018.
- **OWNER REQUESTS CHANGES:** the next agent continues the same #018, creates no new Timeline card and does not publish the current candidate; it makes only the requested Local changes, runs targeted QA, creates a new commit/handoff and waits for approval again.

## Состояние

Local — review, ждёт визуальной приёмки владельца. Production не трогалась и остаётся Release #016 / `v0.14.0`.