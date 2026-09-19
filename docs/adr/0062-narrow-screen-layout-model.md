# ADR 0062: Stable folder widths and preview space

Date: 2026-09-19

## Context

Folder-name measurements and content-dependent preview targets changed column
widths and automatic folding during navigation. The shared static and server UI
needs the same width rules before and after folder contents arrive.

## Decision

- Desktop folders are `20em` wide, using the inherited column font. At the default
  12px density this is 240px, one sixth of a 1440px laptop viewport. Comfortable
  density uses 13px text and 260px columns. Viewport width and names do not change
  this desktop width.
- Phone portrait uses half the viewport width when viewport width is at most
  600px. Phone landscape uses a quarter when viewport height is at most 600px.
  These are viewport rules, not device detection. A short desktop window also
  uses the landscape rule. A square viewport uses the portrait rule.
- The preview fills the remaining strip width and reserves one third of the live
  finder width, whether empty or showing a file. The finder spans the viewport.
  Preview content scrolls inside its pane; an 88ch source line does not widen it.
  Preview controls wrap so that narrow panes do not hide their actions.
- Automatic folding starts at the left and folds the fewest ancestors needed
  when the remainder is strictly less than one third. Equality does not fold.
  The calculation includes both outside paddings, all gaps and folded spines.
  Tests allow 1px for browser geometry rounding, not an earlier fold threshold.
- Automatic folding never folds the focused column or columns to its right.
  Existing folds remain until the user unfolds them. Manual scrolling, spine
  clicks, compressed layout, no-columns layout and fullscreen keep their roles.
- If protected columns and spines leave too little room, the preview can extend
  beyond the finder. This can occur even on a shallow portrait path. Keeping the
  touched column whole takes priority over the preview minimum. When that column
  overflows, the strip pans left only far enough to reveal it. The stage never
  scrolls.
- Selection changes preserve logical fold position rather than a pixel offset
  with a new meaning. A manual partial fold remains partial. Preview focus alone
  does not resize or fold columns. Left returns to the containing column.
  When a new column or density consumes the preview reserve, keyboard selection
  adds the necessary ancestor folds just as mouse selection does. This applies
  at whole-column dial positions; manual partial folds remain authoritative.

The rules live in `ui/core/styles.css`, `folderWidth()` and `previewTarget()` in
`ui/core/dom-renderer.js`, and `automaticFold()` in `ui/core/model/folding.js`.
`render()` uses the live width for every node. `layout()` preserves fold position
when the path or viewport changes. DOM column caching remains in place.

## Measurement

Model tests cover the folding threshold below, at and above equality, multiple
folds, focus protection and retained folds. Browser tests cover 1440×900,
1024×768, 390×844 and 844×390, the 600px boundary, rotation and both densities.
They compare long and short names, empty and file previews, delayed directory
loads, mouse selection and keyboard navigation. Frame sampling checks that
loading and selection do not partially fold the focused column.

## Consequences

Long names truncate instead of widening columns. More ancestors can remain
visible on desktop than with the old content-based preview target. Deep-spine
panning tests need longer paths because phone columns are narrower. Changes to
these rules must update this ADR and both editions' geometry checks.
