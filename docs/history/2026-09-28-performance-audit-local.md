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

## Continuation after the separate #014 release — 2026-09-29

The #015 branch was merged with the verified #014 `main` in its own worktree
(`bf79281`); #014 Production and its Git tag were not changed. Full merged
`manage.py test catalog --settings=aipedia.test_settings` passed 334 tests
with one expected skip. Timeline now has #014 released and #015 in progress.

Two fresh 30-second, AIpediya-process-only Production samples on the published
#014 release measured **4.03% and 3.07% of one CPU**, RSS **190,920 and
191,492 KiB**, five threads, zero Waitress queue warnings and one then zero
new 404s. The shared host load averages were about 2.9 and 3.0–3.3 during
those intervals. Therefore that whole-host load was mostly outside the
AIpediya process in these intervals; the measurements do not identify or
inspect another application. Earlier #013 samples with 12.8–94.2% of one
CPU remain evidence that AIpediya itself can spike. Standard `/proc` access
still did not expose per-process I/O or network-byte deltas. Saved read-only
metrics: `artifacts/server-access/metrics-20260929T133146Z.json` and
`metrics-20260929T133347Z.json`.

Six sequential public requests during the second period all returned 200.
Observed TTFB / total time in seconds: `/` 0.527 / 0.605, `/es/` 0.566 /
0.662, `/tools/` 0.256 / 0.308, ordinary Model 0.427 / 0.521,
price-sorted Models 0.633 / 0.725, sitemap 0.313 / 0.313. Response headers
reported `cf-cache-status: DYNAMIC` for the root. These are a calm #014
sample, **not** a Production after-measurement of the unshipped #015 change.
The much slower #013 sample above was under different traffic conditions,
so it cannot establish a release-level speedup.

The merged #015 Local candidate was profiled read-only against the existing
Local SQLite. Median Models root: **910 ms wall / 906 ms CPU / 234 ms SQL /
26 queries**, versus the earlier unchanged-code baseline 1,634 / 1,516 /
259 ms / 23 queries. Spanish Models: 977 ms wall versus 1,596 ms baseline;
heavy Model (163 evaluations): 1,177 ms wall versus 2,092 ms baseline.
Tools, price sorting and sitemap use unchanged code paths and their timing
variation is not credited to this optimization. Evidence:
`artifacts/performance-015-after-merge.json`.

Cloudflare Dashboard was checked read-only but requires account sign-in.
The AIpediya app has no access log or route/UA aggregation. The historical
404 count is dominated by `/models/`, but the measured current intervals
had zero or one new 404 and no queue warnings. **Crawler share, actual route
frequency and peak-hour TTFB distribution remain unmeasured.** No bot cause
is claimed. A safe traffic export or separately reviewed AIpediya-only
observability mechanism is needed before attributing the earlier CPU spike
to external traffic or declaring the overall host-load root cause complete.

## Local-only observability and controlled burst — 2026-09-29

The app has no Production access log. A disabled-by-default, opt-in request
aggregator is now implemented in the isolated #015 candidate. Every completed
request contributes to a roughly 10-second, per-PID window with UTC start/end,
process CPU and RSS, process I/O when `/proc/self/io` permits it, fixed route
and action classes, status, declared User-Agent class/family, counts, wall and
thread CPU time, SQL count/time, response bytes and coarse latency bins.
Windows Local cannot supply the Linux `/proc` RSS/I/O fields; these are `null`
there. Idle periods extend a window until the next completed request; its
actual `window_ms` is always written, so rates must divide by that duration.
The output rotates at 5 MiB with two backups. Route slugs, raw paths, query
values, cookies, IP addresses, headers and raw User-Agent strings are not
stored. Declared UA family can be spoofed; it is evidence about the header,
not verified crawler identity. Settings keep this instrumentation **off in
Production by default**. No server configuration or files were changed.

The instrumented #015 Waitress ran separately on Local port 18811; the
approved Local on 18810 remained untouched. GETs to Models, Tools, ordinary
and 163-evaluation Model panels, Tool panel, filter, price sort, search,
sitemap and health returned 200. A sentinel in the query, cookie and raw UA
was absent from the JSONL. `gsd_public_check` against 18811: **33/33 PASS**.
The final full Django catalog suite after observability: **340 tests, 1 skip**;
the bounded-group regression test also passed in the targeted 6/6 suite.
`manage.py check` and `git diff --check`: PASS.

Direct wrapper microbenchmark on Local (5 alternating rounds, 5,000 calls per
round with no SQL and 2,000 with `SELECT 1`):

| Request | Bare wall → instrumented wall | Added wall / CPU |
| --- | ---: | ---: |
| Trivial, no SQL | 10.31 → 46.41 µs | 36.10 / 37.50 µs |
| Trivial, one SQL | 45.94 → 96.33 µs | 50.39 / 39.06 µs |

The wrapper overhead is small compared with the measured 0.2–1.3 s Local
catalog requests. The microbenchmark is not a Production throughput test.
Raw ignored evidence: `artifacts/observability-overhead.json` and
`artifacts/request-metrics.jsonl`.

