# Internal Local history screen — post-#015 follow-up

This Local-only task followed the Production PASS of Release #015 / v0.13.2.
The public #015 archive and Production route were not changed by this follow-up.

The Local `/ru/history/` route now serves the same generated document as the
standalone `timeline.html`, checking the embedded registry SHA-256 against
`docs/timeline.json`. A stale generated file returns 503 and does not rebuild
itself on page open. The internal view no longer extends the public site's
`base.html`: it has no catalog header/footer/search, collections, methodology
or privacy navigation. The two top state panels both show Release #015 /
v0.13.2 after the observed deploy. Its horizontal track contains exactly
Release #001–#015 in order; historical unnumbered Local/planned records stay
in the registry and their documents, without interrupting the release track.
The English route selects the English edition; the standalone file retains
its RU/EN switch. Both keep dark/light selection.

The Local route uses a no-network CSP matching the self-contained offline
artifact. General public-site CSP stays strict and unchanged. A mobile
top-bar overflow at 375 px was fixed. The malformed offline meta CSP
`form-action` source was removed so Chromium reports no console errors.

QA on the worktree's Local 18811: real Chromium 4/4 cases PASS (live and file,
1440 and 375 px). All 15 release cards were opened in each case, 60 openings
total. X, Escape, outside click, Enter/Space, focus restoration, RU/EN and
dark/light passed. Browser console errors and failed requests were zero.
Screenshots are in ignored `artifacts/history-015-live-1440.png`,
`history-015-live-375.png`, `history-015-panel-1440.png` and
`history-015-panel-375.png`; the desktop and mobile images were visually
inspected. The final catalog suite passed 341 tests with one expected skip,
including the new Local-history CSP regression; Local public check passed
33/33. Production history
continues to return 404 by the existing Local-only guard.

After fast-forwarding the ordinary Local checkout, the same history browser
gate passed **4/4 and 60/60 card openings** against its normal
`127.0.0.1:18810` service. The normal Local public check passed **33/33**;
the existing SQLite was kept and no migrations applied. The Local-only UI
source commit is `856d80ce0aa19550c0f7c7afdeba36250ee329bc`.

The previous 2026-09-26 offline-history owner visual acceptance remains an
historical fact about that version. No new owner visual approval is claimed
for this Local-only follow-up; its technical and visual checks were performed
by the executor under the owner's instruction to finish this task.
