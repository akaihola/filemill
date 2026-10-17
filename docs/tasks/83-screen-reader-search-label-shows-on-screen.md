---
depends-on: []
---

# Screen-reader search label shows on screen

## Original report and requirements

A review session found this on 2026-10-09 at HEAD
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

## Resolution (2026-10-10)

`ui/core/styles.css` now defines `.sr-only` next to the search rules: a 1 px,
clipped, absolutely positioned box. The label stays in the accessibility tree,
so the search box keeps its accessible name. `static/index.html` was rebuilt
from `ui/`, so both editions carry the rule.

`server/tests/test_browser_new_ui.py::test_search_label_is_read_aloud_but_not_shown`
failed before the fix (label box 105 × 14 px) and passes after it. It checks
that the label's box is at most 1 × 1 px and that `#search-bar` has the
accessible name "Search file contents".
