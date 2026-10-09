---
depends-on: []
---

# Screen-reader search label shows on screen

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-09 at HEAD
`7ff1fd2`.

`ui/core/shell.js:21` gives the search label the class `sr-only`:

```html
<label class="sr-only" for="search-bar">Search file contents</label>
```

No stylesheet in `ui/` defines `.sr-only`. The text "Search file contents" shows
in the top bar, between the breadcrumbs and the search box. It shows in both
editions and in every screen.

The Filemill README screencast records the top bar in every frame. Fix this
before the screencast is captured.

## Acceptance

- The label is not visible.
- The search box keeps the accessible name "Search file contents".
- A browser test checks both.
