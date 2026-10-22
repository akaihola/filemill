import assert from "node:assert/strict";
import {
  path,
  previewNode,
  sel,
  selectedNode,
  setState,
  state,
  visibleKids,
} from "./state.js";
import { autoPreview, selectNode } from "./selection.js";
import { sortKids } from "./sort.js";
import {
  automaticFold,
  columnMetrics,
  columnSpan,
  columnWidth,
  dialStops,
  dialWindow,
  fitCount,
  focusPan,
  foldingAt,
  foldPosition,
  tailShift,
  wideCounts,
  widenedSizes,
} from "./folding.js";
import { keyAction, nextRow, pageSelection } from "./keyboard.js";
import { currentPath, locationState, walkPath } from "./deeplink.js";
import { toggleTask } from "./markdown-tasks.js";
import { safeURL } from "./safe-url.js";

assert.equal(typeof globalThis.document, "undefined");
const file = (name) => ({ name, dir: false });
const readme = file("README.md");
const folder = { name: "sub", dir: true, kids: [readme, file(".hidden")] };
const tree = { name: "root", dir: true, kids: [folder, file("z")] };
setState({ path: [tree], sel: [], focusCol: 0 });
assert.equal(visibleKids(folder).length, 1);
selectNode(0, folder);
path.push(folder);
autoPreview(folder);
assert.equal(selectedNode(), readme);
assert.equal(previewNode(), readme);
assert.deepEqual(currentPath(), ["sub", "README.md"]);
assert.equal(await walkPath(["sub", ".hidden"], async () => {}), true);
assert.equal(state.dotfiles, true);
assert.equal(sel[1], ".hidden");
assert.equal(await walkPath(["missing"], async () => {}), false);
assert.deepEqual(currentPath(), []);
assert.equal(locationState("render", null).replace, false);
assert.equal(locationState("render", "root").replace, true);
/* ADR 0050: a click that opens another folder pushes; choosing a file inside
   the open folder rewrites; ↑/↓, Home/End and paging always rewrite. */
setState({ path: [tree, folder], sel: ["sub"], focusCol: 0 });
assert.equal(locationState("render", "root").key, "root/sub");
assert.equal(locationState("render", "root").replace, false);
assert.equal(locationState("render", "root/sub").replace, true);
state.stepping = true;
assert.equal(locationState("render", "root").replace, true);
assert.equal(locationState("render", null).replace, true);
state.stepping = false;
assert.equal(locationState("render", "root").replace, false);
setState({ path: [tree], sel: [], focusCol: 0 });
const many = Array.from({ length: 3000 }, (_, i) => file(`file${2999 - i}`));
assert.equal(sortKids(many)[0].name, "file0");
assert.equal(columnSpan([200, 300], 1, 10, 20), 350);
assert.deepEqual(foldingAt(0, 100, 0), { raw: 0, folded: 0, t: 0 });
assert.equal(foldingAt(49, 100, 2).folded, 1);
assert.equal(foldingAt(99, 100, 2).folded, 2);
assert.equal(foldPosition(174, 528 * 0.99 / 3), 1);
assert.deepEqual(foldingAt(175, 529, 3), { raw: 1, folded: 1, t: 0 });
assert.equal(foldPosition(150, 200), 0.75);
assert.equal(columnWidth(200, 0, 0, 0.5, 20), 110);
assert.equal(focusPan(1, 0, 10, 210, 100, 10), 0);
assert.ok(Math.abs(tailShift(1, 0, 2, 20, 10) - 60) < 1e-9);
assert.equal(automaticFold([200, 300], 10, 20, 200, 100, 0, 0, false), 0);
assert.equal(automaticFold([200, 300], 10, 20, 200, 100, 0, 0, true), 2);
/* [81] Dial stops. A fling lands on the next stop in its direction; the
   stops left of natural widen the leftmost columns to fill the finder. */
