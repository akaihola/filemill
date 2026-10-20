# Disable server search in local folders from docs question 5

Source: [109], question 5.
Proposed by [115]; approved by the user on 2026-10-20 (question 5). Label: `steward`.

## Recommendation

Hide and disable server content search whenever Open Folder mounts a browser-owned tree, then restore it on return to the served tree.

## Work

1. First add failing browser coverage for entering local mode with a pending search and visible results.
2. Clear results, cancel pending work and prevent late responses or queued input timers from querying or repopulating results in local mode. Do not leave an action that dereferences the null router.
3. Restore served-tree search on leaving local mode and record the behavior in an ADR. Keep the shared core independent of server URLs where this focused change permits; local content search remains separate work.

## Acceptance

Tests cover both transitions, no local-mode /api/search request, no stale result activation, and working served-tree search after return. The test uses delayed responses and observable state.

## User review, 2026-10-20

Approved as the immediate wrong-tree search fix. The desired shared UI and browser-owned search capability are tracked separately in [130]; hiding local search is temporary, not the product goal.

## Implementation, 2026-10-20

The server adapter supplies a search provider to the shared UI. A local mount
removes it before replacing the filesystem or router. This clears the input
and results, hides and disables search, cancels its timer and aborts its
request. Aborted requests cannot publish success or error responses. Old
result buttons cannot navigate. A served mount restores a fresh search.
See [ADR 0091].

The browser regression covers a queued input timer, delayed success and error
responses, a late response after return, and a retained result button. It
checks abort state, request counts, cleared UI and successful result navigation
after return. The first run failed because search remained visible in local mode.

[109]: 109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions
[115]: 115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md
[130]: 130-give-served-and-browser-owned-folders-the-same-content-search.md
[ADR 0091]: ../adr/0091-server-search-stops-at-local-folder-mounts.md
