# Filemill, static edition — Task List

Legend: `[ ]` open · `[~]` in progress · `[x]` done

> History note: this repo previously held a macOS-Finder-replica mock-up with a
> sidebar, toolbar and static example content. It was replaced wholesale by the
> Miller-columns app described in `AGENTS.md`; that work is in git history and
> is not tracked here any more.

---

## ✅ Done — the current app

- [x] **Miller-columns UI** ported from the "Trail" design study: column headers
      with counts, three selection states, trail elbows, fold-to-spine dial,
      ⚙ popover (dotfiles / density / dark theme)
- [x] **All example content removed** — the only data source is a real folder
- [x] **Folder picker welcome screen** + **Open Folder…** in the top bar
- [x] **Single-file build** — Seti icon map and WOFF font embedded; `index.html`
      has zero external references
- [x] **Modular sources** — `src/*.js` + `src/styles.css`, with
      `src/index.html` as a build-free dev entry point and `build-index.py`
      inlining everything for the bundle
- [x] **Lazy directory reads** with spinner / `Empty` / `⚠ No permission` states
- [x] **Preview** — real size and mtime from `getFile()`, inline text and image
      previews, races guarded by `pvToken`
- [x] **Remembered folders** — last 8 roots in IndexedDB; still-granted ones
      re-mount with no dialog, the rest are one click on the welcome screen
- [x] **`file://` guard** — explains the localhost requirement instead of
      failing silently on Chrome's `SecurityError`
- [x] **Keyboard model** — ↑/↓ stay in the focused column, → descends (and
      returns to the row a column was last left on), ← comes back out,
      Home/End, F5 re-reads the focused folder, Escape closes the popover
- [x] **Performance** — column DOM cache, in-place reconciliation, write guards
      and `content-visibility`; ~5 ms re-render and 4–9 ms keystrokes at 3 000
      entries, down from ~500 ms and ~740 ms
- [x] **Spine click unfolds** — the design study advertised it but never wired it
- [x] **Tests** — `test-ui.py` (84 headless checks incl. a perf budget, runs
      against both the bundle and the modular sources), `test-e2e.py` (real
      folder, real picker, persistence, the real clipboard, and refresh plus
      view-state restore against a throwaway folder it creates and deletes),
      `FSA-TEST-CHECKLIST.md` for the rest
- [x] **`hotreload.py`** — retargeted at the dev entry point

---

## ✅ Done — shared with filemill

- [x] **`core/` + `adapters/`** — the UI runs over the File System Access API
      *and* over a server, through three ports (`core/ports.js`): FS, PREVIEW,
      ROUTER. filemill serves `core/` byte-for-byte and fills the ports with
      fetch, Python-rendered fragments and real URL paths
- [x] **Deep links** — the URL follows the selection and a link restores it.
      `#r=<root>&p=<path>` here (a hash survives `file://` and any static host);
      filemill uses the real path. `core/deeplink.js` is shared verbatim.
      Stale links open the deepest folder that still exists; a link to a dotfile
      reveals dotfiles. 12 checks in `test-url.py`
- [x] **`core/shell.js`** — the chrome is emitted by one file, so this app and
      the server one cannot drift apart on markup
- [x] **Publishing** — `.github/workflows/publish.yml` tests every push and
      deploys the bundle to GitHub Pages from `main`. Pages is a secure context,
      so the picker works there; a downloaded file opened from disk cannot use
      it. `./build-index.py --check` fails a stale committed bundle
- [x] **PDF and `.desktop` previews** — object URL in an `<iframe>` (Chromium
      renders PDF natively) and a 20-line INI parse. No bundle cost

---

## 🔭 Open — worth considering

- [x] **Rich previews** — `preview-rich.js` lazy-loads markdown-it (+ footnote,
      deflist, task-lists, anchor), highlight.js and mammoth from a CDN on first
      use, so the bundle stays one portable file. Behind a remembered ⚙ switch
      because it is the only thing here that touches the network; every failure
      falls back to the raw source with a one-line note. Wikilinks resolve
      inside the browsed folder
- [x] **One repo with the server edition** — done; `ui/` is shared, and
      `server/tools/sync-ui.py --check` now guards a *packaging* copy rather
      than two repositories

