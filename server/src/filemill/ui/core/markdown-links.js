/* Shared destinations for rendered Markdown and highlighted source. */
export function markdownHref(href, dir) {
  // Browsers ignore controls in schemes. Reject them before path resolution.
  const scheme = href.replace(/%0[0-9a-f]|%1[0-9a-f]|%20|%7f/gi, "")
    .replace(/[\s\p{Cc}]/gu, "");
  if (/^(?:javascript|vbscript|file|data):/i.test(scheme)) return null;
  if (href.startsWith("~/")) {
    const root = document.documentElement;
    const mounts = JSON.parse(root.dataset.mounts || "[]");
    const path = href.slice(2);
    const mount = mounts.includes(path.split("/", 1)[0])
      ? path.split("/", 1)[0]
      : root.dataset.root;
    return mount && mount !== "/"
      ? `/w/${encodeURIComponent(mount)}/${path}`
      : path;
  }
  if (dir === undefined || /^(?:[a-z][a-z0-9+.-]*:|\/|#|\?)/i.test(href)) {
    return href;
  }
  const [, clean, query = "", fragment = ""] = /^([^?#]*)(\?[^#]*)?(#.*)?$/
    .exec(href);
  const parts = dir ? dir.split("/").map(encodeURIComponent) : [];
  for (const p of clean.split("/")) {
    if (p === "..") parts.pop();
    else if (p && p !== ".") parts.push(p);
  }
  const url = "/" + parts.join("/");
  const params = new URLSearchParams(query);
  if (/\.(?:md|markdown)$/i.test(url) && !params.has("filemill")) {
    return url + (query ? query + "&" : "?") + "filemill=render" + fragment;
  }
  return url + query + fragment;
}

/* Markdown escapes and entities belong to the destination, not its visible
   source. Escape '<' before using a detached textarea to decode entities. */
export function markdownDestination(raw) {
  const decoder = document.createElement("textarea");
  decoder.innerHTML = raw.replace(
    /\\([!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~])/g,
    "$1",
  )
    .replace(/</g, "&lt;");
  return decoder.value.replace(
    /[\s<>"\p{Cc}\P{ASCII}]/gu,
    (c) => encodeURIComponent(c),
  );
}
