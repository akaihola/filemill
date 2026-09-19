import { state } from "./state.js";
const SORT_FIELD = { size: "size", mtime: "mod" };
const NAME_COLLATOR = new Intl.Collator(undefined, { numeric: true });
const byName = (a, b) => NAME_COLLATOR.compare(a.name, b.name);

/* The number to order on, or null for "this row has none". A file the port
   could not open carries `meta.error`; a row inside a database carries
   `meta.virtual` and no size at all. Both are honestly unknown. */
const sortValue = (k, field) => {
  const v = k.meta && !k.meta.error ? k.meta[field] : undefined;
  return typeof v === "number" ? v : null;
};

/* Directories first, then the chosen key, then the name to break ties.
   `kids` is already the filtered copy visibleKids made, so sorting it in place
   never touches node.kids.

   Directories are never ordered by size or time. Neither port can give a
   directory either number: the File System Access API has no `getFile()` for a
   directory handle, and the server build's listing sends metadata for files
   only. A folder ordered by an invented 0 would sit at one end of every size
   sort and mean nothing there, so folders keep the one order that is real for
   them.

   A file whose metadata could not be read sorts last, in name order, in *both*
   directions. Sorting by size descending asks "what is biggest here"; a file
   the app could not open is not the answer, and putting one at the top is how a
   permission error gets read as a result. Last either way keeps the end the
   user is looking at meaningful. The row is never dropped — an unreadable file
   is still a file in that folder, and hiding the rows it failed to stat would
   make the app lie about the directory. */
export function sortKids(kids) {
  const { key, desc } = state.sort;
  const dir = desc ? -1 : 1;
  const field = SORT_FIELD[key];
  return kids.sort((a, b) => {
    const kind = !!b.dir - !!a.dir;
    if (kind) return kind;
    if (field && !a.dir) {
      const av = sortValue(a, field), bv = sortValue(b, field);
      if (av === null || bv === null) {
        if (av !== bv) return av === null ? 1 : -1; /* unknown sinks */
      } else if (av !== bv) {
        return (av < bv ? -1 : 1) * dir;
      }
    }
    return byName(a, b) * (field ? 1 : dir);
  });
}
