---
depends-on: []
---

# Render Markdown and .docx in the browser in both editions

## Goal

One Markdown renderer and one `.docx` renderer, both in `ui/`. The server
edition loads them from its own origin, with no CDN and no consent switch.
The Python renderers and their dependencies are gone. Roadmap phase 6, step 1.

## Steps

1. Read `ui/adapters/preview-rich.js`. It loads pinned versions of
   `markdown-it`, four plugins and `mammoth` from `esm.sh`.
2. Download the same pinned ESM builds into `ui/vendor/`. Record each URL
   and version in `ui/vendor/README.md`. Keep the static bundle small: the
   static edition keeps the CDN path and the consent switch.
3. In `preview-rich.js`, resolve module names through `FILEMILL_CDN` first.
   In the server shell (`_ui_shell` in `app.py`), set `FILEMILL_CDN` to the
   `/ui/vendor/` paths and set the consent flag to on.
4. Port the link rules from `server/src/filemill/rendering.py` into the
   markdown-it setup: `[[PageName]]` wikilinks resolve to a sibling file with
   that name; relative links resolve against the document's folder; links to
   a file under the root become root-relative URLs.
5. Port the behaviour tests from `server/tests/test_rendering.py` (wikilinks,
   relative links, fenced code, footnotes, task lists) to `static/test-rich.py`.
   One check per rule. Run them in both editions.
6. In `ui/adapters/app-http.js`, use `PreviewRich` in the server edition for
   Markdown and `.docx`, and `PreviewHTTP` for virtual paths and `.pptx` only.
7. Delete `rendering.py`, `_preview_md` and `_preview_docx` in `preview.py`,
   `server/tests/test_rendering.py`, and the dependencies `markdown-it-py`,
   `mdit-py-plugins`, `linkify-it-py` and `mammoth` in `server/pyproject.toml`.

## Done when

- The same Markdown file shows the same HTML in both editions.
- `grep -n "markdown_it\|mammoth" -r server/src` prints nothing.
- The ported checks pass in `static/test-rich.py`. All server tests pass.

## Scope

`ui/adapters/{preview-rich.js,app-http.js}`, `ui/vendor/`, `app.py`,
`preview.py`, `rendering.py`, `server/pyproject.toml`, tests.
