/* ═══════════════════════════════════════════════════════════════════════════
   Ports — the three seams between the shared UI and whatever is behind it.

   Everything in core/ is source-agnostic: it knows about nodes, columns and
   keystrokes, never about the File System Access API, HTTP, or a URL scheme.
   The three objects below are what an adapter fills in. Pick a different set
   and the same UI browses a server instead of a local folder.

   ── FS ─ the filesystem ────────────────────────────────────────────────────
   A node is  { name, dir, kids }  plus whatever the adapter needs to fetch it:
       kids === null        directory, not read yet   → spinner
       kids === []          read, and empty (or unreadable — see .denied)
       kids === [Node…]     read
       node.denied          string; shown in place of the rows
       node.meta            { size, mod, type } once loadMeta has run
       node.lastSel         UI scratch — written by the UI, never by an adapter

     ensureLoaded(node) → Promise   fills node.kids (idempotent, debounced)
     loadMeta(node)     → Promise   fills node.meta  (may be a no-op if the
                                    listing already carried the metadata)

   ── PREVIEW ─ the preview body ─────────────────────────────────────────────
     render(node) → Promise<string|null>
         HTML for the preview body, or null for "no inline preview". The pane's
         chrome — header, hero, size/modified list — is core's, and so is the
         staleness guard: a provider may take as long as it likes.
     revoke()  → void                optional; release object URLs

   ── ROUTER ─ the address bar ───────────────────────────────────────────────
     read()          → {root, path:[names…]} | null    the location right now
     write(state)    → void                            reflect state, no reload
     onNavigate(cb)  → void                            back/forward pressed
     Set to null to run with no URL syncing at all.
   ═══════════════════════════════════════════════════════════════════════════ */
let FS = null, PREVIEW = null, ROUTER = null;

const useFilesystem = a => { FS = a; };
const usePreview    = p => { PREVIEW = p; };
const useRouter     = r => { ROUTER = r; };
