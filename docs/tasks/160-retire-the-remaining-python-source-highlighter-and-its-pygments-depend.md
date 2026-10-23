Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1 h. Unlabelled.

This is draft D1 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Shell representations" and "Draft issues"). It holds the acceptance of [[33]](33-shell-for-every-representation.md).

## Why

[33]'s required grep still finds Pygments and `render_source`, and Pygments remains a runtime dependency. Raw bytes and the render/highlight shell checks pass. The separate no-columns mismatch is an authorized supersession: [the accepted layout decision](../adr/0067-drop-no-columns-layout.md) and the accepted removal item require fallback to full-columns.

## What to do

Trace current `render_source` callers and remove the unused Python source-highlighting path, its obsolete tests and the runtime dependency once browser source coverage is confirmed. Keep the accepted no-columns removal and cite its supersession in [33]'s record with a dated note. The RST and archive-member preview API migration is a separate issue, [[162]](162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md); don't delete its live consumers here. If a live caller remains that only that migration can remove, stop and say so in this record.

## Constraints

- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- [33]'s grep has no Pygments or `render_source` matches, and the runtime dependency is gone from `server/pyproject.toml` and the lock.
- Bare and raw byte and render/highlight shell tests pass, alongside the accepted no-columns fallback test.
- The root suite passes as CONTRIBUTING.md says.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).

## Investigation, 2026-10-23

**Blocked by the remaining preview API migration.** Stop condition reached;
no implementation or dependency removal was made.

- `render_source()` has no production callers. Its callers are tests in
  [the preview tests].
- `_highlight_source()` still has a production caller in `render_preview()`
  in [the Python preview module]. It colours source previews before the
  plain-text fallback.
- `withServerVirtualPreview()` in [the HTTP composition] sends archive
  members to `PreviewHTTP.render()`, including Python members and members
  requested in Source mode. That calls `/api/preview`.
- `member_preview_response()` in [the API module] writes member bytes to a
  temporary file and calls `render_preview()`. The existing
  `test_a_member_previews_as_the_file_it_is` in [the API tests] requires
  highlighted HTML for an archived Python file. Git bundle members use the
  same path.

Removing the highlighter or its runtime dependency now would remove live
archive-member highlighting. Moving these consumers to browser rendering
belongs to [the remaining preview API migration], which this task explicitly
excludes. The steward can resume this task after that migration. The unused
source entry point and its tests remain together until then.

The required grep still matches, and the runtime dependency remains. Root
suite and browser qualification were not run: this investigation does not
claim the removal acceptance criteria. No acceptance receipt was recorded,
no implementation was merged, and the issue remains In Progress.

The accepted no-columns fallback is unchanged. A dated supersession note was
added to [the shell representation record].

[the preview tests]: ../../server/tests/test_preview.py
[the Python preview module]: ../../server/src/filemill/preview.py
[the HTTP composition]: ../../ui/adapters/app-http.js
[the API module]: ../../server/src/filemill/api.py
[the API tests]: ../../server/tests/test_api.py
[the remaining preview API migration]: 162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md
[the shell representation record]: 33-shell-for-every-representation.md

## Focused validation, 2026-10-23

Command (four cases passed, exit 0):

```bash
timeout 1800 uv run pytest server/tests/test_docs.py::test_documentation_uses_portable_development_examples server/tests/test_api.py::test_a_member_previews_as_the_file_it_is server/tests/test_resource_routes.py::test_retired_no_columns_layout_falls_back_to_full_columns
```

This confirms the live archive-member contract, the accepted layout fallback
and portable documentation. It does not qualify highlighter removal.

Memory report for that command: **started at once**; wait 0.0 s;
admission MemAvailable 3222 MiB; final MemAvailable 3267 MiB;
starting swap use 2742 MiB; final and peak swap growth 0 MiB;
elapsed 12.0 s; completion exit 0.


## RST dependency recheck, 2026-10-23

