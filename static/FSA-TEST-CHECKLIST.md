# Manual test checklist

`test-ui.py` covers everything a fake handle can reach. `test-e2e.py` covers a
real folder and browser permissions. Use it when checking changes to the real
File System Access API path, especially folder picking, persisted permissions,
real file metadata, refreshes, and view-state restore. It is a manual check,
not part of the automated test suite.

Run the checks from `static/` after starting from a clean browser profile when
you need to exercise the first-run picker:

```bash
uv run --with "playwright==1.61.0" python3 test-ui.py     # headless, ~30 s
uv run --with "playwright==1.61.0" python3 test-e2e.py    # headed, manual picks
```

`test-e2e.py` starts a local server on port `8787` and opens a headed Chromium
window with a persistent profile in `/tmp/filemill-profile`. On the first run,
click **Choose Folder…** and select any local folder. On later runs, the
remembered folder should mount without a dialog, or appear under **Recently
opened** for one click. The script then creates a throwaway folder under the
system temporary directory and prints its path; click **Open Folder…** and pick
that folder when prompted. The script changes and removes files only in this
throwaway folder.

Run the script twice to check both the initial picker and the remembered-folder
path. Review the checks printed in the terminal, the browser window, and the
screenshots in `/tmp/filemill-e2e`. A successful run ends with `passed, 0
failed`; press Enter in the terminal to close the browser. If the script times
out waiting for a pick, or reports a failed check or page error, investigate it
before marking the manual check complete.

---

## Visual

- [ ] **Trail** — the elbow from the selected row into the next column's header
      is continuous and sits in the middle of the gutter. It disappears when
      the selected row scrolls out of its column
- [ ] **Folding** — drag the horizontal scrollbar. Columns narrow from the left
      one at a time. The crossfade to the vertical spine label has no jump
- [ ] **Spine icon** — a folded column still shows the icon of its chosen child
      in the accent dot, and the trail re-anchors to it
- [ ] **Depth recession** — each ancestor column is darker than the focused
      one. The focused column has the accent underline in its header
- [ ] **Selection states** — focused column solid accent, ancestors tinted pill,
      descendants dashed ghost. All three are legible in light *and* dark theme
- [ ] **Long names** — an 80-character filename gets an ellipsis. The column
      stays under 380 px. Hover shows the full name
- [ ] **Icons** — file types get distinct Seti glyphs and colours. An unknown
      extension gets the default glyph, never a blank square

## Real filesystem

- [ ] A folder with thousands of entries opens without a frozen UI. Arrow keys
      stay responsive while you scroll through it
- [ ] A folder you cannot read (for example `/root`) shows "⚠ No permission to
      read", not an empty column
- [ ] Symlinked directories open. A broken symlink does not break the column
- [ ] Non-ASCII names (accents, CJK, emoji) render and sort correctly
- [ ] A file changed on disk shows the new size and mtime after you select it
      again. There is no directory watcher: F5 or ⟳ re-reads the folder
- [ ] ⟳ on a folder on a network share or an unmounted drive: the read fails
      instead of hanging. The column says so instead of keeping the old listing
      with a spinner on top
- [ ] Refresh a folder of 100 000 entries: the old listing stays on screen with
      the ⟳ spinning until the new one is built. It does not blank to
      "Reading…". The rebuild is about 370 ms at 3 000 entries and scales with it
- [ ] Rename the *root* folder while it is open, then press F5: the handle
      still resolves (a handle is not a path), so the columns do not change
- [ ] Sort by size on a folder of 100 000 entries: the column keeps its names on
      screen and spins beside the count while it reads. One `getFile()` per
      entry costs about 300 µs, so expect tens of seconds. Arrow keys and the ⚙
      popover stay responsive
- [ ] Sort by size on a network share or a spinning disk: the same sweep over a
      slow device. The app must stay usable and the strip must keep counting
      down. The duration does not matter
- [ ] Sort by size on a folder with a file the OS will not let you read: the
      file lands at the bottom of the column in both directions, and stays
      visible
- [ ] Large image previews scale to fit. A 100 MB binary shows "No inline
      preview" and is not read

## Permissions and persistence

- [ ] First visit: welcome screen with **Choose Folder…** only
- [ ] After a pick: reload the page → the same folder mounts with **no dialog**
- [ ] Pick 2–3 different folders, then reload → all appear under
      **Recently opened**, most recent first, no duplicates
- [ ] Quit the browser and reopen: Chrome downgrades the grant to "prompt". The
      folders still appear. A click on one shows Chrome's "Let site view
      files?" bar: one click, no OS picker
- [ ] Open a folder three columns deep, quit the browser, reopen, click that
      folder under **Recently opened**: the three columns come back and the
      file is selected again. The button already said where it would land
- [ ] Two remembered folders with the same basename (`~/a/notes`, `~/b/notes`):
      each keeps its own chain. `isSameEntry` tells them apart. A restore that
      mixes them up means something matches on the name
- [ ] Cancel the picker (Esc) → nothing changes, no console error
- [ ] Open `index.html` as a `file://` URL → localhost instructions, not a
      broken picker
- [ ] Firefox/Safari → "no File System Access API" message

## Known limitations (not bugs)

| Limitation | Reason |
|------------|--------|
| Needs `localhost` or HTTPS | Chrome blocks the FSA picker on opaque origins |
| Chrome/Edge desktop only | `showDirectoryPicker` is not in Firefox or Safari |
| No "created" date | FSA's `File` only exposes `lastModified` |
| A disk change does not update the columns | No directory-watch API exists behind either port. The user asks for a refresh: F5, or ⟳ in the focused column's header |
| Permission is re-prompted after a browser restart | Chrome only persists grants for installed PWAs |
| Read-only | The app never asks for `mode: "readwrite"` |
