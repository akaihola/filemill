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
