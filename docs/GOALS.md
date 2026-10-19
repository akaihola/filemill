# Goals of Filemill

This document tells you what Filemill must become. Read it first. Every design
decision in this repository must serve one of these goals. If a change does not
serve a goal here, do not make it.

The text uses Simplified Technical English. Sentences are short. One sentence
gives one fact or one instruction.

## Purpose

Filemill is a file manager. It must be the most intuitive, most obvious and
most practically usable file manager for all desktop, tablet and mobile
operating systems.

"Intuitive" means: a new user finds the next action without instructions.
"Obvious" means: the screen shows what will happen before the user acts.
"Practically usable" means: a user can do real daily work with it, on a real
folder, on the device they have.

## Product goals

1. **Miller columns with intuitive folding.** Each directory is one column.
   A selected entry opens the next column to the right. Columns to the left
   fold into narrow spines when space is small. Folding must never hide the
   column the user just touched, or the column it opened.
2. **World-class embedded preview and editing.** The preview pane shows the
   selected file in its best form. That form is rendered Markdown, highlighted
   source, images, PDF, office documents or database rows. Text files can be edited
   and saved in the same pane.
3. **Structured files as hierarchical columns.** A SQLite database, a JSON
   document or a JSONL file opens as columns, exactly like a directory. The
   user does not learn a second navigation model for structured data.
4. **Two editions, one application.** The server edition browses a directory
   on a server. The static edition browses a directory on the user's own
   machine through the File System Access API and ships as one HTML file.
   Both must look the same and behave the same.
5. **Native applications later.** Filemill must become a native macOS, GNOME
   and Windows application with the same feature set. A Linux WebKitGTK
   prototype exists as of 2026-10-19, [30] and ADR 0079. Cross-platform native
   applications with feature parity remain future work. This goal shapes the
   architecture now. The core must not depend on where a node
   comes from. It must not depend on the browser DOM more than necessary.

## Implicit goals we found in the code

These goals are not written in the task brief. The code and the existing
documents show them. We keep them.

- **One shared UI, zero drift.** `ui/` is one set of files. One commit reaches
  both editions. See [Working on the shared UI](../README.md#working-on-the-shared-ui).
- **Privacy by default.** Folder contents stay in the browser in the static
  edition. Its renderer downloads from a CDN sit behind a remembered switch.
  Application loading and resources that documents reference, such as images,
  also use the network. See the [static edition notes](../README.md#static--one-file-no-server-no-install)
  and ADRs [0035](adr/0035-rich-renderers-lazy-loaded-from-a-cdn-not-bundled.md)
  and [0036](adr/0036-but-behind-a-remembered-switch-defaulting-on.md).
- **No build step for development. No framework. No bundler.** The dev page
  loads the sources directly. See `static/index-dev.html` and
  `ui/adapters/README.md`.
- **Offline reduces fidelity, never function.** A Markdown, reStructuredText
  or DOCX renderer that fails to load falls back to the file's text with an
  offline note. Binary DOCX bytes may have no readable text. See
  `ui/adapters/preview-rich.js`.
- **Large directories stay fast.** The tests set budgets at 3 000 entries.
  Columns are cached as DOM. Name sorting reuses one `Intl.Collator` per
  module instead of `localeCompare` per call. See `ui/core/render.js` and
  `ui/core/model/sort.js`.
- **Keyboard first. URL always in sync.** Every location has a deep link.
  The server edition's Open Folder mode is the exception: it has no
  router, because a URL path names a file under the server's root. See
  `ui/core/deeplink.js`, `ui/adapters/router-*.js` and `ui/adapters/app-http.js`.
- **The URL path is the file path** in the server edition. See
  `server/src/filemill/urls.py`.
- **Decisions are recorded with their measurements.** See `docs/adr/`.
- **Few dependencies, each pin explained.** See `server/pyproject.toml`.
- **The served root is a boundary.** No request escapes it. The app asks for
  write permission only when the user saves or deletes. See `resolve_safe` in
  `server/src/filemill/paths.py` and `ui/adapters/fsa.js`.
- **Installable and portable.** A PWA manifest, one bundled file, published to
  GitHub Pages. See `.github/workflows/publish.yml`.

## Engineering goals

We aim for world-class open source engineering. Each goal below has one test
that a person can apply.

- **Simplicity.** A reader can explain the purpose of any file in one sentence.
  A new feature touches one module, not five.
- **Maintainability.** A new contributor runs both editions and all tests
  within ten minutes of a clean checkout, with the commands in `README.md`.
- **Performance.** A directory of 3 000 entries opens, sorts and searches
  within the budgets in `static/tests/test_ui.py`. A resize does not re-fetch a
  preview.
- **Elegance.** Each concept exists in one place. The code says what it does.
  A comment says why, not what.
- **Honesty.** The test suites are green on `main`. The documents describe
  the code as it is today. A decision that changes behaviour is recorded the
  day it is made.
- **A joy to read and contribute to.** Documents use Simplified Technical
  English. There are fewer lines of prose than lines of code.

## Non-goals

These are choices, not omissions. Do not add them without a recorded decision.

- No JavaScript framework.
- No bundler for development. The bundle exists only for the single-file
  deliverable.
- No telemetry.
- No network use without consent.
- No feature in one edition that the other edition cannot have. Exceptions
  exist today: content search and the SQLite, archive and Git bundle virtual
  filesystems run only in the server edition, because their readers are
  Python, ripgrep or `git`. They are gaps to close, not a design.

## Related documents

- `docs/ARCHITECTURE-REVIEW.md` says how far the code is from these goals.
- `docs/ROADMAP.md` says in what order we close the gap.
