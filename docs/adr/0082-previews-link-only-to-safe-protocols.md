# ADR 0082: Previews link only to safe protocols

Date: 2026-10-19. Issue: [104]. Finding A2 of the
[architecture review](../ARCHITECTURE-REVIEW.md).

## Context

A rendered preview lands in the app page, so any script in it runs as
Filemill. The Markdown wikilink rule turned a whole markdown-it text token into
raw HTML, so an image event handler beside `[[note]]` ran despite
`html: false`. docutils and mammoth escape a document's text but write each link
target as the document gives it. A `javascript:` link in reStructuredText or a
`.docx`, or the `URL` of a `.desktop` file, ran when clicked.

## Decision

- A wikilink becomes markdown-it link tokens. The text around it stays a text
  token, which markdown-it escapes.
- One rule decides a preview's link targets: `http:`, `https:` or `mailto:`, or
  a scheme-less address, which resolves against the page.
  `ui/core/model/safe-url.js` holds the rule, and
  `server/src/filemill/preview.py` has a copy. Browsers drop tabs, newlines and
  leading controls before they read a scheme. The rule therefore tests the
  literal value and treats any colon before the first slash, query or fragment
  as a scheme.
- A link that fails the rule keeps its text and loses its target. A `.desktop`
  URL that fails it is shown as text.
- Converter HTML is checked in the browser on an inert `DOMParser` document.
  Event-handler attributes are removed. `href` and `src` must pass the rule,
  and a picture may also be `data:image/`. A `.docx` can embed a style map that
  names any element. Its output therefore keeps only the tags and attributes
  mammoth writes; any other element is replaced by its contents. The server
  filters the quoted `href` and `src` attributes that docutils writes.
- No sanitizer library is added. The converters' output vocabularies are small
  and known.

## Consequences

Preview links to other protocols, such as `file:`, `ftp:`, `tel:` or an
application's own scheme, no longer open; their text stays. Markdown links keep
markdown-it's validation and `markdownHref`, which already reject
`javascript:`, `vbscript:`, `file:` and `data:` targets. A bare HTML file served
at the server root is a page of its own, outside this rule; `SECURITY.md`
names that trust boundary.

## Embedded images and server output, 2026-10-21

[The security review][review] found that docutils inlines an image for
`:loading: embed` whatever `file_insertion_enabled` says. It read any path the
server could read and inlined an SVG with its event handlers (S2). Its video
markup also writes the address and alternative text unescaped, so the server's
filter of quoted `href` and `src` attributes missed handlers. [Issue 139][139]
amends the decision:

- The server's docutils translator treats `:loading: embed` as `link`. An
  image is always a link, which the browser fetches through the root check.
  `lazy` is kept.
- The server parses docutils' output with the standard library's
  `HTMLParser` and writes each tag again. Event-handler attributes, `data` and
  `xlink:href` are removed, and `href` and `src` must pass the rule. Comments
  are dropped. This covers `/api/preview` opened on its own.
- The browser's converter check also removes `data` and `xlink:href`, and it
  runs on every preview the server renders, members of archives and bundles
  included.

Consequence: a reStructuredText document that embedded an image now shows it
as a linked image, or a broken one when the path is outside the root.

[104]: ../tasks/104-make-preview-content-inert-wikilink-text-and-docx-output-a2.md
[139]: ../tasks/139-stop-rst-previews-and-search-results-from-injecting-live-markup-securi.md
[review]: ../reviews/2026-10-21-security-review.md
