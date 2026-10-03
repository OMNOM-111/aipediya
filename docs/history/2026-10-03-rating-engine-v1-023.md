# Release #023 · v0.20.0 — AIpediya Rating Engine v1.0

READY FOR OWNER REVIEW — PRODUCTION NOT TOUCHED.

Timeline: `RATING-ENGINE-V1-2026-10-03`. Registered before implementation on clean
`main`, baseline `51a48075a7be2ba62d2c47d208c8c6d1ba7c00a7`.
Owner approval is pending. This is the requested Local-only implementation;
no archive/deploy/server/Production QA operation was performed.

## Result

The existing rating column and model panel now display conservative Overall,
tier, rank or global rank interval, Precision and Support separately, structured
evidence audits and three usage profiles. Methodology and all rating labels,
tooltips and context states use the existing 22-locale system. Frozen JSON is pinned to LF by .gitattributes, preserving exact source hashes
after a Windows checkout with core.autocrlf=true. Runtime loads
validated JSON only; the scientific stack is in requirements-dev.txt.

The offline scorer uses the Reference Pack's frozen items, Arena transforms,
Q basket, caps and anchors. New permitted items can be bound by an append-only
ridge ledger with at least five frozen-theta anchor models, then rebuilt.
Unknown items are excluded before caps and configuration choice. Source
invalidation/permission expiry excludes evidence. Stale facts warn without a
score penalty; expired required inputs become bounded before Monte Carlo and
ranking. Snapshot age warns after 7/14 days without request-time rescoring.
See `docs/RATING_ENGINE.md` for commands and file contracts.

## Snapshot

