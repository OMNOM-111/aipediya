# Search & discovery contract (GSD-1.0)

Canonical contract for how AIpediya is exposed to search engines and AI search.
Status of the version: `docs/timeline.json` (GSD-1.0) and `docs/EXECUTION_STATE.md`.
Decisions: `docs/DECISIONS.md` (`D-2026-09-25-locale-paths`, `D-2026-09-25-seo-readiness`,
`D-2026-09-25-facets-pagination`, `D-2026-09-25-datasets-license-gate`,
`D-2026-09-25-discovery-outbox`). GSD-1.0 was released on 2026-09-25. The
Search Visibility Optimization update follows that architecture; release state
and public verification are recorded in `docs/RELEASE.md` and
`docs/history/2026-09-26-search-visibility-release.md`.
The update was published on 2026-09-26 21:47 UTC at commit
`61adedd6ea5e6a0955d51d87374fa2fa9bcc7799`; 45/45 legacy URLs and
1657/1657 public Search checks passed. IndexNow accepted 334 targeted notices;
search-engine recrawl, indexed-page counts and ranking growth remain unverified.

## 1. Language URLs

| Page | English (x-default) | Other locale (example `ru`, `zh-Hans`) |
|---|---|---|
| Models catalog | `/` | `/ru/`, `/zh-hans/` |
| Tools catalog | `/tools/` | `/ru/tools/` |
| Model card | `/models/<record-id>` | `/ru/models/<record-id>` |
| Tool card | `/tools/<record-id>` | `/pt-br/tools/<record-id>` |
| Methodology | `/methodology` | `/uk/methodology` |
| Collections | `/collections/`, `/collections/<slug>` | `/ar/collections/<slug>` |
| Open data | `/datasets/`, `/datasets/models`, `/datasets/tools` | `/ru/datasets/models` |
| Privacy | `/privacy` | `/de/privacy` |
| Context comparison | `/compare/model-context` | `/ru/compare/model-context` (EN/RU only) |
| API token prices | `/api-pricing` | `/ru/api-pricing` (EN/RU only) |

* Path codes are lower-case BCP-47 (`zh-hans`, `zh-hant`, `pt-br`); `hreflang` uses the
  canonical tag (`zh-Hans`, `pt-BR`). One builder: `catalog/locale_urls.py`.
* Language-neutral (never prefixed): `/robots.txt`, `/sitemap.xml`, `/sitemaps/<code>.xml`,
  `/datasets/*.json|csv`, `/datasets/manifest.json`, `/indexnow/<key>.txt`, `/healthz`,
  `/static/`, `/admin/`. `/<locale>/<neutral endpoint>` is 404.
* The path alone decides the language. Cookie, Accept-Language, `CF-IPCountry` and the
  User-Agent never change the language of a URL and never redirect. Responses do not vary
  on Cookie/Accept-Language. A manual switcher choice is remembered only in the browser
  (cookie written by `site.js`); on a page reached from outside the site in another
  language, a small link offers the remembered language — never a redirect.
* Permanent redirects (exactly one hop, verified by tests for every route type):

| Old / non-canonical | New |
|---|---|
| `/?lang=ru` | `/ru/` |
| `/?lang=en` | `/` |
| `/?lang=ru&kind=tool&sort=name_asc` | `/ru/tools/?sort=name_asc` |
| `/models/<id>?lang=de&kind=model&page=1&tab=pricing` | `/de/models/<id>` |
| `/tools/<id>?lang=zh-CN` | `/zh-hans/tools/<id>` |
| `/privacy?lang=uk` | `/uk/privacy` |
| `/zh-Hans/…`, `/pt_BR/…`, `/zh-cn/…`, `/pt/…` | `/zh-hans/…`, `/pt-br/…` |
| `/en/…` | `/…` |
| `/ru` | `/ru/` |
| `/ru/?lang=de` (prefixed path + stray lang) | `/ru/` (path wins) |
| `/?lang=zz` (unknown value) | `/` |
| `/?page=1`, `/ru/?page=1` | `/`, `/ru/` |

  On legacy full-card requests the presentation parameters (`page`, `sort`, `tab`,
  `kind`, `lang`) are discarded in one 301 to the clean canonical card. A confirmed
  hidden alias redirects directly to its published card. Listing filters and
  pagination are retained for visitors but remain robots-blocked and noindex.
  An old `partial=rows|panel` card request returns a fragment with `X-Robots-Tag:
  noindex`, not a full-card redirect. Unknown or unpublished records answer **404** on every form of the
  address (never a redirect to the home page). Region remaps to another language
  (`/be/`, `/ca/`) are 404, not aliases.

