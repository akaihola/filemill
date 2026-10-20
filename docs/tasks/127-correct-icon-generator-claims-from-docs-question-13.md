# Correct icon generator claims from docs question 13

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f#questions), question 13.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md?f); approved by the user on 2026-10-20 (question 13). Label: `steward`.

## Recommendation

Correct stale generator comments instead of inventing a new build tool.

## Work

1. Update [ui/core/icons.js](../../ui/core/icons.js?f) and [ui/vendor/seti-map.js](../../ui/vendor/seti-map.js?f) to describe the committed map, the upstream sources recorded there, and the absence of a tracked generator.
2. Preserve the icon mapping, font, licensing and any known provenance. Do not invent an upstream revision or claim a regeneration command exists.
3. Regenerate [static/index.html](../../static/index.html?f) if copied comments change, then review that only comments changed.

## Acceptance

No current instruction depends on build-seti-map.py, assets and behavior are unchanged, and docs tests plus [static/build-index.py](../../static/build-index.py?f) --check pass.
