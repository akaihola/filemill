# ADR 0069: Hover reveals nothing on touch screens

Date: 2026-10-04.

## Context

On an iPad, the user had to tap a folder two times to open it in the next
column. The first tap did nothing that the user could see.

iOS Safari sends a tap as a hover first. If that hover makes hidden content
visible, Safari keeps the hover and does not send the click. The user must tap
again. A second tap works, because the hover state does not change again.

The ⟳ button in each column header is hidden. The stylesheet showed it on
`.col.focus` and on `.col:hover`. When the user opens a folder, the focus stays
on the column of that folder. The new column is not focused, so its ⟳ button
is hidden. The first tap on a row in that column set `.col:hover` and showed
the button. Safari then dropped the click.

The fault is specific to iOS Safari. Desktop Chromium, Firefox and Safari do
not drop a click after a hover change.

## Decision

On a device without hover (`@media (hover: none)`), a hover does not show
hidden content. The `.col:hover` rule for ⟳ is inside `@media (hover: hover)`.
The focused or busy column still shows ⟳ on every device.

A style that changes only colour or background on hover is safe. Do not use
`:hover` to change `visibility`, `display` or similar properties outside
`@media (hover: hover)`.

## Consequences

One tap opens a folder at every column depth on iOS. On a touch screen, ⟳ shows
only in the focused or busy column. With a mouse, hover shows it in any column,
as before.

`test_touch_tap_opens_folder_first_time` in `static/test-ui.py` emulates a
touch screen in Chromium. It checks that a hover on a row shows no new element.
Then it taps folders at three depths. Chromium does not drop the click, so the
test checks the cause, not the iOS behaviour. A check on a real iPad is still
necessary.
