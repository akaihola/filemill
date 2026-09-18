export function editorModified(ta, mark) {
  const saved = ta.value;
  return () => {
    mark.hidden = ta.value === saved;
  };
}
