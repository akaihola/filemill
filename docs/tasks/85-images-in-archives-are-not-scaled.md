---
depends-on: []
---

# Images in archives are not scaled to the preview pane

## Original report and requirements

A review session found this on 2026-10-09 at HEAD
`7ff1fd2`, in the server edition.

An image file on disk shows scaled to the pane width and to at most 46% of the
window height (`ui/core/styles.css:1140-1142`). An image member of an archive
shows at its natural size. A 1600 px wide image overflows the preview pane.

The member preview comes from the server: `member_preview_response`
(`server/src/filemill/api.py:315`) calls `render_preview`, and
`_preview_image` (`server/src/filemill/preview.py:210`) returns
`<div class="preview-image"><img …></div>`. No CSS rule scales that markup.
`member_preview_response` says a member renders "the way the same file would
render on disk".

## Acceptance

- An image member shows at the same size as the same image on disk.
- A browser test checks a member image wider than the pane.
