---
depends-on: []
---

# Markdown previews show two Raw buttons

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-10 at HEAD
`7ff1fd2`.

For a Markdown file, the preview toolbar reads Raw, Rendered, Raw, Source,
Delete, Fullscreen (`ui/core/render.js:485-502`):

- `#pv-raw` links to the raw file and shows for every file type ([63]).
- `#pv-md-raw` is the second button of the Markdown view group `#pv-md-views`,
  titled "View raw Markdown source". It came with `a61e4eb` ("make Markdown
  views explicit").

Hide the extra one. Keep `#pv-raw`, which every file type shows. `#pv-view`
("Source") already shows the Markdown source; check what `a61e4eb` needed
`#pv-md-raw` for before removing it. WebVTT previews have the same pair
(`#pv-vtt-raw` in `#pv-vtt-views`); give them the same treatment.

The README screencast shows a Markdown toolbar in several scenes.

## Acceptance

- The toolbar of a Markdown preview, and of a WebVTT preview, shows one control
  labelled "Raw".
- Switching between rendered and source views of Markdown still works.
- A browser test checks the toolbar labels of a Markdown preview.

[63]: 63-preview-toolbar-controls.md

## Independent-review follow-up, 2026-10-11

Implemented R1 and R2 from thread `c4d572b0-2089-4760-b246-2942dbe59503`.

- Preview view state no longer depends on URL routing. Markdown and WebVTT
  switch between rendered and source views in the server's Open Folder mode,
  preserving the selection and address bar.
- The static bundle and module build share the server's source-highlighting
  wrapper. Static view changes retain the root folder name in the hash.
- The sole Raw link uses optional `FS.rawURL` for served files and local blobs
  otherwise. Local Raw opens the original bytes in a new tab. Object URLs are
  revoked on preview replacement or view change.

See [ADR 0077](../adr/0077-preview-views-and-raw-links-work-without-routing.md).

Validation:

- Red first: eight bundle/server regression cases failed, followed by four
  failures against the static module build.
- All new source, Raw-tab and Raw-lifecycle regressions pass in both static
  builds and the server's local-folder mode. Tests use the shipped Markdown
  renderer, compare exact source bytes, and cover keyboard activation.
- 21 adjacent server preview/history tests and 11 documentation tests pass.
- Full static module suite: 102 passed. Full static bundle suite: 101 passed,
  one failed at the existing RST Python-globals cleanup assertion. The focused
  rich-preview rerun passed all 51 internal checks without a code change.
  Raw-tab and lifecycle checks added during those runs also pass separately.
- Deno formatting/lint, model checks, Ruff, mypy, bundle consistency and
  `git diff --check` pass.

User acceptance remains pending.