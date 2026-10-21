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

[44]: 44-browser-test-demo-instances.md
