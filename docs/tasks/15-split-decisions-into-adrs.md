---
depends-on: []
---

# Split the decisions table into ADR files

## Goal

Each decision in the table in `static/AGENTS.md` is one ADR (architecture
decision record) file in `docs/adr/`. Roadmap phase 2, step 5.

## Steps

1. Create `docs/adr/` if needed. Continue the numbering after the last file.
2. For each row of the decisions table in `static/AGENTS.md`, write
   `docs/adr/NNNN-<slug>.md` with this shape:

   ```markdown
   # <Title>
   Date: <YYYY-MM-DD from git blame of the row, or today>
   ## Context
   ## Decision
   ## Measurement
   ## Consequences
   ```

   Copy the numbers from the table into `## Measurement`.
3. Replace the table in `static/AGENTS.md` with one link per ADR file.

## Done when

- Every row of the old table has one file in `docs/adr/`, under 40 lines.
- `static/AGENTS.md` has no table, only the links.

## Scope

`static/AGENTS.md` and `docs/adr/`.
