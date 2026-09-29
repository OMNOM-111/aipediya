# Language switching across 22 locales — Local bugfix #014

Release #014 / v0.13.1. The owner reported that selecting Español on Production did not work correctly. This report separates the reproduced fault from menu paths that currently pass. Production remains at #013 until the owner reviews Local and authorizes this exact release.

## Public browser diagnosis before the fix

Chromium navigated by clicking rendered language controls, with JavaScript enabled. The standard expanded menu was opened and the Español item clicked from the English Models root, Tools root, and open Model/Tool panels. The resulting paths were `/es/`, `/es/tools/`, `/es/models/<same slug>` and `/es/tools/<same slug>` respectively. All returned HTTP 200, with no redirects, visible rows/panels, functioning JavaScript, zero console errors and zero critical failed requests. A separate click sweep passed Models and Tools roots for all 22 locales (44/44). The precise owner-observed menu failure has therefore not been reproduced in these states; the original browser URL and symptom are still useful to narrow it further.

For the direct Español menu click from `https://aipediya.com/`: the rendered `href` was `/es/`, the final URL was `https://aipediya.com/es/`, HTTP 200 with an empty redirect chain. The loaded document had `<html lang="es" dir="ltr">`, 150 table rows and working card/theme JavaScript; console errors and failed network requests were both zero. From `https://aipediya.com/tools/`, the rendered `href` was `/es/tools/`, the final URL matched, HTTP 200, 147 rows and a working Tool panel. A few Cloudflare RUM requests were aborted by rapid test navigation in the multi-page pass; these were not critical application requests.

The normal expanded-menu click was also repeated at 375 px from `https://aipediya.com/models/longcat-2-5-preview`: `href=/es/models/longcat-2-5-preview`, final URL identical, HTTP 200, `<html lang="es" dir="ltr">`, 150 rows, panel open, zero console errors and critical failed requests.

A related user-visible fault **was** reproduced on Production when `aipedia_lang=es` was already saved. From `https://aipediya.com/`, opening `longcat-2-5-preview` changed the address through History API:

| Field | Observed value |
| --- | --- |
| URL before language click | `https://aipediya.com/models/longcat-2-5-preview` |
| Español in expanded menu | `/es/models/longcat-2-5-preview` |
| Prominent saved-language link beside menu | `/es/` |
| URL after clicking saved-language link | `https://aipediya.com/es/` |
| HTTP / redirect chain | `200` / none |
| Console errors / critical failed requests | `0` / `0` |
| Loaded HTML / table | `<html lang="es">`, 150 rows, panel closed |
| JavaScript | loaded and operational; wrong destination lost the open card |

The stale link was created once by `offerSavedLanguage()` and lay outside the `a[data-set-lang]` set updated by `syncLanguageLinks()` after `history.pushState`/`replaceState` and Back/Forward. The repair makes that same synchronization update the saved-language link from its corresponding menu target. It applies to every supported locale, with no Spanish branch or URL/translation contract change.

The new permanent browser test was run read-only against the unchanged Production #013 at 375 px with `es`: both baseline cases failed at exactly this check. Models: saved link `/es/` versus menu `/es/models/longcat-2-5-preview`; Tools: saved link `/es/tools/` versus menu `/es/tools/alice-ai-pro-business`. Evidence: `artifacts/locale-switch-production-es-baseline.json` (Local artifact). The same check passes against the repaired Local build.

## Local verification

- Permanent Django regression: all 22 explicit codes, Models and Tools roots, rendered `lang`/`dir` and rows, 22 generated menu links per page, final 200 for representative links, Model/Tool card preservation, UX query retention and dropping `lang`, `kind`, `partial`.
- Permanent Playwright regression: actual menu clicks and saved-language link synchronization, 22 locales, Models/Tools, desktop 1440 px and mobile 375 px, open/close/history/search/filter/sort/theme/RTL and model infinite loading. Report: `artifacts/locale-switch-*.json` (Local, ignored by Git).
- `manage.py test catalog`: 330 OK, one Windows skip. `gsd_public_check --local`: 33/33 PASS. JavaScript syntax and `git diff --check`: PASS.
- The repaired saved-language link was clicked in Local Chromium at 375 px from `/models/longcat-2-5-preview`: both menu and saved link had `/es/models/longcat-2-5-preview`; final HTTP 200, Spanish document, panel open, zero console errors and failed requests.
- Read-only Production baseline `gsd_production_qa` for the unchanged #013: 1657/1657 PASS (`artifacts/locale-switch-production-baseline-gsd.json`). This checks the published baseline, not the new Local code.
- Full Local browser matrix: **88/88 PASS** (22 locales × Models/Tools × 1440/375 px). The combined report `artifacts/locale-switch-local-22.json` records 1,712 interaction checks, 264 actual menu navigations, 0 redirects, 0 non-200 menu responses, 0 console errors, 0 failed requests and 0 HTTP errors. Every locale passed root rendering, Model/Tool panels, X/Escape/outside closing, Back/Forward, search, active filter, sort, light/dark and switching to English and back. Models loaded further rows; Tools had all 147 rows in the initial page. `ar` and `fa` passed RTL direction and page-overflow checks on both viewports. Local visual acceptance by owner: pending. Production release: not authorized.
- Visual screenshots inspected in Local: Spanish Models at 1440 px, Spanish Tool panel at 375 px, Arabic Model panel at 375 px and Persian Tool panel at 1440 px (`artifacts/locale-switch-visual/`). The table, panel and controls are visible without page overflow. This is executor QA; owner visual acceptance remains pending.
- The running Local Waitress process was restarted through the project Local stop/start scripts after Python history changes. `prepare_local_catalog.py` kept the existing SQLite, no migrations applied, and `/ru/history/` showed #014 in review with its source report returning 200. Post-restart Español Models and Tools browser cases at 375 px: 2/2 PASS, zero console errors and failed requests (`artifacts/locale-switch-post-restart-es.json`).

## Handoff

Inspect Local Español and other locales from the ordinary language menu and the saved-language link after opening a card. If the original menu symptom persists in a particular browser or page, provide the initial URL, final URL, and visible error; this will be checked against the saved browser report. After owner visual acceptance, Production requires a separate instruction for Release #014 under `docs/RELEASE.md`.
