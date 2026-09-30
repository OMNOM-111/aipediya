# Organic Search Follow-up / control snapshot — completed 2026-09-30

Status: DONE, read-only. This is not a Release # and it did not change
Production. It closes the post-recrawl control measurement left after Global
Search & Discovery, Search Activation and Search Visibility Optimization.
Google Ads was not launched.

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

## Fresh control snapshot, 2026-09-30

### Google Search Console

The authenticated `sc-domain:aipediya.com` property was read in the existing
Chrome session. The report said it was updated five hours earlier and its
available chart covered September 24–28, 2026:

- 775 impressions, 7 clicks, 0.9% CTR, average position 13.1;
- 115 queries, 561 pages and 87 countries in their respective tables;
- leading visible queries included `google ai studio` (1 click / 10
  impressions), `chat.qwen.ia` (1/2), `claude sonnet 3` (1/1), `groqcloud`
  (0/26), `perplexity` (0/8), `gigachat` (0/5) and `qwen chat` (0/5);
- visible country rows included Iraq 2/5, Russia 1/45, Ukraine 1/29, Iran 1/25,
  Vietnam 1/13, Israel 1/4, USA 0/202, Brazil 0/41, Turkey 0/39 and India 0/32
  (clicks/impressions);
- the Pages table still attributed performance to parameterized URLs such as
  `?sort=...`, `?lang=...`, `?page=...` and `?tab=...`; this does not prove that
  Google selected them as canonical;
- Pages/Indexing still said that data is processing and to retry in about a day,
  so indexed-page and Google-selected-canonical counts are **unavailable / not
  confirmed**, not zero;
- `https://aipediya.com/sitemap.xml` remained **Successful**, submitted
  September 25 and last processed September 29, with 10,421 discovered pages
  and zero videos.

Against the September 24 baseline, the available aggregate increased from 41
to 775 impressions (+734) and from 0 to 7 clicks; average position changed from
8.5 to 13.1. The window and query/page mix also expanded, so the position change
is descriptive and is not attributed to the release.

### Bing Webmaster Tools

- `https://aipediya.com/sitemap.xml` is Success, submitted/crawled September 25,
  with one known sitemap index, 22 discovered child sitemap URLs, zero errors
  and zero warnings. The older “about 1.4K discovered” observation is not reused
  as current data because this screen now reports the 22 index children.
- Search Performance still says to return in 48 hours while data is prepared;
  impressions, clicks, queries, pages and countries are **unavailable / not
  confirmed**.
- Site Explorer / Indexed URLs says **No data available**.
- IndexNow shows 18 self-submitted URLs in the last 22 hours. A visible fresh
  Release #020 URL showed Crawl Status `Pending` and Index Status `Not Indexed`.

### Yandex Webmaster

The authenticated `aipediya.com` property is now accessible. The dashboard
reported no diagnostic errors and four recommendations. Search statistics for
August 27–September 27 explicitly reported 0 impressions and 0 clicks (a real
dashboard zero, not an unavailable value). `sitemap.xml` was OK, last loaded
September 28 at 20:00, with 22 child links; visible child maps were also OK
(471 URLs each in the visible rows, English 488). “All pages” reported **No
indexed pages** and the recent-changes view reported no indexing changes.

### Naver, Brave and IndexNow

- Naver Search Advisor opened signed out and offered Login. Current ownership,
  sitemap and indexing state are **unavailable / not confirmed**. The public
  home page still contains the Naver verification meta tag; historical owner
  screenshots and recovery reports are not presented as current account state.
- Brave Search `site:aipediya.com` surfaced exactly two visible results in this
  bounded snapshot: the home page and GLiNER2.5-Decide; Next was disabled. This
  proves at least those two URLs are discoverable in Brave, not a complete index
  count.
- A fresh read-only Production SQLite snapshot passed integrity/FK checks.
  `indexnow_status` on that snapshot: active pending 0, active retry 0,
  failed unresolved 0, 23,467 sent events, 10,720 accepted URLs and 5,346
  resolved historical failed attempts; last sent at 2026-09-30 19:45:54 UTC.
  Historical failures remain audit history. Acceptance is not indexing.

### Public site and legacy URLs

Read-only public checks were run against `https://aipediya.com`; no Production
configuration, search-console submission, ads or DNS changes were made.

- `tools/gsd_public_check.py https://aipediya.com` — 34/34 PASS. Canonical,
  hreflang, language URLs, robots, sitemap index and sampled sitemap child still
  work; the root contains 22 child maps and the sampled RU map 505 URLs.
- `tools/search_visibility_qa.py --base https://aipediya.com` — 45 known legacy
  URLs checked, failures 0: 25 one-hop 301, 19 correct 404, 1 public fragment
  200/noindex.

Evidence: `artifacts/organic-followup-20260930-gsd-public.json`,
`artifacts/organic-followup-20260930-legacy-urls.json` and the integrity-checked
ignored Production snapshot timestamped `20260930T222914Z`.

### Limited SERP comparison

Two personalized Google result pages were observed without changing filters or
submitting URLs. AIpediya was not found on the first visible page for either
`AIpediya AI models` or `AI model comparison`. The latter matches the earlier
“not among the first visible results” observation; the brand query is weaker
than the prior snapshot that showed AIpediya first. These are location/account
specific snapshots, not proof of causal ranking change.

## Conclusion and external follow-up

The control measurement requested by this card is complete, including explicit
unavailable classifications. Real external follow-up remains: recheck GSC
Pages/canonical after processing completes; recheck Bing performance/indexed
URLs after its data preparation completes; and have the owner restore/sign in
to Naver before checking its property. Yandex and Bing currently provide no
confirmed indexed-page growth. No code, sitemap, robots, canonical, DNS,
catalog or Production change is implied by these external waits.

## Paid Search

The current Paid Search / Google Ads work tail is closed as a deferred planned
card, not a completed experiment. No campaign, budget, ad group, keyword,
Keyword Planner master, billing, spend, paid impression or paid click exists.
Advertising can return only through a separate future owner decision.
