---
depends-on: []
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

## Manual checks

Open a disposable plain-text file and select Edit. In the public demo, you can use
Open local folder to choose a test file on your own computer.

1. Type text, then press Ctrl+Z. The edit should disappear. Press Ctrl+Shift+Z to
   restore it. Use Cmd instead of Ctrl on macOS.
2. Put the same word on two lines. Press Ctrl+F or Cmd+F and enter that word.
   Press Enter to select each match and wrap to the first. Escape closes Find.
   Try a match near the end of a long line; it should scroll into view.
3. Add and remove line breaks. The gutter should add and remove line numbers.
   Paste enough lines to scroll; numbers and text should stay aligned.
4. Make an edit and check the dot beside the file name. Undo back to the original
   text; the dot should disappear. Edit again and Save. Reopen the editor or reload
   the page; the saved text should remain and the dot should be absent.
5. Edit, then resize the window. The text, dot and undo history should survive.
   To discard a test edit, select Cancel and check that the stored text returns.

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

The task remained In Progress during review. The implementation does not change
unrelated issues to address these baseline failures.

## Implementation review

Review reproduced and fixed two find-mode defects. Composition keys now stay with
the input method in both Find and Undo. Find measures the line prefix with browser
text layout to scroll off-screen matches into view, including horizontal scrolling.
Regression checks cover composition Enter, composition undo, long-line matches and
wraparound. The focused server set now has seven cases; both static modes include
the new Find checks.

The tracker audit compared complete issue blocks and their headings against main.
Issue [28] occurs once, under In Progress. Removing its unchanged block and the
separating blank line makes the two tracker files byte-identical. No cross-heading
duplicate was introduced. A global uniqueness proof is blocked by existing issue
[6], which appears under both Scheduled and In Progress on main and this branch.
Removing either copy would violate this task's requirement to retain main's text
for every other issue, so this review leaves both copies unchanged.


## Deployment

Merged into main with merge commits `05f44fc` (editor) and `b210f9a` (asset delivery).
Both worktrees were clean before removing the merged feature worktree and branch.
Issue [28] moved unchanged to Completed; every other tracker byte was preserved.
The pre-existing issue [6] duplication described above remains unchanged.

Restarted `filemill.service` (development tree, port 8334) and
`filemill-public.service` (port 8336, https://filemill.vempai.men/).
Both services are active. The seven changed editor/render/style assets match main
on both origins and through the public domain. Live Chromium checks passed on the
development and public deployments using in-memory files, including a save.

The CDN initially served stale unversioned modules after restart. Commit `1b698a7`
adds content-hashed script/style URLs and an import map for the complete server
module graph. Refresh the browser to receive the new shell and editor. No cache
purge was needed. The static bundle is unchanged by this server delivery fix.

Deployment validation: 13 focused shell/editor tests pass, source lint passes,
and the static bundle freshness check passes. The complete API suite reports
55 passes and seven failures; unmodified main reproduces the identical failures.
Logs: `/tmp/filemill-cache-tests.log`, `/tmp/filemill-cache-api.log`,
`/tmp/filemill-cache-api-main.log`, and `/tmp/filemill-live-check.log`.

## Tracker maintenance on 2026-09-19

Commit `d3de46c` removed the duplicate issue [6] and reconciled tracker statuses.
The duplication and single-issue restrictions above describe the editor task's
review and deployment snapshots, not the current backlog.

[6]: 6-file-kind-classification.md
[28]: 28-editor-features.md
