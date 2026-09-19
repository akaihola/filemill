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
  focusPan,
  foldingAt,
  foldPosition,
  tailShift,
} from "./folding.js";
import { keyAction, nextRow, pageSelection } from "./keyboard.js";
import { currentPath, locationState, walkPath } from "./deeplink.js";

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
    assert.equal(locationState("highlight", null).location.view, undefined);
  }
}
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

console.log("Model checks passed");
