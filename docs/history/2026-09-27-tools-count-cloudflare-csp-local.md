# Tools count and Cloudflare Web Analytics CSP — Local audit, 2026-09-27

## Owner-approved working Local application and review state

The owner accepted the exact canonical master diff and authorized applying it
to the working Local SQLite. The pre-apply plan matched the accepted trial plan
exactly: **167 supported changes**, comprising 27 dates and 140 Public Numbers.
No supported Record ID, name, price, evaluation, description, publication
status or other factual field was in that plan. An online SQLite backup was
saved at `backups/catalog-count-csp-20260927/aipedia-working-before-approved-143.sqlite3`
before `catalog_master sync-local --apply --max-changes 200` applied all 167.

The actual working Local database now has **143 published Tools, 143 numbered,
60 exact dates, 83 approximate dates, 0 undated**, and exactly 1–143 without a
duplicate or gap. All-table comparison against the pre-apply backup found only
`catalog_tool` factual changes: 140 `public_number`, 23 `approx_released` plus
23 `approx_precision`, and four exact `released` updates. Models and every
other factual catalog table were unchanged. The sync also recorded Tool
publication revisions and pending discovery events through the normal save
path: 194 new Tool revisions and 450 discovery events, all `pending` with
`attempts=0`. These are journal and outbox effects, not additional card data
changes or transmitted events.

`catalog_master import` added no rows and renumbered none. `catalog_master
check` is OK; `catalog_master qa` is PASS for Models 321 and Tools 143; the
post-apply plan has zero supported changes. SQLite `integrity_check=ok` and
foreign-key errors=0. The full catalog suite passes **305 tests, one skipped**;
`manage.py check` reports zero issues. On the working Local SQLite, the real
browser showed RU/EN Tools in oldest and newest order (1…143 and 143…1),
all 143 records, and the `≈` display on approximate dates; RU/EN Models remain
321. Browser QA found a pre-existing count-note defect on the fast number-sort
path: it displayed 0 numbered despite numbered rows. The narrow fix in
`catalog/views.py` now counts the filtered queryset for both Models and Tools,
and a regression test covers both sort directions. The Cloudflare CSP code fix
and test from this task were preserved.

The milestone is **READY FOR OWNER REVIEW** in Local. Production remains at
`aa48e11bad7326340463654e33ba5e89769042b9`; no release was performed.
Read-only comparison of the public Production Tools HTML with reviewed Local
gives the [exact visible Production diff](../../artifacts/tool-count-csp-production-public-diff.md):
143 stable Record IDs and names; **140 number changes and 27 displayed date
changes** (four exact, 23 approximate). A database-level server release plan
must still be certified during the authorized release preflight. Existing
read-only SSH transport reached the server but authentication returned
`Permission denied (publickey)` in this session; no key or server state was
modified. A separate owner command is required before any Production change.

## Owner correction: every published Tool receives a chronological number

The owner clarified that **all 143 published Tools must have a verified
chronological position**. The earlier 122/21 trial described below is a
historical intermediate result and its 115-change plan is superseded. Targeted
verification supplied 21 further approximate dates. The canonical master now
contains **60 exact dates, 83 approximate dates, 0 undated published Tools,
and continuous Public Numbers 1–143**. Every approximate date means public
existence was verified by that date or period; it is not an invented official
release day. The full 21-record source and reasoning ledger is
`artifacts/tool-count-csp-date-evidence-20260927.json`.

The chronological refresh appended **140 Public Number changes** to the
Changelog. An online backup of the unchanged working Local database was used
for a fresh trial. Its owner-readable [exact diff](../../artifacts/tool-count-csp-full-trial-diff.md)
and machine-readable plan `artifacts/tool-count-csp-full-trial-plan.json` show **27 date updates and 140
number changes**, no publication changes, deletions or Record ID changes.
There are also 110 pre-existing unsupported differences, including 16 public
fields, explicitly excluded from this minimal sync. The canonical master
backup immediately before the 21-record pass is
`backups/catalog-count-csp-20260927/AIpediya_Model_Verification_Master_before_21.xlsx`.
On the fresh trial database, `catalog_master check` is OK and release `qa` is
PASS (321 Models, 143 Tools, all 143 Tools numbered). SQLite
`integrity_check=ok`, foreign-key errors=0. Replanning after apply/import found
0 remaining supported changes. Rendered RU `/ru/tools/` and EN `/tools/`
contain all 143 rows in both oldest and newest sorts, ordered 1…143 and
143…1 respectively, with approximate date markers visible.
The owner rule is now recorded in `AGENTS.md` and `docs/DECISIONS.md`;
`catalog_master check` rejects a PUBLISHED row without exact or evidenced
approximate date. The full catalog suite passes 304 tests (one skipped).
The CSP code fix described below was preserved unchanged. At the time of this
trial, working Local and Production databases were unchanged; the owner-approved
working Local application is documented above.

## Historical scope and state before approved Local application

