# File System Access API — Manual Test Checklist

The automated script `fsa-test.py` covers most of these. This checklist
captures what to observe *visually* during a live test run, and edge cases
the script doesn't reach.

Run the script:
```
uv run --with "playwright==1.57.0" python3 fsa-test.py
```

---

## Automated checks (covered by fsa-test.py)

| # | Check |
|---|-------|
| 1 | App loads without JS errors |
| 2 | "Open…" button is present in DOM |
| 3 | After picking folder: FSA entry prepended to sidebar |
| 4 | Column 0 shows directory contents |
| 5 | Dot-files (`.DS_Store`, `.git`, etc.) are absent |
| 6 | Path bar shows the picked folder name |
| 7 | Clicking a file: preview name matches filename |
| 8 | Clicking a file: preview shows Size (from `getFile()`) |
| 9 | Clicking a file: preview shows Modified date |
| 10 | Clicking a file: no "Created" row (FSA doesn't expose it) |
| 11 | Status bar shows "1 of N selected" |
| 12 | Clicking a folder: column 1 appears |
| 13 | Cancelling the picker (AbortError) leaves UI unchanged |
| 14 | Alert shown if `showDirectoryPicker` is absent (unsupported browser) |

---

## Visual checks (observe in the browser window)

- [ ] **Spinner** — briefly visible in column 0 while root directory loads
      (fast drives may make this nearly invisible)
- [ ] **Spinner in column 1** — visible when clicking an unloaded sub-folder
      (test on a large directory)
- [ ] **Folder arrow (▶)** — shown for sub-folders; absent for files
- [ ] **Empty folder** — no new column opens; status bar says "0 items"
- [ ] **Sort order** — folders first, then files; each group alpha-sorted
- [ ] **Column width** — auto-computed to fit longest filename
- [ ] **Sidebar highlight** — FSA item at top of Favorites highlighted in blue
- [ ] **Path bar** — shows picked folder name as first breadcrumb; grows as you navigate
- [ ] **Window title** — changes to `"<filename> — Finder"` when a file is selected

---

## Keyboard navigation (manual)

- [ ] Arrow ↓/↑ — navigate items in the focused column
- [ ] Arrow → — open sub-folder (triggers spinner + lazy load)
- [ ] Arrow ← — deselect rightmost item; focus moves left
- [ ] Arrow ← from column 0 — moves focus to sidebar (item gets blue outline)
- [ ] Arrow ↑/↓ in sidebar — moves between sidebar items; FSA item shows correct columns
- [ ] Type-ahead — type partial filename to jump to match (highlighted in yellow)
- [ ] Escape — clears type-ahead

---

## Permission persistence (across browser launches)

- [ ] Re-run `fsa-test.py` with the same `/tmp/fndr-chrome-profile`
- [ ] When you pick the SAME folder again: Chrome does **not** show the
      "Allow site to view and edit files?" confirmation dialog (skipped by profile)
- [ ] When you pick a NEW folder: confirmation dialog appears once, then stored

---

## Edge cases to try manually

- [ ] Pick the root of a large directory (thousands of files) — spinner should
      appear; UI should not freeze; loading completes correctly
- [ ] Pick a folder containing only sub-folders (no files) — preview area shows
      folder info, not "Select a file to see a preview"
- [ ] Click "Open…" twice without picking the first time (cancel both) — no
      duplicate sidebar entries, no JS errors in console
- [ ] Click "Open…", pick folder A; click "Open…" again, pick same folder A —
      sidebar should have exactly one entry for A (deduplication)

---

## Known limitations (not bugs)

| Limitation | Reason |
|------------|--------|
| `Created` date absent in preview | FSA `File` object only exposes `lastModified` |
| Disk free space is "709.59 GB" (mock) | No web API for disk stats |
| OS file picker can't be automated | Browser security; user must interact once |
| Requires Chrome or Edge desktop | `showDirectoryPicker` not in Firefox stable |
| Requires `localhost` or HTTPS | FSA blocked on plain `file://` origin in Chrome |
