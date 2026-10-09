---
depends-on: []
---

# Markdown in archives is not rendered

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-09 at HEAD
`7ff1fd2`, in the server edition.

A Markdown file on disk shows rendered. A Markdown member of an archive shows
as highlighted source.

The browser renders Markdown and `.docx` from the modules in `ui/vendor/`
(`ui/adapters/app-http.js:73-83`). An archive member preview comes from the
server instead: `member_preview_response` (`server/src/filemill/api.py:315`)
calls `render_preview`, which does not dispatch Markdown or `.docx`
(`server/src/filemill/preview.py:57-62`). `member_preview_response` says a
member renders "the way the same file would render on disk".

## Acceptance

- A Markdown member previews rendered, like the same file on disk.
- A `.docx` member previews rendered, like the same file on disk.
- Decide if a Markdown member also opens as columns of its headings, like on
  disk. Record the decision.
