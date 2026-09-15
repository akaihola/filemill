/* ═══════════════════════════════════════════════════════════════════════════
   Static edition — the one module the page loads.

   core/ is the shared UI and knows nothing about where its nodes come from;
   adapters/ chooses. This file names the adapters of the local-folder flavour
   and the app module that wires them (app-fsa.js), which is the only module
   that runs anything at load time. entry-server.js is the counterpart.

   Import order is evaluation order. state.js first: it pulls in shell.js (the
   markup every other module queries) and, through the core cycle, the rest.
   static/build-index.py walks this graph and inlines it in the same order.
   ═══════════════════════════════════════════════════════════════════════════ */
import "./core/shell.js";
import "./core/state.js";
import "./core/ports.js";
import "./core/icons.js";
import "./core/syntax.js";
import "./core/sort.js";
import "./core/render.js";
import "./core/layout.js";
import "./core/trail.js";
import "./core/typeahead.js";
import "./core/nav.js";
import "./core/deeplink.js";
import "./core/settings.js";
import "./core/jsonl.js";
import "./adapters/vfs-csv.js";
import "./core/search.js";

import "./adapters/fsa.js";
import "./adapters/preview-local.js";
import "./adapters/preview-rich.js";
import "./adapters/router-hash.js";
import "./adapters/storage.js";
import "./adapters/app-fsa.js";

/* Test surface — see core/debug.js. */
import { expose, exposeCore } from "./core/debug.js";
import { mount, pendingLoc, setPendingLoc } from "./adapters/app-fsa.js";
import { FSA } from "./adapters/fsa.js";
import { recallRoots, recallView, rememberRoot } from "./adapters/storage.js";

exposeCore();
expose({
  mount: () => mount,
  FSA: () => FSA,
  recallRoots: () => recallRoots,
  recallView: () => recallView,
  rememberRoot: () => rememberRoot,
  pendingLoc: { get: () => pendingLoc, set: setPendingLoc },
});
