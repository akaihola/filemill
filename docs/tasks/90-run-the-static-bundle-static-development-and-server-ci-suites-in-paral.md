---
depends-on: []
---

# Run the static bundle, static development and server CI suites in parallel

## Evidence, 2026-10-12

[Run 38155597653](https://github.com/akaihola/filemill/actions/runs/38155597653)
on 2026-10-11 took 15m 32s. The test job ran three independent suites in
sequence: static bundle, 210.02s; static development, 214.07s; server step,
452s. Lint took 15s and browser installation took 19s.

Splitting the suites should bring feedback time to roughly eight minutes at
those durations, subject to runner availability. This is an estimate from a
failed run, not a measured target. Missing ripgrep caused four 30-second
browser timeouts in that run; its installation is already in the workflow.

## Requirements

Change `.github/workflows/publish.yml` to run the suites as three independent
jobs or matrix legs after lint:

- `uv run --project server pytest static`.
- `uv run --project server pytest static --dev`.
- From `server/`, `uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing`.

Keep all current checks, including the shared model tests and bundle freshness
check. Each browser job installs through the locked server project's
Playwright. Install ripgrep in the server job before its tests. If using a
matrix, disable fail-fast so one suite's failure does not cancel the others.
Publishing must require lint and every test suite to pass, and remain limited
to main outside pull requests.

## Acceptance

- A failing regression check first demonstrates the current serial scheduling;
  the updated workflow passes checks for independent test jobs and publication
  gating. Update existing workflow guards for the final job structure.
- CI runs all three suites concurrently after lint, and each reports its result
  even if another suite fails. A failure in any suite prevents publishing.
- Record a before/after comparison including wall time, summed runner time,
  test counts and outcomes. Faster execution must preserve the quality gate in
  `docs/ARCHITECTURE-REVIEW.md`.
