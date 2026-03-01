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

### #5 – URL reflects current path; deep-link navigation

**Type:** feature

The browser URL should stay in sync with the currently selected file or directory as the
user navigates the column view, and pasting or opening a URL should restore the exact same
view.

**URL scheme** – encode the selected path as a URL-encoded subpath after the origin, e.g.:

```
https://gogo.crane-boa.ts.net:8445/browse/paivi/documents/reports/2025/budget.pdf
```

or as a query parameter if a subpath conflicts with existing routes:

```
https://gogo.crane-boa.ts.net:8445/?path=reports/2025/budget.pdf
```

**Sync while navigating** – after every successful `/click` response, call
`history.pushState()` (or `replaceState` for intermediate directory columns) to update the
browser URL without a full page reload. No server round-trip needed for the URL update
itself.

**Deep-link on load** – when the page is loaded with a non-root path, the server (or
client-side JS on `DOMContentLoaded`) should:

1. Split the path into its components (e.g. `reports`, `2025`, `budget.pdf`).
2. Sequentially open one column per component, exactly as if the user had clicked each
   entry.
3. Scroll the column strip to show the rightmost column and, if the final component is a
   file, render its preview.

**Edge cases to handle:**

- Path no longer exists → show an error column or fall back to root.
- Path escapes the configured root → reject (same `_resolve_safe` logic).
- Browser back/forward buttons → listen to `popstate` and re-render columns to match the
  URL that was popped.

---

## Closed

_(none yet)_