## 2. Publicity policy and readiness registry

`catalog/readiness.py` is the only source for "public" and "indexable" used by pages,
hreflang, sitemaps, collections, datasets and the IndexNow outbox.

* Public = `published=True` (and `entry_type='model'` for models). `published` is the
  existing release contract synchronized from the catalog master through
  `data/release_state.json`; the XLSX is never read at request time. Read-only check at
  GSD baseline: manifest ↔ Local DB 0 mismatches (763 models / 138 tools).
* Per entity × locale: `indexable` | `not-ready` | `not-public`, with a reason.
  Primary text = `description` + (if an English source exists) `suitable`,
  `limitations`. `en` needs the English text; `ru` needs the authored Russian text;
  other locales need a `ContentTranslation` row whose `source_hash` matches the current
  English source, state `current|reviewed`, and non-empty text in the field.
* A field without English source is "not applicable", never a missing translation.
  Brands, IDs, URLs and numbers are not localized fields and do not count as fallback.
* Secondary prose (origin, philosophy, evaluation-gap notes) may fall back to English;
  it is marked `lang="en"` in HTML and does **not** block indexing. The deferred
  eval-gap translation (412,820 billable chars; previously recorded F0 shortfall 108,605
  — historical, not a live quota check) therefore stays a separate item.
* `not-ready` pages still render for people with `noindex,follow`, no canonical and no
  alternates; they are excluded from sitemaps and from other pages' hreflang.
* Registry export: `manage.py seo_report --registry-csv <file>`.

## 3. Page signals

* Localized `<title>` / meta description for catalogs, cards, collections, methodology
  and datasets; one subject `<h1>` per page (catalog H1 is screen-reader visible; on a
  card the card title is the only H1).
* Self-canonical built from `AIPEDIA_PUBLIC_ORIGIN` (never the Host header); reciprocal
  `hreflang` including self and `x-default` (= English, a 200 canonical page); only
  indexable locales appear.
* `html lang/dir` per locale (`ar`, `fa` are RTL).
* JSON-LD: `Organization` (all pages), `BreadcrumbList` (cards, collections,
  methodology, datasets — always paired with the same visible breadcrumb trail), `DataCatalog` (`/datasets/`), `Dataset` + `DataDownload`
  (`/datasets/models|tools`). No ratings, reviews, prices, licenses or addresses are
  asserted. Serialized with `<`, `>`, `&` escaped.
* Open Graph / Twitter card with `static/share-card.png` (1200×630, rendered from the
  existing `brand.svg`) and `static/brand-512.png` as the Organization logo.

## 4. Sitemaps

`/sitemap.xml` is a sitemap index of `/sitemaps/<locale>.xml`. Each child lists every
indexable URL of that locale with all its `xhtml:link` alternates + `x-default`, built
from the registry (`catalog/seo.py:sitemap_urlsets`). `lastmod` = newest of the
editorial check date, last publication change and (per locale) the last translation
update; page views never change it. Limits checked by `seo_report`: ≤ 50,000 URLs and
≤ 50 MB per file (Local 2026-09-25 after reconciliation: 10,035 `<loc>` in 22 files — cards 9,724 (models 6,688 + tools 3,036), ready collections 198 (9 × 22), collections index 22, models listing 22, tools listing 22, methodology 22, privacy 22, dataset pages 3 (English only; absent in Production while datasets are off); 230,742 alternate links; largest file ≈ 1.15 MB / 459 URLs). Plain `?page=N` listing pages are indexable but deliberately not in the sitemap (reached through `<a href>` pagination).

## 5. Parameters, pagination and crawl

