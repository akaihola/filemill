---
depends-on: []
---

# PNG and JPEG preview works unreliably

## Original report

PNG and JPEG preview doesn't work reliably. Sometimes the text
`No inline preview for this file type.` is displayed instead of the image.

Hypothesis: any file above 0.5 gibibytes (2^20/2 bytes) causes the issue.

All files regardless of size should be previewed correctly. If there is a real concern
of large files causing other problems, a work-around needs to be created so at least
some kind of a preview instead of an error message is displayed.

## Example cases

All paths are relative to `agent@gogo:/home/agent/`.

### Images that do work correctly

- my-knowledge/pages/Life/Self-Development/assets/2024-09-15%20wheeloflife%20dot%20io%20results.svg
- my-knowledge/pages/Life/Tottila/assets/*.jpg
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_fi.jpg (516225 bytes)
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_fi%20(Kopio).png (516225
  bytes)
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo.jpg (501402 bytes)
- paivi/documents/kuvat/motivaatiojatkumo/The%20Motivation%20Continuum.jpeg
- repos/ai/hermes-agent/website/static/img/dashboard/admin-system-top.png (519615 bytes)
- repos/ai/hermes-agent/website/static/img/dashboard/admin-channels.png (521851 bytes)

### Images for which the error `No inline preview for this file type.` is displayed

- my-knowledge/pages/Life/Self-Development/assets/2024-09-29%20Discover%20Your%20Value%20Assessment%20akaihola.png
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_fi.png
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_NanoBanana.jpeg
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_v2.jpg
- paivi/documents/kuvat/motivaatiojatkumo/Motivaatiojatkumo_v3.jpg
- repos/ai/kandev/docs/screenshots/review%20dialog.png (528276 bytes)
