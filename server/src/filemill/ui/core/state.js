/* ═══════════════════════════════════════════════════════════════════════════
   State
   ═══════════════════════════════════════════════════════════════════════════ */
const root = document.documentElement;
const finder = document.getElementById("finder");
const rail = document.getElementById("rail");
const stage = document.getElementById("stage");
const strip = document.getElementById("strip");
const trail = document.getElementById("trail");
const welcome = document.getElementById("welcome");

let path = []; // node chain, [0] = root
let sel = []; // per-column selected name
let focusCol = 0;
let widths = []; // natural width per column
let folded = 0; // columns currently folded
let pvToken = 0; // guards async preview fills
let pvFullscreen = false;
const state = {
  dotfiles: root.dataset.hidden === "show",
  sort: { key: "name", desc: false },
};

const GUTTER = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--gutter"));
const SPINE = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--spine-w"));

/* what a column's content-driven width is allowed to be. COL_MAX is 380 not
   268: a vault of 80-character page titles needs the room, and the dial makes
   wide columns affordable — fold what you are not reading. render() narrows
   the ceiling again against the stage, which on a phone is the smaller of
   the two. */
const COL_MIN = 148, COL_MAX = 380;

/* One filtered copy per call, ordered by core/sort.js. Every column build, every
   width measurement and every path walk comes through here, which is what keeps
   the rows and a restored chain agreeing on what row 4 is. */
const visibleKids = (node) =>
  ((kids) => node.ordered ? kids : sortKids(kids))(
    (node.kids || []).filter((k) => state.dotfiles || !k.name.startsWith(".")),
  );

const rowIndex = (node, name) =>
  visibleKids(node).findIndex((k) => k.name === name);

const fmtSize = (b) =>
  b < 1024
    ? `${b} B`
    : b < 1024 ** 2
    ? `${(b / 1024).toFixed(b < 10240 ? 1 : 0)} KB`
    : b < 1024 ** 3
    ? `${(b / 1024 ** 2).toFixed(1)} MB`
    : `${(b / 1024 ** 3).toFixed(2)} GB`;

const fmtDate = (ms) =>
  new Date(ms).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

const splitName = (name) => {
  const i = name.lastIndexOf(".");
  return (i > 0) ? [name.slice(0, i), name.slice(i)] : [name, ""];
};

const previewNode = () => {
  const last = path[path.length - 1], s = sel[path.length - 1];
  const n = s && (last.kids || []).find((k) => k.name === s);
  return (n && !n.dir) ? n : null;
};

const selectedNode = () => {
  const last = path[path.length - 1], s = sel[path.length - 1];
  return s && (last.kids || []).find((k) => k.name === s) || null;
};

/* 88 columns of .pv-text plus its and .pv-body's horizontal padding (30 + 52),
   measured from the real monospace font so it agrees with the CSS min-width */
const codeMin = () =>
  codeMin._w ||= (() => {
    const c = document.createElement("canvas").getContext("2d");
    const cs = getComputedStyle(root);
    c.font = `11.5px ${cs.getPropertyValue("--mono")}`;
    return Math.ceil(c.measureText("0").width * 88) + 82;
  })();

/* target reading width for the preview — the thing scrolling tries to protect.
   Never wider than the stage itself: a phone cannot show 88 columns, and a
   pane that runs past the right edge is clipped, not scrollable — so there
   the pane fits and .pv-body pans over the code instead. */
const previewTarget = () =>
  previewNode()
    ? Math.min(
      760,
      stage.clientWidth,
      Math.max(codeMin(), Math.round(stage.clientWidth * 0.45)),
    )
    : 300;

function measure(node) {
  /* content-driven width, clamped — no manual resizing, no wasted space */
  const c = (measure._c ||= document.createElement("canvas").getContext("2d"));
  const cs = getComputedStyle(root);
  c.font = `${cs.getPropertyValue("--fs-row").trim()} ${
    cs.getPropertyValue("--font")
  }`;
  let w = 0;
  for (const k of visibleKids(node)) {
    w = Math.max(w, c.measureText(k.name).width);
  }
  c.font = `600 ${cs.getPropertyValue("--fs-head").trim()} ${
    cs.getPropertyValue("--font")
  }`;
  w = Math.max(w, c.measureText(node.name).width + 34);
  return Math.min(COL_MAX, Math.max(COL_MIN, Math.ceil(w) + 58));
}