| Parameter | Where | Crawl | Index |
|---|---|---|---|
| (path locale) | all | yes | per readiness |
| `page=N` (N≥2, in range) | catalogs, collections | yes | yes, self-canonical, prev/next |
| `page=1` | catalogs | — | 301 to clean URL |
| `page` invalid / out of range | catalogs | — | 404 |
| `tab` on a card; `page` + anything on a card | cards | robots-blocked unless an exact GSC migration exception | legacy `?lang=` full cards: one 301 to clean card; other duplicates: canonical = clean card |
| `page=N` alone on a card (old panel link) | cards | robots-blocked unless an exact GSC migration exception | canonical = clean card; catalog row links now use the clean card URL |
| `q`, `sort`, `category`, `task`, `developer`, `access`, `status`, `benchmark`, `configuration`, `snapshot`, `evaluated_only`, `price_*`, `platform`, `local`, `ecosystem`, `model`, `tool` | catalogs / cards | robots-blocked | listings: `noindex,follow`, no canonical (a filtered selection is never declared a copy of the root); cards: canonical = clean card |
| `partial=rows|panel` | fragments | robots-blocked unless an exact GSC migration exception | `X-Robots-Tag: noindex`; never carried into links |
| `lang`, `kind` | legacy | — | 301 (section 1) |

`robots.txt` (Production) blocks only the parameters above (`/*?p=` and `/*&p=`), any
query on card URLs (`/models/*?`, `/*/models/*?`, `/tools/*?`, `/*/tools/*?` — canonical
duplicates such as `?tab=` or filters), plus `/admin/` and `/healthz`. Locale paths and
plain listing `page=` stays crawlable. The tools listing uses the limited
`Allow: /tools/?page=` and localized equivalent to distinguish it from tool
cards; `…?page=*&` remains blocked. **No card-wide `Allow: */?page=` rule**
is present. Catalog row links use clean card URLs, while the browser preserves
the original listing URL when a panel is closed. The 45 exact GSC card URL
strings observed on 2026-09-26 have anchored
`Allow: <URL>$` exceptions, so crawlers can read their 301/404/noindex response.
This list is finite; no wildcard `?lang=` permission opens arbitrary facet or
pagination combinations. The own crawler uses the same rules
(`catalog.views.robots_allows`). Every public record
is reachable through plain `<a href>` pagination without JavaScript (own crawler).
Local serves `Disallow: /` and `X-Robots-Tag: noindex, nofollow` on every response.

## 6. Collections (hubs)

Finite registry in `catalog/hubs.py` (10 entries, published records only, minimum
5 records to be indexable, text localized in 22 locales):
`coding-models`, `video-models`, `music-models` (not ready: 4 < 5 records),
`free-tier-models` (price 0 listed; not "free API"), `api-models`,
`open-weight-models` (not "open source"), `models-from-china`,
`models-released-2025` (exact dates only), `long-context-models` (≥ 1,000,000 tokens;
not "better"), `coding-tools`. No per-filter or per-country/year generator exists.
Aggregates for future reports: `manage.py catalog_stats` (current state only; no
history, no rating).

### Search reference pages (Search Visibility Optimization)

Two distinct EN/RU pages use only published records already checked in the
catalog master: `/compare/model-context` compares documented context-window
sizes across models with a known value; `/api-pricing` pairs active primary
standard text-token input and output prices from the **same API service**,
with an official provider-domain price source and normalized scope. Third-party
reseller prices and offers whose scope is explicitly unresolved are excluded.
Both explain their selection and limitations, link to each model card and
source, expose check dates, and link to the existing coding/API/long-context
collections and methodology. They require at least five qualifying rows.
Unknown values are omitted, never zero. Batch/cache/audio/image and special
long-context rates do not enter the standard price comparison. No new model
data, benchmark rankings, country claims or pairwise doorway pages are created.
The other 20 locales have no authored page text and therefore no indexable
versions, sitemap entries or language-switcher links for these two routes.
Card metadata with the known generic “Exact version” wording is enriched for
EN/RU from already published context/API/price-presence facts; master prose,
card data and design remain unchanged.

## 7. Open datasets