This is a Local maintenance audit, not a Production release. Production remains
`aa48e11` with 143 public Tools, 116 numbered Tools and the old CSP. The canonical
master has been updated; the working Local SQLite still has the old dates and
numbers pending the owner's acceptance of the exact sync diff. A trial copy of
Local SQLite passed the sync and QA.

| Source | Total Tool rows | Public | Hidden | Numbered | Unnumbered public | Max № |
|---|---:|---:|---:|---:|---:|---:|
| Canonical master, before research | 145 | 143 | 2 | 116 | 27 | 116 |
| Working Local SQLite | 144 | 143 | 1 | 116 | 27 | 116 |
| Production SQLite, read-only | 144 | 143 | 1 | 116 | 27 | 116 |
| Public `/tools/`, rendered rows | 143 | 143 | 0 visible | 116 | 27 | 116 |
| Canonical master, after research | 145 | 143 | 2 | 122 | 21 | 122 |
| Trial Local SQLite and browser | 144 | 143 | 1 | 122 | 21 | 122 |

The second hidden master row is the unsynced `google-ax` NEEDS_REVIEW
candidate. The hidden Local/Production row is `gpt-live-1-e666ccf6`, an
ARCHIVE alias redirected to the canonical Models record
`gpt-live-1-60f09da9`. Published lifecycle states are 138 active, 3 retired,
1 archived and 1 deprecated; these remain published. Neither a lifecycle
label nor a missing date justifies removal.

All 143 published Record IDs match between master, Local, Production and the
public table. Public numbers 1–116 were contiguous and each matched across
those four sources before research. The master has no duplicate Record ID;
normalised names and aliases have no cross-record collision among published
Tools. The same official URL is shared by two distinct ElevenLabs voice API
features and by four distinct xAI voice/speech API endpoints. One public
parent/child relation is explicitly recorded: `alice-ai-pro-business` is a
`VARIANT_OF` `alice-ai-da730eef`. No additional duplicate or Models/Tools
misclassification was established with sufficient evidence, so no merge or
publication change was made. The product scope of Blackbox AI, Playground AI
and Scale AI remains a specific identity-review question.

## All 27 originally unnumbered published Tools

Every row below is `Publication Decision=PUBLIC`, `Status=PUBLISHED`.
`—` means no verified exact/approximate release date or number. “No” in the
last column means the existing source confirms the entity but not the first
public release of this particular Tool; dates of companies, models or later
versions were not substituted.

| Record ID | Name | Exact | Approx | New № | Why absent before / evidence now sufficient? |
|---|---|---|---|---:|---|
| `artificial-analysis-010a7a4a` | Artificial Analysis | — | — | — | First launch date unverified; about page insufficient: **no**. |
| `blackbox-ai-fee3724c` | Blackbox AI | — | — | — | Assistant/platform/CLI scope and first release unclear: **no**. |
| `cline-e0d25424` | Cline | — | — | — | Repository link alone does not establish the first public release of this identity: **no**. |
| `clova-studio-e224eeb3` | CLOVA Studio | — | — | — | Studio beta/GA unclear; HyperCLOVA X model date is different: **no**. |
| `copyai-289a49f0` | Copy.ai | — | ≈2020-10 | 14 | Previously undated; first anniversary statement supports launch month: **yes**. |
| `deepseek-chat-b3c3f2ff` | DeepSeek Chat | — | — | — | Original chat launch date unverified: **no**. |
| `deepseek-harness-cff5d891` | DeepSeek Harness | — | — | — | First preview day/month not established: **no**. |
| `eleven-sound-effects-fd3e24db` | Eleven Sound Effects | — | — | — | Date for the specific SFX API, distinct from web generator/model checkpoint, missing: **no**. |
| `eleven-speech-engine-5710146f` | Eleven Speech Engine | 2026-05-25 | — | 119 | Official product changelog establishes release: **yes**. |
| `fathom-76015fb2` | Fathom | — | — | — | Homepage has no verified first release date: **no**. |
| `firefliesai-b701b6b4` | Fireflies.ai | — | — | — | Homepage has no verified first release date: **no**. |
| `hugging-face-hub-82f7da3a` | Hugging Face Hub | — | — | — | Current Hub documentation does not establish its first public release: **no**. |
| `humanloop-a16219fe` | Humanloop | 2022-10-05 | — | 25 | Official public LLM platform launch, distinct from earlier preview: **yes**. |
| `ideogram-db27a255` | Ideogram | 2023-08-29 | — | 56 | Official public availability announcement: **yes**. |
| `jasper-90457ca9` | Jasper | — | — | — | Current product site does not establish the first release of this identity: **no**. |
| `kaggle-models-66ec6efe` | Kaggle Models | — | — | — | CLI documentation confirms a separate model-sharing platform, not its first release: **no**. |
| `midjourney-6047a08d` | Midjourney | — | — | — | Current site does not verify the exact or approximate launch of the Tool: **no**. |
| `minimax-speech-recognition-b5f156c4` | MiniMax Speech Recognition | — | — | — | Pricing documentation gives no first API release: **no**. |
| `pika-ea286fc1` | Pika | — | — | — | Current site gives no verified first release: **no**. |
| `playground-ai-7cda7b1d` | Playground AI | — | — | — | Brand versus legacy Board scope needs review; Board closure is not product launch: **no**. |
| `poe-bbc02ad7` | Poe | — | — | — | Initial beta/GA has not been sourced: **no**. |
| `researchrabbit-10836755` | ResearchRabbit | — | — | — | 2025 new-version announcement does not date first public release: **no**. |
| `runway-e34e79e1` | Runway | — | — | — | Company and Gen-1/Gen-2 dates do not establish original app launch: **no**. |
| `scale-ai-f930d93a` | Scale AI | — | — | — | Product scope unclear; 2016 company founding is not a Tool release: **no**. |
| `semantic-kernel-4a327f4f` | Semantic Kernel | 2023-03-17 | — | 40 | Official Microsoft retrospective identifies public repository date: **yes**. |
| `speechify-studio-76c7290f` | Speechify Studio | — | — | — | Studio's own first release is not established: **no**. |
| `youcom-56912a5d` | You.com | — | ≈2021-11 | 20 | Official release identifies public launch month, not day: **yes**. |

