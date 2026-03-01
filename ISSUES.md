# Issues

## Open

### #1 – Add PNG and JPEG preview

**Type:** feature

Show inline image preview for `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, and `.svg` files
when clicked in the column view. Render as a plain `<img>` tag (served via the existing
`/raw` endpoint) with `max-width: 100%` and `max-height: 100%` inside the preview pane,
and a subtle checkerboard background for transparency.

---

### #2 – Show full filename in tooltip when truncated

**Type:** UX / bug

Column entries are fixed-width and long filenames are clipped with CSS `text-overflow:
ellipsis`. When a filename is clipped the user has no way to read it. Add a `title`
attribute to every `<li>` (or its inner `<span>`) containing the full filename so the
browser shows a native tooltip on hover.

---

### #3 – Auto-adjust column width to fit longest filename

**Type:** UX / feature

Column width is currently hard-coded to 220 px. Instead, compute the width from the
longest filename in the currently-visible columns (all columns share the same width),
subject to two constraints:

- **minimum** – wide enough to show the shortest useful name without truncation
- **maximum** – narrow enough that the total width of all open columns plus the preview
  pane still fits horizontally in the viewport without horizontal scroll

The width should be recalculated whenever a new column is opened or closed.

---

### #4 – Zoom button: expand preview to full page width

**Type:** feature

Add a small toggle button (e.g. ⛶ / ✕ or a magnifier icon) in the top-right corner of
the preview pane. When activated:

- the file-column area is hidden (`display: none` or slid out)
- the preview pane expands to fill the full viewport width
- the button icon changes to indicate "zoom out / restore"

When the button is clicked again the layout reverts to the normal columns + preview split.
The zoom state should survive HTMX partial swaps (i.e. re-opening a file while zoomed
keeps the pane zoomed).

---

## Closed

_(none yet)_