`AIpediya Global AI Models Dataset` and `AIpediya AI Tools Dataset` (JSON + CSV,
`/datasets/manifest.json` with SHA-256), schema 1.0.0, dataset version =
`<latest check date>+<content digest>`; allowlist in `catalog/datasets.py`. Excluded:
unpublished records and their links, descriptive prose, third-party benchmark scores,
notes, research, history, translation state, master XLSX. CSV cells starting with
`= + - @ TAB CR` (non-numeric) are prefixed with `'`. Snapshot:
`manage.py export_datasets --out <dir> --check`.

**Publication blocker (owner decision):** no data license has been chosen
(`license: not-granted`, no license asserted in JSON-LD), and redistribution rights for
imported descriptive text and third-party benchmark results are not established (those
fields are excluded). In Production the datasets stay off (`AIPEDIA_DATASETS_PUBLIC=0`,
pages/downloads 404, not in sitemaps, footer link hidden) until the owner picks a
license and enables the flag.

## 8. Search engines, AI search and IndexNow

Verification tokens: `GOOGLE_SITE_VERIFICATION`, `BING_SITE_VERIFICATION`,
`YANDEX_SITE_VERIFICATION` (meta tags already supported). No account access was
available to the implementing agent; nothing is "connected" without owner evidence.

| System | Discovery / verification | Technical readiness (Local) | Live access | Owner action |
|---|---|---|---|---|
| Google Search Console | URL-prefix property: HTML file / HTML tag / GA / GTM / DNS; Domain property: DNS only [G1] | sitemaps, hreflang, canonical, robots ready; meta token env var | Domain property verified by DNS TXT on 2026-09-25; `/sitemap.xml` status Successful | retain TXT; indexing is not implied |
| Bing Webmaster Tools | XML file, `msvalidate.01` meta tag, CNAME, or import from GSC [B1]; IndexNow [B2] | ready; meta token env var; IndexNow outbox | GSC import added `https://aipediya.com/`; sitemap submitted 2026-09-25, status Processing | no verification or sitemap action remaining; IndexNow key remains separate |
| Yandex Webmaster | `yandex-verification` meta tag, HTML file or DNS TXT [Y1]; IndexNow [Y2] | ready; meta token env var | owner reports: verified by DNS TXT, `/sitemap.xml` queued (2026-09-25) | none |
| Seznam | IndexNow (`search.seznam.cz/indexnow`; one engine forwards to all participants) [S1] | outbox ready | none | IndexNow key activation only |
| Naver Search Advisor | IndexNow participant with its own endpoint [I2]. Current console offered HTML file or HTML meta-tag verification | SSR setting and conditional head output implemented; `217/217` catalog tests PASS | meta tag live in Production HTML since 2026-09-25 22:02Z (`160be0f37037`, curl-verified) | click Verify, then submit `https://aipediya.com/sitemap.xml` |
| Baidu (ziyuan) | Official: site must be verified before sitemap submission; ≤ 50,000 URLs and ≤ 10 MB per sitemap file; submission does not guarantee crawling/indexing [BD1]. Concrete verification methods and account requirements: **unverified** (secondary guides only) | `/sitemaps/zh-hans.xml` fits the limits (458 URLs, ≈ 1.2 MB) | no Baidu tab or authenticated session among the inspected Chrome tabs (2026-09-25) | if account is available, register/verify and submit the zh-hans sitemap; otherwise owner may face identity/phone requirements |
| Brave Search | Crawler has no distinct UA; does not crawl what Googlebot may not crawl; noindex (not robots) delists; URL submission at `search.brave.com/submit-url` [BR1] | ready (Googlebot not blocked) | none | optional: submit key URLs |
| IndexNow protocol | Key file, batch POST ≤ 10,000 URLs, codes 200/202/400/403/422/429 [I1]; submission is shared with all participants; participants: Bing, Yandex, Seznam, Naver, Yep, Amazon (+ Internet Archive in the engines list); Google is not listed [I2][I3] | enabled on Production 2026-09-25; root key file `/<key>.txt` returns 200 | initial submission: 10,032 URLs accepted (HTTP 200, 3 POSTs); acceptance is not indexing | automatic: `aipedia-indexnow` scheduler every 300 s |
| OpenAI OAI-SearchBot | search crawler, honors robots; GPTBot = training; ChatGPT-User = user-triggered, robots may not apply; IP lists published [O1] | not blocked by current robots | spoofed-UA 200 only | none required for search visibility |
| PerplexityBot | search (not training), honors robots; Perplexity-User user-triggered, generally ignores robots; IP lists published [P1] | not blocked | spoofed-UA 200 only | none |
| Anthropic Claude-SearchBot | search; ClaudeBot = training; Claude-User = user-triggered; all honor robots.txt [A1] | not blocked | spoofed-UA 200 only | none |

