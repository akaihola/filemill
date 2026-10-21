# Goals of Filemill

This document tells you what Filemill must become. Every design
decision in this repository must serve one of these goals. If a change does not
serve a goal here, do not make it.

These are goals, not a claim that every edition meets them. The [roadmap]
records delivery status; the [architecture review] records implementation gaps.

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
   prototype is qualified; see the [native guide] and [native decision]. Cross-platform native
   applications with feature parity remain future work. This goal shapes the
   architecture now. The core must not depend on where a node
   comes from. It must not depend on the browser DOM more than necessary.

## Implicit goals we found in the code

These goals are not written in the task brief. The code and the existing
documents show them. We keep them.

- **One shared UI, zero drift.** [ui/] is one set of files. One commit reaches
  both browser editions and the native host. See [Working on the shared UI].
- **Privacy by default.** Folder contents stay in the browser in the static
  edition. Its renderer downloads from a CDN sit behind a remembered switch.
  Application loading and resources that documents reference, such as images,
  also use the network. See the [static edition notes] and [consent decision].
- **No build step for development. No framework. No bundler.** The dev page
  loads the sources directly. See [static/index-dev.html] and the [adapter guide].
- **Renderer failure degrades visibly.** A failed rich-renderer load tries a
  bounded text fallback and an offline note. Binary DOCX may have no readable
  text. Server offline copies permit reads of previously visited content, not
  edits or uncached reads. The static worker still has A5 defects. See the
  [rich-preview adapter], [offline decision] and [architecture review].
- **Large directories stay fast.** The tests set budgets at 3 000 entries.
  Columns are cached as DOM. Name sorting reuses one `Intl.Collator` per
  module instead of `localeCompare` per call. See [ui/core/render.js] and
  [ui/core/model/sort.js].
- **Keyboard first, addressable navigation.** Deep links are the goal.
  The server edition's Open Folder mode is the exception: it has no
  router, because a URL path names a file under the server's root. Virtual
  names still have identity and round-trip gaps (A6/A7). See [ui/core/deeplink.js],
  [the path router] and [ui/adapters/app-http.js].
- **The URL path is the file path** in the server edition. See
  [server/src/filemill/urls.py]. Registered API and asset routes still shadow
  some names; the [route-collision task] owns that design decision.
- **Decisions are recorded with their measurements.** See [docs/adr/].
- **Few dependencies, constraints explained.** Distinguish minimum supported versions
  (`>=` floors), deliberate bounded versions (upper limits or `~=` ranges), and
  exact lockfile selections. A floor declares support; it does not prove that
  the minimum was tested. Record evidence for restrictions and mark inherited
  compatibility reasons as unverified when evidence is missing. Unconstrained
  dependencies need no blanket pinning. See the [server dependency comments]
  for reasons and gaps. The [workspace lockfile] records exact selections for
  reproducible development; it does not explain or replace declared ranges.
- **Authorized filesystem zones are a boundary.** The server permits its
  root and direct-root bookmark symlink targets. Public mode also excludes
  hidden paths and refuses writes. Browser folders request write permission
  when saving or deleting. See [server/src/filemill/paths.py],
  [ui/adapters/fsa.js] and the [security policy].
- **Installable and portable.** A PWA manifest, one bundled file, published to
  GitHub Pages. See the [publishing workflow].

## Engineering goals

We aim for world-class open source engineering. Each goal below has one test
that a person can apply.

- **Simplicity.** A reader can explain the purpose of any file in one sentence.
  A new feature touches one module, not five.
- **Maintainability.** A new contributor runs both editions and all tests
  within ten minutes of a clean checkout, with the [contributor commands].
  This remains a target, not a measured setup guarantee.
- **Performance.** A directory of 3 000 entries opens, sorts and searches
  within the budgets in [static/tests/test_ui.py]. A resize does not re-fetch a
  preview.
- **Elegance.** Each concept exists in one place. The code says what it does.
  A comment says why, not what.
- **Honesty.** The test suites are green on `main`. The documents describe
  the code as it is today. A decision that changes behaviour gets an ADR in
  the same change, as the [rules for changes] require.
- **A joy to read and contribute to.** Documents use Simplified Technical
  English. There are fewer lines of prose than lines of code.

## Non-goals

These are choices, not omissions. Do not add them without a recorded decision.

- No JavaScript framework.
- No bundler for development. The bundle exists only for the single-file
  deliverable.
- No telemetry.
- No network use without consent. The current default-on renderer switch is
  narrower than this target; it does not block document resources. The
  [documentation review] records the unresolved consent definition.
- No feature in one edition that the other edition cannot have. Exceptions
  exist today: content search and the SQLite, archive and Git bundle virtual
  filesystems run only in the server edition, because their readers are
  Python, ripgrep or `git`. They are gaps to close, not a design.

## Related documents

- The [architecture review] says how far the code is from these goals.
- The [roadmap] says in what order we close the gap.

[server dependency comments]: ../server/pyproject.toml
[workspace lockfile]: ../uv.lock
[roadmap]: ROADMAP.md
[architecture review]: ARCHITECTURE-REVIEW.md
[native guide]: ../native/README.md
[native decision]: adr/0079-native-shell.md
[ui/]: ../ui/
[Working on the shared UI]: ../README.md#working-on-the-shared-ui
[static edition notes]: ../README.md#static--one-file-no-server-no-install
[consent decision]: adr/0036-but-behind-a-remembered-switch-defaulting-on.md
[static/index-dev.html]: ../static/index-dev.html
[adapter guide]: ../server/src/filemill/ui/adapters/README.md
[rich-preview adapter]: ../ui/adapters/preview-rich.js
[offline decision]: adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md
[ui/core/render.js]: ../ui/core/render.js
[ui/core/model/sort.js]: ../ui/core/model/sort.js
[ui/core/deeplink.js]: ../ui/core/deeplink.js
[the path router]: ../ui/adapters/router-path.js
[ui/adapters/app-http.js]: ../ui/adapters/app-http.js
[server/src/filemill/urls.py]: ../server/src/filemill/urls.py
[route-collision task]: tasks/121-clarify-api-path-collisions-from-docs-question-6.md
[docs/adr/]: adr/
[server/src/filemill/paths.py]: ../server/src/filemill/paths.py
[ui/adapters/fsa.js]: ../ui/adapters/fsa.js
[security policy]: ../SECURITY.md
[publishing workflow]: ../.github/workflows/publish.yml
[contributor commands]: ../CONTRIBUTING.md
[static/tests/test_ui.py]: ../static/tests/test_ui.py
[rules for changes]: ARCHITECTURE-REVIEW.md#rules-for-changes
[documentation review]: reviews/2026-10-22-docs-review.md#open-questions
