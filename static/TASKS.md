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
      Home/End, Escape closes the popover
- [x] **Performance** — column DOM cache, in-place reconciliation, write guards
      and `content-visibility`; ~5 ms re-render and 4–9 ms keystrokes at 3 000
      entries, down from ~500 ms and ~740 ms
- [x] **Spine click unfolds** — the design study advertised it but never wired it
- [x] **Tests** — `test-ui.py` (28 headless checks incl. a perf budget, runs
      against both the bundle and the modular sources), `test-e2e.py` (real
      folder, real picker, persistence), `FSA-TEST-CHECKLIST.md` for the rest
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

- [ ] **Refresh a directory** — nothing re-reads a folder after the disk
      changes. A ⟳ button or F5-on-column would re-run `ensureLoaded` on the
      focused directory (there is no watch API; it has to be manual)
- [ ] **Type-ahead** — typing letters should jump to the matching row in the
      focused column. The previous implementation did prefix → substring →
      fuzzy with `<mark>` highlighting; worth porting
- [ ] **Copy path** — ⌘C / a status-bar click to copy the selected item's path
- [ ] **Virtualised rows** — `content-visibility` made forced layout cheap, but
      a 100 k-entry directory still builds 100 k DOM nodes (~1 s). Only worth
      doing if such folders show up in practice
- [ ] **Sort options** — name / size / mtime, ascending or descending. Needs
      metadata for every row, so it implies a `getFile()` sweep per directory
- [ ] **Remember view state per folder** — restore the last selection chain when
      re-mounting a remembered root
- [ ] **PWA manifest + service worker** — the old app had one; would let the
      bundle be installed and launched as a standalone window
