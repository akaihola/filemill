/* All of `q` in `n`, in order, gaps allowed. No allocation: this runs once per
   entry per keystroke, and a column can hold thousands. */
const taFuzzy = (n, q) => {
  let qi = 0;
  for (let i = 0; i < n.length && qi < q.length; i++) if (n[i] === q[qi]) qi++;
  return qi === q.length;
};

/* Row index of the winner, or -1. Three passes, each stopping at its own first
   hit — a prefix match on row 2 never looks at rows 3…3000. A prefix match on
   row 2 800 still beats a substring match on row 3, which is the point of
   separate passes rather than one scan that scores. */
export function taSearch(lower, q) {
  let i = lower.findIndex((n) => n.startsWith(q));
  if (i < 0) i = lower.findIndex((n) => n.includes(q));
  if (i < 0) i = lower.findIndex((n) => taFuzzy(n, q));
  return i;
}
