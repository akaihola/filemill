/* ═══════════════════════════════════════════════════════════════════════════
   DOM handles and measurements for the browser renderer
   ═══════════════════════════════════════════════════════════════════════════ */
import "./shell.js";
import { state } from "./model/state.js";
state.dotfiles = document.documentElement.dataset.hidden === "show";

export const root = document.documentElement;
export const finder = document.getElementById("finder");
export const rail = document.getElementById("rail");
export const stage = document.getElementById("stage");
export const strip = document.getElementById("strip");
export const trail = document.getElementById("trail");

export const GUTTER = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--gutter"));
export const SPINE = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--spine-w"));

// --column-width is in em, resolved against the inherited column font.
export function folderWidth() {
  const cs = getComputedStyle(strip);
  const ratio = parseFloat(cs.getPropertyValue("--column-ratio"));
  return ratio
    ? finder.clientWidth * ratio
    : parseFloat(cs.getPropertyValue("--column-width")) *
      parseFloat(cs.fontSize);
}

// Reserve the same space for empty, source and rendered previews.
export const previewTarget = () => finder.clientWidth / 3;