const near = (a, b) => assert.ok(Math.abs(a - b) <= 1e-9, `${a} ≠ ${b}`);
assert.equal(fitCount(240, 1440, 480, 10), 3); /* "almost four" */
assert.equal(fitCount(195, 390, 130, 10), 1); /* portrait phone */
assert.deepEqual(wideCounts(4, 3), [3, 2]); /* desktop stops at two */
assert.deepEqual(wideCounts(2, 3), [2]);
assert.deepEqual(wideCounts(1, 3), []); /* a root alone cannot widen */
assert.deepEqual(wideCounts(3, 1), [1]); /* a phone reaches the root */
assert.deepEqual(wideCounts(1, 1), [1]);
const four = [240, 240, 240, 240];
const unit = 0.99 * 1000 / 4;
const stops = dialStops(four, [3, 2], 10, 34);
assert.deepEqual(stops, [-2 * unit, -unit, 0, 3 * unit, 4 * unit, 1000]);
assert.deepEqual(dialStops([240], [], 10, 34), [0, 0.99 * 250, 250]);
assert.deepEqual(dialWindow(stops, 0), { lower: -unit, upper: 3 * unit });
assert.deepEqual(dialWindow(stops, 3 * unit), { lower: 0, upper: 4 * unit });
assert.deepEqual(dialWindow(stops, 1000), { lower: 4 * unit, upper: 1000 });
assert.deepEqual(dialWindow(stops, -2 * unit), {
  lower: -2 * unit,
  upper: -unit,
});
assert.deepEqual(dialWindow(stops, 300), { lower: 0, upper: 3 * unit });
assert.deepEqual(dialWindow(stops, 3 * unit + 0.4), {
  lower: 0,
  upper: 4 * unit,
});
assert.deepEqual(widenedSizes(four, 0, unit, [3, 2], 1440, 10), four);
let wide = widenedSizes(four, -unit, unit, [3, 2], 1440, 10);
near(wide[0], 1400 / 3);
near(wide[2], 1400 / 3);
assert.equal(wide[3], 240);
wide = widenedSizes(four, -2 * unit, unit, [3, 2], 1440, 10);
assert.deepEqual(wide, [705, 705, 240, 240]);
wide = widenedSizes(four, -unit / 2, unit, [3, 2], 1440, 10);
near(wide[0], (240 + 1400 / 3) / 2);
assert.equal(wide[3], 240);
wide = widenedSizes(four, -3 * unit, unit, [3, 2], 1440, 10); /* past the end */
assert.deepEqual(wide, [705, 705, 240, 240]);
assert.equal(keyAction({ key: "ArrowDown" }, { editable: true }), null);
assert.equal(keyAction({ key: "ArrowDown" }, { welcome: true }), null);
assert.equal(keyAction({ key: "c", ctrlKey: true }, {}), "copy");
assert.equal(
  keyAction({ key: "c", ctrlKey: true }, { textSelected: true }),
  null,
);
assert.equal(keyAction({ key: "F5", ctrlKey: true }, {}), null);
assert.equal(keyAction({ key: "x" }, {}), "type");
assert.equal(
  keyAction({ key: "ArrowUp" }, { preview: true }),
  "preview-scroll",
);
assert.equal(
  keyAction({ key: "ArrowRight" }, { preview: true }),
  "preview-right",
);
assert.equal(
  keyAction({ key: "ArrowLeft" }, { preview: true }),
  "preview-back",
);
for (const key of ["ArrowLeft", "Escape"]) {
  assert.equal(
    keyAction({ key }, { preview: true, fullscreen: true }),
    "preview-exit-fullscreen",
  );
  assert.equal(
    keyAction({ key }, { preview: true, fullscreen: true, editable: true }),
    null,
  );
}
assert.equal(keyAction({ key: "Escape" }, { preview: true }), null);
assert.equal(nextRow(0, false, 1, 3), 0);
assert.equal(nextRow(2, true, 1, 3), 2);
assert.deepEqual(
  pageSelection([2, 3, 4].map((index) => ({ index, height: 20 })), 4, 1, 100),
  {
    index: 4,
    scroll: 100,
  },
);

