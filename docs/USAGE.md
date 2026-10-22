# Using Filemill

See the [edition reference] for supported sources and renderer differences.
These instructions cover the two browser editions. The [native guide] lists
the Linux prototype's limits.

## Navigation and folding

Select a folder to open its column. Arrow keys move through entries and
columns. F5 refreshes the focused folder and its open descendants. Browser
reload shortcuts keep their browser meaning.

Opening a new root resets the fold dial. Horizontal scrolling folds or widens
columns in stops. Resizing or folding retains the current preview and its
scroll position. Fullscreen stays active across a resize; use Exit fullscreen
or the browser's fullscreen exit control to return.

Folder clicks add Back steps. Selecting a file inside an open folder rewrites
that step. Keyboard stepping rewrites it even when it opens folders. A
document's temporary loading column adds no step unless its outline is
confirmed. See the [history decision].

## Content search

Search file contents in the focused folder and its subfolders. Search is
case-sensitive and treats the query as literal text. Each file shows its first
matching line. Click a result or press Enter or Space to open it. Clear the
query to cancel. Opening another root clears the search.

Served folders, Open Folder and the static edition use the same control.
Browser-owned files stay in the browser; local search sends no file bytes or
search request to the server. Searches skip hidden entries, `node_modules`,
`__pycache__` and binary files containing NUL bytes. They do not read archive
members or virtual document sections. Ignore files do not affect search.

Search stops at 100 matches, 2,000 visited entries, 32 directory levels,
1 MiB per file or 16 MiB of total text reads. A skipped oversized file or a
reached limit shows “Partial results”. A ten-second deadline reports an error.
Narrow the focused folder when a search is incomplete.
See [the search lifecycle decision].

## Settings and defaults

Open the gear menu to change these settings. Defaults below apply before
stored preferences are loaded.

| Setting | Default | Persistence and scope |
| --- | --- | --- |
| Show dotfiles | Off | Current page; a private server URL with `?hidden=show` starts with them visible. Public mode still refuses hidden paths. |
| Compact rows | On | Current page; switching off selects comfortable density. |
| Dark theme | System preference at startup | Current page; the menu can override it. |
| Sort | Name, ascending | Stored per origin in `filemill.sort`; size and modified sorting may read metadata for each file. |
| Rich previews | On | Stored per origin in `filemill.rich`; static and native CDN renderers use it. Server renderers hide the switch. |

The implementations are [settings], [sort preferences], [initial state] and
[rich-preview consent]. Static recent folders and their selection chains use
IndexedDB separately; JSON collapse choices remain in memory for the session.
Matching JSON paths at the same depth stay collapsed across similar objects.
An explicit expansion takes precedence for that object.

## Preview modes and document links

Markdown and WebVTT offer one Raw link and a Source/Rendered toggle in both
browser editions, including the server's Open Folder mode. Source keeps the
original text and selection. Raw opens browser-owned bytes in a new tab or
opens a served file's raw URL. Some server member Source views remain limited;
see [architecture finding A8].

Rendered Markdown hides HTML comments. Source and Raw keep them. Comments
inside code stay visible; other raw HTML stays escaped. Markdown text and code
wrap on narrow screens, while wide tables scroll inside the preview.

Markdown and RST documents with enough headings open as section columns.
Select the document to preview it whole, or a section to preview that slice.
Served section URLs can open directly. To show a heading inside the whole
Markdown file, use `guide.md?f#heading-slug`. GitHub slugs use lowercase,
remove punctuation and replace spaces with hyphens: `Q1: scope` becomes
`#q1-scope`. Existing renderer IDs also work. An unknown heading keeps the
whole document open. See the [heading-fragment decision].

Served relative Markdown links open rendered unless they select another mode.
Queries and fragments are preserved. In server URLs, bare files return bytes;
`?f` opens the rendered view and `?filemill=highlight` opens source. Layout
accepts `full-columns` (default) and `compressed-columns`.

## Structured files and refresh

JSON and JSONL open as columns in both browser editions. Select a scalar to
preview its value; string values preserve line breaks. JSON documents have
an 8 MiB limit; ordinary text previews have a 512 KiB limit. Larger JSONL uses
a lazy line index. CSV rows also use the shared browser adapters. SQLite,
archive and Git bundle browsing require the server edition.

Refresh a JSON column to read the current file, including an archive member.
Nested columns read the source again too. Selection and preview follow the
new values. Removed keys close their paths; invalid JSON shows an error with
the current source. See the [refresh contract].

## Copy, edit and delete

Right-click an entry, long-press it on touch screens, or use Shift+F10 or the
Context Menu key. Use arrows to choose an action, Enter to run it and Escape
to close the menu. Deletion asks for confirmation and refreshes the folder.
Deleting a folder removes its contents.

If clipboard access is refused, a manual-copy dialog selects the exact value.
Use the browser's copy command or touch selection menu, then close it.

Editing is available when the filesystem can write and the file is editable.
Browser folders request write permission when needed. Public served roots and
offline copies are read-only. Saves check the revision read by the editor;
a conflict keeps the draft. Explicit navigation still discards an open draft.
See the [security policy] for replacement guarantees and limits.

[edition reference]: ../README.md#choose-an-edition
[native guide]: ../native/README.md
[history decision]: adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
[settings]: ../ui/core/settings.js
[sort preferences]: ../ui/core/sort.js
[initial state]: ../ui/core/model/state.js
[rich-preview consent]: ../ui/adapters/preview-rich.js
[architecture finding A8]: ARCHITECTURE-REVIEW.md#a8-preview-source-and-representation-are-conflated
[heading-fragment decision]: adr/0085-markdown-heading-fragments-scroll-the-preview.md
[refresh contract]: adr/0041-core-adapters-three-ports.md#refresh-invalidation-2026-10-21
[security policy]: ../SECURITY.md

[the search lifecycle decision]: adr/0092-shared-content-search-capability.md