- [x] **Refresh a directory** — ⟳ in the focused column's header, or F5.

      For the person browsing: a file another program wrote used to be invisible
      until the whole app was reloaded, and reloading drops the mounted folder,
      every open column and the scroll position. Now one key re-reads the folder
      and everything stays where it is. The strip says what moved — `⟳ 2 new,
      1 gone`, or `⟳ no change`, so a refresh that found nothing still answers.

      Why it has to be manual: neither port can tell the app a directory
      changed. The File System Access API has no watch call, and the server one
      would need a socket the static single file cannot open. A folder read once
      stays as it was read until somebody asks. Polling instead would re-read
      folders nobody is looking at, on a battery, forever.

      **Refresh is not a second way to load a directory.** It empties
      `node.kids` and calls the same `FS.ensureLoaded` every other caller uses,
      so there is one loading path, one debounce, and exactly one writer of
      `node.kids`. Two loaders on one field is a race that reproduces once a
      month on somebody else's machine.

      | Situation | Result |
      | --------- | ------ |
      | The selected entry is still there | Stays selected. Every column open below it stays open |
      | The selected entry is gone | Nothing is selected — selecting whatever slid into its place would preview a file nobody asked for. The cursor stays on that row index, clamped to the shorter list, so ↓ resumes beside it. The strip names what went |
      | A folder deeper in the chain is gone | The chain is walked again by name and stops at the first level that no longer exists. Columns below that close |
      | Refresh lands on a read already in flight | It waits for that read, then re-reads once. `ensureLoaded` hands a concurrent caller the *in-flight* promise, so asking without waiting returns the very listing the refresh was called to replace |
      | The user clicks or presses a key mid-refresh | Whoever the user asked for last wins, and the columns still agree with each other. The refresh drops its repaint by bumping `navSeq`, the counter `choose` already uses for the same reason |
      | A preview was being built for the old node | The re-render calls `fillPreview` on the new node, which bumps `pvToken`; the older read is discarded when it lands |
      | Focus | Stays on the column the user was in, clamped to the new depth |

      Refreshing a parent re-reads the columns open below it as well. It has to:
      a re-read hands back new node objects, so identity is gone and the chain
      must be matched by name anyway. Re-reading is also the honest answer —
      those columns are on screen, and one fresh column beside three stale ones
      is worse than the extra reads. Closed subtrees are untouched.

      The walk is `applyPath`, the one a deep link already used. Three callers
      now share it — refresh, a pasted link, and a restored folder — so they
      cannot disagree about what a half-valid chain means.

      In `ui/core/nav.js` (`refreshColumn`), the button in `render.js`'s
      `buildCol`, and one optional `wantFocus` argument on `applyPath`. The
      server edition gets refresh with no adapter work: `HTTP.ensureLoaded`
      re-fetches for the same reason `FSA.ensureLoaded` re-reads.

      Measured at 3 000 entries, in-page, `test-ui.py`: a refresh rebuilds the
      column in **371 ms**, which is the build cost the column cache exists to
      avoid paying *per keystroke* — here it is paid once, when the user asks,
      because the entry list really did change. The arrow key straight after it
      still costs **7.5 ms**, inside the 4–9 ms budget. 20 checks in
      `test-ui.py`, 3 more in `test-e2e.py` against a real folder
- [x] **Type-ahead** — typing letters jumps to the matching row in the focused
      column. For the person browsing, a folder of 400 entries goes from about
      200 presses of ↓ to three letters. Three rungs run in order over the whole
      column and the first hit wins: prefix, then substring, then fuzzy. Keeping
      them as separate passes is what lets a name *starting* with "notes" beat
      one on row 3 that merely contains it. The rung that matched also decides
      the `<mark>` runs, so the highlight explains the jump: one pill for prefix
      and substring, scattered characters for fuzzy.

      The buffer expires 1.2 s after the last letter, so "re" then "adme" finds
      `readme.md` while a pause starts a new search. Arrows, Home/End and Escape
      keep the meanings the keyboard model already gave them and each ends a
      live search; Escape ends the search when there is one and closes the ⚙
      popover otherwise, so one press does one thing. A letter with Ctrl, ⌘ or
      Alt held is a shortcut, never a search — swallowing ⌘R would break reload.
      Matching runs on the rows the column already holds, so a directory still
      being read reports "still reading" instead of matching a stale list.

      Lives in `ui/core/typeahead.js`, so pykofinder gets it with no adapter
      work: a column is a list of names whichever port filled it. Only two rows
      are rewritten per keystroke, the one that was marked and the one that now
      is; marking every matching row would be an innerHTML write per entry,
      which is the O(entries) cost this app already paid to delete.

      Measured at 3 000 entries, in-page, `test-ui.py`: matching costs **1.1 ms**
      (bundle) and **1.8 ms** (modular sources), and a keystroke that finds
      nothing costs **2.3–3.3 ms** end to end, including the status-strip write.
      A keystroke that *does* find something costs 45.5 ms, against 67.4 ms for
      an arrow key moving through the same column — both numbers are the price
      of selecting a file there (a preview build plus a re-render, ~60 ms), not
      the price of searching. Marking and un-marking a row together measure
      0.07 ms. Nothing in the 4–9 ms keystroke figure above regressed: the
      arrow-key path is untouched