// Imports and calls must work without a browser, including indirect dependencies.
const { readdirSync, readFileSync } = await import("node:fs");
for (const name of readdirSync(new URL(".", import.meta.url))) {
  if (!name.endsWith(".js")) continue;
  const url = new URL(name, import.meta.url);
  const source = readFileSync(url, "utf8");
  assert.doesNotMatch(
    source,
    /\b(document|window|Element|navigator|localStorage|getComputedStyle)\b/,
    name,
  );
  for (const match of source.matchAll(/from\s+"([^"]+)"/g)) {
    assert.match(
      match[1],
      /^\.\/[^/]+\.js$/,
      `${name}: model imports only model modules`,
    );
  }
  await import(url.href);
}
const { rowIndex, setSortKids } = await import("./state.js");
const { taSearch } = await import("./typeahead.js");
setSortKids(sortKids);
state.dotfiles = false;
state.sort = { key: "name", desc: false };
const ordered = { kids: [file("z"), file("a")], ordered: true };
assert.deepEqual(visibleKids(ordered).map((n) => n.name), ["z", "a"]);
assert.equal(rowIndex(ordered, "a"), 1);
state.sort.desc = true;
assert.deepEqual(visibleKids(ordered).map((n) => n.name), ["a", "z"]);
assert.deepEqual(
  visibleKids({ kids: [folder, ...ordered.kids], ordered: true }).map((n) =>
    n.name
  ),
  [folder.name, "a", "z"],
);
state.sort.desc = false;
const metadata = [file("unknown"), { ...file("large"), meta: { size: 20 } }, {
  ...file("small"),
  meta: { size: 1 },
}, folder];
for (const desc of [false, true]) {
  state.sort = { key: "size", desc };
  const sorted = sortKids([...metadata]);
  assert.equal(sorted[0], folder);
  assert.equal(sorted.at(-1).name, "unknown");
  assert.equal(sorted[1].name, desc ? "large" : "small");
}
state.sort = { key: "name", desc: false };
setState({ path: [tree, folder], sel: ["sub", "README.md"], focusCol: 1 });
selectNode(0, tree.kids[1]);
assert.deepEqual(path, [tree]);
assert.deepEqual(sel, ["z"]);
assert.equal((await import("./state.js")).focusCol, 0);
await walkPath(["sub", "README.md"], async () => {}, 50);
assert.equal((await import("./state.js")).focusCol, 1);
assert.equal(locationState("highlight", null).location.view, "highlight");
await assert.rejects(
  walkPath(["sub"], async () => {
    throw new Error("read failed");
  }, 50),
  /read failed/,
);
assert.deepEqual(path, [tree]);
assert.equal((await import("./state.js")).focusCol, 0);
/* A virtual wrapper may decline a row while reading it: the row becomes a
   leaf and stays the selection in its column instead of opening as one. */
const declined = { name: "bad", dir: true, kids: null };
tree.kids.push(declined);
await walkPath(["bad"], async (n) => {
  if (n !== declined) return;
  n.dir = false;
  n.kids = undefined;
});
assert.deepEqual(path, [tree]);
assert.equal(selectedNode(), declined);
tree.kids.pop();
/* A remount replaces the root while a walk waits for a read. Releasing that
   read must leave the new root's path, selection and focus alone and read
   nothing further down the old chain. */
