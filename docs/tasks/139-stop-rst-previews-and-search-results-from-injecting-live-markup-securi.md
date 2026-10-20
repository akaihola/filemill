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
