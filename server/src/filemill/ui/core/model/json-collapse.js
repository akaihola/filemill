// Patterns replace the preview's prefix, retaining absolute depth and suffix.
const collapsed = new Set();
const explicit = new WeakMap();
export const jsonCollapse = {
  record(root, path, depth, open) {
    if (!explicit.has(root)) explicit.set(root, new Map());
    explicit.get(root).set(JSON.stringify(path), open);
    if (!open) collapsed.add(JSON.stringify([depth, path.slice(depth)]));
  },
  open(root, path) {
    const saved = explicit.get(root)?.get(JSON.stringify(path));
    if (saved !== undefined) return saved;
    for (let depth = 0; depth <= path.length; depth++) {
      if (collapsed.has(JSON.stringify([depth, path.slice(depth)]))) {
        return false;
      }
    }
    return true;
  },
};
