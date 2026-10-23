Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1.5 h. Unlabelled.

This is draft D2 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Shared browser fixtures" and "Draft issues"). It holds the acceptance of the tracker item "Run the static and server browser tests through one root `conftest.py` and one Playwright …".

## Why

The request probe still finds `async_playwright`, a Chromium launch and a persistent-context launch in [the static fixture module]. The keyboard suite now uses the shared root browser and has no CDN proxy, but the requested root lifecycle ownership is not complete.

## What to do

Move ordinary asynchronous and persistent-profile browser lifecycle ownership into root fixtures alongside the synchronous fixture. Keep static page construction and fake filesystem setup local. Preserve separate sync and async API adapters, native driver selection, per-test isolation and the persistent profile that folder-handle restoration needs; don't force incompatible event loops through one object.

## Constraints

- Test infrastructure only; no production code change.
- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- A source guard finds browser lifecycle startup only in the root fixture owner, and every suite consumes it.
- The six root shards, the static development suite, the folder-restoration checks and the independent collection checks pass, without weakened assertions or restored CDN proxy plumbing.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker].

## Plan

1. Extend the lifecycle source guard to include suite fixture modules and
   reject all startup outside the root fixture owner. Confirm failure first.
2. Move asynchronous driver selection, browser startup and the persistent
   storage context into root fixtures. Keep static pages and fake handles local.
3. Run the six shards, development mode, folder restoration, independent
   collections and quality gate sequentially under memory monitoring.
4. Merge, record checks against the clean merged commit, and complete the
   tracker item pending acceptance.

This changes test ownership only; no application port or behavior changes.

## Implementation

Root fixtures now own the served module browser, ordinary asynchronous
browser and persistent storage context. Driver selection still supports
the native adapter. Fixture scopes, launch options, per-test pages and
persistent profiles are unchanged. Static page construction and fake
filesystem setup remain local. No CDN proxy was added.

The source guard first failed on six startup calls in the served module
fixture and static fixture module. It passes after the move. It now walks
all Python files in both test trees and gives fixtures no exemption.

## Validation before merge

- Source guard: 1 passed after the expected red run.
- Folder restoration: 1 passed, 82 deselected, bundle mode.
- Quality gate and model checks passed.
- Collection comparison passed: all 1,503 root IDs match the six shards
  with multiplicity and both independent suite collections.
- The first collection comparison used the wrong expected prefix for
  independent collection IDs. Pytest retains the repository prefix when
  invoked from a suite directory. The comparison script was corrected;
  this was a check-script failure, not a product failure.

## Resource reports before merge

Each command ran alone under host memory monitoring. Values are MiB.
The monitor stops the process group below 1,024 available or above 512
swap growth; each command is bounded by a timeout.

- Command: `timeout 1800 uv run pytest static/tests/test_ui.py -k storage --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3467/3369;
  starting swap 2744, maximum growth 4;
  elapsed 10.0 s; exit 0.

- Command: `timeout 1800 bash -c "uvx pre-commit run --all-files && node ui/core/model/test.mjs && python3 /tmp/filemill-161/collections.py"`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3481/3426;
  starting swap 2747, maximum growth 0;
  elapsed 27.0 s; exit 1.


[the static fixture module]: ../../static/tests/conftest.py
[Filemill's tracker]: ../../TASKS.md

- Command: `timeout 1800 python3 /tmp/filemill-161/collections.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3450/3378;
  starting swap 2742, maximum growth 1;
  elapsed 11.0 s; exit 0.

## First merged qualification and correction

The first merge passed keyboard (67), served UI early (157), served UI
late (156), and server contracts (930). Static UI failed: 75 passed,
one failed and seven setup errors. The theme test requested the static
`browser` fixture directly and instead received the root synchronous
served browser, leaving its event loop active. Later asynchronous setup
then failed too. No assertions were changed.

A local asynchronous `browser` adapter now returns the root
`async_browser`. This preserves existing direct consumers, including
save-safety tests, while startup and teardown stay in the root owner.
The failing theme case and following editor-features case both pass
after this correction. Remaining first-merge checks were not started;
all acceptance checks will be recorded against the corrected merge.

### First merge resource reports

Each row describes one evidence-recording call. Commands are the
acceptance commands wrapped by `check-evidence.py record`.

- Command: `timeout 1800 uv run pytest server/tests/test_browser_keyboard.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3248/3395;
  starting swap 2737, maximum growth 29;
  elapsed 339.6 s; exit 0.

- Command: `timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=early`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3398/3389;
  starting swap 2762, maximum growth 14;
  elapsed 319.6 s; exit 0.

- Command: `timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=late`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3394/3244;
  starting swap 2753, maximum growth 5;
  elapsed 390.8 s; exit 0.

- Command: `timeout 1800 uv run pytest server/tests --ignore=server/tests/test_browser_keyboard.py --ignore=server/tests/test_browser_new_ui.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3248/2931;
  starting swap 2717, maximum growth 0;
  elapsed 25.0 s; exit 0.

- Command: `timeout 1800 uv run pytest static/tests/test_ui.py --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2934/3013;
  starting swap 2713, maximum growth 14;
  elapsed 281.5 s; exit 1.

- Command: `timeout 1800 uv run pytest static/tests/test_ui.py -k "theme or editor_features" static/tests/test_save_safety.py server/tests/test_browser_lifecycle.py --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2997/3133;
  starting swap 2706, maximum growth 0;
  elapsed 7.0 s; exit 0.

