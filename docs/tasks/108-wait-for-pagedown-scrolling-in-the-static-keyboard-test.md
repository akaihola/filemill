# Wait for PageDown scrolling in the static keyboard test

Discovered 2026-10-19 while validating [103]. This is separate from A1/A3:
there were no changes to static assets or static tests relative to main
`97c77b63`.

## Reproduction

Run these suites concurrently from the repository root:

```bash
uv run pytest &
uv run pytest static/tests --bundle &
uv run pytest static/tests --dev &
wait
```

The development run intermittently fails
`static/tests/test_ui.py::test_keyboard_horizontal` at line 1434:

```text
await pg.keyboard.press("PageDown")
after = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
assert after > before, f"{before} -> {after}"
AssertionError: 0 -> 0
```

Observed development result: 1 failed, 146 passed in 543.60 s. The parallel
bundle run passed all 147 tests in 528.05 s. Running the single test against
unchanged main immediately afterwards passed in 6.44 s, so this reproduction
is intermittent. The assertion reads immediately after PageDown; asynchronous
native scrolling is a suspected cause, not yet established by an isolated
regression.

## Acceptance

Keep the keyboard navigation, preview focus and positive scrolling assertions.
Wait for observable scrolling where appropriate; do not add fixed sleeps or
relax the gate. Validate both static modes under concurrent browser-test load.

## Implementation plan, 2026-10-19

1. Run the horizontal keyboard test with normal scrolling and with scroll
   writes deferred across animation frames. Confirm that the unchanged
   immediate assertion fails in the deferred case.
2. Wait for each scroll key to move the preview in the expected direction.
   Keep all navigation, focus and positive scroll assertions.
3. Run the root, static bundle and static development suites concurrently.
   Run the repository quality gate. Record results before completion.

The deferred case failed at PageDown with `0 -> 0`; the normal case passed.
This proves that the immediate read can race a deferred scroll write. It does
not establish the browser's cause for the original intermittent failure.

## Implementation and validation, 2026-10-19

The test now waits for `scrollTop` to move in the expected direction after
PageDown, ArrowUp, ArrowDown and PageUp. All existing navigation, preview
focus and directional scroll assertions remain. The regression runs the same
scenario with normal scrolling and with the real `scrollBy` deferred across
three animation frames. There are no fixed sleeps or application changes.

- Red: before the waits, development mode had one pass and one failure. The
  deferred case failed at the PageDown assertion with `0 -> 0`.
- Green: concurrent targeted runs passed both cases in each static mode.
  Development took 8.79 s; bundle took 9.21 s.
- The first full concurrent run passed both keyboard cases in each mode.
  Bundle had 146 passes and two unrelated timeouts in 692.16 s. Development
  had 147 passes and one unrelated timeout in 724.07 s. Typeahead timed out
  in both modes; the 8 MiB scalar JSON preview timed out in bundle mode.
  Both tests and the application code are unchanged by this issue.
- Focused checks on unchanged canonical main passed under browser load.
  The scalar JSON bundle case took 31.50 s. Typeahead passed in both modes,
  taking 9.74 s for bundle and 10.14 s for development.
- The repository pre-commit gate, direct static-test Ruff checks and shared
  model checks passed. The first gate run detected a documentation edit
  during its execution. A second run passed with no concurrent edits.
- A second pair of full static runs overlapped the root browser suite.
  Both keyboard cases passed in each mode again. Bundle had 147 passes and
  one typeahead timeout in 651.87 s. Development had 147 passes and one RST
  viewport failure in 639.66 s. Chromium rejected a viewport resize with
  `Browser.setWindowBounds`: restore the window to normal state first.
  These failures remain outside this issue's scope. No gate was relaxed.
- The full root run passed all 1,079 tests in 1526.03 s with four Docutils
  deprecation warnings. This includes both keyboard cases and the tests that
  failed in separate static runs. Both static modes ran under concurrent
  browser load. The complete set of separate static runs was not all green.
- The full runs above used the base before issue [104] reached main.
  After rebasing onto `4e74ac69` and merging this test change, both keyboard
  cases passed concurrently in each mode again: bundle in 7.46 s and
  development in 7.58 s. The pre-commit gate also passed on the merged tree.
  The full suites were not repeated after that rebase.
