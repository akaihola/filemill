/* ════════════════════════════════════════════════════════════════
   Mock File System (shown before user picks a real folder)
   ════════════════════════════════════════════════════════════════ */
const MOCK_FS = {
  name: '/', type: 'folder',
  children: [
    { name: 'Applications', type: 'folder', children: [
      { name: 'Automator.app', type: 'app' }, { name: 'Calendar.app', type: 'app' },
      { name: 'Finder.app', type: 'app' },    { name: 'Mail.app', type: 'app' },
      { name: 'Safari.app', type: 'app' },    { name: 'System Preferences.app', type: 'app' },
    ]},
    { name: 'Users', type: 'folder', children: [
      { name: 'casey', type: 'folder', children: [
        { name: 'Desktop',   type: 'folder', children: [
          { name: 'Screenshot 2024-03-01.png', type: 'image' },
          { name: 'notes.txt', type: 'doc' },
        ]},
        { name: 'Documents', type: 'folder', children: [
          { name: 'Budget 2024.numbers', type: 'doc' },
          { name: 'Resume.pages', type: 'doc' },
          { name: 'Tax Returns', type: 'folder', children: [] },
        ]},
        { name: 'Downloads', type: 'folder', children: [
          { name: 'macOS Ventura.dmg', type: 'archive' },
          { name: 'Zoom.pkg', type: 'archive' },
        ]},
        { name: 'Movies',    type: 'folder', children: [{ name: 'Vacation 2023.mov', type: 'video' }] },
        { name: 'Music',     type: 'folder', children: [{ name: 'iTunes', type: 'folder', children: [] }] },
        { name: 'Pictures',  type: 'folder', children: [
          { name: 'Photo Library.photoslibrary', type: 'folder', children: [] },
        ]},
        { name: 'OWC', type: 'folder', children: [
          { name: 'Shared Folder', type: 'folder', children: [
            { name: 'High Sierra Slow',      type: 'doc' },
            { name: 'High Sierra Slow.zip',  type: 'archive' },
            { name: 'How to Automate Tasks', type: 'doc' },
            { name: 'How to A…Tasks.zip',   type: 'archive' },
            { name: 'Images',               type: 'folder', children: [] },
            { name: 'Install macOS High Sierra', type: 'file' },
            { name: 'Invoice',              type: 'folder', children: [] },
            { name: 'Just one upgrade',     type: 'doc' },
            { name: 'Just one…grade.zip',   type: 'archive' },
            { name: 'Kernel Panic',         type: 'folder', children: [] },
            { name: 'Kernel Panic.zip',     type: 'archive' },
            { name: 'Mac OS Utilities',     type: 'folder', children: [] },
            { name: 'Mac OS Utilities.zip', type: 'archive' },
            { name: 'Mac Sleep Issues',     type: 'folder', children: [] },
            { name: 'Mac Sleep…s 1.docx',  type: 'doc' },
            { name: 'Mac Sleep Issues.zip', type: 'archive' },
          ]},
          { name: 'Images', type: 'folder', children: [
            { name: 'DJI Drone Lab',             type: 'folder', children: [] },
            { name: 'Download macOS',            type: 'file' },
            { name: 'Earth Day Map',             type: 'folder', children: [] },
            { name: 'External Enclosure Types',  type: 'folder', children: [] },
            { name: 'FileVault',                 type: 'folder', children: [] },
            { name: 'Finder Views Column Cover', type: 'folder', children: [
              { name: 'ColumnView.tiff',        type: 'image',   size: '18.2 MB', dims: '3360 × 2176', created: 'Today, 11:16 AM', modified: 'Today, 11:16 AM', lastOpened: 'Today, 11:36 AM' },
              { name: 'ColumnView640.jpg',      type: 'image',   size: '312 KB',  dims: '640 × 440' },
              { name: 'ColumnView1280.jpg',     type: 'image',   size: '756 KB',  dims: '1280 × 880' },
              { name: 'ColumnViewOptions.tiff', type: 'image',   size: '4.1 MB',  dims: '1600 × 1200' },
              { name: 'ColumnViews440.jpg',     type: 'image',   size: '198 KB',  dims: '440 × 302' },
              { name: 'ColumnViews880.jpg',     type: 'image',   size: '421 KB',  dims: '880 × 604' },
              { name: 'CoverFlow.tiff',         type: 'image',   size: '16.8 MB', dims: '3360 × 2176' },
              { name: 'CoverFlow640.jpg',       type: 'image',   size: '298 KB',  dims: '640 × 440' },
              { name: 'CoverFlow1280.jpg',      type: 'image',   size: '712 KB',  dims: '1280 × 880' },
              { name: 'CoverFlowOptions.tiff',  type: 'image',   size: '3.9 MB',  dims: '1600 × 1200' },
              { name: 'CoverFlowNs440.jpg',     type: 'image',   size: '176 KB',  dims: '440 × 302' },
              { name: 'CoverFlowNs880.jpg',     type: 'image',   size: '388 KB',  dims: '880 × 604' },
              { name: 'CoverFlowTip.tiff',      type: 'image',   size: '2.2 MB',  dims: '1024 × 768' },
              { name: 'CoverFlowip640.jpg',     type: 'image',   size: '145 KB',  dims: '640 × 480' },
              { name: 'CoverFlowp1280.jpg',     type: 'image',   size: '390 KB',  dims: '1280 × 960' },
            ]},
            { name: 'Finder Views Icon List',  type: 'folder', children: [] },
            { name: 'Five Mac Ties Images',    type: 'folder', children: [] },
            { name: 'Forgotten ips Images',    type: 'folder', children: [] },
            { name: 'Get Read…Ac OS Beta',     type: 'folder', children: [] },
            { name: 'High Sierra Screenshots', type: 'folder', children: [] },
            { name: 'High Sierra Slow',        type: 'doc' },
            { name: 'How to Automate Tasks',   type: 'doc' },
            { name: 'Kernel Panic Images',     type: 'folder', children: [] },
            { name: 'Mac OS Utilities',        type: 'folder', children: [] },
            { name: "Mac won't power up",      type: 'doc' },
            { name: 'Mac Sleep Issues',        type: 'doc' },
          ]},
        ]},
      ]},
      { name: 'tnelson', type: 'folder', children: [
        { name: 'Desktop',   type: 'folder', children: [] },
        { name: 'Documents', type: 'folder', children: [] },
        { name: 'Downloads', type: 'folder', children: [] },
      ]},
      { name: 'Shared', type: 'folder', children: [] },
    ]},
  ]
};