- Methodology: AIpediya Rating v1.0
- ID: `LLM.OVERALL@BALANCED-v1.0-2026-10-02-66c30305a6d9`
- Data cutoff: 2026-10-02; created_at is the only build clock field.
- Master SHA-256: `5174bce98bb5578868f9e0c41cfbb05c2940c3465b3247e2a81062becdd2382e`
- Content SHA-256: `66c30305a6d9e7b4cfbaf358e7b62af5fbb134bcb36aed20bd8a8dad6c811c6e`
- Params hash: `fd1153f496cc43d47ac4f8be71a57998c636429a5d28ff19df86b61a686d1e7a`
- Ledger SHA-256: `81d7a9291fb4bca76cf943f85d5540ce0c04394713cd68be5611280944be019b`
- RNG: PCG64, seed 20261003, 6000 draws.
- Counts: **59 Rated / 27 exact / 32 bounded / 66 Provisional / 162 NR**.
- Badge: none. Exact reason: `leaders_statistically_indistinguishable`.
  The largest P(#1) is below 0.50. Table rank #1 is a numerical Overall rank,
  not an awarded #1 badge.

| Frontier candidate | P(#1) | MCSE |
| --- | ---: | ---: |
| GPT-6 Astra | 0.4363 | 0.0064 |
| GPT-5.6 Sol | 0.1543 | 0.0047 |
| Claude Opus 5 | 0.0917 | 0.0037 |

| Profile | Snapshot ID | Content SHA-256 |
| --- | --- | --- |
| BALANCED | `LLM.OVERALL@BALANCED-v1.0-2026-10-02-66c30305a6d9` | `66c30305a6d9e7b4cfbaf358e7b62af5fbb134bcb36aed20bd8a8dad6c811c6e` |
| QUALITY_FIRST | `LLM.OVERALL@QUALITY_FIRST-v1.0-2026-10-02-6846641be669` | `6846641be669179ce15afc2feecb620a790f2d4ebf56270f190cbc7ce03339e3` |
| ECONOMY | `LLM.OVERALL@ECONOMY-v1.0-2026-10-02-766387eeaa06` | `766387eeaa0682632169c00d21b0e32b72b7bae2373081bcd7102a8108a113f6` |

## Computed context statuses

Only LLM.OVERALL has a public numerical rating at launch.

| Context | State |
| --- | --- |
| `LLM.OVERALL` | Ready (условно) |
| `LLM.MATH` | Beta |
| `LLM.LOGIC` | Beta |
| `LLM.CODE` | Insufficient Data |
| `LLM.AGENTS` | Insufficient Data |
| `LLM.LONGDOC` | Insufficient Data |
| `LLM.KNOWLEDGE` | Insufficient Data |
| `LLM.SCIENCE` | Insufficient Data |
| `LLM.VISION` | Insufficient Data |
| `LLM.CHAT` | Insufficient Data |
| `LLM.FORECAST` | Insufficient Data |
| `LLM.MULTILINGUAL` | Insufficient Data |
| `STT.TRANSCRIBE` | Insufficient Data |
| `STT.STREAMING` | Insufficient Data |
| `TTS.NARRATION` | Insufficient Data |
| `TTS.REALTIME` | Insufficient Data |
| `VOICE.AGENT` | Insufficient Data |
| `IMG.GEN` | Insufficient Data |
| `IMG.EDIT` | Insufficient Data |
| `VID.GEN` | Insufficient Data |
| `EMB.RETRIEVAL` | Insufficient Data |
| `DOC.OCR` | Insufficient Data |
| `AUD.MUSIC` | Out of scope v1 |
| `SAFETY.CLASSIFIER` | Out of scope v1 |

Math and Logic fail distinctiveness and remain Beta; CODE evidence from
research-only/Public=NO sources is not promoted. The other evidence gaps are
intentional launch limitations, not unfinished implementation.

## Reference acceptance

Original reference sources are preserved. The executable reference needed an
explicit numeric missing-value dtype for normalized_percent; pandas object
None versus numeric NaN otherwise suppressed seven display-only developer
records. After that compatibility repair, all model classifications, ranks,
gates, context states and numerical outputs match expected; maximum numerical
difference is **1.4210854715202004e-14** (Windows floating-point last bits).
No numerical field was manually adjusted.

The expected content hash therefore is not used as a byte-level hash of the
Windows adaptation. The production-shaped snapshot also adds structured
family/domain/runner metadata, schema/ledger metadata and required fact expiry
handling. Its own deterministic hashes are checked independently.

Reference master SHA: `7bbb0a5c55f40a3b3cbf3e344e2d03fb2418962b249a98853b359b7213c6d3c0`.
Expected snapshot: `LLM.OVERALL@BALANCED-v1.0-2026-10-02-91f01275e857`.
Compatible reference snapshot: `LLM.OVERALL@BALANCED-v1.0-2026-10-02-4e58a07ed2b3`.
Acceptance evidence: `artifacts/rating-v1-023/reference-acceptance.json`.
Reference invariants: 6/6 PASS.

The frozen executable includes three developer Cybench observations. They retain
sigma 1.8 and developer caps; they never count as independent organizations or
satisfy independent gates. This preserves executable precedence over the Closure
workbook's prose claiming no developer contribution.

## Local QA

- Master refresh/check: OK; renumbered 0. Only Meta's Computed UTC changed;
  all catalog, evidence and related data cells are unchanged.
- Catalog QA: PASS, no errors; 17 existing provenance warnings about release
  evidence URLs, retained in the canonical quality queue.
- Sync-local dry-run: intentional master-only bibliography/conditions/related
  rows and nonpublic research stock; no catalog writes applied.
- Full Django suite: **397 tests OK, 1 existing Windows fcntl skip**, 114.271s.
- Rating unit/regression tests: 25; frozen reference, unknown-before-caps,
  Arena z, free API, early evidence, bounds/global rank, context status,
  MCSE/no badge, 6000→12000 threshold, clock independence, fact expiry,
  revoked permission, append-only binding, i18n/RTL and runtime imports.
- Django check, migration check, JS syntax and diff whitespace: PASS.
- Deterministic rebuild/check: all three profiles PASS; Q does not change.
- Browser: 32 combinations RU/EN/zh-Hans/AR × 1440/375 × four states,
  both themes, model panel, hover, keyboard focus and mobile click.
  The in-app browser does not expose raw touch dispatch; the 375 px audit button
  was tested by click through the same mobile activation handler. A physical-device
  touch gesture is not claimed. Tooltip bounds and horizontal overflow: 0 failures.
  Escape closes the audit
  and retains the model panel; fixed native-popover hit-test restoration.
  Profile navigation and Back/Forward restore state. Astra's Q is 77.3% across
  profiles; Overall is 63.1 Balanced, 70.7 Quality first, 47.8 Economy.
  Methodology has all 24 contexts, including RTL on 375 px.
- Console errors: 0; critical network errors: 0 (102 observed responses).

Saved evidence is under `artifacts/rating-v1-023/`; source copies and intermediate
snapshots/tooling are preserved there and ignored by Git. Final snapshots only
remain under `data/rating/snapshots/`. Browser screenshots and JSON are in
`artifacts/rating-v1-023/browser/`.

## File provenance and environment

All changes started from a clean checkout. The master change is refresh metadata;
engine/config/snapshots/translations/UI/tests/docs are authored for #023. Existing
catalog publication state, Record IDs, numbers and Local SQLite records are
preserved. There was no forgotten/unexplained pre-existing WIP.

Canonical Local: http://127.0.0.1:18810/ru/; repository root/main;
`data/local/aipedia.sqlite3`, 343 published Models / 158 Tools, active 287/153.
One loopback listener on 18810; 18811–18819 have no task preview server.
The Local stop wrapper briefly reports an exit-check race after Stop-Process;
the identified PID/listener then exits. No unrelated process was stopped.

Production remains the recorded #022 baseline (v0.19.0 / f46cc435c10e), not
reverified live here. Stale #021 current-state prose in PRODUCT_HISTORY was
corrected to the already-recorded #022 evidence; historical releases are intact.
The lower Russian current-release block in RELEASE.md still labelled #020,
although its leading English block correctly recorded #022. The stale caption
was retained as historical #020 and a matching #022 current pointer added;
AI_CONTEXT now reports the already-documented #022, with no live verification.
GitHub commit/tag and final clean state are recorded in EXECUTION_STATE.

## Remaining tasks

- `RATING-023-OWNER-REVIEW`: owner visually reviews this Local build and records
  acceptance or concrete feedback. Local ✓ / Owner — / Production —.
- A Production phase may begin only after a separate explicit owner command for
  this concrete commit/tag under docs/RELEASE.md. No server action is pending
  inside this implementation task.
- `RATING-V1-EVIDENCE-EXPANSION`: future separate research task for CODE source
  permissions, additional independent runners and reproducible AIpediya tests;
  intake first into master, bind eligible items, rebuild, rerun gates/QA.
- The existing 17 date-provenance warnings remain in the catalog quality queue;
  resolve official/independent dated evidence in a future catalog task, without
  replacing unknowns by invented data.

## Input provenance

| Input | SHA-256 |
| --- | --- |
| AIpediya_Rating_v1.0_Reference_Pack.zip | `ba5b3f235aa5ffefbf8c386d7a01e493aae9cdf6c3e912f2133a227a61ed6f7f` |
| AIpediya_Research_Closure_Report_v1.0_2026-10-03.xlsx | `da91a3bd2446bacb11cbd8940b88eb63ccc4376843b14fca14b861b442c43254` |
| AIpediya_Rating_Context_Registry_v1.2.xlsx | `b4caf8fa8a0a51dde37a4a11045f3148db1857f55d4a623bab1ffa72ea2aba47` |
| AIpediya_LLM.CODE_Evidence_Source_Audit_2026-10-03.xlsx | `268120fe39ff041d9def3b5cb2535ab5c3c3b1020122ddd28b315a370f8f4684` |
| AIpediya_LLM_Overall_DataSupport_run_2026-10-03.xlsx | `52e646c6f2ebcb8a17774380a7cca92230173d48a254360d795b5df1faf240ae` |
| master-before.xlsx | `7bbb0a5c55f40a3b3cbf3e344e2d03fb2418962b249a98853b359b7213c6d3c0` |