## Final merged qualification

The final tested commit is `937b4e8ca1a3ed243023c08db5bd9fbb260ba880`.
The base before the corrective merge is
`e4e36a370441f58ea92a0d3a4c5d0ec11e33a4f5`; its delivery commit is
`937b4e8ca1a3ed243023c08db5bd9fbb260ba880`.
The earlier implementation commits are `99e86ce0` and `f6197ccd`.
All final checks ran from a clean detached checkout of the final tested
commit. The [check receipt] records commands, dependencies and results.

| Check | Final result |
| --- | --- |
| keyboard | 67 passed |
| served-ui-early | 157 passed, 156 deselected |
| served-ui-late | 156 passed, 157 deselected |
| server-contracts | 930 passed |
| static-ui | 83 passed |
| static-adapters | 110 passed |
| static-dev | 193 passed |
| folder-restoration | 1 passed, 82 deselected |
| collections | 1,503 IDs match six shards and independent suite collections |
| quality | All seven pre-commit hooks passed |
| model | Passed |

The six shards cover all 1,503 root tests. The lifecycle source guard
passes in server contracts. Both independent suite collections pass.
No assertions were weakened and no CDN proxy plumbing was restored.

### Retained failed attempts

The first early served UI run at the final commit failed
`test_a_vertical_swipe_over_a_column_ignores_sideways_drift`:
the dial was 10 instead of 0. Recorded wheel gaps were 95.2, 232.9
and 138.2 ms. The helper documents that gaps beyond 180 ms split
a gesture. The complete shard passed on one unchanged retry.
This remains evidence of sensitivity to host timing; no assertion,
gesture threshold or production code was changed.

The first final quality command could not start pre-commit because
PyPI timed out after three fetch retries. Running the same gate with
`uvx --offline` used the cached tool and passed all hooks.

### Final resource reports

Each command below ran through `check-evidence.py record`, one at a
time, under memory monitoring. All normal admissions waited zero
seconds and started above 2,048 MiB. The readings below describe the
recording calls, including their acceptance command subprocesses.

- **collections:** `timeout 1800 python3 /tmp/filemill-161/collections.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2658/2720 MiB;
  starting swap 2757 MiB, maximum growth 0 MiB;
  elapsed 23.1 s; exit 0.

- **folder-restoration:** `timeout 1800 uv run pytest static/tests/test_ui.py -k storage --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2837/2656 MiB;
  starting swap 2757 MiB, maximum growth 0 MiB;
  elapsed 8.0 s; exit 0.

- **keyboard:** `timeout 1800 uv run pytest server/tests/test_browser_keyboard.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2835/2791 MiB;
  starting swap 2705 MiB, maximum growth 142 MiB;
  elapsed 399.9 s; exit 0.

- **model:** `timeout 1800 node ui/core/model/test.mjs`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2872/2870 MiB;
  starting swap 2752 MiB, maximum growth 0 MiB;
  elapsed 1.0 s; exit 0.

- **quality:** `timeout 1800 env MYPY_CACHE_DIR=/tmp/filemill-161/mypy uvx --offline pre-commit run --all-files`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2717/2769 MiB;
  starting swap 2750 MiB, maximum growth 2 MiB;
  elapsed 32.1 s; exit 0.

- **served-ui-early:** `timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=early`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2869/2552 MiB;
  starting swap 2752 MiB, maximum growth 49 MiB;
  elapsed 540.8 s; exit 0.

- **served-ui-late:** `timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=late`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 3127/2857 MiB;
  starting swap 2798 MiB, maximum growth 23 MiB;
  elapsed 676.2 s; exit 0.

- **server-contracts:** `timeout 1800 uv run pytest server/tests --ignore=server/tests/test_browser_keyboard.py --ignore=server/tests/test_browser_new_ui.py`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2859/2706 MiB;
  starting swap 2816 MiB, maximum growth 0 MiB;
  elapsed 64.3 s; exit 0.

- **static-adapters:** `timeout 1800 uv run pytest static/tests --ignore=static/tests/test_ui.py --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2706/2776 MiB;
  starting swap 2814 MiB, maximum growth 9 MiB;
  elapsed 502.4 s; exit 0.

- **static-dev:** `timeout 1800 uv run pytest static/tests --dev`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2773/2880 MiB;
  starting swap 2806 MiB, maximum growth 14 MiB;
  elapsed 1059.3 s; exit 0.

- **static-ui:** `timeout 1800 uv run pytest static/tests/test_ui.py --bundle`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2928/2828 MiB;
  starting swap 2700 MiB, maximum growth 6 MiB;
  elapsed 317.6 s; exit 0.

- **served-ui-early, failed attempt:** `timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=early`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2795/3089 MiB;
  starting swap 2812 MiB, maximum growth 50 MiB;
  elapsed 474.6 s; exit 1.

- **quality, network failure:** `timeout 1800 env MYPY_CACHE_DIR=/tmp/filemill-161/mypy uvx pre-commit run --all-files`.
  Outcome: started at once; wait 0.0 s;
  available admission/final 2716/2722 MiB;
  starting swap 2756 MiB, maximum growth 0 MiB;
  elapsed 50.1 s; exit 1.


No checks remain skipped, stopped or unverified. Completion is pending
steward acceptance.

[check receipt]: 161-move-the-remaining-static-browser-lifecycles-into-the-root-test-fixtur.evidence.json
