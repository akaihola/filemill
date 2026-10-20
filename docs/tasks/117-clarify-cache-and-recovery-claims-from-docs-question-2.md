# Clarify cache and recovery claims from docs question 2

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 2.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Change the documentation, keeping A5 open. Distinguish uncached API reads from cached embedded resources, and distinguish the worker's navigation recovery page from the shell's failed-mount retry.

## Work

1. Correct A5 and server/README.md: /api/raw reads are network-only; same-origin embedded resources outside /api/ can return cached bytes. Keep the cache-isolation and non-navigation offline-miss findings open.
2. Explain that a controlling server worker supplies recovery for failed non-API navigations without a previously cached destination; a first visit without a worker cannot do so. Retain the separate shell mount-retry path recorded in ADR 0063.
3. Clarify SECURITY.md's stale-token wording using ADR 0081: an open or stored shell can retain an old token after restart, but normal navigation does not use the worker's cache.

## Acceptance

The text distinguishes all three read paths and both retry paths without claiming A5 is fixed. Cite sw.js, HTTP.blob and the PWA/token tests; run the server docs, PWA and mutation-policy tests. If behavioral proof is missing, report the gap rather than describing a source check as an end-to-end test.