const inner = { name: "inner", dir: true, kids: null };
const pending = { name: "pending", dir: true, kids: null };
const replacement = { name: "replacement", dir: true, kids: [] };
const reads = [];
let reached, release;
const waiting = new Promise((resolve) => (reached = resolve));
setState({ path: [tree], sel: [], focusCol: 0 });
tree.kids.push(pending);
const walking = walkPath(["pending", "inner"], (n) => {
  reads.push(n.name);
  if (n !== pending) return Promise.resolve();
  reached();
  return new Promise((resolve) => {
    release = () => {
      pending.kids = [inner];
      resolve();
    };
  });
}, 1);
await waiting;
setState({ path: [replacement], sel: [], focusCol: 0 });
release();
assert.equal(await walking, false);
assert.deepEqual(path, [replacement]);
assert.deepEqual(sel, []);
assert.equal((await import("./state.js")).focusCol, 0);
assert.deepEqual(reads, ["root", "pending"]);
tree.kids.pop();
setState({ path: [], sel: [] });
assert.equal(await walkPath([], async () => {}), false);
assert.equal(previewNode(), null);
assert.equal(selectedNode(), null);
setState({
  path: [{ name: "value", json: true, dir: true, value: 0 }],
  sel: [],
});
assert.equal(previewNode(), path[0]);
for (const value of [false, 0, null, "", "first\nsecond"]) {
  const scalar = { name: "scalar", dir: false, json: true, value };
  const object = { name: "object", dir: true, json: true, value: {} };
  const parent = {
    name: "data.json",
    dir: true,
    json: true,
    value: { scalar: value, object: {} },
    kids: [scalar, object],
  };
  setState({ path: [tree, parent], sel: ["data.json", "scalar"] });
  assert.equal(previewNode(), scalar);
  assert.deepEqual(locationState("highlight", "root/data.json"), {
    key: "root/data.json",
    replace: true,
    location: {
      root: "root",
      path: ["data.json", "scalar"],
      view: "highlight",
    },
  });
  for (const selection of [undefined, "object"]) {
    setState({ sel: ["data.json", selection] });
    assert.equal(previewNode(), parent);
    assert.equal(locationState("highlight", null).location.view, "highlight");
  }
}
const emptyKey = { name: "", dir: false, json: true, value: "empty key" };
setState({
  path: [{ json: true, value: { "": "empty key" }, kids: [emptyKey] }],
  sel: [""],
});
assert.equal(previewNode(), emptyKey);
assert.equal(taSearch(["a-note", "note", "n_o_t_e"], "note"), 1);
assert.equal(taSearch(["a-note", "n_o_t_e"], "note"), 0);
assert.equal(taSearch(["n_o_t_e"], "note"), 0);
assert.equal(taSearch(["other"], "note"), -1);
for (
  const key of [
    "ArrowUp",
    "ArrowDown",
    "Home",
    "End",
    "PageUp",
    "PageDown",
    "ArrowLeft",
    "ArrowRight",
    "Enter",
    "Escape",
  ]
) {
  assert.equal(keyAction({ key }, { typeahead: true }), key);
}
assert.equal(keyAction({ key: "Backspace" }, { typeahead: true }), "type");
assert.equal(keyAction({ key: "Backspace" }, {}), null);
assert.equal(keyAction({ key: "x", altKey: true }, {}), null);
/* Alt+←/→ and ⌘←/→ are the browser's Back and Forward. */
for (const key of ["ArrowLeft", "ArrowRight", "ArrowUp", "Enter"]) {
  assert.equal(keyAction({ key, altKey: true }, {}), null);
  assert.equal(keyAction({ key, metaKey: true }, {}), null);
  assert.equal(keyAction({ key, ctrlKey: true }, {}), null);
  assert.equal(keyAction({ key, altKey: true }, { preview: true }), null);
  assert.equal(keyAction({ key, metaKey: true }, { preview: true }), null);
}
assert.equal(keyAction({ key: "c", ctrlKey: true }, {}), "copy");
assert.equal(keyAction({ key: "c", metaKey: true }, {}), "copy");
assert.deepEqual(
  pageSelection([2, 3, 4].map((index) => ({ index, height: 20 })), 3, 1, 100),
  {
    index: 4,
    scroll: 0,
  },
);
assert.deepEqual(
  pageSelection([2, 3, 4].map((index) => ({ index, height: 20 })), 2, -1, 100),
  {
    index: 2,
    scroll: -100,
  },
);
assert.deepEqual(pageSelection([], 0, 1, 100), {
  index: undefined,
  scroll: 0,
});
assert.equal(columnSpan([], 0, 10, 20), 10);
for (const count of [1, 2, 7]) {
  for (let k = 0; k <= count; k++) {
    assert.equal(
      foldingAt(Math.round(k * 0.99 / count * 931), 931, count).folded,
      k,
    );
  }
  assert.equal(foldingAt(931, 931, count).folded, count);
}
assert.equal(columnWidth(200, 0, 1, 0, 20), 20);
assert.equal(columnWidth(200, 2, 1, 0.5, 20), 200);
assert.equal(focusPan(2, 1, 210, 410, 300, 10), 110);
assert.equal(tailShift(0.99, 7, 2, 20, 10), 7);

