Remove the leading § signs from Markdown and reStructuredText hierarchical browsing items, and remove the redundant `§ <heading>` and horizontal line since the actual heading from the document is displayed at the top of the preview anyway.

## Implementation, 2026-10-11

- Remove the section icon from the document adapter. The shared icon renderer
  emits no icon for section rows or folded columns.
- Omit the file summary block for section previews. Continue to render content
  without its metadata element. Keep the preview toolbar and whole-file summary.
- Keep the shared FS and PREVIEW ports and existing section renderers.
  Record the presentation change in ADR 0070.

## Validation

Four browser cases failed before the fix. They cover the row icon and preview
summary for Markdown and reStructuredText. All five document browsing tests
pass against the shared sources. All seven focused bundle and server browser
tests pass. Server checks verify the document's rendered heading, source view
switching, deep-link reloads and whole-file previews after left-arrow navigation.

After rebasing onto `9502cde`, all five source tests, all six pre-commit hooks
and the model checks pass. A broader bundle and server preview run has 51
passes and one Git bundle timeout. That timeout repeats with the unchanged
main frontend in this worktree. The same test passes in the canonical checkout.
It is outside this issue's section presentation change.

Deployment needs a push from the maintainer account. The push rules in
the local agent push policy prohibit pushing `main` from the development account.

After the local merge, eight focused bundle and server browser tests pass in
the canonical checkout, including the Git bundle case. All six pre-commit
hooks and the model checks pass there too.
