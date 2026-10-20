# ADR 0048: A refused clipboard opens manual copying

Date: 2026-08-17. Revised: 2026-10-20, issue [119].

## Context

The clipboard API can refuse a write because of browser policy, permissions or
an insecure context. The original fallback selected the footer path. Menu copy
commands kept the menu open. The footer could truncate the refusal explanation.

## Decision

Show one native modal dialog for refused menu, keyboard and status-path copies.
Close the row menu before the copy attempt. Put the exact refused value in a
labelled, read-only textarea. Focus the field and select its full value.

Show native-copy instructions and the complete error name and message in the
dialog. Keep long values and explanations intact. Wrap text and allow scrolling
within the viewport. Close with Escape or the Close button and restore focus to
the control that had focus before the copy operation.

## Measurement

Browser checks cover all three menu commands on an unselected row at desktop and
narrow widths. They check long absolute paths, long explanations, field selection,
focus return and native copying without another clipboard API call. Keyboard and
status-path checks use the same dialog. Successful copy rotation stays covered.

## Consequences

Both web editions share this presentation. The footer gives a short failure
notice; the dialog holds the full reason. Native copying of selected text does
not require another clipboard API write. Successful copies keep their existing
status notice and rotation behavior.

[119]: ../tasks/119-document-the-menu-copy-exception-from-docs-question-4.md
