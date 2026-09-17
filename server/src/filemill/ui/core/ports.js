/* ═══════════════════════════════════════════════════════════════════════════
   Ports — the three seams between the shared UI and whatever is behind it.

   Everything in core/ is source-agnostic: it knows about nodes, columns and
   keystrokes, never about the File System Access API, HTTP, or a URL scheme.
   The three objects below are what an adapter fills in. Pick a different set
   and the same UI browses a server instead of a local folder.

   ── FS ─ the filesystem ────────────────────────────────────────────────────
   FS.node(name, ...args) → Node creates the adapter's root or child node. The
   core passes the arguments declared by the adapter's node factory and does
   not inspect them.

   Every node has these core fields:
       name       string; display name and path segment
       dir        boolean; true when the node can have children
       kids       null for an unread directory; [] for a loaded empty or
                  unreadable directory; [Node…] for loaded children; undefined
                  for a file or leaf
       denied     string when loading failed; shown instead of directory rows
       meta       {size, mod, type} for known file metadata, {virtual: true}
                  for virtual entries, or {error: string} when metadata failed;
                  absent until loadMeta runs
       loading    Promise while an adapter load is active; otherwise null/absent
       metaDone   boolean UI scratch: every loaded file child was asked for meta
       metaLoading Promise while the core metadata sweep is active; UI scratch
       metaPending number of metadata requests left in that sweep; UI scratch
       metaSwept  {n, ms} summary of the last metadata sweep; UI scratch

   Existing adapter or virtual-filesystem fields:
       handle     File System Access API handle
       parent     parent File System Access API handle, when available
       file       cached File from handle.getFile()
       rel        server root-relative path
       vpath      virtual path inside rel (JSON key, table, or row)
       ordered    boolean; preserve the adapter's documented child order when true
       icon       string; explicit icon glyph
       page       one-based current server listing page
       pages      total server listing pages
       total      total server listing entries
       previewFormat string; requested preview format
       csv        boolean; this node is a CSV virtual directory
       jsonl      boolean; this node is a JSONL virtual directory
       json       boolean; this node is a JSON virtual directory or value
       headers    parsed CSV column names
       csvEmpty   boolean; parsed CSV has no records
       csvError   boolean; CSV parsing/loading failed
       value      parsed JSON value for a virtual node
       record     parsed CSV, JSONL, or JSON table-row value
       jsonError  string; JSON parsing/loading error

     ensureLoaded(node) → Promise   fills node.kids (idempotent, debounced)
     loadMeta(node)     → Promise   fills node.meta (or records {error}); may
                                    be a no-op when the listing has metadata
     blob(node)         → Promise<Blob|null> returns file bytes for preview, or
                                    null when the file cannot be read
   write(node, text)  → Promise   optional; overwrite the file with `text`.
                                    A port without it is read-only — the
                                    preview pane then offers no Edit action.
   remove(node)       → Promise   optional; delete a selected real file or
                                    directory.

   loadMeta is called once per selected file, and once per *row* when the user
   sorts a column by size or by modification time — see core/sort.js. A port
   whose listing already carries the metadata pays nothing for that sort; one
   that does not pays a round-trip per row, which is why name is the default
   order and the only one that never calls this. Record a failure on the node
   (`node.meta = {error}`) rather than rejecting, the way both adapters here do.

   ── PREVIEW ─ the preview body ─────────────────────────────────────────────
     render(node) → Promise<string|null>
         HTML for the preview body, or null for "no inline preview". The pane's
         chrome — header, hero, size/modified list — is core's, and so is the
         staleness guard: a provider may take as long as it likes.
     revoke()  → void                optional; release object URLs

   ── ROUTER ─ the address bar ───────────────────────────────────────────────
     read()          → {root, path:[names…]} | null    the location right now
     write(state, replace) → void                      reflect state, no reload;
                                    use replaceState when replace is true,
                                    pushState otherwise
     onNavigate(cb)  → void                            back/forward pressed
     Set to null to run with no URL syncing at all.

   RouterPath.base is the trailing-slash base URL used by the path router. It
   comes from the current script's data-base attribute, or "/", and is used to
   strip/add the server mount prefix. It is not part of router state.
   ═══════════════════════════════════════════════════════════════════════════ */
export let FS = null, PREVIEW = null, ROUTER = null;

export const useFilesystem = (a) => {
  FS = a;
};
export const usePreview = (p) => {
  PREVIEW = p;
};
export const useRouter = (r) => {
  ROUTER = r;
};
