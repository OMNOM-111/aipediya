# AIpediya Production load audit — isolated Local candidate #015

Release #015 / v0.13.2 is reserved for the performance change on branch
`codex/aipedia-performance-015`. It is **not** part of the approved language
release #014. No Production files, database or service were changed during this
audit. Server reads used only `python tools/server.py preflight` and the new
read-only `python tools/server.py metrics` command through `aipediya-prod`.

## Measured Production baseline (#013)

- Server preflight: `aipedia` RUNNING, `/healthz` 200, release
  `5ba1e566338fc17d9b8965d3be180bc1df268e2e`; only `/srv/aipedia`
  paths were inspected.
- Five separate process samples showed 12.8–94.2% of one CPU. In the 30-second
  high-load sample, four Waitress worker threads each used 22.8–24.5% of one
  CPU; the main thread was nearly idle. RSS ranged about 202–240 MiB, thread
  count 5, file descriptors 9–19, and uptime exceeded 5.5 hours. The SQLite
  file was 352,047,104 bytes. Whole-host load average is shared with other
  projects and is **not** attributed to AIpediya.
- In the same 30-second high-load sample, `app-error.log` appended zero 404
  lines and 11 Waitress queue-depth warnings. Its last 1 MiB historically
  contained 15,358 404 lines, 13,213 under `/models/`, and 1,117 queue
  warnings. The file has no request timestamps or user agents, so that
  historical count cannot be converted to a rate or assigned to bots. The
  current CPU spike was **not** explained by new 404s in the measured interval.
- Standard `/proc` access on the host did not expose reliable per-process I/O
  or socket-byte counters, even with the service UID. The app has no access
  log; endpoint frequency, user-agent mix, Cloudflare cache/bot split and
  per-endpoint Production CPU therefore remain unmeasured. No tunnel files or
  configuration were inspected. IndexNow dispatch is a separate Supervisor
  program, not a loop inside the four Waitress request workers.

One sequential public HTTP sample before any deployment (seconds):

| Route | Status | TTFB | Total | Body bytes |
| --- | ---: | ---: | ---: | ---: |
| `/` | 200 | 2.67 | 3.06 | 400,353 |
| `/es/` | 200 | 2.72 | 2.81 | 404,053 |
| `/tools/` | 200 | 1.63 | 1.69 | 255,315 |
| ordinary Model | 200 | 2.57 | 2.64 | 441,547 |
| heavy Model, 163 evaluations | 200 | 3.04 | 3.15 | 556,341 |
| Tool card | 200 | 1.50 | 1.55 | 262,356 |
| filtered Models | 200 | 2.37 | 2.43 | 238,228 |
| price-sorted Models | 200 | 3.05 | 3.11 | 405,854 |
| `/sitemap.xml` | 200 | 3.69 | 3.69 | 2,246 |

This is a single live sample, not a latency distribution. The raw measurements
are in ignored `artifacts/production-http-before.json` and
`artifacts/server-access/metrics-*.json`.

## Reproduced Local cost and isolated change

The default Models listing materialized all 325 published model objects with
their offers and thousands of evaluation rows, decorated and sorted all 325,
then rendered the first 150. `cProfile` attributed about 1.54 seconds to
related-object prefetching and 0.35 seconds to 325 `decorate()` calls in one
profiled request. SQL was 23 queries / 0.26 seconds median, so this was
primarily Python hydration and allocation, not a classic query-count N+1.

The candidate uses SQL sorting by actual release date and catalog number to
slice the requested page before prefetch/decorating. It falls back to the
existing in-memory path if undated entries are present, preserving the legacy
date-first and undated-last behavior. Regression tests cover backfilled dates,
approximate dates, ties, page boundaries, and decoration count.

Read-only Local test-client medians (3 measured requests per route; milliseconds):

| Route | Wall before → after | CPU before → after | SQL before → after | Queries before → after | Body bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/` | 1,634 → 861 | 1,516 → 813 | 259 → 242 | 23 → 26 | 398,335 both |
| `/es/` | 1,596 → 744 | 1,500 → 734 | 244 → 204 | 23 → 26 | 402,046 both |
| ordinary Model | 2,250 → 705 | 1,703 → 703 | 378 → 209 | 25 → 28 | 439,516 both |
| heavy Model | 2,092 → 990 | 1,969 → 953 | 304 → 226 | 38 → 41 | 554,310 both |
| `/tools/` | 318 → 294 | 313 → 281 | 37 → 34 | 19 → 19 | 253,592 both |
| filtered Models | 739 → 511 | 656 → 500 | 197 → 177 | 23 → 26 | 237,523 both |
| price-sorted Models | 2,387 → 1,240 | 1,750 → 1,234 | 345 → 188 | 23 → 23 | 403,953 both |
| sitemap index | 1,106 → 937 | 1,016 → 906 | 168 → 124 | 20 → 20 | 2,246 both |

Only the chronological Models route changed. Differences for Tools, price
sorting and sitemap are test-run variability and must not be credited to this
optimization. SQL query count rises by three on the fast path (count, undated
check, numbered count) while total wall and CPU time fall. Baseline and final
JSON are preserved as `artifacts/catalog-performance-local-before.json` and
`artifacts/catalog-performance-local-final.json`.

## QA and remaining gate

- Full `manage.py test catalog`: 331 OK, one Windows skip. An initial run
  exposed two chronology regressions; the date-first SQL path and undated
  fallback fixed both, then the entire suite passed.
- `manage.py check`, `catalog_master check`, `catalog_master qa`: PASS; the
  existing master data-quality queue and pending drift were not changed.
- Live Local after the canonical stop/start: `/healthz`, Models EN/ES/RU and Tools
  EN/ES all 200; 22 locales × Models/Tools live HTTP 44/44 with correct
  `lang`, `dir`, and visible rows; `gsd_public_check --local` 33/33.
- The owner confirmed the ordinary browser can open ES/RU, select Español
  from RU/EN, and keep an open Model panel across language switching.
- The automated browser control refused loopback access by security policy.
  The full 88-case browser gate **after** this Python change was not run.
  Candidate #015 remains in progress. No archive, tag or Production deploy.

Next: run the 88-case browser gate in an allowed environment, collect
Production endpoint/user-agent traffic data through an approved AIpediya-only
access-log or Cloudflare analytics route, and compare Production CPU/RSS/TTFB
before and after a separately authorized #015 release. Sitemap graph rebuilds
on each request and computed price sorting still process all Models; optimize
these only after request-frequency evidence shows they matter.
