# Security review, 2026-10-21

Whole-tree security review for [the security scan task][136], checked against
main commit `3c51672fa921d18f1f01d6097c89100c93c48ed5`. It weights what an
outside visitor can reach: the server's routes, providers and previews first,
then the shared UI, the service workers, the native host, CI and test fixtures.
Nothing was fixed in this pass. Line numbers refer to the checked commit.

## Summary

- **No credentials.** No live credential, private key or token appears in the
  tree or anywhere in Git history.
- **Most urgent.** A public instance still accepts saves and deletes (S1).
  Whether an anonymous visitor can use them depends on the deployment's
  proxy, origin setting and file permissions, which are outside this
  repository. Operators of a public instance should check them first.
- **Previews.** Server-rendered reStructuredText can embed files from anywhere
  on the server's disk and inline SVG markup that runs script as Filemill (S2).
  This breaks two promises in [SECURITY.md][security]: inert previews and the
  root check.
- **Requests.** Read routes ignore the Host header, so a website the user
  visits can read a private instance's root through DNS rebinding in browsers
  without loopback protection (S3).

| ID | Severity | Likelihood | Finding | Confidence |
| --- | --- | --- | --- | --- |
| S1 | Medium–high | High where reachable | A public instance accepts saves and deletes | 8 |
| S2 | High | Low–medium | RST previews embed server files and live SVG markup | 8 |
| S3 | High | Low–medium | Read routes accept any Host, so DNS rebinding reads the root | 8 |
| S4 | Medium | Medium | A file name injects attributes into search results | 8 |

Severity is the impact if exploited. Likelihood weighs the preconditions.
Confidence is the independent verifier's score out of 10.

## How the review was done

The `security-review` skill was applied to the whole tree, not to a diff. Six
reviewers each took one area: path containment and public mode; request
authorization and cross-origin attacks; script execution in previews and the
UI; subprocesses, parsers and denial of service; caches and service workers;
and the native host, static edition, CI and fixtures. Each candidate then went
to a separate verifier that tried to prove it wrong, under the skill's
false-positive rules.

