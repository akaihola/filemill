---
depends-on: []
---

# Fix PPTX previews that show unspaced slide text in both modes

## Original report and requirements

Bug: PPTX preview only shows the text found on the slides, and omits spaces and
linefeeds between blocks of text. The preview looks identical in both `Source` and
`Rendered` views. Task c6f1a55d-3d5d-4259-823f-34ad83f18ef3 failed to implement proper
PPTX preview. This issue is probably complicated, so let's get help from a strong
language model and deep online research.

## Related work

This is a later defect report after task `c6f1a55d-3d5d-4259-823f-34ad83f18ef3`.
Keep it separate from the completed slide-text renderer and CDN viewer migration
in [TASKS.md](../../TASKS.md). Their completion does not resolve this report.