assert.deepEqual(columnMetrics([200, 300, 100], 1, 0.5, 2, 10, 20), {
  sizes: [20, 160, 100],
  focusLeft: 210,
  focusRight: 310,
});

// Three 240px columns, three gaps and two outside paddings leave exactly W/3.
for (const [viewport, expected] of [[1154, 1], [1155, 0], [1156, 0]]) {
  assert.equal(
    automaticFold([240, 240, 240], 10, 34, viewport / 3, viewport, 2, 0, false),
    expected,
  );
}
assert.equal(
  automaticFold([240, 240, 240, 240, 240], 10, 34, 480, 1440, 4, 0, false),
  2,
);
assert.equal(automaticFold([240, 240], 10, 34, 480, 1440, 1, 1, false), 1);
assert.equal(automaticFold([195, 195], 10, 34, 130, 390, 0, 0, false), 0);

const { jsonCollapse } = await import("./json-collapse.js");
const origin = {};
const target = ["a", "b", "foo", "c", "bar"];
const sibling = ["x", "y", "z", "c", "bar"];
jsonCollapse.record(origin, target, 3, false);
assert.equal(jsonCollapse.open(origin, sibling), false);
assert.equal(jsonCollapse.open(origin, ["x", "y", "c", "bar"]), true);
assert.equal(jsonCollapse.open(origin, ["x", "y", "z", "d", "bar"]), true);
jsonCollapse.record(origin, sibling, 4, true);
assert.equal(jsonCollapse.open(origin, sibling), true);
assert.equal(jsonCollapse.open(origin, target), false);
assert.equal(jsonCollapse.open({}, sibling), false);
jsonCollapse.record(origin, sibling, 4, false);
assert.equal(jsonCollapse.open(origin, sibling), false);
jsonCollapse.record(origin, ["rows", "0", "a.b", '/"*'], 2, false);
assert.equal(jsonCollapse.open(origin, ["rows", "1", "a.b", '/"*']), false);
assert.equal(jsonCollapse.open(origin, ["rows", "1", "a", "b", '/"*']), true);
jsonCollapse.record(origin, ["root"], 1, false);
assert.equal(jsonCollapse.open(origin, ["other"]), false);

// Unrelated fold rules must not turn a deep preview into all-suffix scans.
let pathReads = 0;
const deepPath = new Proxy(Array(1000).fill("node"), {
  get(target, key, receiver) {
    if (/^\d+$/.test(String(key))) pathReads++;
    return Reflect.get(target, key, receiver);
  },
});
assert.equal(jsonCollapse.open(origin, deepPath), true);
assert.ok(
  pathReads <= deepPath.length * 2,
  `deep path read ${pathReads} times`,
);

// Task checkboxes rewrite exactly one mark, and only on the line rendered.
const tasks = "# T\r\n\r\n- [ ] one\r\n- [x] two\r\n  * [X] nested\r\ntail";
assert.equal(
  toggleTask(tasks, 2, true, "- [ ] one"),
  "# T\r\n\r\n- [x] one\r\n- [x] two\r\n  * [X] nested\r\ntail",
);
assert.equal(
  toggleTask(tasks, 3, false, "- [x] two"),
  "# T\r\n\r\n- [ ] one\r\n- [ ] two\r\n  * [X] nested\r\ntail",
);
assert.equal(
  toggleTask(tasks, 4, false, "  * [X] nested"),
  "# T\r\n\r\n- [ ] one\r\n- [x] two\r\n  * [ ] nested\r\ntail",
);
for (
  const [line, checked, want] of [
    ["+ [ ] a", true, "+ [x] a"],
    ["1. [ ] a", true, "1. [x] a"],
    ["2) [x] a", false, "2) [ ] a"],
    ["> - [ ] a", true, "> - [x] a"],
    ["    - [x] a [ ] b", false, "    - [ ] a [ ] b"],
  ]
) assert.equal(toggleTask(line, 0, checked, line), want);
for (const line of [-1, 5, 1.5, NaN, 0, 1]) {
  assert.equal(
    toggleTask("# T\ntext - [ ] x\n", line, true, "text - [ ] x"),
    null,
  );
}
for (const line of ["- a [ ] b", "- [ ]", "- [x] done"]) {
  assert.equal(toggleTask(line, 0, true, line), null);
}
assert.equal(toggleTask("- [ ] open", 0, false, "- [ ] open"), null);
// A line that no longer reads as rendered is refused, even in the same state.
assert.equal(toggleTask("- [ ] zero\n- [ ] one", 0, true, "- [ ] one"), null);
assert.equal(toggleTask("- [ ] one", 0, true, undefined), null);

