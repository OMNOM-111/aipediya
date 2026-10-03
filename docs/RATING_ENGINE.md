# Rating Engine v1.0 — offline build and runtime contract

The canonical catalog master is the sole evidence source. Reference spreadsheets
are launch research/reference materials, not a second editable result database.
The five original configuration files and the additive owner_estimation_priors.json in data/rating/v1.0 are immutable and
checked by frozen-manifest.json. Scientific/Excel dependencies are Local-only.

## Commands (canonical Local)

Use .venv/Scripts/python.exe manage.py with the following arguments:

- `rating build --profile BALANCED` (also QUALITY_FIRST and ECONOMY): writes an
  immutable JSON snapshot, computed contexts sidecar and updates current.json.
- `rating check --profile BALANCED`: frozen artifacts, schema/eligibility/MCSE,
  content/parameter hashes and deterministic rebuild from current master.
- `rating report --profile BALANCED`: reads/validates the built snapshot and
  prints counts and the conservative ranked/bounded output.
- `rating bind-item --benchmark "approved new benchmark" --family approved_id
  --domain approved_id --item-kind ind`: only permitted Public=YES observations,
  ≥5 known frozen-theta models; ridge binding appended to rating_item_ledger.json.
  For Arena, use `--item-kind arena`; its new mean/SD are frozen in the ledger.
  Existing items, existing Arena transforms and Q basket are unchanged.
- `translate_rating`: existing configured translation provider, source/placeholder
  validation and incremental overlay for the other 20 locales; never reads keys
  or writes evidence/master. Do not use mocked translations as a real result.

Unknown items never influence configuration choice or caps. New observations
must be reviewed in master first. A new item does not join the frozen Q basket.
For a binding decision, archive the evidence and review the mapping. Daily
scoring must never call calibrate. Run master check/QA and all rating gates before
accepting rebuilt snapshots. Canonical write_workbook (import/refresh/editor) and
applied sync-local automatically rebuild all three profiles offline, validate
each, then atomically replace current.json. Editing XLSX externally requires the
ordinary refresh/sync pipeline; release QA blocks a stale master hash or missing
Model. Temporary research workbooks do not update the canonical snapshots.

## Runtime

catalog/rating/presentation.py reads data/rating/snapshots/current.json and the
immutable profile JSONs, cached by file modification stamp. Invalid/missing
snapshots fail closed. It never imports numpy/pandas/scipy/openpyxl or performs
IRT/Monte Carlo in a request. Data facts age relative to data_cutoff; UI may warn
about snapshot age relative to the clock, without changing scores or #1.

Snapshots contain only structured tooltip codes and parameters. RU/EN source
text lives in the original tooltip templates and rating/content.py; other
languages use data/rating/ui_translations.json through the existing context t().
Numeric intervals/dates are isolated in RTL. Benchmark names and technical IDs
are retained. Missing facts are None, not zero. Every PUBLISHED Model, regardless
of catalog status, has a numeric contextual rating and verified/partial/estimated
state. Tools never receive Model ratings. Qualified exact LLM reference records
retain their original context ranks; no cross-context rank is generated. The 24
original context states plus five additive specialist contexts are present.

## Owner Fix within Release #023

The original reference calculator is build_reference_snapshot; its 59 capability
calculations and 27 exact Overall results remain unchanged. Legacy NR/Provisional
and bounded fields are internal evidence diagnostics. The public aipediya_rating
is always numeric. The other 32 former bounded reference estimates stay within
their old bounds. Runtime never calculates a prior or reads Excel.

The additive frozen prior file records calibration master/reference hashes,
contextual means/SD, family anchors and source IDs. It was created once for the
owner correction, not by ordinary builds. Family predictions shrink towards the
context distribution and include predictive variance; they do not copy a parent
version's score. Contextual/global priors for missing capability, comparable price
or declared resource carry uncertainty, while facts remain unknown. The displayed
number is the tenth percentile with no extra missing-data penalty. All profile
weights and the five original reference artifacts are unchanged. Changing this
prior file requires a new explicitly versioned calibration decision.

Context routing uses canonical output modalities/tasks/model type before evidence.
Video with an audio track remains video. Specialized contexts without sufficient
gates stay Insufficient Data even though their Model estimates are numeric. These
fallbacks must not be interpreted as measured task performance. No Ready gate or
independent evidence is fabricated. Public independent records excluded from the
frozen scale remain visible as catalog evidence and do not become scoring inputs.

Release QA checks all three profile snapshots against actual published Model IDs,
excludes Tool IDs, checks master/parameter hashes, finite scores, confidence/gaps,
contexts and record snapshot IDs. An unknown model type fails the build. The
automatic-update regression adds a zero-evidence Model to an isolated copy through
the canonical writer: 344 numeric records, all three profiles, stable old scores
and unchanged prior bytes. No synthetic record enters the real master or Local DB.

## Provenance and QA

Launch report: docs/history/2026-10-03-rating-engine-v1-023.md.
Sources, accepted original/compatible reference, full logs, master comparison,
intermediate snapshots, tooling and browser evidence are preserved under ignored
artifacts/rating-v1-023. Never put Local SQLite or scientific build dependencies
in a production data overwrite. Production requires separate owner authorization
and the unchanged docs/RELEASE.md procedure.
