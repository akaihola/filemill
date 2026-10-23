# ADR 0094: The browser renders members; the server renders only reStructuredText

Date: 2026-10-23. Issue: [162].

Status: Accepted for members and local folders. Where reStructuredText renders
in the server edition awaits the steward's decision in [162].

## Context

`/api/preview` rendered a served `.rst` file and its heading sections with
docutils. It also rendered every archive and Git bundle member that the browser
did not: images, PDF, HTML, `.desktop`, WebVTT and source text. It wrote the
member to a temporary file and dispatched on its suffix ([ADR 0072]). A member
in the Source view got its rendering, not its source. A local folder's `.rst`
file asked for `/api/preview?p=undefined` (A8). The browser already renders
each of those kinds from bytes, and `FS.blob` reads a member from `/api/raw`.

## Decision

- A server-listed member renders in the browser from its own bytes, by its own
  kind, as the same file on disk does (`withMemberPreview` in
  `ui/adapters/app-http.js`). The Source view shows a member's source when its
  kind has source colouring. A member over the provider's read limit, which the
  raw route refuses with 413, shows "Too large to preview".
- A local folder's `.rst` file previews in the browser, as source.
- `/api/preview` renders reStructuredText only: a served file, a section
  (`lines`) or a member. Other kinds answer 404. The Python suffix dispatcher
  and its desktop, PDF, HTML and image renderers are deleted.

## Why reStructuredText stays on the server

Its only browser renderer is docutils on Pyodide ([ADR 0002], [ADR 0064]):
5.9 MB on the wire, 12.9 MB decoded, from jsDelivr. The server edition serves
its other renderer modules itself and hides the download switch ([118]). To
move RST, the server would have to serve Pyodide (about 13 MB and new media
types) or load it from the CDN. The CDN would bring back the switch, need
internet access, take seconds on first use and show source offline.

## Consequences

Python renders only reStructuredText. `render_source` and the Pygments
highlighter keep no production caller; [160] removes them. Members gain the
browser's renderers, such as the WebVTT transcript and playable video.

[118]: ../tasks/118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md
[160]: ../tasks/160-retire-the-remaining-python-source-highlighter-and-its-pygments-depend.md
[162]: ../tasks/162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md
[ADR 0002]: 0002-rst-in-browser.md
[ADR 0064]: 0064-rst-browser-evaluation.md
[ADR 0072]: 0072-archives-browse-by-their-members.md
