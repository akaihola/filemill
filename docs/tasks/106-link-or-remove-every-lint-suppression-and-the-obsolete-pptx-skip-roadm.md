---
depends-on: [102]
---

# Link or remove every lint suppression and the obsolete PPTX skip (roadmap Phase 1)

Steward issue, 2026-10-18, filed from [102]'s audit. Goal: agentic-leverage.

The work, ground rules and acceptance are **Draft 1A** in
`docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md`,
section "Next issue drafts". Follow them as written, including "All drafts
inherit these ground rules".

Its two questions for Antti don't block the work: keep the literal
issue-link policy for every suppression (the draft's default), and keep
local pre-commit plus CI as the enforcement boundary. If a suppression can't
carry an issue link without a policy choice, list it here as a residual
instead of choosing. Record validation and remaining limits here.


## Completion evidence — 2026-10-19

Scope followed Draft 1A. No lint rules, security behavior, provider registration
order or Python compatibility target changed.

### Suppression inventory and corrections

The locked Ruff 0.16.7 reported nine diagnostics at the six suppression sites
with `uv run --project server ruff check server --ignore-noqa`: B008 at the
Typer root argument, S110 at two highlighting fallbacks and SQLite display-key
probing, F401 for four provider imports, and FLY002 at the fixed-wait guard.
None was unused under this Ruff version.

All six suppressions were removed:

- Construct the same Typer argument object once at module scope.
- Use `contextlib.suppress` for best-effort lexer and display-key probing.
  Return `None` explicitly on the outer highlighting failure.
- Import the same providers in the same order, then delete the module bindings.
  Registration has already stored their instances in the registry.
- Give the fixed-wait guard's name parts a variable before joining them.
  The searched name still does not occur literally in that guard.

The obsolete PPTX skip was inside a disabled multiline string containing the
retired LibreOffice renderer tests. Remove that entire dead block and its unused
PPTX builder. Active browser PPTX tests remain in `static/tests/test_rich.py`.
Conditional dependency and platform skips retain their existing reasons.

### Guard and gate

`server/tests/test_suppression_links.py` checks comments in every Git-tracked
Python file. Inline, Ruff file-level and Flake8 file-level `noqa` comments must
carry a `docs/tasks/N-description.md` issue path. Strings and docstrings do
not count. The guard checks syntax, not issue status, link existence or whether
the linked rationale is focused; review must still check those facts.

The new local pre-commit hook runs this guard. CI already runs all pre-commit
hooks in lint; the three browser suite jobs depend on lint, and publishing
requires lint plus all three suites. CONTRIBUTING.md records hook installation,
Ruff's inferred Python 3.12 target, the Deno 2.6.8 CI pin and these dependencies.
The literal issue-link policy and local pre-commit plus CI boundary are retained.

### Validation

- Red: the initial syntax fixtures failed for bare suppressions. With the guard
  implemented, the repository check failed on exactly the six original sites.
  A further red fixture caught Flake8 file-level syntax before it was supported.
- Green: `timeout 1800 uv run --project server pytest -q
  server/tests/test_suppression_links.py server/tests/test_browser_waits.py
  server/tests/test_preview.py server/tests/test_cli.py
  server/tests/test_providers_sqlite.py server/tests/test_vfs.py`:
  **109 passed**, one existing Docutils `writer_name` deprecation warning.
- `uvx pre-commit run --all-files`: all seven hooks passed, including Ruff,
  formatting, mypy, Deno, suppression links and the committed bundle check.
- A fresh Python process confirmed registry order: ArchiveProvider,
  GitBundleProvider, SQLiteProvider, VTTProvider.
- `git diff --check`: passed.

No suppression policy residual remains. Full browser suites and remote CI were
not run for this patch. No push, deployment, restart, remote settings change or
branch-protection change was made. Local gate success does not establish hook
installation by every contributor or protected-branch enforcement. Draft 0C
retains exact-main remote CI proof.
