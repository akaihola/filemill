# pykofinder – LMT milestones

This directory contains a literate-programming reconstruction of the
`pykofinder` Python source tree. Tangling the milestone files in order
rebuilds the project step by step.

## Reading order

1. [Foundation](01-foundation.md) – package metadata and the first runnable CLI stub
2. [Visual design](02-styles.md) – CSS, theming, and formatter setup
3. [Virtual filesystem protocol](03-vfs.md) – VFS abstractions and registry
4. [Column generation](04-columns.md) – breadcrumb and column HTML generation
5. [File previews and Markdown rendering](05-preview.md) – rendering pipeline and preview dispatcher
6. [The web application](06-app.md) – FastHTML routes, path safety, deep links
7. [Command-line interface](07-cli.md) – Typer and uvicorn wiring
8. [VFS providers](08-providers.md) – SQLite, JSON, and CSV providers
9. [Progressive Web App](09-pwa.md) – manifest, service worker, icons
10. [Browser-side behaviour](10-keyboard-js.md) – keyboard navigation, URL sync, dotfiles, zoom, live reload

## Tangling

To tangle the complete project into a fresh output directory:

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
~/go/bin/lmt ../lmt/01-*.md ../lmt/02-*.md ../lmt/03-*.md ../lmt/04-*.md \
  ../lmt/05-*.md ../lmt/06-*.md ../lmt/07-*.md ../lmt/08-*.md ../lmt/09-*.md \
  ../lmt/10-*.md
```

Then install and run it:

```bash
uv sync
uv run pykofinder --help
```

## Notes

- The literate milestones cover `pyproject.toml` and the Python source tree under `src/pykofinder/`.
- The PNG icon files referenced by the manifest are not reproduced directly in LMT because they are binary assets; `09-pwa.md` explains how to regenerate them from the SVG.
- Each milestone includes its own verification commands so you can tangle and inspect the project incrementally.
