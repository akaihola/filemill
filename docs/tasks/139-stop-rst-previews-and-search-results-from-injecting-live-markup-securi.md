---
depends-on: [137]
---

Steward issue, 2026-10-21 02:45. Goal: agentic-leverage (filemill is a tier 1 project in `<steward-vault>/Goals.md`). Estimated 1.5 h.

[The 2026-10-21 security review](../reviews/2026-10-21-security-review.md) ([136]) found two ways for file content or a file name to inject live markup; this issue fixes both:

- **S2, "RST previews embed server files and live SVG markup":** docutils' image directive with `:loading: embed` makes the HTML writer read and inline the image file whatever `file_insertion_enabled` says, absolute paths and `file:` URIs included. An SVG is inlined with all its attributes, `_URL_ATTR` rewrites only ` href=` and ` src=`, and the browser assigns the result to `innerHTML` without `inert()`. Archive and bundle members reach the same renderer. This breaks SECURITY.md's promises of inert previews and the root check.
- **S4, "A file name injects attributes into search results":** `ui/core/search.js` escapes by serializing a text node, which leaves `"`, and puts the result into a double-quoted `data-path`. `ui/core/icons.js` already has an `esc()` that escapes `"`.

It depends on [137], because a red suite blocks every merge.

## What to do

1. Read S2 and S4 with their evidence in the review.
2. S2: refuse embedding in server RST rendering (reject or rewrite `:loading: embed`, or override the writer's embed branch), keep images inside the served root as links, and strip event-handler attributes, `xlink:href` and `data=` from preview output. Run server RST output through the same `inert()` step the browser applies to its own RST and DOCX output. Test an RST file that embeds an image from outside the root and one that embeds an SVG with an event handler; neither may inline the file or keep the handler.
3. S4: build search results with DOM nodes or the existing `esc()`, and test a file name containing `"` and an event attribute.

## Constraints and acceptance

- Memory: before each command, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start the command anyway when at least 1.5 GiB is available. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one heavy command at a time, and bound any background job you start.
- Test fixtures stay inside the test's temporary root; never read files outside it.
- Acceptance: the new tests pass; ordinary RST images and search results look as before; the full server suite and the static checks are green, and SECURITY.md's preview section matches the code.

## Outcome, 2026-10-21

- **S2, server.** [The preview module] renders reStructuredText with a
  docutils translator that treats `:loading: embed` as `link`, so the server
  never reads or inlines an image file. `lazy` is kept. The output is parsed
  with the standard library's `HTMLParser` and every tag written again
  without event-handler, `data` or `xlink:href` attributes; `href` and `src`
  keep the safe-URL rule and comments are dropped. This replaced the regex
  over quoted `href` and `src`, which missed a further hole found while
  probing: docutils writes a video's address and alternative text into its
  fallback link unescaped, so `:alt: <img src=x onerror=…>` produced a live
  handler. Members of archives and bundles use the same renderer.
- **S2, browser.** [The converter check] also drops `data` and `xlink:href`,
  and [the server boot] runs every server preview through it.
- **S4.** [Search] escapes paths, line context and errors with the shared
  `esc()` from `ui/core/icons.js`.
- **Decision and documents.** [ADR 0082] has a dated amendment.
  SECURITY.md, the changelog, [the architecture review] and
  [the security review] record the fix.

### Tests

Each new test failed before the fix:

- [The preview tests]: images from outside the served root, as an absolute
  path and a `file:` URI, and an SVG with `onload`, all under
  `:loading: embed`; video address and alternative-text injection; a guard
  that ordinary, embedded and lazy images inside the root stay
  `<img src="pics/cat.png">` links.
- [The API tests]: an RST member of a ZIP that embeds an SVG.
- [The served UI tests]: a routed `/api/preview` answer with `onerror`,
  `onload`, `xlink:href`, `data` and a `javascript:` link reaches the pane
  without them. A file named `quote" onmouseover="window.__xss=1" data-x=".txt`
  shows as one search result whose `data-path` is the whole name, carries no
  handler and opens the file.
- [The rich tests]: browser RST output with an SVG handler, `xlink:href` and
  `<object data>` keeps none of them.

Fixtures stay in each test's temporary directory: the "outside" files sit
beside the served root, not elsewhere on disk.

### Validation

- Full server suite on the rebased branch: 1189 passed, 1 failed in 24 min.
  The failure was the documentation portability guard, which cannot read a
  sandbox-masked `.claude/loop.md`. Run outside the sandbox, the
  documentation tests pass 27 of 27.
- Static checks: 173 passed with `--bundle`, 173 with `--dev`;
  `static/build-index.py --check` is up to date. Ruff, the format check,
  mypy, `deno fmt --check`, `deno lint` and the suppression-link guard pass.
- An ordinary 270 KB document's output took docutils about six times as long
  as the new parser pass, under heavy load (0.2 MB/s for the pass).

An earlier full run had a second failure,
`test_an_offline_copy_of_a_document_is_read_only`: after the reload the
worker had no copy of the root listing, and the welcome screen replaced the
pane. It is intermittent and not caused by this change. Run alone, it failed
2 times in 8 on this branch and 1 time in 12 with the base commit's sources,
with the same assertion. A likely cause, not verified: the test waits for
copies of the shell and of `/api/raw?p=README.md`, not of the listing, and
those copies can date from the first of its two page loads. The test is
unchanged here.

[The preview module]: ../../server/src/filemill/preview.py
[The converter check]: ../../server/src/filemill/ui/adapters/preview-rich.js
[the server boot]: ../../server/src/filemill/ui/adapters/app-http.js
[Search]: ../../server/src/filemill/ui/core/search.js
[ADR 0082]: ../adr/0082-previews-link-only-to-safe-protocols.md#embedded-images-and-server-output-2026-10-21
[the architecture review]: ../ARCHITECTURE-REVIEW.md#a2-preview-content-can-execute-as-filemill
[the security review]: ../reviews/2026-10-21-security-review.md
[The preview tests]: ../../server/tests/test_preview.py
[The API tests]: ../../server/tests/test_api.py
[The served UI tests]: ../../server/tests/test_browser_new_ui.py
[The rich tests]: ../../static/tests/test_rich.py
