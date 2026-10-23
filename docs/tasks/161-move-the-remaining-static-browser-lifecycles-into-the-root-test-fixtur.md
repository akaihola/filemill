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
