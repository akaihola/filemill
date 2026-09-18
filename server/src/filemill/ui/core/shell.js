/* ═══════════════════════════════════════════════════════════════════════════
   The chrome — top bar, stage, status strip, welcome screen.

   In JavaScript rather than in the HTML file because there are two HTML files
   (a static one and one the server emits) and this markup has to be the same
   in both. A shared *file* would need a build step or a fetch; the static build
   can afford neither, since it has to keep running unbuilt from src/ and, once
   bundled, from a file:// page with no network at all.

   So: one page structure, emitted before anything queries it. Every id below is
   part of the contract core/ relies on — state.js takes its element handles the
   moment it loads, which is why this script comes first.
   ═══════════════════════════════════════════════════════════════════════════ */
document.body.insertAdjacentHTML(
  "afterbegin",
  `
<div id="shell">
  <nav id="bar" aria-label="File navigation">
    <div id="crumbs"></div>
    <form id="search-form" role="search">
      <label class="sr-only" for="search-bar">Search file contents</label>
      <input id="search-bar" type="search" placeholder="Search files…"
             autocomplete="off" aria-controls="search-results">
      <div id="search-results" role="status" aria-live="polite" hidden></div>
    </form>
    <div class="spacer"></div>
    <button class="tb" id="gear" aria-expanded="false" title="Settings">⚙</button>
    <div id="settings" hidden>
      <div class="grp">View</div>
      <button id="s-dot"     role="menuitemcheckbox" aria-checked="false"><span class="tick">✓</span>Show dotfiles</button>
      <button id="s-density" role="menuitemcheckbox" aria-checked="true"><span class="tick">✓</span>Compact rows</button>
      <hr>
      <!-- The hints are the point of this group: sorting by size or date has to
           read every file in the folder, and the menu is where that price can
           be shown before it is paid. Name asks for nothing and is the default. -->
      <div class="grp">Sort by</div>
      <button id="s-sort-name"  role="menuitemradio" aria-checked="true"><span class="tick">✓</span>Name</button>
      <button id="s-sort-size"  role="menuitemradio" aria-checked="false"><span class="tick">✓</span>Size<span class="hint">reads every file</span></button>
      <button id="s-sort-mtime" role="menuitemradio" aria-checked="false"><span class="tick">✓</span>Modified<span class="hint">reads every file</span></button>
      <button id="s-sort-desc"  role="menuitemcheckbox" aria-checked="false"><span class="tick">✓</span>Descending</button>
      <hr>
      <div class="grp" id="s-previews" hidden>Previews</div>
      <button id="s-rich" role="menuitemcheckbox" aria-checked="true" hidden><span class="tick">✓</span>Rich previews<span class="hint">downloads a renderer (13 MB for reStructuredText)</span></button>
      <hr id="s-rich-hr" hidden>
      <div class="grp">Appearance</div>
      <button id="s-theme"   role="menuitemcheckbox" aria-checked="false"><span class="tick">✓</span>Dark theme</button>
      <hr>
      <!-- The hash rides in as data-commit on <html> — the server sets it when
           its checkout has one; the static build has no repository, so the
           version stands alone. -->
      <div class="grp">About</div>
      <div class="ver">Filemill 0.1.0${
    document.documentElement.dataset.commit
      ? ` · ${document.documentElement.dataset.commit}`
      : ""
  }</div>
    </div>
  </nav>

  <div id="finder">
    <div id="rail">
      <div id="stage">
        <svg id="trail"></svg>
        <div id="strip"><!-- columns + preview injected here --></div>
      </div>
    </div>
  </div>

  <div id="status">
    <span id="st-path" title="Click to copy this path"></span>
    <span id="st-copy"></span>
    <div class="spacer"></div>
    <span id="st-find"></span>
    <span id="st-sort"></span>
    <span id="st-refresh"></span>
    <span id="st-fold"></span>
    <span class="status-hints">
      <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
      <span><kbd>→</kbd> open</span>
      <span><kbd>←</kbd> back</span>
      <span><kbd>a…z</kbd> find</span>
      <span><kbd>F5</kbd> refresh</span>
      <span><kbd id="kbd-copy">⌘C</kbd> copy path</span>
    </span>
    <span class="status-fold"><kbd>⇧</kbd>+wheel fold</span>
  </div>
  <div id="row-menu" role="menu" hidden></div>
</div>

`,
);

/* Nothing to export: the page structure is the product. The empty export
   marks the file as a module, which is what lets the entry import it for
   its effect alone. */
export {};
