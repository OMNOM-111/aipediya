# Release #015 / v0.13.2 — AIpediya performance

Published on 2026-09-29 from exact code commit
`b8f07026630124f179fd386d60cddbc9beaf2751` (tag
`release-2026-09-28-performance-audit`). Archive:
`aipedia-code-b8f070266301.zip`, SHA-256
`19436aab5928860c412c9f1ddf4afd2174062d1de6f0e286ee65f88b467527eb`.
The release contains SQL-first pagination for chronological Models listings,
optional bounded request aggregates (disabled by default), related tests and
code-only release preflight support. Historical tracked catalog-plan files in
the archive were **not applied**: `catalog_plan=null` in the preflight and
deployment reports. No Local SQLite or secret was packaged or copied.

## Cause and Local gate

The application previously hydrated all 325 published Models and related
offers/evaluations, decorated and sorted every record, then displayed the
first 150. SQL-first pagination now slices the requested chronological page
before relationship prefetch and decoration. The Local matched profile measured
Models root median wall 1,910→1,085 ms, thread CPU 1,719→1,016 ms and traced
Python peak allocation 37.89→19.81 MiB. SQL time was 264→261 ms with 23→26
queries; this was mostly a Python hydration/allocation cost, not a simple SQL
N+1. Full details and raw evidence paths are in
`docs/history/2026-09-28-performance-audit-local.md`.

Final Local gate: 340 Django catalog tests PASS (one expected skip), 88/88
Chromium menu-switch cases PASS (1,712 checks; 264 menu navigations; zero
console, failed-request, HTTP or redirect errors), GSD Local 33/33 PASS,
`catalog_master check` and `qa` PASS. The owner explicitly authorized this
exact checked #015 / v0.13.2 performance release in the 2026-09-29 request.

## Deployment and data integrity

- Server read-only preflight: #014 process RUNNING, `/healthz` 200, database
  present; only the AIpediya application boundary was used.
- Preflight online backup:
  `aipedia-preflight-015-20260929T194225Z.sqlite3`; isolated trial PASS,
  identical catalog SHA-256 before/after
  `369ad4984a740c6201b54433539dbb17ae1aaed05164d4d1aea201659e674419`.
- Publication dry-run: 0 Model changes, 0 Tool changes, 325/147 public; code
  deploy dry-run PASS. Applied migrations: none.
- Deployment backup:
  `aipedia-before-code-20260929T194250Z.sqlite3`; retained after snapshot
  `aipedia-after-code-20260929T194250Z.sqlite3`. Deployment status
  `deployed-origin-verified`; `/healthz` 200 reported the exact commit above.
- `server.py catalog` and `verify-release` PASS: SQLite integrity `ok`, FK 0,
  325 published Models, 147 published Tools, 5,010 evaluations (2,741 public),
  982 benchmarks, 999 sources; no factual table or catalog column changed.

## Live before → after

Three public HTTPS GETs per route in each phase; table reports median TTFB.
All samples returned HTTP 200 without redirects and response body byte counts
were unchanged. Conditions were live and uncontrolled, so these are observed
latencies rather than a matched server CPU experiment.

| Route | #014 before ms | #015 after ms | Change | Body bytes |
| --- | ---: | ---: | ---: | ---: |
| `/` Models | 484.27 | 347.25 | −28.3% | 400,353 |
| `/es/` Models | 472.22 | 325.48 | −31.1% | 404,053 |
| ordinary Model panel | 468.19 | 359.65 | −23.2% | 441,547 |
| heavy Model panel, 163 evaluations | 473.97 | 352.96 | −25.5% | 556,341 |
| filtered Models | 279.96 | 268.13 | −4.2% | 238,228 |
| price-sorted Models | 468.61 | 456.58 | −2.6% | 405,854 |
| `/tools/` | 253.95 | 209.82 | −17.4% | 255,315 |
| Tool panel | 327.30 | 205.14 | −37.3% | 262,356 |
| sitemap index | 376.29 | 356.24 | −5.3% | 2,246 |
| `/healthz` | 158.14 | 142.23 | −10.1% | 122 |

The Tools, price sort and sitemap code paths were unchanged. Their live
differences reflect varying traffic/network conditions and are not credited
to the Models optimization. Raw samples:
`artifacts/performance-015-production-before.json` and `-after.json`
(ignored local evidence).

AIpediya PID accounting, not whole-host load: the last 30-second predeploy
sample on #014 measured 9.0% of one CPU and RSS 192,668 KiB. Postdeploy #015
normal-traffic samples measured 3.6% / 148,844 KiB, then 3.2% / 170,364 KiB
after the browser run. RSS depends on uptime/cache state, so these readings
are not a controlled memory saving. During 697 paced Public QA requests the
PID used 12.33% of one CPU over 30 seconds. During four concurrent Chromium
language-test shards it used 57.77% and 176,060 KiB, with zero 404s and zero
Waitress queue warnings in that measured window. One later queue-depth-1
warning was logged during the full browser campaign, with all requests and
interactions passing. Per-process I/O deltas were unavailable from the host's
standard `/proc` counters. The shared-host load average is not attributed to
AIpediya. The earlier 94.2% PID peak is explained by the reproduced expensive
Models request path under concurrency; old logs cannot assign its requester
to a user or crawler. Optional privacy-preserving aggregates remain available
for a future peak and are disabled by default.

## Public acceptance

- Full GSD Production QA: **1,657/1,657 PASS** across 697 paced requests,
  including all 22 locale roots and Tools listings, SSR panels, pagination,
  sitemap and unpublished records. Report:
  `artifacts/release-015-production-qa.json` (ignored local evidence).
- Public smoke check: **34/34 PASS**.
- `catalog_master qa --production`: **PASS**, with the existing 191 documented
  data-quality queue items and 17 provenance warnings; no catalog edits were
  made in this release.
- Real Chromium browser against `https://aipediya.com`: **88/88 PASS** for 22
  locales × Models/Tools × desktop/375 px, 1,712 checks, 264 language-menu
  navigations, zero console errors, failed network requests, HTTP errors and
  redirects. Open Model and Tool, Back/Forward, search, filters, sort, infinite
  loading, light/dark and Arabic/Persian RTL passed. Report:
  `artifacts/locale-switch-015-production-88.json` (ignored local evidence).

Release #015 is complete on Production. The internal history screen is a
separate Local-only follow-up after this deployment; it does not alter the
published #015 archive.
