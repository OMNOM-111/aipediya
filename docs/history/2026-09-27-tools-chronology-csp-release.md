# Tools chronology and Cloudflare CSP — Production release, 2026-09-27

Owner approved the exact Local state and release of commit
`cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`. Previous Production was
`aa48e11bad7326340463654e33ba5e89769042b9`. Code archive:
`artifacts/code-release/aipedia-code-cf4ac9a33f8d.zip`, SHA-256
`8af0a16c7044a8208e5ac38aa1d6a156621c670ccbaeb17640895c7f6e46c7a0`.
The 333-file archive contains no SQLite or secret. No Local DB was copied.
The annotated tag `release-2026-09-27-tools-chronology-csp` points to the
published commit; release docs and the server-access contract were committed
as `c9ebe7b` and pushed to `origin/main` with the tag.

## Server trial and deployment

- Canonical `python tools/server.py preflight` via `aipediya-prod`: PASS;
  hostname `1cdfd28f030e`, remote user `stratforge`, only service `aipedia`
  RUNNING, AIpediya root/DB/tooling present. Strict known-host verification.
- Upload to `/tmp/aipedia-code-cf4ac9a33f8d-8af0a16c7044.zip`: remote
  SHA-256 matches. Server release preflight online-backed-up Production SQLite
  to `/srv/aipedia/backups/aipedia-preflight-tools-csp-20260927T191301Z.sqlite3`.
  Trial `migrate` (none), `catalog_master apply-plan` dry-run then apply: 167
  writes; publication-state dry-run: 0 Models / 0 Tools flag changes. Trial
  SQLite integrity `ok`, foreign keys 0. Trial Tool field diff was exactly
  140 `public_number`, 4 `released`, 23 `approx_released`, 23
  `approx_precision`; Model rows were unchanged.
- Deploy dry-run PASS. Actual `tools/deploy_code_release.py` made
  `/srv/aipedia/backups/aipedia-before-code-20260927T191327Z.sqlite3`, stopped
  only `aipedia`, migrated with no schema changes, applied the same 167 writes,
  applied publication manifest with 0 flag changes, switched app, started only
  `aipedia`, and verified origin `/healthz` against the exact commit. Post-deploy
  backup: `/srv/aipedia/backups/aipedia-after-code-20260927T191327Z.sqlite3`;
  previous app: `/srv/aipedia/releases/before-code-20260927T191327Z`.

## Production verification

- Live server SQLite: 143 published Tools, 143 numbered, range 1–143 without
  duplicate or gap; 60 exact, 83 approximate, 0 undated. 321 published Models.
  `PRAGMA integrity_check=ok`; foreign-key violations 0. Production service
  RUNNING; `/healthz` release `cf4ac9a33f8d4467510d6b76ebe115ce7e1803d3`.
- Read-only `server.py verify-release` compared live SQLite with the
  pre-deploy online backup. The only changed factual table is `catalog_tool`;
  changed columns and counts are exactly 140 numbers, 4 exact dates, 23
  approximate dates and 23 precisions. Model rows, offers, evaluations,
  descriptions and other factual catalog tables are unchanged.
- Public browser: RU and EN Tools each show 143 records, oldest 001→143 and
  newest 143→001, with `≈` displayed for approximate dates. RU/EN Models
  each show 321. Browser console reported no warning/error during checks.
- Public HTTP CSP: `script-src 'self'` plus exact Cloudflare beacon URL and
  versioned path prefix, `connect-src 'self'`; no wildcard or inline/eval
  relaxation. Real browser network observed versioned beacon HTTP 200 and
  same-origin `/cdn-cgi/rum` HTTP 204, with no CSP load failure.
- `catalog_master check`: OK; `catalog_master qa --production`: PASS.
  Local `manage.py check`: 0 issues; full catalog suite: 308 tests OK, one
  expected skip. GSD public check: 34/34 PASS; full GSD Production QA:
  1,657/1,657 PASS across 697 requests, no failures. No rollback required.

## Scope and access contract

The release archive is the approved Tools/CSP code and data plan. The new
`tools/server.py`, server preflight script, SSH config template, regression
tests, and access documentation were added after the archive was built and
do not alter this published application release. The workstation user SSH
config contains the `aipediya-prod` alias, without secret material. AIpediya
server scope stayed within `/srv/aipedia`, `/tmp/aipedia-*`, and its own service.