/* ════════════════════════════════════════════════════════════════
   Sidebar Data
   ════════════════════════════════════════════════════════════════ */
// Extra FSA-picked roots are prepended at runtime
const SIDEBAR_ITEMS = [
  { label: 'iCloud Drive', path: ['iCloud Drive'], icon: sidebarIcon('#4a9eff','☁'),  type:'builtin' },
  { label: 'Dropbox',      path: ['Dropbox'],      icon: sidebarIcon('#1070cf','⬡'),  type:'builtin' },
  { label: 'AirDrop',      path: ['AirDrop'],
    icon: `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
      <defs><radialGradient id="airdrop2"><stop offset="0%" stop-color="#4af"/><stop offset="100%" stop-color="#07c"/></radialGradient></defs>
      <circle cx="8" cy="8" r="7.5" fill="url(#airdrop2)"/>
      <text x="8" y="12" font-size="9" text-anchor="middle" fill="white">⊕</text></svg>`,
    type:'builtin' },
  { label: 'Desktop',      path: ['Users','casey','Desktop'],   icon: sidebarIcon('#8b5cf6','🖥'), type:'mock' },
  { label: 'OWC',          path: ['Users','casey','OWC'],       icon: sidebarIcon('#ff7f00','O'),  type:'mock', selected: true },
  { label: 'tnelson',      path: ['Users','tnelson'],           icon: sidebarIcon('#5a5a5a','t'),  type:'mock' },
  { label: 'Documents',    path: ['Users','casey','Documents'], icon: sidebarFolderIcon('#1070cf'), type:'mock' },
  { label: 'Applications', path: ['Applications'],              icon: sidebarFolderIcon('#888'),    type:'mock' },
  { label: 'Movies',       path: ['Users','casey','Movies'],    icon: sidebarFolderIcon('#5e5ce6'), type:'mock' },
  { label: 'Pictures',     path: ['Users','casey','Pictures'],  icon: sidebarFolderIcon('#ff4d94'), type:'mock' },
  { label: 'Music',        path: ['Users','casey','Music'],     icon: sidebarFolderIcon('#ff3b30'), type:'mock' },
  { label: 'Downloads',    path: ['Users','casey','Downloads'], icon: sidebarFolderIcon('#4cd964'), type:'mock' },
  { label: 'All My Files', path: ['All My Files'],              icon: sidebarIcon('#888','◫'),      type:'builtin' },
];

const SIDEBAR_TAGS = [
  { label: 'Today',     color: '#ff3b30' },
  { label: 'Yesterday', color: '#ff9500' },
  { label: 'This Week', color: '#4cd964' },
];
