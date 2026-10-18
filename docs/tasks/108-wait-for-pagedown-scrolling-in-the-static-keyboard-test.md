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
