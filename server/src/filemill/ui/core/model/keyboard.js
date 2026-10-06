export const typeaheadKey = (event, live) =>
  !event.ctrlKey && !event.metaKey && !event.altKey &&
  (event.key.length === 1 || (event.key === "Backspace" && live));

export function keyAction(event, context) {
  if (context.editable || context.welcome) return null;
  const key = event.key;
  /* Alt+←/→ and ⌘←/→ are the browser's Back and Forward, and the other
     modified keys are its shortcuts too. Only the copy chord is ours. */
  if (
    !context.preview && key === "c" && (event.metaKey || event.ctrlKey) &&
    !context.textSelected
  ) return "copy";
  if (event.altKey || event.metaKey || event.ctrlKey) return null;
  if (context.preview) {
    if (context.fullscreen && ["ArrowLeft", "Escape"].includes(key)) {
      return "preview-exit-fullscreen";
    }
    if (key === "ArrowRight") return "preview-right";
    if (key === "ArrowLeft") return "preview-back";
    return ["ArrowUp", "ArrowDown", "PageUp", "PageDown"].includes(key)
      ? "preview-scroll"
      : null;
  }
  if (key === "Delete") return "delete";
  if (typeaheadKey(event, context.typeahead)) return "type";
  if (
    [
      "ArrowDown",
      "ArrowUp",
      "Home",
      "End",
      "PageUp",
      "PageDown",
      "ArrowRight",
      "Enter",
      "ArrowLeft",
      "Escape",
    ].includes(key)
  ) return key;
  if (key === "F5" && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    return "refresh";
  }
  return null;
}
export const nextRow = (index, selected, direction, count) =>
  selected ? Math.max(0, Math.min(count - 1, index + direction)) : index;
export const entryRow = (index, count) =>
  Math.max(0, Math.min(count - 1, index < 0 ? 0 : index));
export function pageSelection(visible, selected, direction, height) {
  const edge = direction < 0 ? visible[0] : visible.at(-1);
  const index = edge?.index;
  const rowHeight = edge?.height || 0;
  const lines = rowHeight ? Math.max(1, Math.floor(height / rowHeight)) : 1;
  return {
    index,
    scroll: index !== undefined && index === selected
      ? direction * lines * rowHeight
      : 0,
  };
}
