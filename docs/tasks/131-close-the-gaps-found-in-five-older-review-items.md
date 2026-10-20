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


## Implementation, 2026-10-20

- Correct the historical import claim in [the reconciliation]. The imports
  existed at its snapshot; they were not a later regression.
- Condense [ADR 0036] to 37 lines, keeping its original decision and both
  dated corrections.
- Name the remaining UI thresholds, wheel conversion, menu spacing, copy
  formats and row overscan. Add one-line reasons to the tuning constants.
  [Model state] already names its formatting precision and unit constants.
  Zero/one bounds, index steps and unit exponents remain ordinary arithmetic.
- Add Docutils and Pygments stubs to the development groups in the
  [server configuration] and its [workspace mirror], and update the [lock file].
- Move the [archive provider] compatibility import to module scope. The
  Python-version guard keeps the package optional on Python 3.14+. Type
  checking sees the compatibility API on every supported Python version.

## Validation

The new structural checks first failed on the two local imports, the 46-line
ADR and unnamed or unexplained UI tuning values. Direct mypy first reported
four missing-stub errors. After the changes, the focused archive, document
and structural checks pass. Backend round trips cover the compatibility
package and the standard library with the optional package blocked.

Final results:

- `uvx pre-commit run --all-files`: all seven hooks pass.
- `uv run --project server mypy server/src` from the repository root and
  `uv run mypy src` from the server project: 16 source files pass. The root
  workspace command `uv run mypy server/src` also passes.
- Focused archive, documentation and structural tests: 47 pass.
- `node ui/core/model/test.mjs`: model checks pass.
- Browser selection covering folds, wheel state, virtual rows and menu copy:
  18 pass with `--bundle`. With `--dev`, 17 pass and the narrow-folder walk
  in `test_folding_dial` times out. That test passes alone on retry (42.49 s).
  No browser test or assertion was changed to obtain the pass.
- `git diff --check`: passes.

The focused commands are:

```bash
uv run --project server pytest -q server/tests/test_review_conditions.py server/tests/test_archive_provider.py server/tests/test_docs.py
uv run --project server pytest static/tests/test_model.py static/tests/test_ui.py --bundle -q -k 'virtual or folding or fold or wheel or copy_menu_unselected or long_press'
uv run --project server pytest static/tests/test_model.py static/tests/test_ui.py --dev -q -k 'virtual or folding or fold or wheel or copy_menu_unselected or long_press'
uv run --project server pytest static/tests/test_ui.py --dev -q -k test_folding_dial
```

No acceptance checkboxes change. No push or deployment is part of this work.

[the reconciliation]: 95-reconcile-tasks-md-with-the-code-16-in-progress-and-109-legacy-complet.md
[ADR 0036]: ../adr/0036-but-behind-a-remembered-switch-defaulting-on.md
[Model state]: ../../ui/core/model/state.js
[lock file]: ../../uv.lock
[archive provider]: ../../server/src/filemill/providers/archive.py

[server configuration]: ../../server/pyproject.toml
[workspace mirror]: ../../pyproject.toml
