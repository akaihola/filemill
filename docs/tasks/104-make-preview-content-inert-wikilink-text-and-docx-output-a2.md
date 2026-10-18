# Make preview content inert: wikilink text and DOCX output (A2)

Steward issue, 2026-10-18. Goal: agentic-leverage. Step 2 of the remediation
order in `docs/ARCHITECTURE-REVIEW.md`: finding A2 (P1). Still on `main`: the
wikilink rule in `ui/adapters/preview-rich.js` turns a whole markdown-it text
token into `html_inline`, so text beside `[[note]]` renders as raw HTML
despite `html: false`, and `docxHTML` inserts converter HTML unsanitized.

## Work

Read the review's A2 section and "Remediation order" step 2 first; their
acceptance criteria are this issue's.

1. Rewrite wikilinks as link tokens, or escape all untouched text in the
   token. Malformed wikilinks are escaped.
2. Sanitize DOCX output and URL-bearing fields (DOCX, `.desktop` links)
   with an explicit safe-protocol list. Do not add a security framework.
3. Tests, red first: crafted Markdown with an event-handler image beside a
   wikilink stays inert, with and without wikilinks; links, code and
   footnotes still render; unsafe DOCX and `.desktop` URLs do not execute.
4. Document the trust boundary of bare-HTML web serving at the server root
   in `SECURITY.md`; it keeps working. Mark A2 resolved in the review, dated.

## Ground rules

- Change only what A2 needs; A8's renderer unification is separate.
- No push, deployment, restart or remote setting. Never weaken a gate.

## Acceptance

- The review's A2 acceptance holds, each point backed by a test.
- Root `uv run pytest`, both static modes and `uvx pre-commit run
  --all-files` pass; record the commands and timings here.
- Security fix: acceptance stays with Antti.

## Implementation (2026-10-19)

[ADR 0082] records the decision.

- `ui/adapters/preview-rich.js`: the wikilink rule splits a text token into
  text, `link_open`, label text and `link_close` tokens. markdown-it escapes the
  text on both sides. A malformed wikilink is never matched, so it stays text.
- `ui/core/model/safe-url.js`: `safeURL` allows `http:`, `https:`, `mailto:`
  and scheme-less addresses. It tests the literal value, because browsers drop
  tabs, newlines and leading controls before they read a scheme.
  `server/src/filemill/preview.py` has the Python copy, `safe_url`.
- `inert()` in `preview-rich.js` checks converter HTML on a `DOMParser`
  document. It removes event-handler attributes and unsafe `href` and `src`
  values; a picture may also be `data:image/`. For `.docx` it also keeps only
  the tags and attributes mammoth writes, because a document can embed a style
  map that names any element.
- Both `.desktop` renderers (`ui/core/renderers.js`, and `_preview_desktop` for
  archive members on the server) show an unsafe URL as text.
- Scope note: the audit found that docutils also writes `javascript:` link
  targets as given. reStructuredText is not named in this issue, but it is the
  same A2 defect. Both renderers now apply the rule: the browser's Pyodide path
  through `inert()`, the server's `_preview_rst` through `_safe_links`.
- `SECURITY.md` names the trust boundary of HTML served at the server root.
  `test_bare_path_serves_html_as_html` keeps that serving working.

Tests, each red before its fix:

| Acceptance point                                    | Test                                                         |
| --------------------------------------------------- | ------------------------------------------------------------ |
| Crafted Markdown inert with and without a wikilink  | `static/tests/test_rich.py::test_markdown_stays_inert`       |
| Malformed wikilinks escaped                         | same test, `[[ <img …>` and `[[x]`                           |
| Links, code and footnotes still render              | same test, and `test_vendored_renderers`                     |
| Unsafe `.docx` URLs do not execute                  | `test_unsafe_urls_are_not_links` (`javascript:`, `data:`)    |
| Unsafe `.desktop` URLs do not execute (browser)     | `test_unsafe_urls_are_not_links`                             |
| Unsafe `.desktop` URLs do not execute (server)      | `server/tests/test_preview.py::test_preview_desktop_unsafe_url_is_text` |
| reStructuredText links (browser, server)            | `test_rich.py::test_rst_links_keep_only_safe_urls`, `test_preview.py::test_rst_links_keep_only_safe_urls` |
| The rule's edge cases                               | `ui/core/model/test.mjs`                                     |
| Bare-HTML serving keeps working                     | `server/tests/test_resource_routes.py::test_bare_path_serves_html_as_html` |

Red evidence: the Markdown test found two live `<img onerror>` elements (beside
the wikilink and after the malformed one). The `.docx` and browser
reStructuredText tests found `href="javascript:…"`. The browser `.desktop` card
rendered `<a href="javascript:window.__xss=4">`, checked against the original
`renderers.js` in `--dev` mode. The server tests failed on all five unsafe
`.desktop` URLs and on the `javascript:` reStructuredText link.

[ADR 0082]: ../adr/0082-previews-link-only-to-safe-protocols.md

## Validation (2026-10-19)

Run on the development host one at a time, before the rebase onto `main`:

| Command                                                         | Result                    | Wall time |
| --------------------------------------------------------------- | ------------------------- | --------- |
| `uv run pytest -q --tb=short --durations=20` (root)             | 1009 passed               | 962 s     |
| `uv run pytest static/tests --dev -q --tb=short --durations=10` | 150 passed                | 360 s     |
| `uvx pre-commit run --all-files`                                | all six hooks passed      | 10 s      |
| `deno run --allow-read=ui/core/model ui/core/model/test.mjs`    | model checks passed       | < 1 s     |

After the rebase onto `main` (with [103], [105] and [106]; this ADR became
0082 because [103] took 0081):

| Command                                                         | Result                    | Wall time |
| --------------------------------------------------------------- | ------------------------- | --------- |
| `uv run pytest -q --tb=short --durations=5` (root)              | 1087 passed               | 1269 s    |
| `uv run pytest static/tests --dev -q --tb=short --durations=5`  | 150 passed                | 651 s     |
| `uvx pre-commit run --all-files`                                | all seven hooks passed    | 7 s       |
| `deno run --allow-read=ui/core/model ui/core/model/test.mjs`    | model checks passed       | < 1 s     |

The root run includes the bundle-mode static suite. The suites and
pre-commit ran outside the agent sandbox: the docs portability guard and uv's
tool directory need it. `server/tests/test_docs.py` passed again after the
final documentation edits. Security fix: acceptance stays with Antti.
