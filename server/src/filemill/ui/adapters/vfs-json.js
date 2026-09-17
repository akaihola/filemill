/* ═══════════════════════════════════════════════════════════════════════════
   JSONL — a file of one JSON object per line, browsed as a column of rows.

   The client-side counterpart of the server's SQLite provider: a `.jsonl`
   file opens as a column, one row per line, and a row previews as its
   key/value pairs. Both builds get it by wrapping their FS and PREVIEW ports
   here — see adapters/app-fsa.js and adapters/app-http.js — so core/ still
   sees nothing but nodes.

   The row label is one key chosen once per file: unique across every record,
   preferring short text (title, name, description…) over other scalars
   (timestamp, id…), and falling back to the line number. Unique because the
   selection, the URL and applyPath all name a row by it.
   ═══════════════════════════════════════════════════════════════════════════ */
import { esc } from "../core/icons.js";
import { render } from "../core/render.js";
import { TEXT_MAX } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";

const JSONL_MAX = TEXT_MAX;
const JSONL_LABEL = 60; /* as the server's MAX_LABEL_LEN */
const JSONL_TEXT = ["title", "name", "description", "summary", "label"];
const JSONL_SCALAR = ["timestamp", "time", "ts", "id", "uuid", "key"];
const JSON_MAX = TEXT_MAX;

const isJsonl = (n) => classifyFile(n.name).preview === "jsonl";
const isJson = (n) => classifyFile(n.name).preview === "text" && /\.jsonc?$/i.test(n.name);
const jsonlLabel = (v) =>
  ((s) => s.length > JSONL_LABEL ? s.slice(0, JSONL_LABEL - 1) + "…" : s)(
    String(v),
  );

/* The labels a key would give, or null when it cannot name every row. */
function jsonlLabels(records, key) {
  const seen = new Set();
  const out = [];
  for (const r of records) {
    const v = r[key];
    if (v === undefined || v === null || typeof v === "object") return null;
    const s = jsonlLabel(v);
    if (!s || s.startsWith(".") || seen.has(s)) {
      return null; /* dotfile filter */
    }
    seen.add(s);
    out.push(s);
  }
  return out;
}

function jsonlKey(records) {
  const keys = Object.keys(records[0] || {});
  const first = (pref) => [
    ...pref.filter((k) => keys.includes(k)),
    ...keys.filter((k) => !pref.includes(k)),
  ];
  const short = (k) =>
    records.every((r) =>
      typeof r[k] === "string" &&
      r[k].length <= JSONL_LABEL
    );
  for (const k of first(JSONL_TEXT)) {
    if (short(k) && jsonlLabels(records, k)) return k;
  }
  for (const k of first(JSONL_SCALAR)) if (jsonlLabels(records, k)) return k;
  return null;
}

function jsonlRows(node, records) {
  const key = jsonlKey(records);
  const labels = key
    ? jsonlLabels(records, key)
    : records.map((_, i) => `line ${i + 1}`);
  return records.map((record, i) => ({
    name: labels[i],
    dir: false,
    vpath: String(i + 1),
    icon: "📋",
    rel: node.rel,
    ordered: true,
    meta: { virtual: true },
    record,
  }));
}

function jsonlParse(text) {
  const records = [];
  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    let v;
    try {
      v = JSON.parse(lines[i]);
    } catch {
      v = null;
    }
    if (!v || typeof v !== "object" || Array.isArray(v)) {
      throw new Error(`Not valid JSONL: line ${i + 1}`);
    }
    records.push(v);
  }
  return records;
}

