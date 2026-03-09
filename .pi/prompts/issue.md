---
description: Add a new open issue to ISSUES.md and TASKS.md
---

Add a new issue to this pykofinder project for: $ARGUMENTS

Steps:

1. Read `ISSUES.md` to find the current highest issue number and determine the next one.
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
