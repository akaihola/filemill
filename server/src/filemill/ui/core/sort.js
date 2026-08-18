/* ═══════════════════════════════════════════════════════════════════════════
   Sort order — name, size or modification time, ascending or descending.

   The three keys do not cost the same, and that asymmetry is the whole design.

   A listing already carries the names, so sorting by name reads what the column
   is holding: no fetch, no wait, no code below `sortKids` runs at all. It is the
   default for that reason.

   Size and modification time are not in a File System Access API listing.
   `entries()` yields a name and a handle; a size costs one `getFile()` per row.
   Ordering 3 000 entries by size therefore means 3 000 reads before the first
   row can be placed — the sweep this file exists to manage. It runs when the
   user picks one of the two keys that needs it, on the directories on screen,
   once each.

   One sweep serves both metadata keys: `getFile()` hands back the size and the
   mtime together, so switching from size to modified re-sorts what is already
   in hand and fetches nothing.

   Nothing here knows where metadata comes from. `FS.loadMeta` does, which is
   what makes this shared: pykofinder's listing carries size and mtime already,
   so its sweep finds nothing to fetch and returns on one `if`. The same option
   costs the server build a comparison and the local build a syscall per row.
   ═══════════════════════════════════════════════════════════════════════════ */

const SORT_KEYS  = ["name", "size", "mtime"];
const SORT_FIELD = { size: "size", mtime: "mod" };    /* node.meta field per key */
const SORT_LABEL = { name: "name", size: "size", mtime: "modified" };

const sortNeedsMeta = () => state.sort.key !== "name";

const byName = (a, b) => a.name.localeCompare(b.name, undefined, { numeric: true });

/* The number to order on, or null for "this row has none". A file the port
   could not open carries `meta.error`; a row inside a database carries
   `meta.virtual` and no size at all. Both are honestly unknown. */
const sortValue = (k, field) => {
  const v = k.meta && !k.meta.error ? k.meta[field] : undefined;
  return typeof v === "number" ? v : null;
};

/* Directories first, then the chosen key, then the name to break ties.
   `kids` is already the filtered copy visibleKids made, so sorting it in place
   never touches node.kids.

   Directories are never ordered by size or time. Neither port can give a
   directory either number: the File System Access API has no `getFile()` for a
   directory handle, and pykofinder's listing sends metadata for files only. A
   folder ordered by an invented 0 would sit at one end of every size sort and
   mean nothing there, so folders keep the one order that is real for them.

   A file whose metadata could not be read sorts last, in name order, in *both*
   directions. Sorting by size descending asks "what is biggest here"; a file
   the app could not open is not the answer, and putting one at the top is how a
   permission error gets read as a result. Last either way keeps the end the
   user is looking at meaningful. The row is never dropped — an unreadable file
   is still a file in that folder, and hiding the rows it failed to stat would
   make the app lie about the directory. */
function sortKids(kids) {
  const { key, desc } = state.sort;
  const dir = desc ? -1 : 1;
  const field = SORT_FIELD[key];
  return kids.sort((a, b) => {
    const kind = !!b.dir - !!a.dir;
    if (kind) return kind;
    if (field && !a.dir) {
      const av = sortValue(a, field), bv = sortValue(b, field);
      if (av === null || bv === null) {
        if (av !== bv) return av === null ? 1 : -1;      /* unknown sinks */
      } else if (av !== bv) {
        return (av < bv ? -1 : 1) * dir;
      }
    }
    return byName(a, b) * (field ? 1 : dir);
  });
}

/* ── The sweep ──────────────────────────────────────────────────────────────
   One sweep per directory, one in-flight promise held on the node, one writer
   of the metadata — the shape `FS.ensureLoaded` already has for `node.kids`, so
   a second render during a sweep joins the one running instead of starting a
   rival. `metaDone` is the counterpart of `kids !== null`: this directory has
   been asked, and asking again would be 3 000 syscalls for an answer already in
   memory. */
function ensureMeta(node) {
  if (node.metaLoading) return node.metaLoading;
  const kids = node.kids;
  const todo = kids.filter(k => !k.dir && !k.meta);
  /* Nothing to fetch: the listing carried it (pykofinder), or a preview already
     did. Settle it here, before columnFor runs, so a column that needs no sweep
     is built once in the right order rather than built and rebuilt. */
  if (!todo.length) { node.metaDone = true; return null; }

  let done = 0;
  node.metaLoading = (async () => {
    const t0 = performance.now();
    await Promise.all(todo.map(k => FS.loadMeta(k)
      /* The port promises to *fill* node.meta, not that it never rejects. One
         rejection escaping here would leave metaLoading set and metaDone false
         for good, and the column would spin at the user until the tab closed.
         Recording the error on the row puts it in the same bucket
         FSA.loadMeta already uses for a file it could not open, which is the
         bucket sortValue reads as "unknown". */
      .catch(err => { k.meta = { error: String((err && err.message) || err) }; })
      /* One status write per row would cost more than the sweep it reports.
         Every 64th is an update per ~8 ms at the rates measured here, which is
         faster than anyone reads. */
      .then(() => { if (++done % 64 === 0) sortProgress(done, todo.length); })));
    node.metaSwept = { n: todo.length, ms: Math.round(performance.now() - t0) };
    /* A refresh replaces node.kids wholesale. A sweep that started on the old
       array has just filled objects nobody can see, and marking the *new* list
       done would leave it ordered by whatever its rows happened to carry. */
    if (node.kids === kids) node.metaDone = true;
    node.metaLoading = null;
  })();
  return node.metaLoading;
}

