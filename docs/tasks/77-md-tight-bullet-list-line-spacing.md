Line spacing for bullet lists is much smaller than for normal paragraphs. This makes rendered Markdown files look out of balance. See `docs/tasks/line-spacing-screenshot.png`.
## Cause and fix (2026-10-07)

`ui/core/styles.css` set `line-height: 1.65` on `.pv-body p` only, so list items
kept the browser default (`normal`, about 1.2). The same rule now also covers
`.pv-body li`, giving bullets the paragraph colour and line height. The static
bundle `static/index.html` was rebuilt.

Validation: `test_markdown_list_items_share_paragraph_line_height` in
`server/tests/test_browser_new_ui.py` fails before the fix (`19.8px` vs
`normal`) and passes after it.
