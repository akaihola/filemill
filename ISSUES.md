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

## Open issues

_No open issues at this time._