/* Called from render(), so no navigation path has to remember to ask: whatever
   is on screen gets the metadata the current sort needs, exactly once. Sorting
   by name needs none, so the default never reaches `ensureMeta` at all — the
   expensive path is entered by the option that asked for it and by nothing
   else. */
function sweepMeta(node) {
  if (!FS || !node.dir || node.kids === null || node.metaDone || node.metaLoading
      || !sortNeedsMeta()) return;
  const p = ensureMeta(node);
  if (!p) return;                            /* answered without fetching */
  p.then(() => {
    /* The second half of the guard choose() uses on its own reads: a sweep can
       outlive the column that started it, and re-rendering for a directory that
       is no longer open would reorder nothing and cost a rebuild. The metadata
       it collected is kept either way — it is a fact about those files, and
       stepping back into the folder finds it there.

       Dropping the repaint is safe rather than lossy because columnFor treats
       `metaDone` like `kidsRef`: any later render rebuilds a column whose DOM
       predates its sweep. Nothing can be left showing an order it no longer
       has. */
    if (!path.includes(node)) return;
    render(true);
  });
}

/* ── What the strip says ────────────────────────────────────────────────────
   A sort that reads 3 000 files takes a visible moment, and a column that sits
   there in name order while it happens looks like a sort that did nothing. */
const sortSay = msg => {
  const el = document.getElementById("st-sort");
  if (el) el.textContent = msg;
};

const sortProgress = (done, total) =>
  sortSay(`⇅ ${SORT_LABEL[state.sort.key]} — read ${done} of ${total}`);

/* Written by render(), so it follows the focused column. Silent on the default
   (name, ascending): a strip that always says something says nothing. */
function sortStatus() {
  const busy = path.find(n => n.metaLoading);
  if (busy) return `⇅ ${SORT_LABEL[state.sort.key]} — reading ${busy.kids.length} entries…`;
  const { key, desc } = state.sort;
  if (key === "name" && !desc) return "";
  const swept = sortNeedsMeta() && path[focusCol] && path[focusCol].metaSwept;
  return `⇅ ${SORT_LABEL[key]} ${desc ? "↓" : "↑"}`
       + (swept ? ` · ${swept.n} read in ${swept.ms} ms` : "");
}

/* ── Remembering it ─────────────────────────────────────────────────────────
   localStorage, not the per-folder record in IndexedDB. The sort is a property
   of how a person reads a list, not of the folder they are reading — the same
   argument that already keeps dotfiles, density and the rich-preview switch out
   of that record. It is also the only store both builds have: pykofinder serves
   this file and has no remembered folders at all. And the record offers nowhere
   to hang it: `keepView` fires from `ROUTER.write`, which core calls when the
   *location* changes, and choosing a sort moves nobody.

   A remembered size sort does mean a mount can start a sweep the user did not
   ask for in this session. They did ask for it, last session, and the column
   says so while it reads. */
const SORT_STORE = "filemill.sort";

function loadSort() {
  try {
    const [key, dir] = String(localStorage.getItem(SORT_STORE) || "").split(":");
    if (SORT_KEYS.includes(key)) state.sort = { key, desc: dir === "desc" };
  } catch (err) { /* private mode, or an opaque file:// origin — keep the default */ }
}

function setSort(key, desc) {
  state.sort = { key, desc };
  try { localStorage.setItem(SORT_STORE, `${key}:${desc ? "desc" : "asc"}`); }
  catch (err) { /* the sort still applies; it just will not survive a reload */ }
  syncSortMenu();
  /* cacheSig carries the sort, so this drops every cached column and rebuilds
     it in the new order — the same route the dotfile and density switches take
     for the same reason. */
  render(true);
}

function syncSortMenu() {
  for (const k of SORT_KEYS) {
    const b = document.getElementById(`s-sort-${k}`);
    if (b) b.setAttribute("aria-checked", String(state.sort.key === k));
  }
  const d = document.getElementById("s-sort-desc");
  if (d) d.setAttribute("aria-checked", String(state.sort.desc));
}

loadSort();
syncSortMenu();