The six new official date sources are [Copy.ai](https://www.copy.ai/blog/series-a),
[ElevenLabs](https://elevenlabs.io/docs/changelog/2026/5/25),
[Humanloop](https://humanloop.com/blog/llm-launch),
[Ideogram](https://ideogram.ai/publicly-available),
[Microsoft](https://devblogs.microsoft.com/agent-framework/hello-world/), and
[You.com](https://you.com/resources/youdotcom-usd50m-series-b-press-release).
The month-only dates are approximate and are stored as such. Other official
entity links and the record-specific review reasons remain in the master.

## Reviewable Local sync diff

The canonical workbook backup is
`backups/catalog-count-csp-20260927/AIpediya_Model_Verification_Master_before.xlsx`
(SHA-256 `A337CC548DEE62FB15F88A254ABD1688F068F39F78EAF21654286C48BBC09CAD`).
The changed master SHA-256 is
`3F3FA042203712F30AE6649E4C3072A0FBBF77CB264195D5E576251237B79CC6`.
Its `Changelog` records the six date changes and 109 Public Number changes.
The exact machine-readable sync diff is
`artifacts/tool-count-csp-trial-plan.json`: **6 release-date changes and 109
number changes**, 0 publish/unpublish, 0 aliases/redirects/merges, 0 additions
or deletions. It also reports 110 pre-existing unsupported master/Local field
differences (16 public, 94 service/representation); they are not applied by
this sync. A repeated plan after trial apply and import had **0 supported
changes**.

The trial used an online SQLite backup at
`backups/catalog-count-csp-20260927/aipedia-trial.sqlite3` and a separate
copy of the workbook. `catalog_master check` is OK; `catalog_master qa` is PASS
on that trial (143 public, 122 numbered). Against the unchanged working Local,
QA correctly fails on 115 pending date/number differences. Working Local and
Production SQLite were not written. The working Local apply awaits acceptance
of this exact diff under `AGENTS.md` and `docs/CATALOG_MASTER.md`.

## CSP finding and code change

The current public response has `script-src 'self'`. Cloudflare inserts
`https://static.cloudflareinsights.com/beacon.min.js/v31…` into public HTML;
this URL is blocked by the public CSP. The injection is observed, but a
Cloudflare Dashboard setting and successful telemetry POST were not verified.
The code change is only in `catalog/middleware.py`: permit the exact
`beacon.min.js` path and its versioned subpath in `script-src`, and state
`connect-src 'self'` for the documented same-origin `/cdn-cgi/rum` endpoint.
No wildcard, `unsafe-inline`, `unsafe-eval` or other directive relaxation was
introduced. [Cloudflare FAQ](https://developers.cloudflare.com/web-analytics/faq/)
documents this CSP setup; the [CSP specification](https://www.w3.org/TR/CSP/)
defines the trailing-slash path-prefix match. `catalog/tests/test_csp.py`
asserts these exact security properties.

The trial browser loaded EN Models (321) and EN/RU Tools (143, 122 numbered,
21 undated) under the new CSP; no errors were recorded on the EN Models or
Tools tabs. The catalog test suite passed 303 tests (one skipped),
`manage.py check` found no issue, and `git diff --check` found no error.
The new Local history card is visible and its source link returned HTTP 200
after the report was added to the fixed Local source allowlist. Production
history access remains excluded by the existing environment gate.
Cloudflare edge injection cannot be verified in Local. After a separately
approved Production release, check the beacon load, actual `/cdn-cgi/rum`
request, console, strict CSP and Models/Tools UI in a real browser.
