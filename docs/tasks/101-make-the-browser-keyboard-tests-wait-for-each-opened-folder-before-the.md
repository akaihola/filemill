# Make the browser keyboard tests wait for each opened folder before the next key

Steward issue, 2026-10-18. Goal: agentic-leverage (filemill is a tier-1
project in `/home/agent/my-knowledge/pages/Goals.md`). The roadmap's Phase 0
wants both suites green on `main`, and a red run holds back acceptance of
everything else.

[100] found `server/tests/test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor`
timing out under suite load, at `focusCol === 1 && path.length >= 2`, while
it passed five isolated reruns in 2.25–2.61 s. It presses ArrowRight before
the folder opened by ArrowDown has loaded. [99]'s `88766300` added that wait
to the sibling `test_arrow_navigation_keeps_fold_animation_running`, but not
to this test. Other browser tests may share the pattern.

## Work

1. Reproduce under load, the way [100] did: run the server suite with the
   two static suites in parallel, and note which browser tests time out.
2. Audit every browser test under `server/tests/` and `static/tests/` that
   presses a key depending on a folder, column or preview that an earlier
   key started loading, without waiting for it. List each test with its
   verdict in this file.
3. Add the missing waits the way `88766300` did, in test code only. If a
   test shows the UI itself dropping or misapplying a key, that is a
   product finding: report it with its evidence and leave the test as it
   is.
4. Validate: each changed test passes five isolated reruns, and the full
   server suite passes twice in a row on the branch, with `--durations=20`.

## Ground rules

- Change only tests under `server/tests/` and `static/tests/`, this
  description file and the issue's tracker moves. No product code.
- Follow `AGENTS.md`: red-green, so record the failing run under load
  before the fix.
- Don't push, deploy or restart services.

## Acceptance

- The audit list is here, and every test it marks as racing waits for the
  state it needs.
- Two consecutive full server-suite passes, recorded in a
  `## Result, YYYY-MM-DD` section with their commands and timings.
