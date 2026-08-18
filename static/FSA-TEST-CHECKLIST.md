# Manual test checklist

`test-ui.py` covers everything a fake handle can reach and `test-e2e.py` covers
a real folder. This file is what is left: things you have to *look at*, and
things only a real browser session can produce.

Run both first:

```bash
uv run --with "playwright==1.61.0" python3 test-ui.py     # headless, ~30 s
uv run --with "playwright==1.61.0" python3 test-e2e.py    # headed, one folder pick
```

---

## Visual

- [ ] **Trail** — the elbow from the selected row into the next column's header
      is continuous, sits in the middle of the gutter, and disappears when the
      selected row is scrolled out of its column
- [ ] **Folding** — dragging the horizontal scrollbar narrows columns from the
      left one at a time; the crossfade to the vertical spine label has no jump
- [ ] **Spine icon** — a folded column still shows the icon of its chosen child
      in the accent dot, and the trail re-anchors to it
- [ ] **Depth recession** — ancestor columns are progressively darker than the
      focused one; the focused column has the accent underline in its header
- [ ] **Selection states** — focused column solid accent, ancestors tinted pill,
      descendants dashed ghost; all three legible in light *and* dark theme
- [ ] **Long names** — an 80-character filename ellipsises without widening the
      column past 380 px; hovering shows the full name
- [ ] **Icons** — file types get distinct Seti glyphs and colours; unknown
      extensions fall back to the default glyph, never a blank square

## Real filesystem

- [ ] A folder with thousands of entries opens without freezing the UI, and
      arrow keys stay responsive while scrolling through it
- [ ] A folder you cannot read (e.g. `/root`) shows "⚠ No permission to read",
      not an empty column
- [ ] Symlinked directories open; a broken symlink does not break the column
- [ ] Non-ASCII names (accents, CJK, emoji) render and sort sensibly
- [ ] A file changed on disk shows the new size/mtime after re-selecting it
      (there is no directory watcher; F5 or ⟳ re-reads the folder)
- [ ] ⟳ on a folder held on a network share or an unmounted drive: the read
      fails rather than hanging forever, and the column says so instead of
      keeping the old listing with a spinner on top
- [ ] Refresh a folder of 100 000 entries: the old listing stays on screen with
      the ⟳ spinning until the new one is built, rather than blanking to
      "Reading…" — the rebuild is ~370 ms at 3 000 entries and scales with it
- [ ] Rename the *root* folder while it is open, then F5: the handle still
      resolves (a handle is not a path), so the columns are unaffected
- [ ] Large image previews scale to fit; a 100 MB binary shows "No inline
      preview" rather than trying to read it

## Permissions and persistence

- [ ] First visit: welcome screen with **Choose Folder…** only
- [ ] After picking: reload the page → mounts the same folder with **no dialog**
- [ ] Pick 2–3 different folders, then reload → all appear under
      **Recently opened**, most recent first, no duplicates
- [ ] Quit the browser entirely and reopen: Chrome downgrades the grant to
      "prompt", so the folders still appear but clicking one shows Chrome's
      "Let site view files?" bar — one click, no OS picker
- [ ] Open a folder three columns deep, quit the browser, reopen, click that
      folder under **Recently opened**: the three columns come back and the
      file is selected again. The button already said where it would land
- [ ] Two remembered folders with the same basename (`~/a/notes`, `~/b/notes`):
      each keeps its own chain. `isSameEntry` is what tells them apart, so a
      restore that mixes them up means something is matching on the name
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
| The disk changing does not update the columns on its own | No directory-watch API exists behind either port, so refresh is a thing the user asks for: F5, or ⟳ in the focused column's header |
| Permission is re-prompted after a browser restart | Chrome only persists grants for installed PWAs |
| Read-only | The app never asks for `mode: "readwrite"` |
