# Organic Search Growth Check — planned for 2026-10-07

Status: PLANNED, read-only, Local-only. This is not a Release # and has no
SemVer. Production, SEO, catalog data, search-engine submissions and advertising
must not be changed by creating this plan.

This card continues the completed
`ORGANIC-SEARCH-FOLLOWUP-2026-09-30`; it does not reopen or alter that card.

## Purpose

On October 7, capture a new comparable Search and traffic snapshot to determine
whether organic visibility and real visits continue to grow, whether Google and
Bing have finished processing, whether confirmed indexed canonical coverage has
expanded, and whether another organic follow-up is needed. Paid Search remains a
separate owner decision and is never launched automatically from this check.

## Baseline recorded on 2026-09-30

- Google Search Console, available September 24–28: 775 impressions, 7 clicks,
  0.9% CTR, average position 13.1, 115 queries, 561 pages and 87 countries.
  Sitemap was Successful with 10,421 discovered URLs. Pages/Indexing/canonical
  data was still processing and therefore unavailable, not zero.
- Earlier Google baseline: 41 impressions, 0 clicks and average position 8.5.
  Average position must not be compared outside context because the time window
  and query mix changed.
- Bing: sitemap Success, 22 child sitemaps, zero errors and zero warnings;
  Search Performance was still preparing and Indexed URLs showed No data.
- Yandex: sitemap OK; the available report showed 0 impressions and 0 clicks,
  and indexed pages were not displayed.
- Naver: Search Advisor was signed out; ownership, sitemap and indexing were
  unavailable / not confirmed. The public verification meta remained present.
- IndexNow: active pending 0, retry 0, unresolved failures 0 and 10,720 accepted
  URLs. Acceptance is not indexing evidence.
- Brave: the bounded `site:` snapshot surfaced at least two results; no complete
  indexed-page count was available.
- Legacy URLs: 25 × 301, 19 × 404, 1 × 200/noindex, failures 0.

## Read-only measurement for October 7

Use comparable windows, preferably the latest seven complete days versus the
previous seven complete days. Record unavailable facts as
`недоступно / не удалось подтвердить`, not as zero.

- Google Search Console: impressions, clicks, CTR, average position, unique
  queries, pages, countries, top queries, top landing pages and, only where the
  data supports it, branded versus non-branded queries. Check sitemap discovered
  count, Pages/Indexing completion, indexed pages, canonical state and exclusion
  reasons.
- Bing Webmaster: sitemap, discovered and indexed URLs, Search Performance,
  impressions, clicks, queries, pages and countries/regions when available.
- Yandex Webmaster: sitemap, indexed pages, impressions, clicks and queries when
  available.
- Naver: ownership, sitemap and indexing/search status only if the owner has
  restored access; otherwise record the state as unavailable.
- IndexNow: pending, retries, unresolved failures, accepted URL count and the
  state of recent submitted URLs. Never equate accepted with indexed.
- Brave: repeat the same bounded method used on September 30.
- Cloudflare Web Analytics, if already available read-only: visits, page views,
  comparable-period change and available leading countries/pages. Keep GSC
  clicks, Cloudflare visits, page views and impressions as separate metrics.

No URL submission, SEO edit, sitemap/robots/canonical change, Production action
or advertising action belongs to this measurement.

## Decision gate

1. **Organic growth continues:** if impressions, clicks, index coverage and real
   organic visits show meaningful continued growth, do not launch Paid Search;
   record the growth and schedule another organic control only if needed.
2. **Data is still immature:** if Google/Bing still process data or the comparable
   window is too small, make no negative conclusion, do not launch advertising,
   and schedule another reasonable control interval.
3. **Mature but weak plateau:** only if indexing is sufficiently mature, the
   technical state is healthy, and comparable evidence shows flat/falling
   impressions, minimal clicks/organic visits and no useful non-branded query
   expansion, present a separate `Paid Search Experiment — candidate for owner
   decision`. A future proposal may retain the limit of up to $15/month, but no
   campaign, billing, Keyword Planner master, keywords, budget or spend may be
   created without a separate owner decision.

Paid Search is a paid-traffic instrument, not a way to improve or conceal weak
organic ranking. Organic and paid evidence must remain separate.
