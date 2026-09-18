---
depends-on: [17]
---

# Browser text editor

The shared preview editor writes through `FS.write`. Both the server and static
editions use these five files:

- `ui/editor/editor.js` reads text, mounts the controls, and saves through the port.
  It keeps the existing UTF-8, file-size and line-length limits.
- `ui/editor/undo.js` records text changes and selections. Ctrl+Z undoes a change;
  Ctrl+Shift+Z redoes it. Cmd works on macOS. New input clears the redo history.
  Composition input forms one undo entry.
- `ui/editor/find.js` opens literal search with Ctrl+F, Cmd+F, or the Find button.
  Enter selects the next match and wraps at the end. While search is open, Enter
  advances from either the search field or the selected text. Escape closes search
  and returns focus to the editor. Empty queries and missing matches change no text.
- `ui/editor/gutter.js` numbers logical lines, including an empty final line.
  The numbers track the textarea's vertical scroll. Text does not wrap in edit mode.
- `ui/editor/modified.js` compares the text with its initial textarea value. A dot
  in the pane title marks unsaved changes. Undo back to the initial text clears it.

Save locks editing and undo while the write is pending. Success returns to a fresh
preview and clears the dot. Failure keeps the text, restores the controls, and
shows the error. Reopening or reloading a saved file starts clean. Cancel returns
to the stored text. Navigation retains its existing discard behavior.

`renderPreview()` preserves an active editor for the same node during resize.
Navigation and explicit preview replacement end that editor session. Late reads
and write results cannot replace another file's editor or display errors in it.
The editor uses callbacks to the renderer and adds no import cycle.

## Checks

From `static/`, run the focused checks against both builds:

```bash
uv run --with "playwright==1.61.0" python3 test-ui.py --editor
uv run --with "playwright==1.61.0" python3 test-ui.py --dev --editor
```

From `server/`, run:

```bash
uv run pytest tests/test_browser_new_ui.py -k 'editor or saved_plaintext'
```

These checks cover the four features, modified-state transitions, failed writes,
save/reopen/reload, resize, selection restoration, newline normalization,
composition, and late read/write completion after navigation. The static checks
use fake file handles. Their `file://` fixture stubs service-worker registration.
Use the installed Nix browsers; do not run `playwright install`.

Rebuild and check the generated bundle after UI changes:

```bash
static/build-index.py
static/build-index.py --check
deno fmt --check ui/editor/
deno lint --ignore=ui/vendor ui/
```

Also run `deno task check`, both full `static/test-ui.py` modes, the full
`server/tests/test_browser_new_ui.py` suite, and `pre-commit run --all-files`.
Record failures against an untouched main checkout before treating them as editor
regressions. Keep the `TASKS.md` diff to the unchanged issue [28] block moved from
Scheduled to In Progress. Do not change other issues or duplicate section headings.

## Validation on 2026-09-18

- Both focused static modes pass. The six focused server cases pass.
- All 71 server UI cases ran in bounded batches after the rebase: 57 pass and 14
  fail. The exact 14 failing test names match an untouched `ff11672` main checkout,
  where 51 pass and 14 fail. The failures cover existing navigation, source
  highlighting, JSON/JSONL and CSV behavior. No new editor case fails.
- Both full static modes stop before the editor section at the hidden `dup.jsonl`
  row click. The untouched main bundle reproduces that timeout and the same six
  earlier assertion failures. Use `--editor` to run the focused checks separately.
- The bundle build and freshness check pass. Editor module formatting, all
  non-vendor UI lint, Python syntax, and the changed Python tests' lint pass.
- Repository-wide checks remain blocked by existing failures. Main and this branch
  each report nine non-vendor UI files needing formatting and 2,358 vendor lint
  findings. Pre-commit also reports existing Python formatting failures and two
  `api.py:174` mypy argument-type errors, reproduced on untouched main. The full
  Deno formatter exceeded the bounded run; the remaining hooks ran separately.

The task status remains In Progress for review. The implementation does not change
unrelated issues to address these baseline failures.
