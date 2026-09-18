import { FS } from "../core/ports.js";
import { TEXT_MAX } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";
import { esc } from "../core/icons.js";
import { editorUndo } from "./undo.js";
import { editorFind } from "./find.js";
import { editorGutter } from "./gutter.js";
import { editorModified } from "./modified.js";

const EDIT_MAX_LINE = 10_000; // Avoid unusably wide editor lines.
let activeEditor = null;

export function closeEditor() {
  if (activeEditor) activeEditor.mark.hidden = true;
  activeEditor = null;
}

export function editingPreview(node) {
  if (activeEditor?.node === node && activeEditor.pane.isConnected) {
    return activeEditor.pane;
  }
  closeEditor();
  return null;
}

export async function editableText(node) {
  if (
    !FS.write || !classifyFile(node.name, node).editable ||
    (node.meta?.size ?? 0) > TEXT_MAX
  ) return null;
  try {
    const blob = await FS.blob(node);
    if (!blob || blob.size > TEXT_MAX) return null;
    const text = new TextDecoder("utf-8", { fatal: true }).decode(
      await blob.arrayBuffer(),
    );
    return !text.includes("\0") &&
        text.split(/\r?\n/).every((line) => line.length <= EDIT_MAX_LINE)
      ? text
      : null;
  } catch (_) {
    return null;
  }
}

export async function openEditor(node, current, refresh) {
  if (!current()) return;
  const edit = document.getElementById("pv-edit");
  if (edit.disabled) return;
  edit.disabled = true;
  const text = await editableText(node);
  edit.disabled = false;
  if (!current() || text === null) return;
  const pane = document.getElementById("preview");
  const host = pane.querySelector("#pv-content");
  const mark = pane.querySelector("#pv-modified");
  pane.querySelector("#pv-edit").hidden = true;
  host.innerHTML = `
    <div class="pv-find" hidden>
      <label>Find <input type="search" aria-label="Find in file"></label>
      <button type="button">Next</button><output aria-live="polite"></output>
    </div>
    <div class="pv-editor-lines">
      <div class="pv-gutter-clip" aria-hidden="true"><pre id="pv-gutter"></pre></div>
      <textarea id="pv-editor" wrap="off" spellcheck="false" aria-label="Edit ${
    esc(node.name)
  }"></textarea>
    </div>
    <div class="pv-edit-bar">
      <button id="pv-save">Save</button><button id="pv-cancel">Cancel</button>
      <button id="pv-find-open">Find</button>
      <span class="pv-err" id="pv-edit-err" role="alert"></span>
    </div>`;
  const ta = host.querySelector("textarea");
  ta.value = text;
  const session = { node, pane, mark };
  activeEditor = session;
  const live = () => current() && activeEditor === session && ta.isConnected;
  const updateModified = editorModified(ta, mark);
  const updateGutter = editorGutter(ta, host.querySelector("#pv-gutter"));
  const changed = () => {
    updateModified();
    updateGutter();
  };
  editorUndo(ta, changed);
  editorFind(host, ta);
  changed();
  ta.focus();
  ta.setSelectionRange(0, 0);
  ta.scrollTop = 0;
  host.querySelector("#pv-cancel").onclick = () => {
    if (live()) refresh();
  };
  const save = host.querySelector("#pv-save");
  const error = host.querySelector("#pv-edit-err");
  save.onclick = async () => {
    if (!live() || save.disabled) return;
    const submitted = ta.value;
    save.disabled = ta.readOnly = true;
    error.textContent = "";
    try {
      await FS.write(node, submitted);
      if (live()) refresh();
    } catch (err) {
      if (!live()) return;
      error.textContent = String(err.message || err);
      save.disabled = ta.readOnly = false;
    }
  };
}
