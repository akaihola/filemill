Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D1 of [the 2026-10-22 architecture review][drafts], filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Move the meaningful parser fixtures to tests that exercise the registered JavaScript VTT renderer, then remove Python `parse`, its helpers, `default_fmt` and `render_preview`. Keep the small empty-listing provider and its registration, and update the provider test/source map.

## Acceptance

- Timestamps, voices, YouTube metadata and blank payloads, malformed input and source preservation keep coverage on the live implementation.
- Ordinary VTT listing, raw bytes, empty virtual listing and suffix URLs keep their responses.
- No application code calls the deleted renderer; no cross-language parser generator replaces it.
- Update the A12 entry in [the architecture review][architecture] to say what is done.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker][tracker].

## Implementation plan

1. Pin the live registered JavaScript renderer with the meaningful Python
   fixtures. Pin the provider registration and HTTP responses before deletion.
2. Remove the unreachable Python parser and renderer. Keep the empty-listing
   provider and registration. Update A12 and the source/test map together.
3. Run focused browser, provider and documentation checks and the quality gate,
   one command at a time with memory monitoring. Rebase and merge to main,
   then complete the tracker entry pending acceptance.

This removes no reachable behavior or port, so no new ADR is needed.

## Outcome, 2026-10-22

Removed Python `parse`, `_cue`, `_read`, regex helpers, `default_fmt` and
`render_preview`. The provider keeps only `handles`, empty `list_entries`
and registration. Current production dispatch never called the removed code;
no JavaScript implementation, port or response behavior changed.

The [shared UI browser tests][browser-tests] now run the former Python
fixtures through `renderNode` and the application-registered VTT renderer.
They cover timestamps, voices, tags, multiline cues, YouTube metadata and
blank payloads, malformed headers and cues, orphan text, empty transcripts,
and exact escaped CRLF source. Existing tests still cover Source and Rendered
navigation. The [provider tests][provider-tests] pin case-insensitive
registration, ordinary listing as a file, original raw bytes, empty root and
nested virtual listings, and a successful virtual-suffix shell response.
The [source/test map][test-map] and A12 now describe this split. No parser
generator or replacement abstraction was added.

## Verification

- Before deletion: 22 focused VTT checks passed, including the new pinning
  tests and the old Python renderer tests. This is a behavior-preserving
  retirement; pinning preceded the implementation change.
- After deletion: all 16 focused VTT checks passed.
- Documentation checks: all 27 passed.
- Caller review: the only remaining production references to `vtt_provider`
  are registration imports; no caller needs the removed methods.
- Full browser suites were excluded as required by this issue. Native checks
  do not apply to this Python deletion and browser-test transfer.
- Quality gate: each check passed, but the first invocation returned exit 1
  because this task record was edited while the suppression hook ran.
  Pre-commit reported a changed file; the hook's 11 tests passed. The second
  gate invocation passed all seven hooks with exit 0.

## Memory guard

Each command had a 1,800-second timeout and ran alone. The guard checked host
memory and swap every 0.5 seconds, with the launch prompt's stop thresholds.
Readings below use MiB. No command was stopped by the guard.

- **started at once:** `uv run --project server pytest -q server/tests/test_vtt_provider.py server/tests/test_browser_new_ui.py -k vtt`; wait 0.0 s; admission MemAvailable 2352; final 2315; starting swap 2466; swap growth 29; elapsed 104.7 s; exit 0.
- **started at once:** `uv run --project server pytest -q server/tests/test_vtt_provider.py server/tests/test_browser_new_ui.py -k vtt`; wait 0.0 s; admission MemAvailable 2428; final 2513; starting swap 2494; swap growth -3; elapsed 45.2 s; exit 0.
- **started at once:** `uv run --project server pytest -q server/tests/test_docs.py`; wait 0.0 s; admission MemAvailable 2476; final 2163; starting swap 2490; swap growth 0; elapsed 4.6 s; exit 0.
- **started at once:** `uvx pre-commit run --all-files`; wait 0.0 s; admission MemAvailable 2317; final 2332; starting swap 2489; swap growth -188; elapsed 26.6 s; exit 1.

- **started at once:** `uvx pre-commit run --all-files`; wait 0.0 s; admission MemAvailable 2401; final 2379; starting swap 2301; swap growth 0; elapsed 4.0 s; exit 0.

[architecture]: ../ARCHITECTURE-REVIEW.md#a12-smaller-defects-dead-code-and-audits

[drafts]: ../reviews/2026-10-22-architecture-review.md#draft-issues
[tracker]: ../../TASKS.md

[browser-tests]: ../../server/tests/test_browser_new_ui.py
[provider-tests]: ../../server/tests/test_vtt_provider.py
[test-map]: ../../server/CONTRIBUTING.md#source-layout
