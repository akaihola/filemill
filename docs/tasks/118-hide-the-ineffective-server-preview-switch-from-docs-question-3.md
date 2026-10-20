# Hide the ineffective server preview switch from docs question 3

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f#questions), question 3.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md?f); approved by the user on 2026-10-20 (question 3). Label: `steward`.

## Recommendation

Hide the rich-preview download switch in the server edition while its active renderers need no third-party downloads. Preserve the switch in editions that use it.

## Work

1. Start with a failing browser test for the switch being absent in the served tree and Open Folder mode.
2. Keep server Markdown and DOCX previews working with the stored switch off. Preserve static and native download consent; base visibility on the edition's actual renderer use without changing rendering behavior.
3. Update [ADR 0036](../../docs/adr/0036-but-behind-a-remembered-switch-defaulting-on.md?f) and relevant current guidance in the same change.

## Acceptance

Server tests cover both modes and retained rendering, and static consent tests still pass. No general network-blocking claim or new settings framework is introduced.

## Implementation plan, 2026-10-20

- Add browser regressions for served files and the Open Folder button with
  `filemill.rich` stored as `off`. Check the hidden setting and Markdown/DOCX.
- Initialize consent UI after each edition registers its renderers. Show it
  only when a registered rich renderer needs a third-party module.
- Keep the renderer and consent checks unchanged. Update ADR 0036, the current
  server guidance and the architecture review. Rebuild the static bundle.
- Run the server regressions, static consent checks, and repository gates.

## Implementation and validation, 2026-10-20

The consent UI now initializes after renderer registration in all three entry
adapters. It appears when a registered rich renderer needs a CDN module.
Server rendering and the stored consent value are unchanged. ADR 0036, README
server guidance and the architecture review describe this scope.

- Red: both new browser cases failed because `s-rich` was not hidden.
- Green: both cases pass through served files and the Open Folder button,
  including Markdown and DOCX rendering with stored consent off.
- Server renderer-registration and no-CDN browser checks pass (4 checks with
  the new cases). The final new-case rerun passes both checks.
- Static development consent/RST checks: 5 passed. Bundle consent and loaded
  renderer checks: 3 passed. Bundle RST checks: 3 passed on isolated rerun.
  The first bundle RST run counted two cleanup calls instead of one; the
  unchanged test passed on rerun. No assertion was weakened.
- Documentation checks: 21 passed. Model checks and the complete pre-commit
  gate pass, including formatters, linters, mypy and bundle freshness.
- Native entry initialization retains CDN consent. The native GUI suite and
  full server suite were not run.
