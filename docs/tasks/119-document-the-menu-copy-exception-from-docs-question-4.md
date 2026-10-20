# Offer manual copying in a pop-up when clipboard access fails

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f), question 4.
User review, 2026-10-20. Label: `steward`.

## Decision

Approved replacement for the earlier menu exception: close the row menu after clipboard refusal and show a pop-up containing the exact text that could not be copied. Put the refusal explanation and manual-copy instructions in that pop-up; the footer currently truncates the explanation even on a wide laptop screen.

## Work

1. Start with a failing browser test for each menu command, including a row that is not selected: the menu closes and the pop-up contains exactly the intended name, relative path or absolute path.

2. Make the text selectable and usable with native copy commands; copying selected text must not reopen the failure flow. Preserve long paths in full, using a scrollable or wrapping text field instead of truncating the copy value.

3. Show the full refusal reason and simple manual-copy instructions in the pop-up. Provide a label, keyboard focus, dismissal by Escape and focus return. Test desktop and narrow/touch layouts, including a long refusal explanation.

4. Use the same failure presentation for keyboard/status-path copy where applicable, while preserving successful copying and ordinary selected-text copying. Update [ADR 0048](../adr/0048-a-refused-clipboard-selects-the-path-instead.md?f) in the same change.

## Acceptance

A refused menu copy closes the menu and exposes the complete intended value for manual copying, without another clipboard permission requirement. The explanation is readable in the pop-up; the footer is not its only source. Successful copy rotation and native text copying still pass their checks.

## Implementation plan

- Add browser regressions for all three menu commands on an unselected row.
- Use one native modal dialog in the shared UI for all copy refusals. Show the
  full error and exact value in a labelled, selected, read-only text field.
- Close the menu before copying. Restore the original focus after dismissal.
- Check narrow layouts, long values, keyboard copying and successful rotation.
- Update ADR 0048, the architecture review and the generated static bundle.

## Result, 2026-10-20

Menu copy commands close the menu before the clipboard write. A refused write
opens the shared native dialog for menu, keyboard and status-path copies. The
labelled, read-only text field contains the exact value and selects all of it.
The dialog shows the full error and native-copy instructions. Long content wraps
and scrolls. Escape and Close restore the prior focus. Native text copying does
not call the clipboard API again. The footer keeps a short failure notice.

## Validation

- Red: all six new menu cases failed because the dialog did not exist. The cases
  cover each command on an unselected row at desktop and narrow widths.
- Green: nine source dialog checks, four source status-copy checks and thirteen
  bundle checks passed in the final focused reruns. Narrow checks use real touch
  input. They include long paths, long error messages, selection and dismissal.
- Earlier copy runs passed 26 checks in each static mode, including successful
  rotation, native text copying, stale requests and interaction resets. The
  refused-copy assertions were then corrected and passed in the focused reruns.
- Five server keyboard/status checks and two server menu/copy checks passed.
- All pre-commit checks, shared model checks and the generated-bundle check passed.
- The full suites were attempted, then interrupted. A server Markdown-link test
  failed on both this branch and unchanged main. The large-JSON source case
  failed during the broad run, then passed alone on both main and this branch.
  The broad bundle run passed 31 checks before interruption. These results do
  not establish a complete suite pass.
- The T3 preview could not open because its host lacks browser libraries. Browser
  validation used the repository's managed Chromium setup.
