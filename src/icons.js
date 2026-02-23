/* ════════════════════════════════════════════════════════════════
   Icon SVGs — small (16px) and big (128px) and sidebar
   ════════════════════════════════════════════════════════════════ */

function mix(hex, f) {
  const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
  return '#' + [r,g,b].map(v => Math.round(v*f+255*(1-f)).toString(16).padStart(2,'0')).join('');
}

/* ── Small icons (16 px) ─────────────────────────────────────── */

function folderSVG(color='#f5a623') {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="5.5" width="16" height="9.5" rx="1.5" fill="${color}"/>
    <rect x="0" y="4"   width="6"  height="3"   rx="1"   fill="${mix(color,0.75)}"/>
  </svg>`;
}
function imageSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="2" width="14" height="12" rx="1.5" fill="#4cd964"/>
    <polygon points="1,11 5,7 8,10 11,7 15,11 15,14 1,14" fill="#2fa84f" opacity="0.7"/>
    <circle cx="5" cy="5.5" r="1.5" fill="#fff" opacity="0.85"/>
  </svg>`;
}
function videoSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="3" width="14" height="10" rx="1.5" fill="#5e5ce6"/>
    <polygon points="6,5.5 11,8 6,10.5" fill="white"/>
  </svg>`;
}
function audioSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="2" width="14" height="12" rx="1.5" fill="#ff9500"/>
    <text x="8" y="11" font-size="8" text-anchor="middle" fill="white">♪</text>
  </svg>`;
}
function docSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 1h7l3 3v11H3z" fill="white" stroke="#ccc" stroke-width="0.5"/>
    <path d="M10 1v3h3" fill="none" stroke="#ccc" stroke-width="0.5"/>
    <line x1="5" y1="6"  x2="11" y2="6"  stroke="#aaa" stroke-width="1"/>
    <line x1="5" y1="8"  x2="11" y2="8"  stroke="#aaa" stroke-width="1"/>
    <line x1="5" y1="10" x2="9"  y2="10" stroke="#aaa" stroke-width="1"/>
  </svg>`;
}
function archiveSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 1h7l3 3v11H3z" fill="#e8e8e8" stroke="#ccc" stroke-width="0.5"/>
    <path d="M10 1v3h3" fill="none" stroke="#ccc" stroke-width="0.5"/>
    <line x1="7" y1="1" x2="7" y2="14" stroke="#bbb" stroke-width="2" stroke-dasharray="2,1"/>
  </svg>`;
}
function codeSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 1h7l3 3v11H3z" fill="#fff" stroke="#ccc" stroke-width="0.5"/>
    <path d="M10 1v3h3" fill="none" stroke="#ccc" stroke-width="0.5"/>
    <text x="8" y="12" font-size="7" text-anchor="middle" fill="#1070cf" font-family="monospace">&lt;/&gt;</text>
  </svg>`;
}
function appSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="1" width="14" height="14" rx="3" fill="#1070cf"/>
    <circle cx="8" cy="8" r="3" fill="white" opacity="0.9"/>
  </svg>`;
}
function fileSVG() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 1h7l3 3v11H3z" fill="white" stroke="#ccc" stroke-width="0.5"/>
    <path d="M10 1v3h3" fill="none" stroke="#ccc" stroke-width="0.5"/>
  </svg>`;
}

function getIconSVG(node) {
  if (node.type === 'folder')  return folderSVG();
  if (node.type === 'image')   return imageSVG();
  if (node.type === 'video')   return videoSVG();
  if (node.type === 'audio')   return audioSVG();
  if (node.type === 'doc')     return docSVG();
  if (node.type === 'archive') return archiveSVG();
  if (node.type === 'code')    return codeSVG();
  if (node.type === 'app')     return appSVG();
  return fileSVG();
}

/* ── Big preview icons (128 px) ──────────────────────────────── */

function bigFolderSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="fg2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="rgba(255,255,255,0.3)"/>
      <stop offset="1" stop-color="rgba(0,0,0,0.1)"/>
    </linearGradient></defs>
    <rect x="2"  y="26" width="124" height="92" rx="10" fill="#f5a623"/>
    <rect x="2"  y="26" width="124" height="92" rx="10" fill="url(#fg2)"/>
    <rect x="2"  y="18" width="46"  height="18" rx="7"  fill="#e59016"/>
  </svg>`;
}
function bigImageSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <rect x="6"  y="10" width="116" height="108" rx="6" fill="#fff" stroke="#d0d0d0"/>
    <polygon points="6,90 38,54 66,82 90,58 122,90 122,118 6,118" fill="#4cd964" opacity="0.55"/>
    <circle cx="42" cy="38" r="14" fill="#f5a623" opacity="0.85"/>
  </svg>`;
}
function bigDocSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 4h68l30 28v92H14z" fill="white" stroke="#ccc" stroke-width="1.5"/>
    <path d="M82 4v28h30" fill="none" stroke="#ccc" stroke-width="1.5"/>
    <line x1="28" y1="48" x2="100" y2="48" stroke="#1070cf" stroke-width="4" stroke-linecap="round"/>
    <line x1="28" y1="62" x2="100" y2="62" stroke="#ddd" stroke-width="3" stroke-linecap="round"/>
    <line x1="28" y1="76" x2="100" y2="76" stroke="#ddd" stroke-width="3" stroke-linecap="round"/>
    <line x1="28" y1="90" x2="72"  y2="90" stroke="#ddd" stroke-width="3" stroke-linecap="round"/>
  </svg>`;
}
function bigArchiveSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 4h68l30 28v92H14z" fill="#f0f0f0" stroke="#ccc" stroke-width="1.5"/>
    <path d="M82 4v28h30" fill="none" stroke="#ccc" stroke-width="1.5"/>
    <line x1="56" y1="4" x2="56" y2="124" stroke="#bbb" stroke-width="8" stroke-dasharray="10,6"/>
  </svg>`;
}
function bigVideoSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="16" width="120" height="96" rx="8" fill="#5e5ce6"/>
    <polygon points="46,38 90,64 46,90" fill="white"/>
  </svg>`;
}
function bigFileSVG() {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 4h68l30 28v92H14z" fill="white" stroke="#ccc" stroke-width="1.5"/>
    <path d="M82 4v28h30" fill="none" stroke="#ccc" stroke-width="1.5"/>
  </svg>`;
}

function getBigIcon(node) {
  if (!node) return '';
  if (node.type === 'folder')  return bigFolderSVG();
  if (node.type === 'image')   return bigImageSVG();
  if (node.type === 'video')   return bigVideoSVG();
  if (node.type === 'doc')     return bigDocSVG();
  if (node.type === 'archive') return bigArchiveSVG();
  return bigFileSVG();
}

/* ── Sidebar icons ───────────────────────────────────────────── */

function sidebarIcon(color, symbol) {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <circle cx="8" cy="8" r="7.5" fill="${color}"/>
    <text x="8" y="12" font-size="9" text-anchor="middle" fill="white" font-family="system-ui">${symbol}</text>
  </svg>`;
}
function sidebarFolderIcon(color) {
  return `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M1 5.5A1.5 1.5 0 012.5 4h4l1 1.5H13.5A1.5 1.5 0 0115 7v5.5A1.5 1.5 0 0113.5 14h-11A1.5 1.5 0 011 12.5z" fill="${color}"/>
    <path d="M1 5.5A1.5 1.5 0 012.5 4h3.5l1 1.5H2.5A1.5 1.5 0 001 7z" fill="${color}" opacity="0.6"/>
  </svg>`;
}
