# Adapters for the shared UI

The [edition reference] owns the capability and renderer comparison. The
[shared UI instructions] explain the single packaged source, development page
and generated bundle. This guide covers adapter wiring.

## Entry points and ports

The three [entry modules] load static, server or native adapters. The
[DOM-free model] owns selection, sorting, folding, keys and deep links. Adjacent
browser modules render the model. [The port contract] defines FS, PREVIEW and
ROUTER, common node fields and optional capabilities.

| Host   | Filesystem                                | Preview composition | Router                                 |
| ------ | ----------------------------------------- | ------------------- | -------------------------------------- |
| Static | [browser filesystem]                      | [static boot]       | [hash router]                          |
| Server | [HTTP filesystem], or FSA for Open Folder | [server boot]       | [path router], or none for Open Folder |
| Native | [native adapter]                          | [native boot]       | Native in-memory history               |

Nodes begin with `name`, `dir` and `kids`. `kids === null` means unread.
Adapters add metadata and virtual-source fields. The contract is not yet
exhaustive: core still checks `vpath` and builds HTTP search requests. The
[architecture review] records those boundary gaps.

Refresh awaits an active load, clears common listing state, then calls the
optional FS `invalidate(node)` before `ensureLoaded`. [JSON adapter] owns
parsed-source invalidation, including nested JSON and changed archive members.
[The refresh decision] records this contract.

Editable Blobs carry their revision. `write(node, text, expected)` rejects
conflicts, and the editor retains the draft's revision.
[The replacement decision] defines the HTTP, FSA and native guarantees and
limits.

## Rendering

[The renderer registry] holds `{kind, render, fallback}` entries. App modules
register core renderers and their host-specific additions. PREVIEW returns body
markup; core owns the toolbar, retained preview DOM and generation guard.

`app-http.js` adds Markdown, `.docx`, `.pptx` and the `offline` fallback from
[rich-preview adapter]. Served RST and supported server-member previews use its
`PreviewHTTP` wrapper. The server shell maps Markdown/DOCX modules to vendored
assets; PPTX extracts slide text without a download. See the [edition reference]
for download consent, fidelity and fallback behavior.

Open Folder reads browser-owned bytes. It disables URL sync because server paths
cannot name those files. Its RST route remains broken: the shared RST override
asks the server for a node without a server-relative path. Member Source
requests also lack a representation parameter, so RST and HTML can still render.
Native Source lacks the browser editions' highlighting wrapper. These are [A8],
not feature-parity guarantees.

[The highlighting wrapper] selects browser source mode for supported ordinary
files. The server virtual wrapper can instead use the Python preview endpoint.
Fenced code uses the shared syntax highlighter. Keep renderer choice and source
capability distinct as A8 is repaired.

[edition reference]: ../../../../../README.md#choose-an-edition
[shared UI instructions]: ../../../../../README.md#working-on-the-shared-ui
[entry modules]: ../
[DOM-free model]: ../core/model/
[The port contract]: ../core/ports.js
[browser filesystem]: fsa.js
[static boot]: app-fsa.js
[hash router]: router-hash.js
[HTTP filesystem]: http.js
[server boot]: app-http.js
[path router]: router-path.js
[native adapter]: native.js
[native boot]: app-native.js
[architecture review]: ../../../../../docs/ARCHITECTURE-REVIEW.md
[JSON adapter]: vfs-json.js
[The refresh decision]: ../../../../../docs/adr/0041-core-adapters-three-ports.md#refresh-invalidation-2026-10-21
[The replacement decision]: ../../../../../docs/adr/0090-revision-checked-file-replacement.md
[The renderer registry]: ../core/renderers.js
[rich-preview adapter]: preview-rich.js
[A8]: ../../../../../docs/ARCHITECTURE-REVIEW.md#a8-preview-source-and-representation-are-conflated
[The highlighting wrapper]: preview-local.js
