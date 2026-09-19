---
depends-on: []
---

# Keep ancestor folding unchanged during Up/Down navigation

## Original report and requirements

Task 04ce9574-92c8-4a4c-8148-32d2e827c13d didn't fix the erratic folding/unfolding of
the parent column. Hard rule: Up/down navigation must never change folding state of
ancestor folder columns.

## Related work

[46] records the earlier down-arrow-specific symptom. This follow-up states
the stronger invariant for both directions after an attempted fix.

[46]: 46-down-arrow-ancestor-unfolding.md
