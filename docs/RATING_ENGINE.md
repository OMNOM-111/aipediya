# Rating Engine v1.0 — offline build and runtime contract

The canonical catalog master is the sole evidence source. Reference spreadsheets
are launch research/reference materials, not a second editable result database.
The five original configuration files in data/rating/v1.0 are immutable and
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
accepting rebuilt snapshots; a changed master should invalidate deterministic
check until a new snapshot is deliberately built.

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
are retained. Missing values are None, not zero. Only LLM.OVERALL shows numerical
ratings; all 24 context states are computed on every build.

## Provenance and QA

Launch report: docs/history/2026-10-03-rating-engine-v1-023.md.
Sources, accepted original/compatible reference, full logs, master comparison,
intermediate snapshots, tooling and browser evidence are preserved under ignored
artifacts/rating-v1-023. Never put Local SQLite or scientific build dependencies
in a production data overwrite. Production requires separate owner authorization
and the unchanged docs/RELEASE.md procedure.
