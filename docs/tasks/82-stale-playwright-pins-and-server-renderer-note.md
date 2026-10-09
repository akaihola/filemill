---
depends-on: []
---

# Update stale Playwright 1.61 pins and the server renderer note

## Original report and requirements

A session in `~/prg/filemill-screencast` found these on 2026-10-09 while it read
the documents to plan a screencast.

### Playwright pins

`server/pyproject.toml:58` pins `playwright~=1.63.0`. `server/uv.lock` locks
1.63.0. `$PLAYWRIGHT_BROWSERS_PATH` holds `chromium-1243` and
`chromium_headless_shell-1243`. These places still name 1.61:

- `README.md:134-136`: `uv run --with "playwright==1.61.0"` for the static tests.
  `--with` overrides the pin, so these commands fail to launch a browser.
- `server/CONTRIBUTING.md:174-178`: says the Nix bundle holds revision 1228 and
  only 1.61.x launches.
- `static/FSA-TEST-CHECKLIST.md:9`
- `static/measure-rst.py:4`
- `static/test-e2e.py:8`
- `.github/workflows/publish.yml:80`: CI installs 1.61.0 and downloads its own
  browser, so it still works. Decide if CI follows the local pin, and say why in
  a comment.

The comment at `server/pyproject.toml:50-57` is correct. It names 1.61.0 as a
measured failure.

One version number repeated in six files goes stale again at the next bump.
Consider one source, for example "the version in `$UV_CONSTRAINT`".

### Server renderer note

`ui/adapters/README.md:60-63` says `app-http.js` adds only `.pptx` from
`preview-rich.js`, because the Python renderers keep Markdown, `.docx` and
`.rst`. `ui/adapters/app-http.js:73-83` adds `md`, `markdown`, `docx`, `pptx`
and `offline`. Only reStructuredText stays with Python. `README.md`, section
"server — the Python edition", already says this.

## Acceptance

- No document or script names a Playwright version that cannot launch the
  browsers in `$PLAYWRIGHT_BROWSERS_PATH`, except as a recorded measurement.
- `ui/adapters/README.md` matches `ui/adapters/app-http.js`.