Crawler verification (real vs spoofed): Googlebot — reverse + forward DNS
(`googlebot.com`, `google.com`, `googleusercontent.com`) or published IP JSON [G2];
Bingbot — Verify Bingbot tool [B3]; YandexBot — reverse + forward DNS (`yandex.ru/.net/.com`)
[Y3]; OpenAI / Perplexity — published IP JSON [O1][P1]. None of this was possible from
Local (no server logs), so **real-bot access is unverified**.
Google-Extended is a robots product token for Gemini training, not a crawler; it does not
affect Google Search inclusion or ranking [G3].

**Training-access policy: not defined by the owner.** No owner decision on training
crawlers (GPTBot, ClaudeBot, Google-Extended, …) exists in `docs/DECISIONS.md`. The
current robots.txt baseline has no AI-agent-specific lines; GSD-1.0 keeps that baseline
unchanged (it adds only facet/parameter rules under `User-agent: *`). The absence of a
block is the inherited state, **not** an approved allow-all policy; choosing one is an
owner decision outside GSD-1.0.

Official sources (retrieved 2026-09-25):
[G1] https://support.google.com/webmasters/answer/9008080 ·
[G2] https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests ·
[G3] https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers ·
[G4] https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites ·
[B1] https://www.bing.com/webmasters/help/add-and-verify-site-12184f8b ·
[B2] https://www.bing.com/indexnow/getstarted ·
[B3] https://www.bing.com/toolbox/verify-bingbot ·
[Y1] https://yandex.com/support/webmaster/service/rights.html ·
[Y2] https://yandex.com/support/webmaster/indexing-options/index-now.html ·
[Y3] https://yandex.com/support/webmaster/robot-workings/check-yandex-robots.html ·
[S1] https://o-seznam.cz/napoveda/vyhledavani/seznambot/protokol-indexnow/ ·
[BD1] https://ziyuan.baidu.com/college/courseinfo?id=267&page=2 ·
[BR1] https://search.brave.com/help/brave-search-crawler ·
[I1] https://www.indexnow.org/documentation ·
[I2] https://www.indexnow.org/searchengines.json ·
[I3] https://www.indexnow.org/faq ·
[O1] https://developers.openai.com/api/docs/bots ·
[P1] https://docs.perplexity.ai/docs/resources/perplexity-crawlers ·
[A1] https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

Production UA probe (2026-09-25, 12 GETs of `/` from one client IP): browser, Googlebot,
bingbot, YandexBot, OAI-SearchBot, GPTBot, ChatGPT-User, PerplexityBot, ClaudeBot,
Claude-SearchBot, Baiduspider and curl UAs all received 200 via Cloudflare. This proves
only that spoofed UAs from this IP are not blocked; real crawler access (verified IPs)
and actual crawling are **unverified** (no logs / console access).

Prepared Cloudflare scope (not applied; needs the owner): keep "verified bots" allowed
for search crawlers; if AI bot blocking is ever enabled, exempt `OAI-SearchBot`,
`PerplexityBot`, `Claude-SearchBot` (search) separately from training bots; cache rule:
HTML is not cached with cookies (the site sets no language cookie server-side).

### IndexNow outbox

* `DiscoveryEvent` (migration 0018) is written only by model signals: create / publish /
  significant change (visible fields, prices, access, facts, evaluations) → `upsert` for
  locales indexable now; unpublish / delete / slug change → `remove` for the locales that
  were indexable *before* the change; translation change → `upsert` of that one locale URL.
  One pending row per URL (dedup). Page views never write. Bulk `QuerySet.update` does not
  emit events (by design of Django signals).
