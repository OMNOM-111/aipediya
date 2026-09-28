# Reconciliation / cleanup #013 — 28.09.2026

Release `release-2026-09-28-reconciliation-cleanup`, `v0.13.0`. This report records the read-only Production baseline and the Local reconciliation. Production result is recorded separately after release QA.

## Baseline and decisions

The original audit found 1,067 `unsupported` items: 954 comparisons of unrelated SQLite integer primary keys and 113 substantive differences (13 potentially useful, 93 research/service fields, one hidden duplicate, six requiring review). The baseline and provenance are in `2026-09-28-unsupported-master-production-audit.md`. Production snapshot: `artifacts/catalog-release-20260927/production-baseline-20260928T193212Z.sqlite3` (SHA-256 `8393660832892e1f422358be892b86bb2050eba9745de82b6b972da093837cce`). Master and Local before state are in ignored `backups/reconciliation-cleanup-20260928/`.

`master_sync` now compares aux rows by natural/composite key before falling back to an integer PK. The repeat baseline plan has **zero unsupported**, 13 supported writes, and 513 explicitly intentional Master-only or storage-representation differences. The latter total includes 402 evaluation scores that SQLite stores rounded to three decimal places; the old diagnostic had missed them. It does not represent 513 records to publish.

| Difference | Count | Decision and reason |
| --- | ---: | --- |
| Access Service URL | 11 | APPLY: replace generic service/pricing links with exact official page or model card; clone shared Service where needed. All eleven URLs were checked against official pages and in Local cards. |
| Offers service provider | 1 shared Service | APPLY: Kimi API operator is Moonshot AI, consistent with Master Offers and [Moonshot AI](https://www.moonshot.ai/). Also corrected three stale Master Access provider cells with Changelog entries. |
| Furniture Assembly benchmark category | 1 shared Benchmark | APPLY: `image` is the correct benchmark category because [Epoch AI](https://epoch.ai/benchmarks/furniture-assembly) describes photographs and manuals; corrected three inconsistent Master Evaluation cells with Changelog entries. |
| Access Source URL | 46 | MASTER_ONLY: evidence link, distinct from the public Service URL. |
| Offers Billing Unit | 48 | MASTER_ONLY: editorial unit label when a standard unit code already determines the public display. |
| Evaluation Score precision | 402 | MASTER_ONLY representation: Master retains source precision; SQLite `DecimalField` stores three decimal places. All 402 compare equal after that rounding. |
| Origins Position | 4 | MASTER_ONLY representation: Master is 1-based, database is 0-based. |
| Tool Platforms Source URL | 3 | MASTER_ONLY: platform evidence URL. |
| Source Title, Models and Tools | 4 | MASTER_ONLY shared Source bibliography: Qwen3Guard Stream 4B/8B; Antigravity CLI; Semantic Kernel. Public Source URL remains unchanged. |
| Tools Supported Models | 4 | MASTER_ONLY free text: GitHub Copilot, Alice AI Pro Business, Qwen Intelligence, Yandex AI Studio. These are dynamic/customer-selected scopes, without exact stable Model Record IDs. |
| Hidden Evaluation Source Model | 1 | MASTER_ONLY: previously hidden superseded duplicate, marked `superseded_duplicate_of`; remains out of public results and historical evidence is preserved. |
| Pending MiniMax Offer row | 1 | MASTER_ONLY research: no stable Research Key or verified currency; `verification_pending`, not a public `$0` price. |

The first 19 items requiring individual decision are the eleven Access URLs (APPLY), two Tools Source Titles (MASTER_ONLY), two Qwen3Guard Source Titles (MASTER_ONLY), and four Tools Supported Models (MASTER_ONLY). `UNRESOLVED = 0`. The original 93 research/service warnings were reviewed by type. There is no evidence of an earlier implementation task for the 1,067 warning cleanup; the audit card and this #013 release are the explicit follow-up.

## Local and trial evidence

- Master backup SHA-256 `014c9f23b60a6182664f7d4cddc1841d6b7dc2f2c0f1a867cbec5f23035f5110`; Local backup SHA-256 `7d1b9196fd69b1dbba8101daa67f69fc4c6b997355e51fcb6b88a86e5dc02786`.
- Trial on copied Local: 13 changes, `catalog_master qa` PASS. Trial on copied Production baseline: release plan 13 writes; `apply-plan` pending → applied; repeated call idempotent; `catalog_master qa` PASS.
- Working Local: 13 changes; 325 Models / 147 Tools, `catalog_master refresh` renumbered 0, `check` OK, `qa` PASS, repeat plan 0 writes / 0 unsupported; SQLite integrity `ok`, foreign-key violations 0, Django `check` 0 issues. Full catalog suite: 327 tests OK, one Windows-only skip.
- Browser Local: affected eleven Access URLs present in their cards (nine Models, two Tools), Models/Tools counts 325/147, Checks tab, English, Russian, Arabic RTL, dark/light, 375 px mobile and 1440 px desktop without document overflow; console errors 0. No unrelated catalog data was changed.

## Working-tree inventory

- Existing official history reports for timeline status and traffic analytics, old `data/release/v013/` candidate files, and the original GSD task brief were retained in `docs/history/`/release data and committed as project history. The old v013 plan was restored byte-for-byte from its candidate archive (SHA-256 `fd6281a04eb0962381cc9651374a90f3d69f99fc5276be6257e0b78cdace1c13`); the new Release #013 plan lives separately in `data/release/reconciliation-20260928/`.
- Four Windows cache copies formerly under literal `%SystemDrive%/` were moved without deletion to ignored `artifacts/reconciliation-cleanup-20260928/quarantine/%SystemDrive%/` after source/hash inspection.
- `.claude/launch.json`, the local History shortcut, and `data/research/` remain at their original paths and are explicitly Git-ignored as local user data. Backup and trial SQLite remain ignored in `backups/` and `artifacts/`.
- Only identified temporary XLSX rebuild files may be removed; unknown untracked user files are retained and classified.

## Release closure

Production baseline, preflight, backup, exact archive/deploy, public QA, release tag, final commit and actual state are appended after the release. Timeline remains `review` until Public QA passes.
