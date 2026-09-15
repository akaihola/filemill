/* ═══════════════════════════════════════════════════════════════════════════
   Settings popover
   ═══════════════════════════════════════════════════════════════════════════ */
import { render } from "./render.js";
import { setSort, SORT_KEYS } from "./sort.js";
import { root, state } from "./state.js";

export const gear = document.getElementById("gear"),
  panel = document.getElementById("settings");
export const closeSettings = () => {
  panel.hidden = true;
  gear.setAttribute("aria-expanded", "false");
};
const toggle = (id, get, set) => {
  const b = document.getElementById(id);
  b.onclick = () => {
    set(!get());
    b.setAttribute("aria-checked", String(get()));
    render(true);
  };
  b.setAttribute("aria-checked", String(get()));
};

/* Everything the old classic script did at load time. Called by the app
   module once every core module has been evaluated. */
export function initSettings() {
  gear.onclick = (e) => {
    e.stopPropagation();
    panel.hidden = !panel.hidden;
    gear.setAttribute("aria-expanded", String(!panel.hidden));
  };
  document.addEventListener("click", (e) => {
    if (!panel.contains(e.target)) closeSettings();
  });

  root.dataset.theme = matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";

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
}