* `manage.py indexnow_dispatch [--send]`: dry run unless `AIPEDIA_ENV=production`,
  `AIPEDIA_INDEXNOW_ENABLED=1`, a key and `--send`. Host allowlist, live-state gate
  (upsert URL must be 200, removed URL 301/302/404/410 on Production; the
  probe does not follow a redirect to its canonical destination), batch ≤ 10,000,
  200/202 → sent; 400/422 → failed; 403 → abort, keep pending; 429/5xx/network →
  exponential backoff, `--max-attempts` (default 6) then failed. Acceptance ≠ indexing.
* `manage.py notify_indexnow --url … | --all` only queues (no network).
* Scheduler (Production, since 2026-09-25 22:41Z): supervisord program
  `aipedia-indexnow` (same pattern as `aipedia-backup`) runs
  `/srv/aipedia/bin/indexnow-dispatch-loop` (`deploy/indexnow-dispatch-loop.sh`):
  `indexnow_dispatch --send --batch 1000` every 300 s
  (`AIPEDIA_INDEXNOW_INTERVAL_SECONDS`), only pending events that are due, with the
  normal live-state gate; never `--all`. `flock -n /srv/aipedia/data/indexnow-dispatch.lock`
  prevents overlapping runs; a manual run must use the same lock. Logs:
  `/srv/aipedia/logs/indexnow.log` (URLs and HTTP status only, never the key).
  `--all` was used once, for the URL-architecture release (2026-09-25).
  `tools/deploy_code_release.py` holds the same lock from before `stop aipedia` through
  migrate, publication state, app switch, start/healthz and any rollback (released in
  `finally`, and by the kernel on a crash), so dispatch never runs during a deploy; if a
  dispatch is running, the deploy waits up to 600 s, otherwise aborts before any change.
* Status: `manage.py indexnow_status` (also in `seo_report` → `outbox`): `active_pending`,
  `active_retry` (need attention), `failed_unresolved` (really undelivered) versus
  `failed_resolved_historical` (failed attempts whose URL was accepted later — audit only).

## 9. Monitoring

`manage.py seo_report --out <json> [--html all] [--crawl] [--registry-csv <csv>]`:
registry totals (entity URLs separate from translation rows), sitemap graph and limits,
production-mode HTML audit (canonical/hreflang/noindex/lang/dir/H1/title/description vs
sitemap), robots-respecting own crawl, outbox state. Server logs, search consoles and AI
referrals are reported as `not_connected` with `null` values — never zero.

## 10. Owner actions (updated 2026-09-25)

1. Google Search Console is verified as Domain property by DNS TXT; the main sitemap is
   Successful. Bing imported the site from GSC and its main sitemap is Processing.
2. Yandex Webmaster: verified by DNS TXT, main sitemap queued (owner report).
3. Naver: the meta tag is live in Production HTML (`160be0f37037`). Owner: click Verify
   in Naver Search Advisor, then submit `https://aipediya.com/sitemap.xml`.
4. Baidu was not present in the inspected open tabs; no submission was made.
5. IndexNow: enabled (key in the `[program:aipedia]` environment, root key file). The
   initial submission of all 10,032 public URLs was accepted. Future changes are sent
   automatically by the `aipedia-indexnow` scheduler (every 300 s); no owner action.
6. Decide the training-crawler policy (currently not defined; robots baseline unchanged).
7. Datasets: choose a data license (or keep off). Then `AIPEDIA_DATASETS_PUBLIC=1`.
8. Review agent-drafted translations of the new short texts
   (`data/discovery_translations.json`, `review_status: unreviewed`).

## Advertising

Advertising remains off unless all of these are nonempty: `AIPEDIA_ADS_ENABLED=1`,
`AIPEDIA_ADS_CLIENT`, and `AIPEDIA_ADS_SLOT`. `AIPEDIA_ADS_TXT` should contain only the
approved vendor declaration. One labelled placement is then rendered in normal document
flow; the provider script loads only after visitor consent.
