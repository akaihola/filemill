Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h. Unlabelled.

This is draft D3 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Browser PPTX" and "Draft issues"). It holds the acceptance of the tracker item "Render `.pptx` in the browser …", and the stylesheet cleanup's follow-up depends on it.

## Why

The PPTX request probe confirms local slide-text extraction and the removal of the Python runtime renderer, but fails because the preview API still exists for other formats and virtual members.

## What to do

Inventory the remaining direct and virtual-member consumers of the preview API, then move only those consumers to the existing raw-byte access and browser renderer registry. Preserve RST heading slices, archive and member identity, source-versus-rendered behaviour, offline fallback and content limits before deleting the route. Keep this a renderer migration with no new framework. If a required capability can't be preserved, stop and record the exact unsupported case in this task record for the steward rather than deleting it.

## Constraints

- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- No preview-API route or client caller remains; the Python PPTX renderer and its runtime package stay absent.
- Real PPTX text, RST slice and archive-member regression tests pass, plus both browser modes (development and bundle), with no supported rendering capability removed.
- The root suite passes as CONTRIBUTING.md says.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).

## Steward decision, 2026-10-23 17:20

**Option 3.** Keep the narrowed route as the server edition's
reStructuredText renderer. It keeps offline rendering with no third-party
download, the hidden download switch approved in [118] and immediate
rendering, and it adds nothing. Options 1 and 2 each give up one of those
or add about 13 MB of vendored runtime, which is Antti's call.

The first acceptance item now reads: no preview-API route or client caller
remains except the narrowed `/api/preview` for served reStructuredText
(files, their heading sections and `.rst` archive or bundle members), which
answers 404 for every other kind; the Python PPTX renderer and its runtime
package stay absent. Finish with the check receipt at the merged commit and
the completion move.

The tracker items "Render `.pptx` in the browser …" and "Delete
`server/src/filemill/styles.py` …" keep their own text. Their "delete
`/api/preview`" and "no other server route emits HTML" conditions stay
unmet for this one route and wait for Antti's choice between keeping it
and option 1.

## Inventory, 2026-10-23

The only client caller was `PreviewHTTP` in [the server composition]. Server
routes and helpers behind it were `api_preview` in [the app module],
`member_preview_response` and the unused `preview_fragment` in [the API
module], and `render_preview` in [the Python preview module]. The native and
static editions never called the route.

| Consumer | Before | After |
| --- | --- | --- |
| Served `.rst` file | `/api/preview?p=` (docutils) | Unchanged: the unsupported case below |
| `.rst` heading section | `/api/preview?p=&lines=` | Unchanged: the unsupported case below |
| `.rst` archive or bundle member | `/api/preview?p=&v=` | Unchanged: the unsupported case below |
| Local-folder `.rst` (Open Folder) | `/api/preview?p=undefined`, 404, then source | Browser source; no request (A8) |
| Member: image, PDF, HTML, `.desktop`, WebVTT, video, text and source | `/api/preview?p=&v=`, temporary file, Python suffix dispatch | Browser registry from `/api/raw?p=&v=` bytes, by the member's own kind |
| Member in `?filemill=highlight` | `/api/preview` (rendered: HTML iframe, RST output) | Browser source for kinds with colouring, as for files (A8) |
| Member over the provider read limit | Server "Too large to preview" HTML | Raw route 413; the browser shows "Too large to preview." |
| Markdown, `.docx`, `.pptx` member | Already browser | Unchanged |

Preserved: archive and member identity (`p` and `v` stay separate; the raw
route keeps the hidden-path and provider checks); RST heading slices; the
16 MiB member and 512 KiB text limits; offline copies (the server worker
keeps `/api/raw` reads, and `HTTP.blob` marks them stale); the HTML sandbox;
the Python PPTX renderer and `python-pptx` runtime package stay absent.

## Unsupported case for the steward: served reStructuredText

**Stopped short of deleting `/api/preview`.** The route now renders
reStructuredText only and answers 404 for every other kind. Its remaining
client is `PreviewHTTP`, for served `.rst` files, their heading sections and
`.rst` archive or bundle members.

The browser renderer registry's only RST renderer is docutils on Pyodide
([ADR 0002], [ADR 0064]): 5.9 MB on the wire and 12.9 MB decoded, from
jsDelivr. The server edition serves its other renderer modules from
`/ui/vendor/` and hides the download switch because it needs no third-party
module; the user approved that in [118]. Moving served RST to the registry
would remove one of these capabilities:

- RST rendering with no third-party download and no internet access, on a
  LAN or offline-from-internet server;
- the hidden download switch: it would reappear, and turning it off or
  losing the CDN would show RST as source with an offline note;
- immediate rendering: first use would take seconds (ADR 0064 measured
  6–15 s cold).

Options for the steward:

1. Vendor Pyodide 0.29.4 and the docutils wheel under `ui/vendor/` (about
   13 MB in the repository and wheel). `/ui/{path}` would need `.wasm`,
   `.zip`, `.json` and `.whl` media types, `FILEMILL_CDN` a `pyodide` entry,
   and `app-http.js` the `rst` registry entry instead of `PreviewHTTP`.
   Sections and members already reach the renderer through `FS.blob`.
2. Accept the CDN in the server edition: register the `rst` entry, delete
   the route, and accept the switch, network and latency changes above.
