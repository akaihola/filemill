Steward issue, 2026-10-21 23:50, from Antti's review of the security approvals. Goal: agentic-leverage (Filemill is tier 1 in `<steward-vault>/Goals.md`). Labelled `security`: it changes a trust boundary, so it stays on Claude (steward decision D68). Estimated 1.5 h.

The steward's review of [139] found that it fully fixes S4 and the file-reading half of S2, but only narrows the script half of S2 ([the security review](../reviews/2026-10-21-security-review.md)). docutils writes some directive fields (a video's alt text and address among them) into its HTML as raw markup. The server's `_Inert` pass in `server/src/filemill/preview.py` and the browser's `inert()` both remove a fixed list of attributes but keep every element and every other attribute. So a crafted `.rst` file in a browsed folder can still place frames, embeds, forms, a base element or SVG animation in the preview pane. Filemill sets no Content-Security-Policy and serves raw HTML unsandboxed on its own origin, which makes those elements matter.

## What to change

1. Replace both denylists with one allowlist of the elements and attributes docutils actually writes for the directives Filemill renders, the way the `.docx` path already does. Drop anything else as text or remove it; keep the existing safe-protocol rule for links and image sources.
2. Apply the same allowlist to reStructuredText rendered in the browser.
3. Correct SECURITY.md's statement that markup in RST text stays text, and add a line to ADR 0082 or a new ADR.

## Acceptance

- Server and browser tests: a frame, embed, form, base or SVG animation element arriving through a directive field (video alt text and address included) is rendered as text or removed, and an ordinary RST document (headings, lists, tables, code, links, images, admonitions) renders as before.
- The existing preview, API and rich-preview tests pass.
- Defensive scope only: no payloads or exploit steps in the code, tests, commit messages or thread beyond the minimal element names the tests need.
- Don't restart `filemill.service` or `filemill-public.service`: the running instances predate [138], and a restart before hopeli's home-manager rebuild would refuse the hostnames they are reached by (see nixos-config's [Give every deployed Filemill the hostnames it is reached by before its next restart](http://hopeli/repos/nixos-config/docs/tasks/79-give-every-deployed-filemill-the-hostnames-it-is-reached-by-before-its.md?f)). The steward restarts them once that is deployed.

## Outcome, 2026-10-22

- **Server.** [The preview module] lists the elements and attributes
  docutils' HTML5 writer produces, `RST_TAGS` and `RST_ATTRIBUTES`. The
  list was read from rendering every standard directive and role, and a set
  of math, with docutils 0.23 (the server's) and 0.21.2 (Pyodide 0.29.4's),
  and checked against the writers' source. It includes the MathML docutils
  0.23 writes for math. `_Inert` writes an element only when it is listed and
  replaces any other with its contents; an attribute stays only when it is
  listed, and `href` and `src` keep the safe-protocol rule. An image docutils
  would write as a plugin `<object>` keeps only its text.
- **Browser.** [The converter check] has the same list as `RST_HTML` and
  applies it to the reStructuredText Pyodide renders. [The server boot]
  applies it to the server's reStructuredText; the server's other previews
  keep the plain check, so their frames stay.
- **One list.** A test reads `RST_HTML` from the script and compares it with
  the server's sets.
- **Documents.** SECURITY.md no longer says markup in reStructuredText text
  stays text. [ADR 0082] has a dated amendment, and the changelog,
  [the architecture review] and [the security review] record the change.

Not changed: `class`, `style` and `id` stay with any value, as docutils
writes them, so a document can still style and position its own content.

### Tests

Each new element test failed before the fix:

- [The preview tests]: a frame, embed, form, base and SVG animation element
  in a video's alternative text and in its address, ten cases; the list
  equals the browser's copy. A guard that an ordinary document (headings,
  lists, tables, code with line numbers, links, footnotes, images, a figure,
  a video, admonitions, a sidebar, contents and math) comes out element for
  element as docutils wrote it passed before and after.
- [The rich tests]: docutils' output for both video fields, rendered by the
  browser's path, keeps none of those elements; an ordinary document's
  output keeps every element and attribute.
- [The served UI tests]: a routed server reStructuredText answer with those
  elements reaches the pane without them.

### Validation

- Root suite (server and static bundle), 1452 tests: 1450 passed and 2
  failed. The root run reached its 50-minute bound at 98 %; the 29 tests
  it had not reached passed on their own. The documentation portability
  guard failed because the sandbox masks `.claude/loop.md`; outside the
  sandbox the documentation tests pass 27 of 27.
  `test_an_offline_copy_of_a_document_is_read_only` showed its known
  intermittent welcome-screen failure ([139]'s outcome records it on the
  base commit too). Run alone it passed 2 times in 3. It previews a
  Markdown file, which this change does not touch.
- Static suite with `--dev`: 186 passed, 1 failed. `test_folding_dial`
  measured a column clipped by 42 px under load; alone it passed 3 times
  in 3, and it passed in the bundle run. This change touches no layout.
- Focused runs: the preview tests 69 of 69, the rich tests 16 of 16 with
  `--dev`, and 38 served UI tests on reStructuredText, archive members,
  PDF and HTML previews, the last showing that frames in the server's
  other previews stay.
- Every standard directive and role and a set of math, rendered by
  docutils 0.21.2 and 0.23 with the server's and the browser's settings,
  stay within the list; the server's check leaves that document's 475
  elements unchanged.
- Quality gate, each hook's command run directly: Ruff, the format
  check, mypy, `deno fmt --check`, `deno lint`, the suppression-link
  guard and `static/build-index.py --check` pass.

[The preview module]: ../../server/src/filemill/preview.py
[The converter check]: ../../server/src/filemill/ui/adapters/preview-rich.js
[The server boot]: ../../server/src/filemill/ui/adapters/app-http.js
[ADR 0082]: ../adr/0082-previews-link-only-to-safe-protocols.md#known-elements-only-2026-10-22
[the architecture review]: ../ARCHITECTURE-REVIEW.md#a2-preview-content-can-execute-as-filemill
[the security review]: ../reviews/2026-10-21-security-review.md
[The preview tests]: ../../server/tests/test_preview.py
[The rich tests]: ../../static/tests/test_rich.py
[The served UI tests]: ../../server/tests/test_browser_new_ui.py
[138]: 138-make-public-instances-read-only-and-check-host-on-every-route-security.md
[139]: 139-stop-rst-previews-and-search-results-from-injecting-live-markup-securi.md
