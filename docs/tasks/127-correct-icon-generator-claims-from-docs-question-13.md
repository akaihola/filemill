# Correct icon generator claims from docs question 13

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 13.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Correct stale generator comments instead of inventing a new build tool.

## Work

1. Update ui/core/icons.js and ui/vendor/seti-map.js to describe the committed map, the upstream sources recorded there, and the absence of a tracked generator.
2. Preserve the icon mapping, font, licensing and any known provenance. Do not invent an upstream revision or claim a regeneration command exists.
3. Regenerate static/index.html if copied comments change, then review that only comments changed.

## Acceptance

No current instruction depends on build-seti-map.py, assets and behavior are unchanged, and docs tests plus static/build-index.py --check pass.