3. Keep the narrowed route as the server edition's RST renderer, and amend
   this issue's and [163]'s "no preview route" acceptance to allow it.

[ADR 0094] records the member migration and this case. Until the steward
chooses, this issue's first acceptance item is unmet, and [163] stays blocked.
[160] is unblocked: archive members no longer reach the Pygments highlighter.

## Red evidence, 2026-10-23

- API tests, before the implementation: 13 failed (non-RST file and member
  preview requests returned 200 instead of 404).
- New browser tests, run in a clean checkout of the base commit with only the
  new tests applied: 10 failed and 1 passed. The failures were
  `test_a_local_rst_file_makes_no_server_preview_request`, six
  `test_a_member_renders_in_the_browser_from_its_bytes` cases (code, desktop,
  PDF, WebVTT, HTML, image), two
  `test_a_member_in_the_source_view_shows_its_source` cases (HTML and RST),
  and `test_an_oversized_member_says_so` (it requested `/api/preview`). The
  pass was `test_an_rst_member_is_still_rendered_by_the_server`, a
  preservation check.

## Validation, 2026-10-23

Commands ran from the repository root on the branch rebased onto main
`937b4e8c`. The shards ran on `3207b587`. Before the merge, the implementation
commit gained only the README, roadmap and server README wording and the
static test fix below.

- Quality gate, run as its hook commands: Ruff, Ruff format, mypy, Deno
  format and lint, the suppression-link guard and bundle freshness passed. The
  static bundle is unchanged. `node ui/core/model/test.mjs` passed.
- `server/tests/test_docs.py`: 29 passed with the sandbox off; the sandbox
  hides a file the portability guard reads.
- Focused browser run (`-k "member or local_rst_file or archive or bundle or
  rst or cdn or registers"`): 49 passed.
- Root shards, `timeout 1800` each: keyboard 67 passed; served-ui-early 162
  passed (162 deselected); served-ui-late 162 passed (162 deselected);
  server-contracts 904 passed; static-ui 83 passed.
- static-adapters: 109 passed, 1 failed. Static development suite: 192
  passed, 1 failed. Both failures were `test_rst_viewport` in the static rich
  tests: it imported the renamed `_preview_rst`. The test now calls
  `render_rst` with the file's bytes.
- After the fix, on `1b8b097d`: static-adapters 110 passed, and
  `timeout 1800 uv run pytest static/tests/test_rich.py --dev` 16 passed. With
  the earlier runs, the six root shards and the static suite in both modes
  pass. The other 192 development tests did not change.
- No evidence receipt was recorded. This issue is not complete, so the
  completion move was not made.

## Memory reports

All guarded runs: **started at once**, with no wait (0–1 s). Each admission
was above 2 GiB, and no run hit a stop threshold. Peak swap growth is the
highest reading while the run lasted.

| Command | Admission / final MemAvailable | Start swap | Swap growth (final, peak) | Elapsed | Exit |
| --- | --- | --- | --- | --- | --- |
| First red browser run, superseded (edits landed mid-run) | 2597 / 2648 MiB | 2661 MiB | 83, 92 MiB | 155 s | 1 |
| Red browser run at the base commit | 2801 / 2581 MiB | 2762 MiB | 77, 85 MiB | 173 s | 1 |
| Focused green browser run | 2759 / 2547 MiB | 2838 MiB | −3, 12 MiB | 201 s | 0 |
| keyboard shard | 2921 / 2849 MiB | 2797 MiB | 21, 21 MiB | 600 s | 0 |
| served-ui-early shard | 2849 / 2949 MiB | 2818 MiB | −5, 5 MiB | 513 s | 0 |
| served-ui-late shard | 2946 / 2556 MiB | 2813 MiB | 1, 7 MiB | 744 s | 0 |
| server-contracts shard | 2556 / 2643 MiB | 2814 MiB | −35, 0 MiB | 49 s | 0 |
| static-ui shard | 2643 / 2926 MiB | 2779 MiB | −23, 0 MiB | 450 s | 0 |
| static-adapters shard | 2926 / 2723 MiB | 2756 MiB | 16, 17 MiB | 334 s | 1 |
| static development suite | 2723 / 3140 MiB | 2772 MiB | 19, 29 MiB | 774 s | 1 |
| static-adapters shard, rerun | 3115 / 2744 MiB | 2786 MiB | −62, 0 MiB | 329 s | 0 |
| static rich tests, development mode, rerun | 2744 / 2717 MiB | 2724 MiB | −4, 0 MiB | 101 s | 0 |

[the server composition]: ../../ui/adapters/app-http.js
[the app module]: ../../server/src/filemill/app.py
[the API module]: ../../server/src/filemill/api.py
[the Python preview module]: ../../server/src/filemill/preview.py
[ADR 0002]: ../adr/0002-rst-in-browser.md
[ADR 0064]: ../adr/0064-rst-browser-evaluation.md
[ADR 0094]: ../adr/0094-the-browser-renders-members-the-server-only-restructuredtext.md
[118]: 118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md
[160]: 160-retire-the-remaining-python-source-highlighter-and-its-pygments-depend.md
[163]: 163-check-that-no-server-preview-html-route-remains-after-the-preview-api-.md
