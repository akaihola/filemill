/* ════════════════════════════════════════════════════════════════
   PWA Setup
   ════════════════════════════════════════════════════════════════ */
(function setupPWA() {
  const manifest = {
    name: 'Finder — Column View', short_name: 'Finder',
    start_url: '.', display: 'standalone',
    background_color: '#ececec', theme_color: '#c8c8c8',
    icons: [{ src: 'data:image/svg+xml,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">' +
      '<rect width="192" height="192" rx="40" fill="#1070cf"/>' +
      '<text x="96" y="130" font-size="110" text-anchor="middle" fill="white">⌘</text></svg>'
    ), sizes: '192x192', type: 'image/svg+xml' }]
  };
  const mlink = document.createElement('link');
  mlink.rel = 'manifest';
  mlink.href = URL.createObjectURL(new Blob([JSON.stringify(manifest)], { type: 'application/manifest+json' }));
  document.head.appendChild(mlink);

  if ('serviceWorker' in navigator) {
    const sw = `const C='finder-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.add('/')));self.skipWaiting();});
self.addEventListener('activate',e=>{self.clients.claim();});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));});`;
    navigator.serviceWorker.register(
      URL.createObjectURL(new Blob([sw], { type: 'application/javascript' }))
    ).catch(() => {});
  }
})();

/* ════════════════════════════════════════════════════════════════
   Init — start with mock data (OWC → Images → Finder Views Column Cover → ColumnView.tiff)
   ════════════════════════════════════════════════════════════════ */
// Derive activeSidebarIdx from the label so it's resilient to list reordering
activeSidebarIdx = SIDEBAR_ITEMS.findIndex(s => s.label === 'OWC');

initToMockPath(
  ['Users', 'casey', 'OWC'],
  ['Images', 'Finder Views Column Cover', 'ColumnView.tiff']
);
render();
scrollToActiveColumn();
pushHistory();

setTimeout(() => {
  document.getElementById('columns-container').focus();
  focusedColIdx = Math.max(0, columns.length - 2);
}, 50);

// Restore previously-authorised FSA handles from IndexedDB (no user gesture needed
// for queryPermission — only 'granted' ones are restored silently).
restoreFSAHandlesFromIDB();
