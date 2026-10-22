import { initSettings } from "./settings.js";
import { initLayout } from "./layout.js";
import { initSort, setSortActions } from "./sort.js";
import { sortKids } from "./model/sort.js";
import { setSortKids } from "./model/state.js";
import { setDeepLinkActions } from "./deeplink.js";
import { colCache, render, setActions } from "./render.js";
import {
  choose,
  copyPath,
  refreshColumn,
  renderCrumbs,
  saySt,
  unfoldTo,
} from "./nav.js";

export function initCore() {
  initSort();
  setSortKids(sortKids);
  setActions({
    choose,
    copyPath,
    refreshColumn,
    renderCrumbs,
    saySt,
    unfoldTo,
  });
  setSortActions({ render });
  setDeepLinkActions({ render, colCache });
  initLayout(render);
  initSettings();
}
