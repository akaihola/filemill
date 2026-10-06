---
depends-on: []
---

# Fix Back/Forward navigation across folders, previews and raw files

## Original report and requirements

Bug: Back and Forward navigation doesn't work correctly. Fix browser history
management so that navigating back and forward works as expected when moving
between folders and files and raw files. Also make sure
`Alt`+`ArrowLeft`/`ArrowRight` works as expected.

## Related work

[58] records the earlier Raw-to-preview URL regression. This report also covers
folder navigation and Alt+ArrowLeft/ArrowRight, so it remains a separate task.

[58]: 58-raw-history-preview-mode.md

## Findings (2026-10-06)

Reproduced with Playwright against the server edition:

- `Alt`+`ArrowLeft`/`ArrowRight` never reached the browser. `keyAction` in
  `ui/core/model/keyboard.js` ignored modifier keys, so the finder moved focus
  between columns and called `preventDefault()`, which suppressed the browser's
  Back/Forward shortcut. The same applied to `Cmd`+`ArrowLeft`/`ArrowRight` in
  the preview.
- `locationState` in `ui/core/model/deeplink.js` keyed history on the _open_
  column chain, so merely opening a sibling folder, by `↑`/`↓` or a click in the
  same column, pushed one history entry per folder. [ADR 0050] says history
  pushes on _entering_ a column and rewrites otherwise. Back from a deep file
  skipped the folder it was entered from and landed two levels up.
- Raw round trips ([58]) were sound: Back from `?filemill=raw` reloads the shell
  at the rendered URL and routing resumes from there.

## Plan

1. Key history on the chain down to the _focused_ column: `path[0..focusCol]`.
   Moving to another column pushes; moving within a column rewrites.
2. `keyAction` returns `null` for `Alt`, `Meta` and `Ctrl` (except copy)
   combinations so the browser keeps its history shortcuts.
3. Tests: `ui/core/model/test.mjs` for both rules;
   `server/tests/test_browser_new_ui.py` for sibling folders not stacking
   history, Back retracing columns, and `Alt`+`ArrowLeft` staying unhandled.

[ADR 0050]: ../adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
