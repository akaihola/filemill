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
- Don't restart `filemill.service` or `filemill-public.service`: the running instances predate [138], and a restart before hopeli's home-manager rebuild would refuse the hostnames they are reached by (see nixos-config's issue on Filemill origins). The steward restarts them once that is deployed.
