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

The examples below use generic filenames in place of private source paths.
The extensions and recorded byte sizes are unchanged.

### Images that do work correctly

- `images/results.svg`
- `images/photos/*.jpg`
- `images/diagram-fi.jpg` (516225 bytes)
- `images/diagram-fi%20(copy).png` (516225 bytes)
- `images/diagram.jpg` (501402 bytes)
- `images/diagram%20continuum.jpeg`
- `images/dashboard-system.png` (519615 bytes)
- `images/dashboard-channels.png` (521851 bytes)

### Images for which the error `No inline preview for this file type.` is displayed

- `images/assessment.png`
- `images/diagram-fi.png`
- `images/diagram-generated.jpeg`
- `images/diagram-v2.jpg`
- `images/diagram-v3.jpg`
- `images/review%20dialog.png` (528276 bytes)

## Diagnosis (2026-09-28)

Every failing example is over 512 KiB (524 288 bytes); every working one is under.
Two causes, both already fixed on `main` before this review:

- `PreviewLocal.render` declined any file over `TEXT_MAX` before fetching it, images
  included. Fixed in `5d55bd4`, which limits that gate to text. Only the static edition
  had a regression test, with fake image bytes.
- Until `fbd49ae` (2026-09-21), the server's service worker answered navigations from
  its cache first. A shell cached before `5d55bd4` kept loading the old, versioned
  modules, so a page opened from a stale URL still showed the message. Which pages were
  stale depended on browsing history, hence "sometimes".

On 2026-09-28 all six failing examples previewed and decoded on the deployed service.
`server/tests/test_browser_new_ui.py::test_an_image_past_the_text_ceiling_is_previewed`
now covers the server edition with real PNG and JPEG files over the ceiling. It fails
when the old size gate is restored and passes on `main`.

The static edition's `sw.js` still serves `index.html` stale-while-revalidate, so the
first load after a deployment runs the previous bundle. That is architecture finding
A5 (remediation step 4), not this issue.
