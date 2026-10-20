# ADR 0086: New fold moves cancel older glides

Date: 2026-10-19. Issue: [94].

## Context

The fold dial can defer a smooth scroll until the next animation frame.
An older callback can then run after an instant move and replace it. A root
mount can also leave a native smooth scroll running. The refresh browser test
reproduced this: a fresh root ended with its only column folded and its rows
hidden. Two focused regressions failed with `folded === 1` and `dial() === 125`
where both values must be zero.

## Decision

Keep `layout.js` as the single scroll writer. Each smooth callback checks that
its glide is still current before it writes. An instant move cancels the
current glide. Mounting a root uses that instant move to reset the dial before
the first render. The reset clears the old settle timer, so the first layout
establishes the new scrollbar range at once. A restored path then uses the
existing layout rules.

The 2026-10-20 history reconciliation keeps the wheel-axis lock from
[ADR 0084]. The root reset also clears the old gesture's axis, accumulated
travel and preview latch. Cancelling its settle timer would otherwise leave
that axis active after the gesture ends. A browser regression first failed
because a sideways swipe after a root mount did not move the dial.

## Consequences

New roots start with visible rows. A queued glide cannot undo a later move.
The same behavior applies to all editions through the shared root mount.
Browser tests cover both cancellation cases and the full refresh scenario.
Preview reuse and general navigation cancellation remain A9 work.

[94]: ../tasks/94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md
[ADR 0084]: 0084-a-wheel-gesture-keeps-the-axis-it-started-on.md
