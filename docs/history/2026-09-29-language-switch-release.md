# Release #014 / v0.13.1 — Production language switching

The owner accepted the verified Local #014 and explicitly authorized this exact Production release on 2026-09-29. The source baseline was `77e7f53cd8aa621b392d52d5b5ae8851ab77456c`. The #015 performance branch was excluded.

## Candidate and isolation

- Code archive: `artifacts/code-release/aipedia-code-1ac95d75b7a6.zip`, SHA-256 `2d3859774837a7d9f4a256554b153811c3da8105195bb6afda0240da07e7588a`; deployed release id `1ac95d75b7a6d80eb24301f352a88275c28d4bce`.
- Manifest: code candidate, 372 files, five reviewed release-history/test overlays on the exact source baseline. `static/site.js` matches the baseline after Git newline normalization; #015 `catalog/views.py` changes are absent. No SQLite, secret, or old catalog plan is present.
- Isolated extraction: `manage.py check` PASS; full `manage.py test catalog --settings=aipedia.test_settings` 332 OK, one expected skip; `release_history.py --release-id LANGUAGE-SWITCH-2026-09-28 --html` PASS.

## Production execution

- Read-only `tools/server.py preflight` PASS. `release-preflight` PASS on online backup `/srv/aipedia/backups/aipedia-preflight-014-20260929T130337Z.sqlite3`; trial integrity OK, foreign-key violations 0, 325 Models / 147 Tools, publication-state changes 0. `catalog_plan` was null and no `catalog_master apply-plan` ran.
- `tools/server.py deploy --dry-run` PASS. Live deploy used the same archive and created `/srv/aipedia/backups/aipedia-before-code-20260929T130406Z.sqlite3`, after backup `/srv/aipedia/backups/aipedia-after-code-20260929T130406Z.sqlite3`, and previous application `/srv/aipedia/releases/before-code-20260929T130406Z`.
- Live deploy PASS with no migrations and no publication-state changes. `/healthz` reported `environment=production` and release id `1ac95d75b7a6d80eb24301f352a88275c28d4bce`; service `aipedia` RUNNING. Server catalog check: integrity OK, foreign-key violations 0, 325 Models / 147 Tools.
- The pre/post backup comparison PASS: factual catalog tables changed `[]`; Models, Tools, Evaluations, Sources and Benchmarks stayed at 325 / 147 / 5,010 / 999 / 982. The read-only comparison tool and its synthetic-database regression were extended for code-only #014 after its previous #012/#013-only expectation rejected the unchanged result.

## Public browser verification

- On desktop, the rendered English-menu Español link was `/es/`; clicking it from `https://aipediya.com/` loaded `https://aipediya.com/es/`, `<html lang="es" dir="ltr">`, and 150 visible table rows. The open Model `longcat-2-5-preview` switched from `/es/models/...` to `/ru/models/...` with the panel and slug preserved. Browser Back and Forward returned the correct language and open Model each time.
- The Tools tab loaded 147 rows. Opening `alice-ai-pro-business` rewrote the menu link to `/es/tools/alice-ai-pro-business`; clicking Español loaded that exact URL and preserved the Tool panel.
- At 375 px, switching the same open Tool to Arabic and Persian loaded `/ar/tools/alice-ai-pro-business` and `/fa/tools/alice-ai-pro-business`, each with HTTP 200, `dir="rtl"`, 147 rows and the same open panel. Desktop viewport restored to 1280 px. Console errors 0; critical failed network requests and HTTP 4xx/5xx observed during CDP capture 0.
- Earlier accepted Local evidence: 88/88 browser menu cases across 22 locales and two viewports; fresh Local SSR 44/44 roots, 44/44 panels, and 1,936 canonical language links. The owner's ordinary browser check of Local Español was accepted as the visual gate; the loopback browser-tool policy was explicitly waived for this release.

## Public QA and closeout

- `gsd_production_qa.py --commit 1ac95d75...` PASS **1,657/1,657**, 697 requests, 0 failures, including all locale roots, Tools listings, panels, redirects, pagination, robots, sitemap and 472 hidden records. Evidence: `artifacts/code-release/release-014-production-qa.json`.
- `gsd_public_check.py` PASS **34/34**. Evidence: `artifacts/code-release/release-014-public-check.json`.
- `catalog_master qa --production` PASS: 325 Models / 147 Tools, numbered 325 / 147, the Production release id matches. Its 191 explicit data-quality queue entries and 17 provenance warnings are existing nonblocking research items, not #014 mutations. Evidence: `artifacts/code-release/release-014-master-qa.json`.
- Final Local source regression: full `manage.py test catalog --settings=aipedia.test_settings` 333 OK (one expected skip); after the final Timeline text update, targeted history tests 11/11 PASS and `release_history.py --html` PASS.
- All Production gates passed. Timeline #014 is closed against the live health release id after the complete QA; the final Git commit/tag and GitHub origin verification record the documentation closeout separately from the deployed candidate baseline.