console.log("Model checks passed");

/* Documents browse by headings: the outline is the model's, DOM-free. */
const { outline } = await import("./headings.js");
const markdown = [
  "---",
  "title: front matter",
  "---",
  "intro",
  "# Guide",
  "text",
  "## Install",
  "```",
  "# not a heading",
  "```",
  "### Linux",
  "## Use ##",
  "## Install",
  "Setext",
  "======",
  "## *Tail* [link](x) `code`",
  "",
].join("\n");
const sections = outline(markdown, "md");
assert.deepEqual(sections.map((s) => s.name), ["Guide", "Setext"]);
const [guide, setext] = sections;
assert.deepEqual(guide.kids.map((s) => s.name), [
  "Install",
  "Use",
  "Install (2)",
]);
assert.deepEqual(guide.kids[0].kids.map((s) => s.name), ["Linux"]);
assert.deepEqual([guide.start, guide.end], [4, 13]);
assert.deepEqual([guide.kids[0].start, guide.kids[0].end], [6, 11]);
assert.deepEqual([guide.kids[0].kids[0].start, guide.kids[0].kids[0].end], [
  10,
  11,
]);
assert.deepEqual([guide.kids[2].start, guide.kids[2].end], [12, 13]);
assert.deepEqual([setext.start, setext.end], [13, 17]);
assert.deepEqual(setext.kids.map((s) => s.name), ["Tail link code"]);
assert.deepEqual(outline("no headings\n\n    # indented code\n", "md"), []);
assert.deepEqual(outline("", "markdown"), []);
const rst = [
  "=====",
  "Title",
  "=====",
  "",
  "Part A",
  "------",
  "text",
  "",
  "Sub",
  "~~~",
  "",
  "Part B",
  "------",
  "::",
  "",
  "    code",
  "    ====",
  "",
  "Part A",
  "------",
  "short",
  "--",
  "",
].join("\n");
const rstSections = outline(rst, "rst");
assert.deepEqual(rstSections.map((s) => s.name), ["Title"]);
assert.deepEqual(rstSections[0].kids.map((s) => s.name), [
  "Part A",
  "Part B",
  "Part A (2)",
]);
assert.deepEqual(rstSections[0].kids[0].kids.map((s) => s.name), ["Sub"]);
assert.deepEqual([rstSections[0].start, rstSections[0].end], [0, 23]);
assert.deepEqual([rstSections[0].kids[0].start, rstSections[0].kids[0].end], [
  4,
  11,
]);
assert.deepEqual([rstSections[0].kids[1].start, rstSections[0].kids[1].end], [
  11,
  18,
]);
assert.deepEqual(outline("plain\n\ntext\n", "rst"), []);
/* As browsed: a lone top title names the file, its subsections are the
   column; fewer than two sections in all is nothing to browse. */