export const withVirtual = (fs) => ({
  ...fs,
  async ensureLoaded(node) {
    if (!node.jsonl && !node.json) {
      await fs.ensureLoaded(node);
      for (const k of node.kids || []) {
        if (!k.dir && isJsonl(k)) {
          Object.assign(k, {
            dir: true,
            kids: null,
            jsonl: true,
            fileKind: classifyFile(k.name, { jsonl: true }),
            ordered: true,
          });
        }
        if (!k.dir && isJson(k)) {
          Object.assign(k, {
            dir: true,
            kids: null,
            json: true,
            ordered: true,
          });
        }
      }
      return;
    }
    if (node.json) {
      if (node.value !== undefined) {
        if (node.kids === null) node.kids = jsonKids(node, node.value);
        return;
      }
      if (node.loading) return node.loading;
      node.loading = (async () => {
        try {
          const blob = await fs.blob({ ...node, dir: false, vpath: "" });
          if (!blob) throw new Error("Cannot read file");
          if (blob.size > JSON_MAX) {
            throw new Error("Too large to browse (over 512 KB)");
          }
          const value = JSON.parse(await blob.text());
          if (value === null || typeof value !== "object") {
            node.dir = false;
            node.value = value;
            node.kids = undefined;
          } else {
            node.value = value;
            node.kids = jsonKids(node, value);
          }
        } catch (err) {
          node.jsonError = String(err.message || err);
          node.dir = false;
          node.kids = undefined;
        }
        node.loading = null;
      })();
      return node.loading;
    }
    if (node.kids !== null) return;
    if (node.loading) return node.loading;
    node.loading = (async () => {
      try {
        /* Decline before fetching where the listing carried a size: HTTP.blob
           buffers the whole response. The blob.size test stays for the port
           whose listing does not. */
        const big = "Too large to browse (over 512 KB)";
        if ((node.meta?.size ?? 0) > JSONL_MAX) throw new Error(big);
        /* The node is a directory to core; the port still reads it as the
           file it is (FSA.loadMeta skips directories). */
        const blob = await fs.blob({ ...node, dir: false });
        if (!blob) throw new Error("Cannot read file");
        if (blob.size > JSONL_MAX) throw new Error(big);
        node.kids = jsonlRows(node, jsonlParse(await blob.text()));
      } catch (err) {
        node.denied = String(err.message || err);
        node.kids = [];
      }
      node.loading = null;
    })();
    return node.loading;
  },
});

export const withVirtualPreview = (provider) => ({
  revoke() {
    provider.revoke?.();
  },
  render(n) {
    if (n.record) {
      const cell = (v) =>
        v !== null && typeof v === "object" ? JSON.stringify(v) : String(v);
      const rows = Object.entries(n.record)
        .map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(cell(v))}</td></tr>`)
        .join("");
      return Promise.resolve(
        `<div class="pv-rich"><table class="pv-kv">${rows}</table></div>`,
      );
    }
    if (!n.json || n.value === undefined) return provider.render(n);
    const text = typeof n.value === "string" ? n.value : JSON.stringify(n.value);
    return Promise.resolve(
      n.value !== null && typeof n.value === "object"
        ? null
        : `<pre class="pv-text pv-json-value">${esc(text)}</pre>`,
    );
  },
});

/* JSON documents use the same virtual-node contract as JSONL and SQLite. The
   value stays on each node so the preview can answer locally; vpath is only a
   stable address for the shared router and server-shaped nodes. */
function jsonValue(parent, name, value, vpath) {
  const container = value !== null && typeof value === "object";
  return {
    name,
    dir: container,
    kids: container ? null : undefined,
    vpath,
    icon: container ? "📁" : "◻",
    json: true,
    value,
    rel: parent.rel,
    ordered: true,
    meta: { virtual: true },
  };
}

function jsonKids(node, value) {
  if (
    Array.isArray(value) && value.length &&
    value.every((v) => v && typeof v === "object" && !Array.isArray(v))
  ) {
    const key = jsonlKey(value);
    const labels = key && jsonlLabels(value, key);
    return value.map((record, i) => ({
      name: labels?.[i] || `item ${i + 1}`,
      dir: false,
      vpath: node.vpath ? `${node.vpath}/${i}` : String(i),
      icon: "📋",
      rel: node.rel,
      ordered: true,
      meta: { virtual: true },
      record,
    }));
  }
  const entries = Array.isArray(value)
    ? value.map((v, i) => [String(i), v])
    : Object.entries(value);
  return entries.map(([name, value], i) =>
    jsonValue(node, name, value, node.vpath ? `${node.vpath}/${i}` : String(i))
  );
}
