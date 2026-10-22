/* Content search is available only while the adapter supplies a provider. */
import { focusCol } from "./model/state.js";
import { currentPath } from "./model/deeplink.js";
import { applyPath } from "./deeplink.js";
import { ROUTER } from "./ports.js";
import { esc } from "./icons.js";

const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-bar");
const searchResults = document.getElementById("search-results");
let searchTimer;
let searchController;
let searchProvider;

export function setContentSearch(provider) {
  clearTimeout(searchTimer);
  searchController?.abort();
  searchProvider = provider;
  searchForm.hidden = !provider;
  searchInput.disabled = !provider;
  searchInput.value = "";
  showSearch("");
}

function showSearch(message, results = false) {
  searchResults.hidden = !message;
  searchResults.classList.toggle("search-list", results);
  searchResults.innerHTML = message;
}

async function runSearch() {
  clearTimeout(searchTimer);
  if (!searchProvider) return;
  const q = searchInput.value.trim();
  searchController?.abort();
  if (!q) return showSearch("");
  const controller = searchController = new AbortController();
  if (q.length > 200 || /[\r\n]/.test(q)) {
    return showSearch(
      "Search error: Search query must be one line of at most 200 characters",
    );
  }
  showSearch("Searching…");
  try {
    const focused = currentPath().slice(0, focusCol).join("/");
    const data = await searchProvider(q, focused, controller.signal);
    if (controller.signal.aborted) return;
    const notice = data.partial ? "Partial results — search limit reached" : "";
    if (!data.matches.length) return showSearch(notice || "No matches");
    data.matches.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
    showSearch(
      (notice ? `<div>${notice}</div>` : "") +
        data.matches.map((m) =>
          `<button type="button" class="search-result" data-path="${
            esc(m.path)
          }">` +
          `<span class="search-path">${esc(m.path)}:${m.line}</span>` +
          `<span class="search-context">${esc(m.context)}</span></button>`
        ).join(""),
      true,
    );
    searchResults.querySelectorAll(".search-result").forEach((button) => {
      button.onkeydown = (event) => {
        if (event.key === "Enter" || event.key === " ") event.stopPropagation();
      };
      button.onclick = async () => {
        if (controller.signal.aborted || !searchProvider) return;
        const names = button.dataset.path.split("/");
        document.documentElement.dataset.filemill = "render";
        ROUTER?.write({ path: names, view: "render" }, false);
        showSearch("");
        await applyPath(names);
      };
    });
  } catch (err) {
    if (!controller.signal.aborted && err.name !== "AbortError") {
      showSearch(`Search error: ${esc(err.message)}`);
    }
  }
}

if (searchForm) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch();
  });
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchController?.abort();
    showSearch("");
    if (searchProvider) searchTimer = setTimeout(runSearch, 250);
  });
}

setContentSearch(null);
