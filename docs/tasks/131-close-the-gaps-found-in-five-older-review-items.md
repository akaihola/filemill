Steward issue, 2026-10-20 17:00. Goal: agentic-leverage. From the "Needs a fix" list of the steward's [evidence pass over filemill's 127 older review items](http://hopeli/my-knowledge/agents/steward/log/2026-10-20-filemill-older-evidence.md?f#needs-a-fix-10). Each item below sits under `## Completed / Accepted` as `[ ]`, but one of its own conditions doesn't hold on `main`, so it can't be accepted. Fixing the gap lets Antti accept it.

## Work

For each item, make its stated condition true on `main`, or, if that would be wrong, write the reason in the item's description (or under the item, for a legacy bullet without one) and leave the code alone. Don't change any `[ ]` or `[x]`.

1. **"Reconcile TASKS.md with the code" ([95](95-reconcile-tasks-md-with-the-code-16-in-progress-and-109-legacy-complet.md))**: its reconciliation said production had no function-local imports, but `server/src/filemill/providers/archive.py` imports `zstandard` inside two functions (lines 60 and 68, from 97ca55f1 on 2026-10-07). Correct that statement in its description file.
2. **"Split the decisions table in static/AGENTS.md into one dated ADR file per decision"**: ADR 0036 is 46 lines against the item's under-40-line criterion. Shorten it, or split it, without losing a decision.
3. **"Give each magic number in ui/core/state.js, layout.js, nav.js, render.js a name"**: `ui/core/layout.js` still has literal half-pixel thresholds, including lines 136 and 202. Name each remaining magic number in those four files with a one-line reason.
4. **"Add ruff and mypy to the dev group in server/pyproject.toml … Fix all findings"**: a direct `mypy` run reports four `import-untyped` errors for docutils and Pygments. Add their stub packages to the dev group, or a scoped override with a comment, so a direct run passes.
5. **"Reduce app.py to routing … No imports inside functions"**: the two `zstandard` imports above. Move them to module level with an optional-dependency guard, or record why they must stay lazy.

Leave the other five items of that list alone: they depend on removing `/api/preview` or are larger design changes.

## Acceptance

- Each of the five conditions holds on `main`, or its reason is written down.
- The repository gate and the focused tests for the touched files pass.
- No pushes or deploys.
