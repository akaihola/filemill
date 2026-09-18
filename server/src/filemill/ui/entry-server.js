/* ═══════════════════════════════════════════════════════════════════════════
   Server edition — the one module the shell loads.

   The counterpart of entry-static.js: the same core/, the server's adapters,
   and app-http.js to wire them. Both filesystem adapters are present because
   "Open local folder…" switches between them at runtime; app-http.js is what
   selects. server/src/filemill/app.py emits one <script type="module"> for
   this file and nothing else.
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
import "./adapters/vfs-json.js";
import "./core/search.js";
import "./core/mount.js";

import "./adapters/http.js";
import "./adapters/preview-http.js";
import "./adapters/preview-local.js";
import "./adapters/preview-rich.js";
import "./adapters/vfs-csv.js";
import "./adapters/router-path.js";
import "./adapters/fsa.js";
import "./adapters/storage.js";
import "./adapters/app-http.js";

/* Test surface — see core/debug.js. */
import { expose, exposeCore } from "./core/debug.js";
import { mount } from "./adapters/app-http.js";
import { FSA } from "./adapters/fsa.js";
import { classifyFile } from "./core/file-kind.js";
import { addRenderers, RENDERERS, renderNode } from "./core/renderers.js";
import { recallRoots } from "./adapters/storage.js";

exposeCore();
expose({
  mount: () => mount,
  FSA: () => FSA,
  classifyFile: () => classifyFile,
  RENDERERS: () => RENDERERS,
  addRenderers: () => addRenderers,
  renderNode: () => renderNode,
  recallRoots: () => recallRoots,
});
