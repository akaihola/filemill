# Issues

Each issue has an explicit **Status** field: `open`, `in-progress`, or `closed`.

When closing an issue, set `**Status:** closed` and add a `**Closed:** YYYY-MM-DD` date.
**Closed issues are pruned from this file immediately upon closing** – their full text
lives in git history and can be retrieved with the commands below.

---

## Finding past issues in git

Closed issue blocks were removed from this file to keep the agent context lean.
The full text of every issue is preserved in git history.

```bash
# Show every commit that touched ISSUES.md (one line each)
git log --oneline -- ISSUES.md

# Search commit messages for an issue number or keyword
git log --oneline --all --grep="#24" -- ISSUES.md
git log --oneline --all --grep="keyboard" -- ISSUES.md

# Show the full diff for a specific commit (replace <hash> with the commit hash)
git show <hash> -- ISSUES.md

# Show the state of ISSUES.md as it was at a given commit
git show <hash>:ISSUES.md | less

# Grep across ALL historical versions of ISSUES.md for a keyword
git log -p -- ISSUES.md | grep -A 20 "ArrowLeft must update"

# Find the commit that removed a specific issue block
git log -p -- ISSUES.md | grep -B 5 "^-## #34"
```

---

## #43 – Mobile preview fills 100 % width; rightmost column peek needed as scroll hint

**Type:** UX
**Status:** open

After #42, `#preview` is given `min-width: 90vw` on narrow viewports, but in practice it expands to fill the full available width, leaving no visible edge of the directory column to signal that the user can scroll left. The peek – a few pixels of the rightmost column visible on the right – is the essential affordance that makes the swipe gesture discoverable.

**Planned fix / implementation sketch:**

- Change the mobile media-query rule in `styles.py` from `min-width: 90vw` to a fixed `width: 90vw` (with `flex-shrink: 0` and `max-width: 90vw`) so the preview cannot grow past 90 % of the viewport regardless of content width.
- Ensure `#finder` retains `overflow-x: auto` so the remaining 10 % column peek is reachable by scrolling.
- Update the corresponding tests in `tests/test_rendering.py` that assert the mobile CSS values.

---

## Open issues

_No open issues at this time._
