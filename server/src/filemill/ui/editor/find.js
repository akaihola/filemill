export function editorFind(host, ta) {
  const bar = host.querySelector(".pv-find");
  const input = bar.querySelector("input");
  const status = bar.querySelector("output");
  let last = -1;
  const next = () => {
    const query = input.value;
    if (!query) {
      status.textContent = "";
      last = -1;
      return;
    }
    let start = ta.value.indexOf(query, last + 1);
    if (start < 0) start = ta.value.indexOf(query);
    last = start;
    status.textContent = start < 0 ? "No matches" : "Match found";
    if (start >= 0) {
      ta.focus();
      ta.setSelectionRange(start, start + query.length);
      const line = ta.value.slice(0, start).split("\n").length - 1;
      ta.scrollTop = line * parseFloat(getComputedStyle(ta).lineHeight);
    } else input.focus();
  };
  const close = () => {
    bar.hidden = true;
    ta.focus();
  };
  host.querySelector("#pv-find-open").onclick = () => {
    bar.hidden = false;
    input.focus();
    input.select();
  };
  bar.querySelector("button").onclick = next;
  input.addEventListener("input", () => {
    last = -1;
    status.textContent = "";
  });
  host.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === "f") {
      e.preventDefault();
      host.querySelector("#pv-find-open").click();
    } else if (
      !bar.hidden && (e.target === input || e.target === ta) &&
      e.key === "Enter"
    ) {
      e.preventDefault();
      next();
    } else if (!bar.hidden && e.key === "Escape") {
      e.preventDefault();
      close();
    }
  });
}
