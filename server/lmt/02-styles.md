# Milestone 02 – Visual design

Every Finder clone lives or dies by its visual polish. This milestone
defines the complete CSS for the application – layout, column panels,
breadcrumb bar, preview pane, and responsive behaviour – together with
Pygments formatter objects for syntax highlighting.

The JavaScript that drives keyboard navigation and interactivity is _not_
included yet; we define placeholder strings here and fill them in as the
final milestone.

## Pygments setup

We create a global `HtmlFormatter` used by the Markdown code-fence
highlighter and by the file-preview renderer. Two additional formatters
generate the CSS rules for the "friendly" Pygments theme.

```python src/filemill/styles.py
from pygments.formatters import HtmlFormatter

PYGMENTS_FORMATTER = HtmlFormatter(nowrap=True)
HIGHLIGHT_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")
FRIENDLY_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")

APP_CSS = (
<<<css layout>>>
+ <<<css breadcrumb>>>
+ <<<css columns>>>
+ <<<css preview>>>
+ <<<css mobile>>>
+ <<<css dynamic>>>
)

COLUMN_JS = <<<column js>>>

LIVE_RELOAD_JS = <<<live reload js>>>
```

## Layout foundations

The outermost elements use flexbox to fill the viewport. `#app-shell` is a
vertical flex container (breadcrumb on top, finder below); `#finder` is a
horizontal flex container where each `.column` and the `#preview` pane sit
side by side. `overflow: hidden` on `body` prevents double scrollbars –
individual columns and the preview pane scroll independently.

```python "css layout"
"""
body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
    background: #f0f0f0;
    margin: 0;
    overflow: hidden;
    height: 100vh;
    height: 100dvh;
}

#app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
}

#finder {
    display: flex;
    flex: 1;
    min-height: 0;
    overflow-x: auto;
    overflow-y: hidden;
}
"""
```

## Breadcrumb bar

The breadcrumb sits at the top of the shell and shows the path from root
to the current selection. It also houses two toggle buttons pushed to the
right via `margin-left: auto`: one for dotfile visibility and one for
zoom mode.

```python "css breadcrumb"
"""
#breadcrumb {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    font-size: 12px;
    background: #ebebeb;
    border-bottom: 1px solid #c7c7c7;
    flex-shrink: 0;
    color: #333;
    overflow: hidden;
}

.bc-toggle {
    margin-left: auto;
    flex-shrink: 0;
    padding: 1px 6px;
    border: 1px solid #bbb;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    font-size: 11px;
    font-family: "SF Mono", "Fira Code", monospace;
    color: #999;
    line-height: 1.4;
    user-select: none;
}
.bc-toggle:hover {
    background: #e8e8e8;
}
.bc-toggle.active {
    background: #0070c9;
    color: #fff;
    border-color: #0070c9;
}
.bc-toggle.active:hover {
    background: #005da6;
}

/* Dotfiles: hidden by default, visible when body carries .show-dotfiles */
.column li.dotfile {
    display: none;
}
body.show-dotfiles .column li.dotfile {
    display: list-item;
}
body.show-dotfiles .column li.dotfile > a {
    opacity: 0.65;
}
/* Always show the selected dotfile entry even when dotfiles are hidden
   (e.g. deep-link restore to a hidden path segment). */
body:not(.show-dotfiles) .column li.dotfile.selected {
    display: list-item;
}

.bc-root, .bc-seg {
    font-weight: 500;
}

.bc-sep {
    color: #999;
    margin: 0 4px;
}

/* Virtual breadcrumb segments */
.bc-virtual {
    font-style: italic;
    color: #555;
}
"""
```

## Column panels

