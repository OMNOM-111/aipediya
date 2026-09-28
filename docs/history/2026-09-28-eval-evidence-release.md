# Evaluation Evidence — Release #012 / v0.12.0 (2026-09-28)

- Card: `EVAL-EVIDENCE-AUDIT-2026-09-27` (same existing Timeline card).
- Owner approval: handoff to Codex on 2026-09-28 explicitly accepted the latest tested Local state and authorized its Production publication. Handoff reason: Claude limit.
- Previous Production: `9ddba83c176aa3f6793362d6345b797c76ddf987` (`release-2026-09-27-catalog-325-147`).
- Deployed candidate/release id: `d349d6de42cbe49dd55134a7ca792f6bce85ab7e`; archive `aipedia-code-d349d6de42cb.zip`, SHA-256 `faf755db0497b0e3c718ab3b655edb46d51499936a7f247d8e93a280ed0b3127`.
- Git commit/tag: `655fb90185b76a8597b53a5829db4e8e8c63dc97` / `release-2026-09-28-eval-evidence`. The candidate was built from `main` HEAD `2fd442cb487c2c9ff2ea2acc00070a0c17164f47` plus 40 explicit file overlays. All 356 archive files that belong in Git match this tag after normal Git text normalization (0 mismatches); `BUILD.json` and `MANIFEST.json` are generated archive metadata. The deployed release id remains `d349d6de42cb...`.
- Deployment: `tools/server.py` through configured `aipediya-prod`; server program `aipedia` only. Deploy time: 2026-09-28 16:37:24 UTC. Pre-deploy rollback backup: `/srv/aipedia/backups/aipedia-before-code-20260928T163724Z.sqlite3`; previous app: `/srv/aipedia/releases/before-code-20260928T163724Z`. Separate preflight trial backup: `/srv/aipedia/backups/aipedia-preflight-eval-evidence-20260928T163608Z.sqlite3`.

## Exact data delta

The plan was built against a fresh online snapshot of the live Production database (SHA-256 `896ccef92ffa70c02f30069a138ffece7d1e3981d83ce4076c12c6f0e4b2d642`), not against intermediate Local audit counts. Plan: `data/release/eval-evidence-20260928/catalog_plan.json`, SHA-256 `6673697d432f80ffbfe9a4b45145a2566e6373604e4bd2358ad22dcdd92e17a3`.

| Table | Before | After | Explanation |
| --- | ---: | ---: | --- |
| `catalog_evaluation` | 906 | 5,010 | 4,104 new rows; 16 existing visibility changes |
| Public evaluations | 851 | 2,741 | Explicit developer-result publication plus independent/research rules |
| `catalog_source` | 436 | 999 | 563 sources required by new evaluations |
| `catalog_benchmark` | 35 | 982 | 947 benchmarks required by new evaluations |
| Published Models / Tools | 325 / 147 | 325 / 147 | No identity, number, date or publication changes |

`verify-release` compared the live database with the rollback backup and found no other factual table changes. Offers, Access, Models, Tools, translations, pricing and publication state were unchanged. No Local SQLite was uploaded.

## QA evidence

- Local: master `refresh`/`check`/`qa` PASS; `manage.py check` 0 issues; 315 catalog tests OK (1 skip); SQLite integrity `ok`, FK 0; repeat sync plan 0 writes. Nine-card browser smoke across RU/EN/ar, desktop/phone, themes; no page overflow or console errors.
- Isolated archive: 357 manifest files, SQLite/secrets 0; unpacked code passed 315 tests (1 skip). Local trial on a copy of the live Production snapshot applied 4,120 writes, repeat plan 0, QA PASS, integrity `ok`, FK 0.
- Server preflight: PASS on an online Production backup. Trial produced 5,010 evaluations and 2,741 public evaluations, 325/147 published records, 0 publication changes, integrity `ok`, FK 0; Offers/Access/Models/Tools unchanged. Server deploy dry-run PASS.
- Post-deploy: `/healthz` returned `d349d6de42cb...`, `aipedia` RUNNING; `verify-release` PASS, integrity `ok`, FK 0; `catalog_master qa --production` PASS; `gsd_public_check` 34/34 PASS. Public Chrome smoke: twelve RU/EN/ar/fa/de/zh-hans cases, desktop/phone, RTL, dark/light, no horizontal overflow or console errors. Public MTEB block showed three rows plus 123 in an expandable section; expansion and collapse worked.
- Full `gsd_production_qa`: 1,657/1,657 PASS, 697 public requests, 10,396 sitemap locs, 472 hidden model slugs checked, 0 failures. Report: `artifacts/catalog-release-20260927/gsd-production-qa.json`.

## Accepted metrics

325 published Models; 159/325 (48.9%) with public independent evidence; 280/325 (86.2%) with any verified numerical evaluation; 50 independent + developer; 91 developer-only; 17 research-only; 45 without numerical results; 17 exact-version unresolved (8 exact-version-not-found and 9 identity-ambiguous). Every published model has an evaluation status. These are the accepted master metrics; the UI keeps developer scores separate from independent evidence and does not expose research-only scores.

## Existing limitation

The master-to-Production sync diagnostic reports 1,067 unsupported differences (971 public fields, 96 service/representation fields), whereas working Local reports 113. The **pre-deploy** Production snapshot showed the same 1,067 differences. They were not created by this release; they concern unsupported Offers, Origins, Tool Platforms and other pre-existing fields. The evaluation release neither changed them nor proved full byte-for-byte equivalence of all Local and Production data. A separate scoped plan is required before any such data change.

Known evidence gaps carried from the accepted Local audit include Nova 2 Pro report retrieval, GPT Transcribe evidence available only in an X post, and Apertus 70B's pending report. No new benchmark research was part of this release.
