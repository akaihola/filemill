# Architecture summary

Read this first, then only the sections of
[the architecture review](ARCHITECTURE-REVIEW.md) that the issue touches.
Find a section by its heading, e.g.
`grep -n '^### A9' docs/ARCHITECTURE-REVIEW.md`. The review holds the
evidence, line references and acceptance, and wins where the two differ.
When a change alters a finding's status, update the finding in the review
and its line in the section index below.

## Principles

- **One UI, three hosts.** The server, static and native editions share
  `ui/` and call the core initializer once. Renderer, port and root choices
  stay in each host's composition.
- **Three small ports.** FS, PREVIEW and ROUTER, with optional capabilities.
  Adapters own byte access, parsing and refresh invalidation. Editable Blobs
  carry a revision; writes reject a different expected revision.
- **DOM-free model.** `ui/core/model/` uses no browser APIs.
- **Root-relative resources.** A URL names a real file and an optional
  virtual remainder. API calls keep real path `p` and member path `v` apart.
- **Authorize before acting.** Host, Origin and a per-process token are
  checked before a body is read. Saves are revision-checked atomic
  replacements (ADR 0090). Public mode refuses all mutations.
- **Files are durable data.** Offline copies are marked; the editor refuses
  stale reads (ADR 0089).
- **Rules for changes.** A port or behaviour decision gets an ADR in the
  same change. Code a change retires is deleted in the same change. Keep the
  shared UI and the concatenating builder; add no framework, bundler, ORM,
  general `ViewSpec` or cache manager without a failing, measured case. Make
  existing modules deeper by hiding their invariants. Fix A9 before expanding
  the native preview workload. Stay within the issue being implemented.

## Module map

- [server/src/filemill/](../server/src/filemill/): `cli.py` starts Uvicorn
  and Starlette in `app.py` (resource resolution, Host middleware);
  `urls.py` views and `?f`; `paths.py` root, bookmarks and public mode;
  `mutations.py` write policy; `api.py` saves; `vfs.py` and `providers/`
  SQLite, archive and Git bundle members; `preview.py` server RST rendering;
  `static/sw.js` the server worker.
- [ui/](../ui/), a symlink to the server package's shared frontend:
  `core/ports.js`; `core/model/` selection, sorting, folding stops, deep
  links, headings, safe URLs and task changes; `core/layout.js` scroll,
  settling, wheel locking and fullscreen; `core/render.js` columns and the
  retained preview; `core/nav.js` navigation; `adapters/` hosts, filesystems
  and renderers, with `app-http.js` composing rendering; `editor/`.
- [static/](../static/): `build-index.py` concatenates `index.html`;
  `sw.js` is the static worker (A5).
- [native/webview/main.c](../native/webview/main.c): the Linux WebKitGTK
  prototype; `ui/adapters/native.js` has writes but no remove.
- Browser state: IndexedDB folder handles, localStorage settings, history
  navigation.

## Section index

Read a section when the issue touches the topic after its dash.

- How to read this review — severity, status and evidence conventions.
- Architecture as it is — the principles and module map in full, with line
  references.
- What is healthy — boundaries and test guards to keep; changing tests or
  CI; root browser lifecycle ownership and local page setup.
- Rules for changes — the full change rules.
- Findings — the severity and status table.
- A5. The static service worker retains the old policy — Changed, P1:
  static `sw.js` freshness, offline misses, shared-origin caches.
- A6. Virtual identity is still a display name — Changed, P2: deep links,
  selection by name, virtual member addresses.
- A7. SQLite keys collide; provider errors look empty — Changed, P2: the
  SQLite provider, provider error reporting.
- A8. Preview source and representation are conflated — Changed, P2:
  Source, Rendered and Raw for RST, members and native.
- A9. Broader preview and navigation async ownership — Changed, P2: preview
  lifetime, `nav.js`, `walkPath`, remounts, stale async work.
- A10. Limits still do not bound acquired work — Changed, P2: search, saves,
  file reads, archives, bundles, DOCX and PPTX sizes.
- A11. The command audit remains unverified — Changed, P3: advertised
  commands and documentation claims.
- A12. Smaller defects, dead code and audits — Changed, P3: folder
  persistence, dead code, cross-language limits, provider discovery,
  accessibility.
- A14. Bundle eviction removes an active repository — Resolved: Git bundle
  cache and repository lifetime.
- Resolved since the earlier reviews — reopening needs new evidence.
- A13. JSON-column refresh keeps the old parsed value — Resolved: JSON
  refresh and adapter invalidation.
- A1. The directory index escapes the root check — Resolved: directory
  indexes and root containment.
- A2. Preview content can execute as Filemill — Resolved: preview
  sanitizing, wikilinks, HTML frames.
- A3. Mutations accept unrelated-origin requests — Resolved: Origin, Host
  and token checks.
- A4. Saves can truncate or overwrite newer content — Resolved: atomic,
  revision-checked saves.
- Resolved portions and retained earlier repairs — an older finding or
  retired code that seems to recur.
- Remediation order — choosing or ordering architecture work.
- Draft issues — the steward's drafts for new findings.
- A13 draft — resolved; history only.
- A14 draft — resolved; history only.
