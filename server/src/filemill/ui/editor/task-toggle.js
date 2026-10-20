import { FS } from "../core/ports.js";
import { toggleTask } from "../core/model/markdown-tasks.js";
import { editableSnapshot } from "./editor.js";

const BOX = "input.task-list-item-checkbox[data-source-line][data-source-text]";

/* A rendered task checkbox rewrites its own source line, outside the editor.
   The file is read again first, so a line that changed since the render is
   refused rather than overwritten. The write goes to the node that was
   rendered, even if the preview has moved on by the time it lands. */
export function enableTaskToggles(host, node, current, report) {
  const boxes = () => host.querySelectorAll(BOX);
  for (const box of boxes()) box.disabled = false;
  host.onchange = async (event) => {
    const box = event.target.closest?.(BOX);
    if (!box) return;
    // Disabling drops focus; give it back so preview keys keep working.
    const focused = document.activeElement === box;
    for (const b of boxes()) b.disabled = true;
    try {
      const snapshot = await editableSnapshot(node);
      const text = snapshot?.text ?? null;
      const next = text === null ? null : toggleTask(
        text,
        Number(box.dataset.sourceLine),
        box.checked,
        box.dataset.sourceText,
      );
      if (!current()) return;
      if (next === null) {
        box.checked = !box.checked;
        report("Checkbox not saved: the source changed");
        return;
      }
      try {
        await FS.write(node, next, snapshot.revision);
        // The box now stands for the rewritten line; a second click needs it.
        const source = box.dataset.sourceText;
        box.dataset.sourceText = toggleTask(source, 0, box.checked, source);
      } catch (err) {
        if (!current()) return;
        box.checked = !box.checked;
        report(`Checkbox not saved: ${String(err.message || err)}`);
      }
    } finally {
      if (current()) {
        for (const b of boxes()) b.disabled = false;
        if (focused) box.focus();
      }
    }
  };
}
