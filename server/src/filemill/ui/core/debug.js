/* ═══════════════════════════════════════════════════════════════════════════
   Test surface.

   The browser tests in static/ and server/tests/ reach app internals as page
   globals — page.evaluate("sel"), "mount(__local())", "setSort(…)". Module
   scope hides them, so each entry module republishes the names the tests read,
   as live getters. Nothing in the app itself goes through here; the surface
   goes away when the static tests move under pytest (TASKS.md [25]).
   ═══════════════════════════════════════════════════════════════════════════ */
import { applyPath } from "./deeplink.js";
import { foldUnit, range, stripSpan } from "./layout.js";
import { refreshColumn } from "./nav.js";
import { FS, PREVIEW, ROUTER } from "./ports.js";
import { colCache, render } from "./render.js";
import { gear } from "./settings.js";
import { ensureMeta, loadSort, setSort } from "./sort.js";
import {
  focusCol,
  folded,
  path,
  pvToken,
  sel,
  state,
  visibleKids,
  widths,
} from "./model/state.js";
import { finder, previewTarget, root, stage, strip } from "./dom-renderer.js";
import { TA_IDLE } from "./typeahead.js";
import { taSearch } from "./model/typeahead.js";

/* Each value is a getter, or a property descriptor when a test also assigns. */
export function expose(bindings) {
  for (const [name, b] of Object.entries(bindings)) {
    const desc = typeof b === "function" ? { get: b } : b;
    Object.defineProperty(globalThis, name, { ...desc, configurable: true });
  }
}

export function exposeCore() {
  expose({
    sel: () => sel,
    path: () => path,
    focusCol: () => focusCol,
    widths: () => widths,
    folded: () => folded,
    pvToken: () => pvToken,
    state: () => state,
    root: () => root,
    finder: () => finder,
    stage: () => stage,
    strip: () => strip,
    welcome: () => document.getElementById("welcome"),
    gear: () => gear,
    FS: () => FS,
    PREVIEW: () => PREVIEW,
    ROUTER: () => ROUTER,
    render: () => render,
    colCache: () => colCache,
    refreshColumn: () => refreshColumn,
    applyPath: () => applyPath,
    setSort: () => setSort,
    loadSort: () => loadSort,
    ensureMeta: () => ensureMeta,
    visibleKids: () => visibleKids,
    previewTarget: () => previewTarget,
    stripSpan: () => stripSpan,
    foldUnit: () => foldUnit,
    range: () => range,
    taSearch: () => taSearch,
    TA_IDLE: () => TA_IDLE,
  });
}
