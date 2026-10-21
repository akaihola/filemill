Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Labelled `review`: a verification, routed to GPT (steward decision D68). Estimated 1 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[44] (browser-test demo instances) waits in the review queue: the local instructions exist, but whether the documented instances can be found through the intended development dashboard was never checked. Triage section "Prepare the specific repairs", item "Filemill demo instances".

## Work

1. Read [44]'s request and the dashboard it names. Check with fixtures or an isolated run whether the documented instances are discoverable there.
2. Record any missing integration as it is, with the file that would need to change, instead of inferring it from the local instructions.

## Acceptance

- [44]'s task file gains a dated note: evidence that matches the original request, or the exact missing piece and a drafted issue for it.
- No deployment and no change to a running instance. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.
