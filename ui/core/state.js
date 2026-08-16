/* ═══════════════════════════════════════════════════════════════════════════
   State
   ═══════════════════════════════════════════════════════════════════════════ */
const root    = document.documentElement;
const finder  = document.getElementById("finder");
const rail    = document.getElementById("rail");
const stage   = document.getElementById("stage");
const strip   = document.getElementById("strip");
const trail   = document.getElementById("trail");
const welcome = document.getElementById("welcome");

let path = [];                                           // node chain, [0] = root
let sel  = [];                                           // per-column selected name
let focusCol = 0;
let cursor = {};                                         // col index -> row index
let widths = [];                                         // natural width per column
let folded = 0;                                          // columns currently folded
let pvToken = 0;                                         // guards async preview fills
const state = { dotfiles: false };

const GUTTER = () => parseInt(getComputedStyle(root).getPropertyValue("--gutter"));
const SPINE  = () => parseInt(getComputedStyle(root).getPropertyValue("--spine-w"));

const visibleKids = node =>
  (node.kids || []).filter(k => state.dotfiles || !k.name.startsWith("."))
    .sort((a,b) => (!!b.dir - !!a.dir) || a.name.localeCompare(b.name, undefined, {numeric:true}));

const fmtSize = b =>
  b < 1024 ? `${b} B`
  : b < 1024 ** 2 ? `${(b / 1024).toFixed(b < 10240 ? 1 : 0)} KB`
  : b < 1024 ** 3 ? `${(b / 1024 ** 2).toFixed(1)} MB`
  : `${(b / 1024 ** 3).toFixed(2)} GB`;

const fmtDate = ms => new Date(ms).toLocaleString(undefined,
  { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

const splitName = name => {
  const i = name.lastIndexOf(".");
  return (i > 0) ? [name.slice(0,i), name.slice(i)] : [name, ""];
};

const previewNode = () => {
  const last = path[path.length - 1], s = sel[path.length - 1];
  const n = s && (last.kids || []).find(k => k.name === s);
  return (n && !n.dir) ? n : null;
};

/* target reading width for the preview — the thing scrolling tries to protect */
const previewTarget = () => previewNode()
  ? Math.min(760, Math.max(420, Math.round(stage.clientWidth * 0.45)))
  : 300;

function measure(node) {
  /* content-driven width, clamped — no manual resizing, no wasted space */
  const c = (measure._c ||= document.createElement("canvas").getContext("2d"));
  const cs = getComputedStyle(root);
  c.font = `${cs.getPropertyValue("--fs-row").trim()} ${cs.getPropertyValue("--font")}`;
  let w = 0;
  for (const k of visibleKids(node)) w = Math.max(w, c.measureText(k.name).width);
  c.font = `600 ${cs.getPropertyValue("--fs-head").trim()} ${cs.getPropertyValue("--font")}`;
  w = Math.max(w, c.measureText(node.name).width + 34);
  /* 380 not 268: a vault of 80-character page titles needs the room, and the
     dial makes wide columns affordable — fold what you are not reading. */
  return Math.min(380, Math.max(148, Math.ceil(w) + 58));
}
