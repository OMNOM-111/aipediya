# Universal daily catalog release tooling — Release #017

Status: DONE in Local. Production is still Release #016; this technical package
does not require a separate Production deploy.

GitHub: commit `b6f0178741df7ad5425f0f061c2ed2185aa08dc3` was pushed to
`origin/main` on 2026-09-29. No Production tag was created.

Owner: PASS. The owner accepted Release #017 on 2026-09-29 and confirmed that
the universal daily catalog release mechanism is implemented, verified and
accepted without Production publication.

## Scope

Make the existing AIpediya release tooling universal for future daily catalog
updates. A future catalog package must derive its Production baseline, expected
before/after counts, created and updated records, and allowed related-table
changes from the current Production snapshot, Timeline, canonical master output
and the concrete `catalog_plan`, not from a new hardcoded Release # or fixed
Models/Tools counts.

## Current implementation notes

- `tools/server_release_preflight.py` validates catalog-plan trials dynamically:
  plan scope, final published/numbered counts, existing-row changes and created
  critical rows are derived from the concrete `catalog_plan`. Historical #012,
  #013 and #016 catalog plans use the same path; future catalog plans for #018+
  no longer require a Python allowlist entry.
- `tools/server_compare.py` discovers the deployed `catalog_plan` by release
  id/tag and verifies the factual database diff from that plan. Code-only
  releases remain strict: any factual catalog table change fails.
- `tools/server.py catalog` checks integrity, FK count, continuous numbering and
  published==numbered without fixed Models/Tools totals.

Hardcoded assumptions removed from runtime release tooling: `sequence == 16`,
Release #016 plan-count branch, 325/147 predecessor counts, 331/149 final counts,
fixed evaluation/source/benchmark totals for post-#013 releases, and the server
catalog check that required exactly 331 Models / 149 Tools.

## QA

PASS in Local.

- Focused release/history regression:
  `manage.py test catalog.tests.test_server_access_contract catalog.tests.test_release_history catalog.tests.test_product_history --settings=aipedia.test_settings`
  — 20 tests PASS.
- Full Local catalog suite:
  `manage.py test catalog --settings=aipedia.test_settings` — 344 tests PASS,
  1 skip.
- `tools/release_history.py` — PASS.
- `tools/build_product_history.py` rebuilt `timeline.html` from the same
  `docs/timeline.json` card.

Universal catalog-plan trials covered in tests:

- future catalog plan sequence without a new release-number allowlist;
- plan with created records and computed final counts;
- update of an existing record;
- several related changes (`access_service`, `service_provider`,
  `benchmark_category`, `org_country`);
- foreign existing-row/table changes blocked;
- wrong final Production count blocked;
- already-applied plan state accepted as idempotent;
- code-only release comparison remains strict.

## Production

Not published. The current public site remains Daily Catalog Update Release #016
with 331 Models / 149 Tools.

## Next daily catalog update

The next daily catalog update can use this mechanism without changing release
tooling for the next Release # or for specific Models/Tools counts.