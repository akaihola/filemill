---
depends-on: [32]
---

# Serve the shell for every representation except raw

## Goal

The URL contract in `urls.py` stays: `/path/file.md?filemill=render` and
`?layout=no-columns` keep working for readers and for the embedding
dashboard. The server no longer renders a representation. It sends bytes for
`raw` and the shell for everything else. The client renders the view.
Roadmap phase 6, step 2.

## Steps

1. Read `urls.py` and the `resource` route in `app.py`. Read `_ui_shell`: it
   already writes `data-filemill` and `data-layout` on `<html>`.
2. In `resource`, keep the `raw` branch and the directory redirect. For every
   other view and layout, return `_ui_shell(state, "/")`.
3. In `ui/core/`, read `document.documentElement.dataset.filemill`. When it is
   `highlight`, show the source view of the deep-linked file. When it is
   `render`, show the rendered preview. This replaces `render_source`.
4. In `ui/core/layout.js`, read `dataset.layout`. When it is `no-columns`,
   hide the columns and show the preview pane at full width.
5. Move the representation switch (the links that `_view_switch_html` made)
   to the shell in `ui/core/shell.js`, as one control in the preview header.
6. Delete `_view_switch_html`, `_representation_html`, `_document_page`,
   `render_source` and `_highlight_source`. Delete `pygments` from
   `server/pyproject.toml`.
7. Update `server/tests/test_resource_routes.py`: each non-raw request now
   returns the shell with the right data attributes. Keep `test_urls.py`.
8. Add one check in `static/test-ui.py` for `no-columns` and one for
   `highlight`, using the data attributes on a test page.

## Done when

- `curl -s localhost:8000/README.md?filemill=render` returns the shell with
  `data-filemill="render"`.
- `curl -s localhost:8000/README.md` returns the raw bytes.
- `grep -rn "pygments\|render_source" server/src` prints nothing.
- All static and server tests pass.

## Scope

`app.py`, `preview.py`, `urls.py`, `ui/core/{shell.js,layout.js,render.js}`,
tests.
