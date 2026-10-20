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
