/* Native edition: shared DOM renderer with native-backed ports. */
import "./core/shell.js";
import "./core/dom-renderer.js";
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
import "./adapters/vfs-csv.js";
import "./adapters/vfs-doc.js";
import "./core/search.js";
import "./core/mount.js";

import "./adapters/app-native.js";
import { expose, exposeCore } from "./core/debug.js";
import { mountNative } from "./adapters/app-native.js";
import { classifyFile } from "./core/file-kind.js";
import { addRenderers, RENDERERS, renderNode } from "./core/renderers.js";
import { nativeCall, NativeFS } from "./adapters/native.js";
exposeCore();
expose({
  nativeCall: () => nativeCall,
  NativeFS: () => NativeFS,
  mount: () => mountNative,
  classifyFile: () => classifyFile,
  addRenderers: () => addRenderers,
  RENDERERS: () => RENDERERS,
  renderNode: () => renderNode,
});