const { sections: browse } = await import("./headings.js");
assert.deepEqual(browse(markdown, "md").map((s) => s.name), [
  "Guide",
  "Setext",
]);
assert.deepEqual(browse("# T\n\n## A\n\n## B\n", "md").map((s) => s.name), [
  "A",
  "B",
]);
assert.deepEqual(
  browse("---\nx: 1\n---\n\n# T\n## A\ntext\n## B\n", "markdown").map((s) =>
    s.name
  ),
  ["A", "B"],
);
assert.deepEqual(browse(rst, "rst").map((s) => s.name), [
  "Part A",
  "Part B",
  "Part A (2)",
]);
assert.deepEqual(browse("# Leaf\n**bold** text\n", "md"), []);
assert.deepEqual(browse("# T\n\n## Only\n", "md"), []);
assert.deepEqual(browse("intro\n\n# Guide\n\ntext\n", "md"), []);
assert.deepEqual(
  browse("intro\n\n# Guide\n\n## Install\n", "md").map((s) => s.name),
  ["Guide"],
);
assert.deepEqual(browse("Guide\n=====\n\ntext\n", "rst"), []);

/* A document selected in its folder previews whole, like a file; an opened
   document or section previews when nothing inside it is selected. */
const section = { name: "Intro", dir: false, section: { start: 0, end: 1 } };
const document_ = { name: "guide.md", dir: true, doc: true, kids: [section] };
const shelf = { name: "shelf", dir: true, kids: [document_, file("a.txt")] };
setState({ path: [shelf], sel: ["guide.md"], focusCol: 0 });
assert.equal(previewNode(), document_);
assert.equal(locationState("render", null).location.view, "render");
setState({ path: [shelf, document_], sel: ["guide.md"], focusCol: 0 });
assert.equal(previewNode(), document_);
sel[1] = "Intro";
assert.equal(previewNode(), section);
assert.equal(locationState("highlight", null).location.view, "highlight");
/* A missing heading anywhere in a section URL restores the whole document. */
const group = { name: "Group", dir: true, section: {}, kids: [section] };
document_.kids.push(group);
for (
  const suffix of [["Missing"], ["Group", "Missing"], [
    "Group",
    "Intro",
    "Missing",
  ]]
) {
  setState({ path: [shelf], sel: [], focusCol: 0 });
  assert.equal(await walkPath(["guide.md", ...suffix], async () => {}), false);
  assert.equal(previewNode(), document_);
  assert.deepEqual(currentPath(), ["guide.md"]);
}
const readmeDoc = { name: "README.md", dir: true, doc: true, kids: [] };
const library = { name: "library", dir: true, kids: [readmeDoc, file("b")] };
setState({ path: [library], sel: [], focusCol: 0 });
autoPreview(library);
assert.equal(sel[0], "README.md");
assert.equal(previewNode(), readmeDoc);

/* Folder preview filenames are ordinary headings inside documents. */
for (const name of ["README", "README.md", "index.html"]) {
  for (const kind of ["doc", "section"]) {
    const child = { name, dir: false, section: {} };
    const parent = { name: "Parent", dir: true, kids: [child], [kind]: true };
    setState({ path: [parent], sel: [], focusCol: 0 });
    autoPreview(parent);
    assert.deepEqual(sel, [], `${kind} must not auto-select ${name}`);
    assert.equal(previewNode(), parent);
    assert.deepEqual(currentPath(), []);
  }
  const parent = { name: "Folder", dir: true, kids: [file(name)] };
  setState({ path: [parent], sel: [], focusCol: 0 });
  autoPreview(parent);
  assert.deepEqual(sel, [name], `folders still auto-select ${name}`);
}

/* A preview links to a safe protocol or a scheme-less address only (A2). */
for (
  const url of [
    "https://example.com/",
    "HTTP://example.com/",
    "mailto:a@example.com",
    "sib.md",
    "../a/b:c",
    "#top",
    "?q=1",
    "/abs",
    "",
  ]
) assert.ok(safeURL(url), url);
for (
  const url of [
    "javascript:alert(1)",
    "JavaScript:alert(1)",
    " javascript:alert(1)",
    "java\tscript:alert(1)",
    "\u0001javascript:alert(1)",
    "data:text/html,x",
    "vbscript:msgbox(1)",
    "file:///etc/passwd",
  ]
) assert.ok(!safeURL(url), url);
