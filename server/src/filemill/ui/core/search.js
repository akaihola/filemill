/* Server-only content search. The control stays hidden in local FSA mode. */
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

function showSearch(message, results = false) {
  searchResults.hidden = !message;
  searchResults.classList.toggle("search-list", results);
  searchResults.innerHTML = message;
}

async function runSearch() {
  const q = searchInput.value.trim();
  searchController?.abort();
  if (!q) return showSearch("");
  searchController = new AbortController();
  showSearch("Searching…");
  try {
    const focused = currentPath().slice(0, focusCol).join("/");
    const r = await fetch(
      `/api/search?q=${encodeURIComponent(q)}&p=${encodeURIComponent(focused)}`,
      {
        signal: searchController.signal,
        headers: { Accept: "application/json" },
      },
    );
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || `${r.status} ${r.statusText}`);
    if (!data.matches.length) return showSearch("No matches");
    showSearch(
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
        const names = button.dataset.path.split("/");
        document.documentElement.dataset.filemill = "render";
        ROUTER.write({ path: names, view: "render" }, false);
        showSearch("");
        await applyPath(names);
      };
    });
  } catch (err) {
    if (err.name !== "AbortError") {
      showSearch(`Search error: ${esc(err.message)}`);
    }
  }
}

if (searchForm && document.documentElement.dataset.root) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch();
  });
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(runSearch, 250);
  });
} else {
  searchForm?.remove();
}