Each column is a fixed-width vertical scrolling list. The width comes from
a CSS custom property `--col-width` that the JavaScript recalculates whenever
the column set changes (we'll add that code in Milestone 10). Items use
absolute-positioned emoji icons in a left gutter.

The selection highlight uses macOS-style blue (`#0070c9`). When keyboard
navigation is active, columns to the left of the focused one get a muted
"ancestor" highlight, and columns to the right get a faded "descendant"
tint, giving the user a clear sense of where they are in the tree.

```python "css columns"
"""
.column {
    width: var(--col-width, 220px);
    height: 100%;
    overflow-y: auto;
    border-right: 1px solid #c7c7c7;
    background: #fff;
    flex-shrink: 0;
}

.column ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.column li a {
    display: block;
    padding: 4px 8px 4px 24px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #000;
    text-decoration: none;
    cursor: pointer;
    position: relative;
}

.column li.selected > a {
    background: #0070c9;
    color: #fff;
}

.column li.selected > a .icon {
    color: #fff;
}

/* ── Column focus-state highlights (keyboard navigation) ─────────────────── */
/* Ancestor columns (left of focus): muted steel-blue – shows the path taken  */
.col-ancestor li.selected > a {
    background: #6fa3be;
    color: #fff;
}

/* Descendant columns (right of focus): very light – "remembered, waiting"    */
.col-descendant li.selected > a {
    background: #dceef7;
    color: #6090a8;
}

.col-descendant li.selected > a .icon {
    color: #6090a8;
}

.column li:not(.selected) a:hover {
    background: #e8e8e8;
}

.icon {
    position: absolute;
    left: 6px;
}
"""
```

## Preview pane

The preview pane takes up at least one-third of the viewport (`min-width:
33.333vw`). Different preview types – Markdown, PDF, images, code, PPTX
slides – each get their own class with tailored styling. The Markdown
preview deserves particular attention: headings, code blocks, tables,
blockquotes, task lists, and links are all styled to feel native.

```python "css preview"
"""
#preview {
    flex: 1;
    min-width: 33.333vw;
    overflow-y: auto;
    padding: 1rem 1.5rem;
    background: #fff;
    border-left: 1px solid #c7c7c7;
}
#preview:has(.preview-db-spreadsheet) {
    padding: 0;
}

.preview-md {
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
}

.preview-md h1, .preview-md h2, .preview-md h3,
.preview-md h4, .preview-md h5, .preview-md h6 {
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    font-weight: 600;
}

.preview-md h1 { font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
.preview-md h2 { font-size: 1.4em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
.preview-md h3 { font-size: 1.2em; }

.preview-md p { margin: 0.6em 0; }

.preview-md code {
    background: #f3f3f3;
    border-radius: 3px;
    padding: 0.1em 0.3em;
    font-size: 0.9em;
    font-family: "SF Mono", "Fira Code", monospace;
}

.preview-md pre {
    background: #f3f3f3;
    border-radius: 5px;
    padding: 0.8em 1em;
    overflow-x: auto;
    margin: 0.8em 0;
}

.preview-md pre code {
    background: none;
    padding: 0;
    font-size: 0.85em;
}

.preview-md .highlight {
    background: #f3f3f3;
    border-radius: 5px;
    padding: 0.8em 1em;
    overflow-x: auto;
    margin: 0.8em 0;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.85em;
}

.preview-md table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.8em 0;
}

.preview-md th, .preview-md td {
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
}

.preview-md th {
    background: #f0f0f0;
    font-weight: 600;
}

.preview-md blockquote {
    border-left: 3px solid #0070c9;
    margin: 0.8em 0;
    padding: 0.2em 1em;
    color: #555;
    background: #f8f8f8;
}

.preview-md ul, .preview-md ol {
    margin: 0.4em 0;
    padding-left: 1.8em;
}

.preview-md li { margin: 0.2em 0; }

.preview-md input[type="checkbox"] { margin-right: 0.4em; }

.preview-md hr {
    border: none;
    border-top: 1px solid #eee;
    margin: 1.2em 0;
}

.preview-md a { color: #0070c9; }

.preview-pdf iframe {
    width: 100%;
    height: 90vh;
    border: none;
}

.preview-pptx .slide {
    border: 1px solid #ddd;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: #fafafa;
}

.preview-pptx .slide h3 {
    margin: 0 0 0.5em 0;
    font-size: 1em;
    color: #666;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.3em;
}

.preview-raw {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.85em;
    background: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    padding: 1rem;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
}

.preview-error {
    color: #c00;
    font-style: italic;
}

.preview-empty {
    color: #999;
    font-style: italic;
    padding: 1rem;
}

.preview-image {
    background-color: #fff;
    background-image:
        linear-gradient(45deg, #ccc 25%, transparent 25%),
        linear-gradient(-45deg, #ccc 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #ccc 75%),
        linear-gradient(-45deg, transparent 75%, #ccc 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    display: inline-block;
    max-width: 100%;
}

.preview-image img {
    display: block;
    max-width: 100%;
    max-height: 100%;
}

body.zoomed .column {
    display: none;
}
body.zoomed #preview {
    width: 100vw;
    min-width: unset;
    box-sizing: border-box;
}
"""
```

## Mobile responsive

On narrow viewports the preview expands to nearly the full width, and
columns peek from the left – the user swipes horizontally to navigate.

```python "css mobile"
"""
/* ── Mobile: preview dominates, columns peek from the right ─────────────── */
@media (max-width: 700px) {
    #preview {
        min-width: 90vw;
        flex-shrink: 0;
    }
}
"""
```

## Dynamic styles

The Pygments theme CSS and VFS-specific styles (spreadsheet tables,
format-toggle bars, key-value detail views, pagination) are generated at
import time using f-string interpolation of the `HIGHLIGHT_CSS` and
`FRIENDLY_CSS` variables.

```python "css dynamic"
f"""
/* Pygments syntax highlighting */
.highlight {{ background: #f3f3f3; }}
{HIGHLIGHT_CSS}

/* Source code preview block */
.preview-code {{
    padding: 0.5rem;
}}
.preview-code .highlight {{
    border-radius: 5px;
    overflow-x: auto;
}}

{FRIENDLY_CSS}

/* ── VFS / format toggle ──────────────────────────────────────────────── */
.fmt-bar {{
    display: flex;
    gap: 4px;
    padding: 4px 8px;
    background: #f5f5f5;
    border-bottom: 1px solid #ddd;
    flex-shrink: 0;
}}
.fmt-btn {{
    padding: 2px 8px;
    border: 1px solid #bbb;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    font-size: 12px;
}}
.fmt-btn.active {{
    background: #0070c9;
    color: #fff;
    border-color: #0070c9;
    cursor: default;
}}

/* DB spreadsheet preview */
.preview-db-spreadsheet {{
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
}}
.db-table-wrap {{
    flex: 1;
    overflow: auto;
    min-height: 0;
}}
.db-table {{
    border-collapse: collapse;
    font-size: 12px;
    width: 100%;
}}
.db-table th {{
    background: #f0f0f0;
    border: 1px solid #ddd;
    padding: 4px 8px;
    position: sticky;
    top: 0;
    z-index: 1;
    white-space: nowrap;
}}
.db-table td {{
    border: 1px solid #eee;
    padding: 4px 8px;
    white-space: nowrap;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
}}

/* DB KV row detail */
.preview-db-row {{
    padding: 1rem;
    overflow: auto;
    height: 100%;
    box-sizing: border-box;
}}
.db-kv-table {{
    border-collapse: collapse;
    width: 100%;
}}
.db-kv-table th {{
    text-align: left;
    padding: 4px 12px 4px 0;
    color: #666;
    font-weight: 600;
    white-space: nowrap;
    vertical-align: top;
    min-width: 120px;
}}
.db-kv-table td {{
    padding: 4px 0;
    word-break: break-word;
}}

/* DB pagination bar */
.db-pagination {{
    padding: 6px 8px;
    border-top: 1px solid #ddd;
    font-size: 12px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
    color: #555;
}}
.db-pagination a {{
    color: #0070c9;
    text-decoration: none;
    cursor: pointer;
}}
"""
```

## JavaScript stubs

The two JavaScript strings – `COLUMN_JS` for keyboard navigation, URL
sync, zoom, and dotfile toggling, and `LIVE_RELOAD_JS` for the SSE-driven
auto-refresh – are the capstone of the project. For now we leave them as
empty strings; Milestone 10 will fill them with the real implementation.

```python "column js"
""
```

```python "live reload js"
""
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md
uv sync
python -c "from filemill.styles import APP_CSS, COLUMN_JS; print(f'CSS: {len(APP_CSS)} chars, JS: {len(COLUMN_JS)} chars')"
```
