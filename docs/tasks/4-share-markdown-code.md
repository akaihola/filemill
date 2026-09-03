---
depends-on: []
---

# One renderer for Markdown fenced code, in both builds

Fenced code in a Markdown preview was coloured twice, differently. The static
edition downloaded highlight.js and its light-only stylesheet from a CDN
(`ui/adapters/preview-rich.js`); the server edition ran Pygments inside
markdown-it-py (`server/src/filemill/rendering.py`) — but the shared UI never
loads Pygments' stylesheet, so those spans arrived uncoloured. Source files,
meanwhile, were already coloured by `ui/core/syntax.js` in both builds.

## The seam

markdown-it (JS) and markdown-it-py emit the same fence markup when neither
has a highlighter configured:

```
<pre><code class="language-python">escaped source</code></pre>
```

So both renderers now emit exactly that, and `hlFences(host)` in
`ui/core/syntax.js` colours every `pre > code.language-*` once the fragment
is in the pane. It is called from one place, `fillPreview` in
`ui/core/render.js`, so every provider — server round-trip, upload, CDN
markdown-it — gets the same treatment. `HL_ALIAS` learned the spellings a
fence uses that a file extension does not (`python`, `javascript`, …).

Only `pre > code` nodes are touched. Paragraphs keep markdown-it's default:
a source newline inside a paragraph stays whitespace, never a `<br>`, and
`.pv-rich` gains no `white-space: pre-wrap`. Mermaid fences are a
`<div class="mermaid">` and are skipped by construction.

## What changed

- `ui/core/syntax.js`: `hlFences`, six fence-name aliases.
- `ui/core/render.js`: `fillPreview` calls `hlFences` after setting the pane.
- `ui/adapters/preview-rich.js`: highlight.js and its CSS are gone from the
  CDN list; markdown-it is created with no `highlight` option.
- `ui/core/styles.css`: the `.pv-rich .hljs` rule is gone.
- `server/src/filemill/rendering.py`: no `highlight` option, no Pygments.
  The `layout=no-columns` page shares this instance and therefore shows
  fences as plain `<pre><code>`; Pygments still colours whole source files.
- Tests: `server/tests/test_rendering.py`, `server/tests/test_browser_new_ui.py`,
  `static/test-rich.py` assert the shared classes and the intact paragraph.
