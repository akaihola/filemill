/* ═══════════════════════════════════════════════════════════════════════════
   Settings popover
   ═══════════════════════════════════════════════════════════════════════════ */
const gear = document.getElementById("gear"),
  panel = document.getElementById("settings");
const closeSettings = () => {
  panel.hidden = true;
  gear.setAttribute("aria-expanded", "false");
};
gear.onclick = (e) => {
  e.stopPropagation();
  panel.hidden = !panel.hidden;
  gear.setAttribute("aria-expanded", String(!panel.hidden));
};
document.addEventListener("click", (e) => {
  if (!panel.contains(e.target)) closeSettings();
});

const toggle = (id, get, set) => {
  const b = document.getElementById(id);
  b.onclick = () => {
    set(!get());
    b.setAttribute("aria-checked", String(get()));
    render(true);
  };
  b.setAttribute("aria-checked", String(get()));
};
toggle("s-dot", () => state.dotfiles, (v) => state.dotfiles = v);
toggle(
  "s-density",
  () => root.dataset.density === "compact",
  (v) => root.dataset.density = v ? "compact" : "comfortable",
);
toggle(
  "s-theme",
  () => root.dataset.theme === "dark",
  (v) => root.dataset.theme = v ? "dark" : "light",
);

/* Radios rather than three toggles: one key is active, and a menu that lets you
   uncheck every one of them has no answer for what the column is ordered by.
   Direction is separate because it applies to whichever key is chosen — and
   because flipping it re-sorts what is already in memory, with no second sweep.
   setSort (core/sort.js) stores the choice and re-renders. */
SORT_KEYS.forEach((k) => {
  document.getElementById(`s-sort-${k}`).onclick = () =>
    setSort(k, state.sort.desc);
});
document.getElementById("s-sort-desc").onclick = () =>
  setSort(state.sort.key, !state.sort.desc);

/* Only the builds that can actually fetch a renderer show the switch — on the
   server build the previews come from Python and nothing is downloaded, so the
   row would be a promise the page does not keep. preview-rich.js reveals it. */
function offerRichToggle(get, set) {
  document.getElementById("s-previews").hidden = false;
  document.getElementById("s-rich").hidden = false;
  document.getElementById("s-rich-hr").hidden = false;
  toggle("s-rich", get, set);
}
