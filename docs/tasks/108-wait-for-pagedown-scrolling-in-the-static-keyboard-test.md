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