Two changes to the skill were needed for this task. Denial of service stayed
in scope. Candidates with a verifier confidence of 7 or more are findings;
the rest are listed under [Considered and not reported](#considered-and-not-reported).

Reviewers ran small probes only: Starlette's `TestClient` against temporary
roots, and docutils, SQLite and ripgrep calls on temporary files. Verifiers
read code and did not run it. No live instance was contacted. Nothing in the
repository changed except this report and the task's tracker entries.

Findings already open elsewhere are referred to, not repeated:
[A4][a4] (save safety), [A5][a5] (static worker), [A10][a10] (unbounded
work), [the Raw view decision][116-task], [route collisions][121] and
[the network-consent scope][125].

## Findings

### S1. A public instance accepts saves and deletes

**Medium–high.** `--public` hides dotted paths, but nothing else changes.
Save and delete stay enabled, and every public shell carries the mutation
token.

- **Evidence.**
  - [server/src/filemill/cli.py][cli], lines 36–37, set `app.state.public`.
    The flag reaches only the hidden-path checks.
  - [server/src/filemill/app.py][app], line 206, puts `data-mutation-token`
    into every shell. Lines 353–378 authorize save and delete through
    `mutations.authorized` and refuse only hidden paths.
  - [server/src/filemill/mutations.py][mutations], lines 44–47, count an
    origin as local from the Origin and Host header text alone. The peer
    address is never checked.
  - [server/src/filemill/api.py][api], lines 383–386, delete a folder with
    `shutil.rmtree`.
  - [server/tests/test_public_mode.py][public-tests], line 210, asserts that a
    public shell carries the token.
- **Limits.** Save only overwrites existing valid text files of at most
  8 MiB. Delete refuses the root and hidden paths, but removes hidden children
  of a visible folder.
- **Documentation.** The general threat model says a network client can
  authorize writes. The [public-instance section][security-public],
  [server/README.md][server-readme] and the changelog say nothing about writes.
  [ADR 0087][adr-0087], line 77, mentions only in passing that an authorized
  client can still delete.
- **Deployment.** [The public-mode task][128] records that the demo is a
  public instance on loopback behind a proxy. Whether it is writable depends
  on that proxy's Host handling and the service account's permissions. This
  review did not inspect or probe either.

### S2. RST previews embed server files and live SVG markup

**High for script, medium for disclosure.** docutils' image directive accepts
`:loading: embed`. Its HTML writer then reads the image file and inlines it,
whatever `file_insertion_enabled` says.

- **Evidence.**
  - [server/src/filemill/preview.py][preview], lines 201–215, render RST with
    `raw_enabled` and `file_insertion_enabled` off. Neither setting gates the
    embed branch of docutils 0.23's `HTMLTranslator.visit_image` in
    `writers/_html_base.py`. That branch calls `uri2path` and reads the file,
    with absolute paths and `file:` URIs accepted.
  - An image becomes a `data:image/...` URI, which line 49 keeps. An SVG is
    inlined as markup with all its attributes. An SVG that fails to parse is
    inlined as raw text.
  - Line 36's `_URL_ATTR` rewrites only ` href=` and ` src=`. It leaves event
    handlers, `xlink:href` and `data=` alone.
  - The browser inserts the result unsanitized:
    [ui/adapters/app-http.js][app-http], line 126, returns `response.text()`,
    and [ui/core/render.js][render], line 739, assigns it to `innerHTML`.
    `inert()` in [ui/adapters/preview-rich.js][rich], line 359, runs only on
    browser RST and DOCX output.
  - Archive and bundle members reach the same renderer through
    [server/src/filemill/api.py][api], lines 351–354.
- **Limits.** Reading arbitrary non-image files such as private keys was not
  proven: docutils guesses the media type from the URI, and non-image types
  are dropped by line 49. `<script>` inserted through `innerHTML` does not run.
  Event handlers do, and the whole document runs when `/api/preview` is opened
  directly.
- **Related.** [A2][a2] fixed link targets and wikilinks; this is a separate
  path. A `docutils.conf` in the process directory can also turn `raw` and
  `include` back on, but anyone who can write it can already serve an
  `index.html` (see [Considered and not reported](#considered-and-not-reported)).

### S3. Read routes accept any Host, so DNS rebinding reads the root

**High impact, low–medium likelihood.** Only save and delete look at Host.
Every read route answers any Host, so a page whose name rebinds to
`127.0.0.1` reads the private root as its own origin.

- **Evidence.**
  - [server/src/filemill/app.py][app], line 32, creates `Starlette()` without
    middleware. [server/src/filemill/cli.py][cli], line 53, adds none.
  - The only Host check is [server/src/filemill/mutations.py][mutations],
    line 41, and only `api_save` and `api_delete` call it (app.py lines 356
    and 367).
  - `api_dir`, `api_search`, `api_raw`, `api_preview` and `resource`
    (app.py lines 266–350 and 419–486) never look at Host.
  - Private instances serve dotfiles.
  - [ADR 0081][adr-0081], line 45, says "The Host allowlist also rejects an
    arbitrary DNS name resolving to loopback". That is true for writes only.
- **Preconditions.**
  - A browser without loopback rebinding protection. Chromium's Local Network
    Access blocks it; default Firefox and Safari do not.
  - A known or guessed port.
  - A resolver that passes rebinding answers.
  - The page staying open for up to a minute.

### S4. A file name injects attributes into search results

**Medium.** Search results are built as HTML strings. The escape helper does
not escape `"`, and its output lands in a double-quoted attribute.

- **Evidence.**
  - [ui/core/search.js][search], lines 13–17, escape by serializing a text
    node, which leaves `"` as is.
  - Lines 45–46 interpolate the result into `data-path="…"` on a `<button>`,
    and line 22 assigns the markup to `innerHTML`.
  - The path is ripgrep's, unchanged ([server/src/filemill/api.py][api],
    lines 117–120).
  - [ui/core/icons.js][icons], line 38, already has an `esc()` that escapes
    `"`.
- **Limits.** An injected `onclick` is overwritten at line 57, and autofocus
  does not fire while the search bar has focus. Hover, focus and pointer
  handlers do. The context and second path span are text and are safe.

## Not finished

A safety check stopped the writing of this report twice, so it ends after
S4. Still to write:

- the findings after S4 that the review verified, of medium and low
  severity;
- a fix and a drafted issue for every finding, S1 to S4 included;
- the steward's deployment note for S1;
- the [SECURITY.md][security] claims that do not hold;
- the coverage of each area, and the candidates considered and not
  reported.

The verifier results for all of these are in the HAI-136 session's
transcript.

[136]: ../tasks/136-security-scan-of-filemill-served-roots-mutations-previews-caches-and-h.md
[116-task]: ../tasks/116-sandbox-the-raw-view-of-html-files-inside-archives-with-a-content-secu.md
[121]: ../tasks/121-clarify-api-path-collisions-from-docs-question-6.md
[125]: ../tasks/125-clarify-network-consent-scope-from-docs-question-11.md
[128]: ../tasks/128-never-list-or-serve-hidden-files-on-a-public-instance.md
[a2]: ../ARCHITECTURE-REVIEW.md#a2-preview-content-can-execute-as-filemill
[a4]: ../ARCHITECTURE-REVIEW.md#a4-saves-can-truncate-or-overwrite-newer-content
[a5]: ../ARCHITECTURE-REVIEW.md#a5-the-static-service-worker-retains-the-old-policy
[a10]: ../ARCHITECTURE-REVIEW.md#a10-limits-still-do-not-bound-acquired-work
[adr-0081]: ../adr/0081-authorize-server-mutations.md
[adr-0087]: ../adr/0087-a-public-instance-never-lists-or-serves-hidden-paths.md
[security]: ../../SECURITY.md
[security-public]: ../../SECURITY.md#public-instances
[server-readme]: ../../server/README.md
[cli]: ../../server/src/filemill/cli.py
[app]: ../../server/src/filemill/app.py
[api]: ../../server/src/filemill/api.py
[mutations]: ../../server/src/filemill/mutations.py
[preview]: ../../server/src/filemill/preview.py
[public-tests]: ../../server/tests/test_public_mode.py
[app-http]: ../../ui/adapters/app-http.js
[rich]: ../../ui/adapters/preview-rich.js
[render]: ../../ui/core/render.js
[search]: ../../ui/core/search.js
[icons]: ../../ui/core/icons.js
