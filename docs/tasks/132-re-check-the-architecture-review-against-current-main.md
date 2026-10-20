Steward issue, 2026-10-20 20:00. Goal: agentic-leverage (filemill is a tier 1 project in `<steward-vault>/Goals.md`). Labelled `review` (steward decision D68). Estimated 1.5 h.

[The architecture review](../ARCHITECTURE-REVIEW.md) was checked against commit `1cb03863` on 2026-09-25. Since then `main` has gained 191 commits besides tracker moves and about 16,000 changed lines under `server/src`, `static` and `native`. Findings may be resolved, stale or missing, and the remediation order may no longer fit.

## What to do

1. Re-read the cited code for each finding at current `main` and record that commit. Mark each finding open, changed, or resolved; move a resolved one to "Resolved since the earlier reviews" with the commit or issue that resolved it.
2. Review the code added since `1cb03863` for new findings, in the document's style and severity scale. Apply the `honey` principles (over-engineering, speculative generality, dead code, verbose code) and the deep-module vocabulary of the `codebase-design` skill where they are installed. Cite files and lines.
3. Update "Architecture as it is" where the code moved, and rewrite "Remediation order" for what is left.
4. Under a new "Draft issues" heading at the end, draft one issue per new P1 or P2 finding: title, why, what to change, acceptance. Don't file them; the steward does.

## Constraints and acceptance

- Documentation only: no code, test or tracker changes besides this issue's own moves.
- The documentation tests stay green: `server/tests/test_docs.py` rejects private paths and host names in Markdown.
- Memory: before each command, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start the command anyway when at least 1.5 GiB is available. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB.
- The document names the commit it was checked against, and every finding has a status.