Fresh matched Local baseline (#014 code) → optimized #015 medians from three
requests per route, against the same SQLite file, with the metrics flag off.
Memory is a **separate** traced Python allocation peak, not process RSS:

| Route | Wall ms | CPU ms | SQL ms / queries | Body bytes | Python peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/` | 1,910 → 1,085 | 1,719 → 1,016 | 264 / 23 → 261 / 26 | 398,335 both | 37.89 → 19.81 |
| `/es/` | 1,336 → 1,038 | 1,297 → 969 | 223 / 23 → 282 / 26 | 402,046 both | 37.81 → 19.69 |
| `/tools/` | 245 → 281 | 250 → 266 | 28 / 19 → 32 / 19 | 253,592 both | 6.07 → 6.10 |
| ordinary Model panel | 1,423 → 1,104 | 1,422 → 1,047 | 211 / 25 → 266 / 28 | 439,516 both | 38.09 → 19.96 |
| 163-evaluation Model panel | 1,496 → 1,213 | 1,469 → 1,172 | 208 / 38 → 262 / 41 | 554,310 both | 39.77 → 21.63 |
| Tool panel | 302 → 386 | 297 → 344 | 31 / 21 → 44 / 21 | 260,620 both | 6.08 → 6.08 |
| filtered Models | 632 → 760 | 609 → 688 | 145 / 23 → 206 / 26 | 237,523 both | 15.78 → 15.81 |
| price-sorted Models | 1,509 → 1,327 | 1,484 → 1,313 | 234 / 23 → 197 / 23 | 403,953 both | 37.89 → 37.99 |
| sitemap index | 977 → 1,011 | 938 → 1,000 | 148 / 20 → 124 / 20 | 2,246 both | 16.65 → 16.67 |

Only the default chronological Models route uses the optimized query path.
The unchanged Tools, price-sort and sitemap route differences are test-run
variation, not claimed improvements. Large Model panels also include the
faster Models list. Local evidence: ignored
`artifacts/performance-015-before-memory.json` (copied with matching SHA-256
from the main-checkout baseline) and `artifacts/performance-015-after-memory.json`
in this worktree.

A **synthetic** four-client, 16-request burst against 18811 included four
each of Models root, 163-evaluation Model, Tools root and sitemap. All 16
returned 200 in 11.33 s. Windows process accounting for the exact 18811 PID
recorded 135.8% of one CPU over 11.6 s. The telemetry active window recorded
138.31% of one CPU over 10.56 s, with 4 Models root, 4 heavy Model, 4 sitemap
and 3 Tools completions inside that window; the final request fell in the
next window. These 15 completions accumulated 405 SQL executions and about
6.35 s measured SQL time. The synthetic UA was declared `GPTBot`; this
**does not** establish that real GPTBot or any crawler caused the historical
Production peak. It demonstrates a reproducible app-side mechanism by which
several CPU-heavy requests can exceed the earlier 94.2% sample without a
restart or IndexNow dispatch.

The historical Production spike remains **unattributed by request source**.
Its PID accounting proves it was AIpediya process CPU rather than merely
another process on the shared host; the existing log lacks routes, UA, status
distribution and durations in that interval. The already deployed #014
cannot retroactively emit these metrics. To close #015, obtain a safe
historical Cloudflare HTTP Analytics export with route/status/UA/time buckets,
or separately authorize an AIpediya-only telemetry rollout and capture a
future comparable peak, then correlate its PID/window/route/SQL data. Keep
#015 `in_progress` and do not publish the optimization on Local speed alone.
The measured PID had already run over 5.5 hours and the four Waitress request
threads, rather than its main thread, consumed the peak. This argues against
startup/restart or a separate `aipedia-indexnow` management process being the
direct CPU source in that sample; it does not identify the real requester.

The future #015 code package is limited to the existing chronological Models
pagination change in `catalog/views.py`, its regression tests, opt-in request
aggregates in `catalog/observability.py` and settings/tests, repeatable Local
profilers, read-only AIpediya process metrics tooling, and Timeline/status
documentation. It contains no catalog master plan, catalog data sync, Local
SQLite, or Production telemetry enablement. No release archive or tag has
been built while the root-cause and owner Local acceptance gates remain open.

## Final Local gate and owner authorization — 2026-09-29

The owner accepted the demonstrated application defect as the #015 root
cause: all 325 published Models and their related data were hydrated before
pagination. The inability to classify the historical requesters as humans or
crawlers is retained as a diagnostic limitation, **not** a blocker to fixing
that measured CPU and allocation cost. The owner explicitly authorized this
exact Performance Release #015 / v0.13.2 after complete Local QA.

The final source-code baseline is `5686b1c41bddf0d6729eb299056670dfb26e6d85`.
The last code change made the server preflight and post-release backup
comparison accept subsequent code-only releases while still rejecting an
unspecified catalog plan and checking that every catalog table is unchanged.
Its contract tests passed. No catalog data, migrations, Local SQLite or
publication state were changed in Local.

The candidate ran independently on `127.0.0.1:18811`, leaving the normal
18810 Local server alone. Four Playwright shards covered all 22 locales,
Models and Tools, desktop 1440 px and mobile 375 px: **88/88 PASS**, 1,712
checks, 264 actual menu navigations, zero redirects, console errors, failed
network requests or HTTP errors. The menu clicks exercised root and open
Model/Tool, X/Escape/outside, Back/Forward, search, filter, sort, query
preservation, themes, infinite loading and RTL. Combined ignored report:
`artifacts/locale-switch-015-local-88.json` (source shards `-a` through `-d`).
After the preflight-tool change: full catalog suite **340 tests, one skip**;
`manage.py check`, GSD Local **33/33**, `catalog_master check: OK`, and
`catalog_master qa: PASS`. The master retains its known research-only data
quality queue and deferred Local sync drift; this code-only release does not
sync it.

The predeploy #014 public route probe returned 200 for three sequential
requests each to ten routes. Median TTFB (ms): Models `/` 484, Spanish 472,
Tools 254, ordinary Model 468, 163-evaluation Model 474, Tool panel 327,
filter 280, price sort 469, sitemap 376 and `/healthz` 158. Its ignored JSON
is `artifacts/performance-015-production-before.json`. This is a calm live
baseline, not yet an after result. The candidate is now `review`, Local ✓,
Owner ✓, Production —. The release archive, server preflight, deploy and
public after-measurements follow under `docs/RELEASE.md`.
