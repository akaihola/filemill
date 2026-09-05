---
depends-on: [21, 22]
---

# Write and test the narrow-screen layout model

## Goal

The narrow-screen layout has a written model and one test per device class.
Roadmap phase 4, step 5. See `docs/ARCHITECTURE-REVIEW.md`, finding 8.

## Steps

1. Read `applyScroll` and its parts in `ui/core/layout.js`, and the fold
   rules in `ui/core/state.js`.
2. Write `docs/adr/NNNN-narrow-screen-layout.md`. Answer these questions in
   the `## Decision` section, one sentence each:
   - Which columns fold when the viewport is narrower than the columns?
   - Which column pans into view after a tap or a key press?
   - Which column is promised to stay fully on screen?
   - What happens to the preview column?
3. In `static/test-ui.py`, add one check per device class. Use these
   viewports: phone portrait 390 x 844, phone landscape 844 x 390, tablet
   1024 x 768, desktop 1440 x 900.
4. Each check opens three levels of folders and asserts the promises from the
   ADR: the touched column is fully on screen, and the opened column is on
   screen.

## Done when

- The ADR exists and is under 40 lines.
- The four checks pass in `--dev` and bundle mode.

## Scope

`docs/adr/`, `static/test-ui.py`, `ui/core/layout.js` if a promise fails.
