---
description: Add a new open issue to ISSUES.md and TASKS.md
---

Add a new issue to this filemill project for: $ARGUMENTS

Steps:

1. Determine the next issue number by taking the maximum of:
   - The highest `## #N` number visible in the current `ISSUES.md`, and
   - The highest number ever used in the full Git history of `ISSUES.md`:
     ```bash
     git log -p -- ISSUES.md | grep -oE '^\+## #[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1
     ```
     Add 1 to whichever is larger. This prevents reusing a number that was
     assigned to a closed (and therefore pruned) issue.
2. Read `TASKS.md` to understand the open backlog.
3. Write a concise issue block and insert it into `ISSUES.md` just before the `## Open issues` heading, using this exact format:

```
## #N – <title>

**Type:** bug | feature | UX | test | chore | refactor
**Status:** open

<One or two sentences describing the problem or desired behaviour. Include root cause if known.>

**Planned fix / implementation sketch:**

- <bullet points describing the approach, files to change, etc.>
```

4. Add a matching `[ ] #N <title>` line to the **Open** section of `TASKS.md`.
5. Commit both files: `git commit -m "docs: open issue #N – <title>"`

Keep the block factual and brief. Do not mark the issue in-progress; leave that for `/plan`.