- [x] **Copy path** — ⌘C / Ctrl+C, or a click on the status-bar path, copies the
      selected item's path. The strip now joins with `/` rather than ` / `,
      because clicking it copies the string on screen and the two have to match.
      `navigator.clipboard.writeText` can be refused, and a silent refusal is
      the worst outcome: the next paste hands over whatever was there before and
      nothing says so. A refusal therefore names the error and selects the path,
      which puts the browser's own copy one keystroke away and needs no
      permission, because the user presses it. In `ui/core/nav.js` next to
      `renderCrumbs`, which is what writes that path. Note the root is a folder
      *name*: the File System Access API never hands out an absolute path, so
      `workspace/mixed/note.md` is everything the app knows
- [ ] **Virtualised rows** — `content-visibility` made forced layout cheap, but
      a 100 k-entry directory still builds 100 k DOM nodes (~1 s). Only worth
      doing if such folders show up in practice
- [ ] **Sort options** — name / size / mtime, ascending or descending. Needs
      metadata for every row, so it implies a `getFile()` sweep per directory
- [x] **Remember view state per folder** — re-mounting a remembered root
      restores the selection chain it was left on.

      For the person browsing: a folder left open three columns deep used to
      reopen at its root, so every visit began by re-walking the same three
      rows. Now the columns come back and the file is selected again. The
      welcome screen's "Recently opened" buttons say where each one will land
      (`workspace › notes › drafts`), which is the only place on that screen the
      kept chain is visible before you commit to a click.

      The record in IndexedDB grew a field instead of gaining a neighbour:

          { handle: FileSystemDirectoryHandle, path: ["notes", "drafts"] }

      A second store keyed by folder would need its own key — and a handle is
      not a path, so the only honest key is the handle already in this record.
      Two stores would also drift the first time one is pruned to 8 and the
      other is not. `asRoot` normalises a bare handle on read, so a database
      written by the previous build keeps all eight of its folders.

      The chain is a list of *names*. Node objects are built from a read that
      has not happened when the page loads, and a name outlives anything. It is
      the same list a deep link carries, so `applyPath` restores both.

      | Situation | Result |
      | --------- | ------ |
      | Every name still exists | The columns reopen, the file is selected, the row is scrolled into view |
      | A folder partway down is gone | The walk stops there. Columns above it are open, nothing below is, and nothing is selected in the column it stopped at |
      | The remembered file is gone, its folder is not | The folder opens with no selection, rather than picking whatever now sits in that row |
      | The folder was last left on its own root | Nothing to restore, so it mounts plainly |
      | A deep link is in the address bar | The link wins. The user followed it just now; the chain is only where they last stopped |
      | The database predates the chain | `asRoot` reads a bare handle as `{handle, path: []}` — the upgrade costs nobody their folders |
      | A truncated chain is saved back | Yes, truncated. The app remembers where the user actually is; keeping a chain that no longer exists would be storing a selection that is not real |

      Saving hangs off `ROUTER.write`, which core already calls on every
      selection change and nowhere else, so `ui/adapters/app-fsa.js` wraps it
      rather than core growing a hook — the server build has no remembered
      folders to hook. Writes are debounced 400 ms and skip unchanged
      locations, because `render()` also runs on resize and walking a column
      with ↓ held is one location change per keystroke; a write per keystroke
      would be the per-entry cost this app spent a rewrite deleting, in
      another costume. `visibilitychange` flushes the pending write, so a tab
      closed 100 ms after the last click still records it.

      `mounted` is set only once a mount finishes, so the mount's own renders
      cannot save a bare root over the very chain they are about to restore.

      In `ui/adapters/storage.js` and `ui/adapters/app-fsa.js` — both adapters,
      because a remembered *handle* is what this build has and the server build
      has a root path instead. No `ui/core/` file changed for this. 10 checks in
      `test-ui.py`, 3 more in `test-e2e.py` against a real folder the test
      creates, edits and deletes
- [ ] **PWA manifest + service worker** — the old app had one; would let the
      bundle be installed and launched as a standalone window
