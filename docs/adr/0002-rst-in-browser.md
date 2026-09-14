# ADR 0002: Render reStructuredText with docutils on Pyodide

Status: accepted, 2026-09-14.

## Context

The static edition renders Markdown and `.docx` in the browser with libraries
fetched from a CDN on first use, behind a remembered consent switch
(`ui/adapters/preview-rich.js`). `.rst` files fell through to the plain
source view. The task was to find a client-side renderer, preferring an
existing JavaScript library or a pre-packaged Python-in-the-browser build,
and to plan a home-grown port only if neither existed.

## Alternatives

1. **A JavaScript parser.** The only candidates on npm are `restructured`
   0.0.11 and its wrapper `rst2html` 1.0.4, both last released in 2022, 157 KB
   as an ES module. On a 50-line sample they turn hyperlinks, every directive
   (`code-block`, `note`, `image`), simple and grid tables, field lists and
   footnotes into `rst-unknown` divs or plain text, print comments and
   footnote bodies as content, and emit a literal `<script>` in the source
   unescaped. Rejected.
2. **docutils on Pyodide.** docutils 0.21.2 is a pure-Python wheel inside the
   official Pyodide 0.29.4 distribution, with no dependencies. Verified on
   the same sample: every construct above renders as it does on the command
   line, and text is escaped. Chosen.
3. **A port of docutils to JavaScript or WebAssembly by us.** Not needed;
   option 2 is the pre-packaged Python solution the task asked for first.

## Decision

`preview-rich.js` gets one more pinned CDN entry, `pyodide`, pointing at the
immutable jsDelivr release directory, and a `.rst` branch that boots the
interpreter once per session, loads `docutils`, and renders with
`publish_parts(..., writer_name="html5")`. `raw` and file insertion are
disabled, so a document can neither inject markup nor read files; system
messages are suppressed. The same consent switch, offline fallback and
512 KB limit apply as for Markdown. The server edition is unchanged: it
never loads this adapter and keeps showing `.rst` as highlighted source.

## Measurement

Cold download from jsDelivr, once per session, measured on 2026-09-14:

| asset                        | bytes      | on the wire (brotli) |
|------------------------------|-----------:|---------------------:|
| pyodide.mjs                  |     17,616 |                    – |
| pyodide.asm.js               |  1,074,322 |              226,426 |
| pyodide.asm.wasm             |  8,647,684 |            2,672,378 |
| python_stdlib.zip            |  2,424,002 |            2,386,400 |
| pyodide-lock.json            |    122,027 |               26,288 |
| docutils-0.21.2 wheel        |    587,408 |              566,702 |
| **total**                    | **12.9 MB**|          **≈5.9 MB** |

Time on the development server with the assets already local, under deno:
interpreter boot 4.5 s, `loadPackage("docutils")` 0.3 s, first render 1.7 s
(importing docutils), later renders well under a second. In headless
Chromium on the same server, cold cache, through its outbound proxy: 8.2 s
from click to rendered text. The rejected
JavaScript option would have been 157 KB and instant, which is why it was
tried first.

## Consequences

- `.rst` renders in the static edition for anyone who leaves rich previews
  on, at the cost of one 13 MB download per session. The switch's hint says
  so.
- The interpreter stays resident for the session, roughly 50–100 MB of
  memory, paid only after the first `.rst` is opened.
- Relative image paths resolve against the page, as they do for Markdown in
  the static edition today.
- Issue [27] in `TASKS.md` asked for this experiment behind a renderer
  registry that does not exist yet; this ADR records its measurements
  without the registry.
