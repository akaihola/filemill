Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Labelled `review`: a verification, routed to GPT (steward decision D68). Estimated 1 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[The browser-test demo task][44] waits in the review queue: the local instructions exist, but whether the documented instances can be found through the intended development dashboard was never checked. Triage section "Prepare the specific repairs", item "Filemill demo instances".

## Work

1. Read [the original request][44] and the dashboard it names. Check with fixtures or an isolated run whether the documented instances are discoverable there.
2. Record any missing integration as it is, with the file that would need to change, instead of inferring it from the local instructions.

## Acceptance

- [The original task file][44] gains a dated note: evidence that matches the original request, or the exact missing piece and a drafted issue for it.
- No deployment and no change to a running instance. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.

## Verification plan, 2026-10-21

1. Recover the dashboard identity from the original task history. Trace its
   current source and installation rule.
2. Copy the original and current dashboard HTML to disposable fixtures.
   Check the three demo links without opening their destinations.
3. Add the dated evidence and any repair draft to [the original task][44].
   Keep link discovery separate from service availability and fixture parity.
4. Run documentation checks and the required gate under the memory guard.
   Merge the record to main and complete this verification, pending acceptance.

## Result, 2026-10-21

[The dated discovery record][evidence] contains the original request's
provenance, source revisions, snapshot hashes, a repeatable check and the
draft repair. The original dashboard has all three fixture links. The current
dashboard source and installed page have none. The required change belongs
to the external dashboard source named in that record.

The draft is deliberately unfiled. No endpoint, service, deployment or running
instance changed. The original demo task retains its unchecked acceptance.
This verification's two acceptance conditions are satisfied by the dated
evidence and repair draft.

## Validation

- **Discovery:** isolated HTML fixtures; original page passes, current source
  and installed page fail as expected. The combined probe exits 1 to expose
  the missing integration. The exact command in the task note was also run
  against all three snapshots, with exits 0, 1 and 1 respectively.
- **Documentation:** `uv run --project server pytest -q
  server/tests/test_docs.py` passed all 27 checks.
- **Repository gate:** `uvx pre-commit run --all-files` passed all seven
  hooks, including the static bundle consistency check.
- **Record checks:** relative reference targets exist; `git diff --check`
  passes. The architecture review now links the dated dashboard finding.
- **Boundary:** no destination availability, browser rendering or full
  browser-suite run is claimed. This change records a verified integration
  gap; its repair remains separate work.

## Memory guard

Commands ran sequentially with a process-group timeout and memory monitor.
The monitor enforced the 1024 MiB available-memory floor and 512 MiB maximum
swap growth. Every command was **started at once**, with a 0.0 s admission
wait. Values below are MiB; swap change is final use minus starting use.
No command was stopped. Each process group was cleaned up on exit.

| Command | Timeout | Admission | Final | Starting swap | Swap change | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Isolated discovery probe | 30 s | 2815.5 | 2820.5 | 2242.8 | 0.0 | 0.3 s | Exit 1 |
| Documentation tests | 180 s | 2887.4 | 2771.8 | 2241.4 | 0.0 | 12.0 s | Exit 0 |
| Pre-commit gate | 180 s | 2859.2 | 2879.6 | 2241.2 | -3.0 | 36.9 s | Exit 0 |

[44]: 44-browser-test-demo-instances.md
[evidence]: 44-browser-test-demo-instances.md#dashboard-verification-2026-10-21
