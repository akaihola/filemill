---
depends-on: []
---

# Make static/test-ui.py run to its end and fix its failing checks

## Goal

`static/test-ui.py` reports every check. One thrown `await` fails one check.
It does not stop the run. Then the three known failures are fixed.

## Steps

1. Read `main()` in `static/test-ui.py`. It is one long function of sections.
   Each section calls `check(name, cond, detail)`.
2. Wrap each section in a small `async def` or in a `try`/`except Exception`
   block. On an exception, call `check(name, False, str(exc))` and continue.
3. Run `cd static && ./test-ui.py --dev` and `./test-ui.py`. Save the list of
   failed checks.
4. Fix the `.pv-content` timeout. It is the check near line 1012 that waits
   for `inner_text(".pv-content")` to equal `"a"`. Find why the preview does
   not show. Fix the cause in `ui/`, not the test.
5. Fix the two "edit starts at the top" checks. The editor must open with the
   cursor at line 1, column 1, and the scroll position at 0.
6. Rebuild the bundle with `./build-index.py` if you changed `ui/`.

## Done when

- `./test-ui.py --dev` and `./test-ui.py` print zero failed checks.
- The run does not stop before the last section.

## Scope

`static/test-ui.py`, `ui/core/`, `ui/adapters/`. See
`docs/ARCHITECTURE-REVIEW.md`, finding 1.
