# Organic Search Follow-up / control snapshot — planned for 2026-09-30

Status: PLANNED. This is not a Release # and it does not change Production.
It restores the organic follow-up that was left after Global Search & Discovery,
Search Activation and Search Visibility Optimization. Google Ads is explicitly
deferred and must not be launched in this task.

## Why this exists

Search Visibility Optimization v2 was deployed on 2026-09-26 and verified the
technical site behavior: 45 legacy GSC URLs, robots exceptions, clean SSR card
links, four finite EN/RU search pages and IndexNow dispatch handling. The release
report explicitly left the real search-engine outcome open: recrawl, indexed URL
selection, queries, countries, impressions, clicks and average position needed a
later control snapshot.

The only visible open card at month end was `Paid Search Experiment / Google Ads`.
Its own text said the paid step should happen only after a 2026-09-30 organic
control measurement. That prerequisite was not a finished task and was easy to
lose behind the paid-search card, so it is restored here as an organic planned
follow-up.

## Previous baseline

- Search Visibility release report: 45 known GSC legacy URLs technically fixed;
  public sitemap 10,190 URLs across 22 child maps; Search QA 1657/1657 PASS.
- GSC last available data in the report: 41 impressions, 0 clicks, average
  position 8.5 for 2026-09-24; sitemap Successful; indexing report still
  processing.
- Bing: sitemap Success / about 1.4K discovered in the audit; Search Performance
  was still preparing.
- Yandex: DNS verification and sitemap were owner-reported earlier; fresh console
  state was not available.
- Naver: verification meta tag was deployed and prior screenshots reported
  ownership/sitemap, but account recovery after login restriction was not
  confirmed.
- IndexNow: release report recorded 330 redirected legacy URL notices and four
  new page notices accepted by the scheduler, with active pending/retry and
  unresolved queues at 0. Acceptance is not indexing.
- Brave: prior re-fetch request was owner-reported as accepted; indexing status
  unknown.

## Current public-site check, 2026-09-29

Read-only public checks were run against `https://aipediya.com`; no Production
configuration, search-console submission, ads or DNS changes were made.

- `tools/gsd_public_check.py https://aipediya.com` — 34/34 PASS. Canonical,
  hreflang, language URLs, robots, sitemap index and sampled sitemap child still
  work.
- `tools/search_visibility_qa.py --base https://aipediya.com` — 45 known legacy
  URLs checked, failures 0: 25 one-hop 301, 19 correct 404, 1 public fragment
  200/noindex.

## Still unfinished

- Google Search Console: fresh Pages/Indexing, canonical selection, sitemap
  processing, impressions, clicks, average position, queries, countries and URL
  examples after recrawl.
- Bing Webmaster Tools: fresh sitemap/indexing state, discovered/indexed URLs,
  performance, queries/pages/countries if available.
- Yandex Webmaster: fresh verification/role, sitemap/indexing and query data if
  available.
- Naver: current account recovery, property and sitemap state; do not register
  or submit again unless the existing state is unavailable and the owner approves.
- IndexNow: current queue/log state; do not treat accepted submissions as
  indexing evidence.
- Brave and other already connected channels: check only existing available
  status; do not start new onboarding here.
- Repeat the saved SERP/control-query snapshot only as observation, not as proof
  of ranking causation.

## Paid Search

Paid Search / Google Ads remains a separate future experiment. No campaign,
budget, ad group, Keyword Planner master, spend, impressions or paid clicks exist.
The owner decision on 2026-09-29 is: organic global search availability and
actual indexing first; advertising only if the owner separately returns to it.