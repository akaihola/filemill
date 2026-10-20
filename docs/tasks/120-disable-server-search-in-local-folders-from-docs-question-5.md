# Disable server search in local folders from docs question 5

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f#questions), question 5.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md?f); approved by the user on 2026-10-20 (question 5). Label: `steward`.

## Recommendation

Hide and disable server content search whenever Open Folder mounts a browser-owned tree, then restore it on return to the served tree.

## Work

1. First add failing browser coverage for entering local mode with a pending search and visible results.
2. Clear results, cancel pending work and prevent late responses or queued input timers from querying or repopulating results in local mode. Do not leave an action that dereferences the null router.
3. Restore served-tree search on leaving local mode and record the behavior in an ADR. Keep the shared core independent of server URLs where this focused change permits; local content search remains separate work.

## Acceptance

Tests cover both transitions, no local-mode /api/search request, no stale result activation, and working served-tree search after return. The test uses delayed responses and observable state.

## User review, 2026-10-20

Approved as the immediate wrong-tree search fix. The desired shared UI and browser-owned search capability are tracked separately in [130](130-give-served-and-browser-owned-folders-the-same-content-search.md?f); hiding local search is temporary, not the product goal.
