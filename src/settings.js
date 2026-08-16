/* ═══════════════════════════════════════════════════════════════════════════
   Settings popover
   ═══════════════════════════════════════════════════════════════════════════ */
const gear = document.getElementById("gear"), panel = document.getElementById("settings");
const closeSettings = () => { panel.hidden = true; gear.setAttribute("aria-expanded", "false"); };
gear.onclick = e => {
  e.stopPropagation();
  panel.hidden = !panel.hidden;
  gear.setAttribute("aria-expanded", String(!panel.hidden));
};
document.addEventListener("click", e => { if (!panel.contains(e.target)) closeSettings(); });

const toggle = (id, get, set) => {
  const b = document.getElementById(id);
  b.onclick = () => { set(!get()); b.setAttribute("aria-checked", String(get())); render(true); };
  b.setAttribute("aria-checked", String(get()));
};
toggle("s-dot",     () => state.dotfiles,                    v => state.dotfiles = v);
toggle("s-density", () => root.dataset.density === "compact",
                    v => root.dataset.density = v ? "compact" : "comfortable");
toggle("s-theme",   () => root.dataset.theme === "dark",
                    v => root.dataset.theme = v ? "dark" : "light");