Rebased onto main `e409e13959b6969873d447f3daa8b9bcf37fe651`, including
[162] and [163]. The archive-member blocker above is superseded: archive
and Git bundle members now render from bytes in the browser. The separate
`render_source()` entry point has no production callers.

**Blocked: served RST code blocks still need Pygments through docutils.**
The narrowed `/api/preview` route calls `render_rst()` in [the Python preview
module]. Its `publish_parts()` call keeps docutils' default syntax
highlighting. Docutils 0.23 uses Pygments internally for a language-labelled
code block. This dependency is separate from Filemill's unused source
highlighter.

The following probe used the unchanged route. It sets docutils' own
`with_pygments` availability flag to false after imports, simulating its
missing-package branch without uninstalling packages or changing the route.
The separate unused Filemill highlighter was never invoked.

```bash
timeout 120 uv run python - <<'PYCODE'
import tempfile
from pathlib import Path

import docutils.utils.code_analyzer as analyzer
from starlette.testclient import TestClient

import filemill.app as module

source = ".. code-block:: python\n\n   def answer():\n       return 42\n"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "code.rst").write_text(source)
    module.app.state.root = root
    with TestClient(module.app, base_url="http://localhost") as client:
        baseline = client.get("/api/preview", params={"p": "code.rst"})
        original = analyzer.with_pygments
        try:
            analyzer.with_pygments = False
            missing = client.get("/api/preview", params={"p": "code.rst"})
        finally:
            analyzer.with_pygments = original
    assert baseline.status_code == missing.status_code == 200
    assert '<span class="keyword">' in baseline.text
    assert '<span class="keyword">' not in missing.text
    assert "Pygments package not found." not in baseline.text
    assert "Pygments package not found." not in missing.text
PYCODE
```

The equivalent saved-script probe passed, exit 0. With Pygments, the response
contains `<span class="keyword">def</span>` and
`<span class="literal number integer">42</span>`. Without it, the response
contains plain `<code>def answer():\n    return 42</code>` with no token
spans. No warning appears in either response: `report_level=5` suppresses
it. The loss of code highlighting alone meets the user's stop condition.

Two earlier probe attempts were corrected: the default TestClient host was
rejected with 403 (exit 1); then an assertion expecting a visible warning
failed (exit 1). The final probe uses localhost and asserts the observed
absence of that warning. Neither failure is an application regression.

Antti must choose how to preserve served RST code-block highlighting before
Pygments can be removed. No route, implementation, dependency or lockfile
change was made. The unused highlighter was left intact under the explicit
stop instruction. The issue stays In Progress. Root and browser suites and
the full quality gate were not run; no removal acceptance or merge receipt
is claimed, and no implementation was merged.

Memory reports for the saved-script command
`timeout 120 uv run python /tmp/filemill-160-rst-probe.py`:

- **Initial host probe:** started at once; wait 0.0 s; admission
  MemAvailable 2819 MiB; final 2724 MiB; starting swap 2257 MiB;
  final growth -1 MiB, peak growth 0 MiB; elapsed 2.0 s; exit 1.
- **Localhost warning probe:** started at once; wait 0.0 s; admission
  MemAvailable 2777 MiB; final 2799 MiB; starting swap 2256 MiB;
  final and peak growth 0 MiB; elapsed 1.0 s; exit 1.
- **Confirmed highlighting-loss probe:** started at once; wait 0.0 s;
  admission MemAvailable 2815 MiB; final 2811 MiB; starting swap 2256 MiB;
  final and peak growth 0 MiB; elapsed 1.0 s; exit 0.

[162]: 162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md
[163]: 163-check-that-no-server-preview-html-route-remains-after-the-preview-api-.md

Documentation check passed (one case, exit 0):

```bash
timeout 1800 uv run pytest server/tests/test_docs.py::test_documentation_uses_portable_development_examples
```

Memory report: **started at once**; wait 0.0 s; admission MemAvailable
2805 MiB; final MemAvailable 2809 MiB; starting swap 2256 MiB;
final and peak swap growth 0 MiB; elapsed 2.0 s; exit 0.
