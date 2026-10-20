---
depends-on: [120]
---

# Give served and browser-owned folders the same content search

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f), question 5.
User review, 2026-10-20. Label: `steward`.

## Decision

Approved direction: the search control, results and interaction should be identical for served content and browser-owned folders. The temporary hiding fix in [120] remains necessary until this capability is implemented.

[120]: 120-disable-server-search-in-local-folders-from-docs-question-5.md?f

## Work

1. Use one shared search UI with equivalent query behavior, focused-folder scope, result presentation, keyboard activation, cancellation and empty/error states.

2. Put the search operation behind an adapter capability. The server uses its content search and the browser reads only its granted folder; local search must not upload file contents or call the server's search endpoint.

3. Bound traversal, reads and returned matches, and indicate partial results. Invalidate pending searches when the root or query changes. Open local results through navigation without requiring a URL router.

4. Start with failing browser checks for both sources and mode transitions. Document the capability and any measured limits in the behavior ADR.

## Acceptance

Equivalent fixtures produce equivalent visible results and interactions in both modes. Tests show no server search request for a browser-owned folder and no stale results after switching roots. The search control is restored in local mode once it has real local functionality.
