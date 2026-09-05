---
depends-on: [17]
---

# Grow the text editor

## Goal

The editor in the preview pane has undo, find, a line gutter and a "modified"
mark. Each feature is one file. Roadmap phase 8, step 4.

## Steps

1. Create `ui/editor/`. Move the current editor code from the preview
   adapters into `ui/editor/editor.js`. It writes through the `FS.write` port
   only.
2. Add `ui/editor/undo.js`: keep a stack of `{start, end, text}` changes.
   `Ctrl+Z` undoes, `Ctrl+Shift+Z` redoes.
3. Add `ui/editor/find.js`: `Ctrl+F` opens a one-line input. `Enter` moves to
   the next match. `Escape` closes it.
4. Add `ui/editor/gutter.js`: a column with line numbers that scrolls with
   the text.
5. Add `ui/editor/modified.js`: show a dot in the pane title when the text
   differs from the saved text. Clear it after save.
6. Add one check per feature in `static/test-ui.py`.

## Done when

- The four checks pass in both editions.
- `ls ui/editor/` shows five files.

## Scope

`ui/editor/`, the preview adapters, `static/test-ui.py`.
