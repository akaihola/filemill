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
document.body.insertAdjacentHTML("afterbegin", `
<div id="shell">
  <div id="bar">
    <div id="crumbs"></div>
    <div class="spacer"></div>
    <span id="local-badge" hidden>
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.4 3.2h4.1l1.3 1.7h7.8c.6 0 1 .4 1 1v7c0 .6-.4 1-1 1H1.4c-.6 0-1-.4-1-1V4.2c0-.6.4-1 1-1z"/></svg>
      <span class="nm"></span>
      <button id="leave-local" title="Back to the served folder">✕</button>
    </span>
    <button class="tb" id="open" title="Open a folder on this machine">
      <svg class="tb-ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.4 3.2h4.1l1.3 1.7h7.8c.6 0 1 .4 1 1v7c0 .6-.4 1-1 1H1.4c-.6 0-1-.4-1-1V4.2c0-.6.4-1 1-1z"/></svg>
      Open Folder…</button>
    <button class="tb" id="gear" aria-expanded="false" title="Settings">⚙</button>
    <div id="settings" hidden>
      <div class="grp">View</div>
      <button id="s-dot"     role="menuitemcheckbox" aria-checked="false"><span class="tick">✓</span>Show dotfiles</button>
      <button id="s-density" role="menuitemcheckbox" aria-checked="true"><span class="tick">✓</span>Compact rows</button>
      <hr>
      <div class="grp">Previews</div>
      <button id="s-rich" role="menuitemcheckbox" aria-checked="true" hidden><span class="tick">✓</span>Rich previews<span class="hint">downloads a renderer</span></button>
      <hr id="s-rich-hr" hidden>
      <div class="grp">Appearance</div>
      <button id="s-theme"   role="menuitemcheckbox" aria-checked="false"><span class="tick">✓</span>Dark theme</button>
    </div>
  </div>

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
    <span id="st-refresh"></span>
    <span id="st-fold"></span>
    <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
    <span><kbd>→</kbd> open</span>
    <span><kbd>←</kbd> back</span>
    <span><kbd>a…z</kbd> find</span>
    <span><kbd>F5</kbd> refresh</span>
    <span><kbd id="kbd-copy">⌘C</kbd> copy path</span>
    <span><kbd>⇧</kbd>+wheel fold</span>
  </div>
</div>

<div id="welcome">
  <svg class="mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.4 3.2h4.1l1.3 1.7h7.8c.6 0 1 .4 1 1v7c0 .6-.4 1-1 1H1.4c-.6 0-1-.4-1-1V4.2c0-.6.4-1 1-1z"/></svg>
  <h1 id="w-title">Filemill</h1>
  <p id="w-msg">Pick a folder on this machine to browse it in Miller columns.
     Nothing leaves the browser — the folder is read locally, on demand.</p>
  <button class="btn" id="w-pick">Choose Folder…</button>
  <div id="w-recent" hidden>
    <div class="rec-head">Recently opened</div>
    <div class="rec-list"></div>
  </div>
  <p class="note">Needs a Chromium-based desktop browser (File System Access API).</p>
</div>`);
