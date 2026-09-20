// Patterns replace the preview's prefix, retaining absolute depth and suffix.
const collapsed = new Map();
const explicit = new WeakMap();
export const jsonCollapse = {
  record(root, path, depth, open) {
    if (!explicit.has(root)) explicit.set(root, new Map());
    explicit.get(root).set(JSON.stringify(path), open);
    if (!open) {
      if (!collapsed.has(path.length)) collapsed.set(path.length, new Map());
      const depths = collapsed.get(path.length);
      if (!depths.has(depth)) depths.set(depth, new Set());
      depths.get(depth).add(JSON.stringify(path.slice(depth)));
    }
  },
  open(root, path) {
    const saved = explicit.get(root)?.get(JSON.stringify(path));
    if (saved !== undefined) return saved;
    for (const [depth, suffixes] of collapsed.get(path.length) || []) {
      if (suffixes.has(JSON.stringify(path.slice(depth)))) {
        return false;
      }
    }
    return true;
  },
};
