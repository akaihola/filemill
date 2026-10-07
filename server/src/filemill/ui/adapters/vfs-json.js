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

   A JSONL file over TEXT_MAX is never parsed whole (ADR 0068). One pass over the
   blob's byte stream records the span of each line; rows are named by line
   number and a row's record is parsed from its slice only when it is opened
   or previewed. A bad line fails on its own row, not the file.
   ═══════════════════════════════════════════════════════════════════════════ */
import { esc } from "../core/icons.js";
import { render } from "../core/render.js";
import { JSON_MAX, TEXT_MAX } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";
import { jsonHTML } from "../core/syntax.js";

const JSONL_LABEL = 60; /* as the server's MAX_LABEL_LEN */
const JSONL_TEXT = ["title", "name", "description", "summary", "label"];
const JSONL_SCALAR = ["timestamp", "time", "ts", "id", "uuid", "key"];

const isJsonl = (n) => classifyFile(n.name).preview === "jsonl";
const isJson = (n) =>
  classifyFile(n.name).preview === "text" && /\.jsonc?$/i.test(n.name);
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
  return records.map((record, i) =>
    jsonValue(node, labels[i], record, String(i + 1), String(i))
  );
}

/* Byte spans of the non-blank lines, from one pass over the stream. */
async function jsonlIndex(blob) {
  const spans = [];
  const reader = blob.stream().getReader();
  let base = 0, start = 0, blank = true;
  const close = (end) => {
    if (!blank) spans.push([start, end]);
    start = end + 1;
    blank = true;
  };
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    let from = 0;
    for (;;) {
      const nl = value.indexOf(10, from);
      const to = nl < 0 ? value.length : nl;
      if (blank) {
        for (let i = from; i < to; i++) {
          const b = value[i];
          if (b !== 32 && b !== 9 && b !== 13) {
            blank = false;
            break;
          }
        }
      }
      if (nl < 0) break;
      close(base + nl);
      from = nl + 1;
    }
    base += value.length;
  }
  close(base);
  return spans;
}

function jsonlLazyRows(node, blob, spans) {
  return spans.map(([start, end], i) => ({
    name: `line ${i + 1}`,
    dir: true,
    kids: null,
    vpath: String(i + 1),
    icon: "{}",
    json: true,
    jsonRoot: node,
    jsonPath: [String(i)],
    rel: node.rel,
    ordered: true,
    meta: { virtual: true },
    span: { blob, start, end },
  }));
}

/* Parse one lazy row from its slice. A line that is not a JSON object turns
   the row into a leaf whose preview reports it, so the other rows stay. */
function loadRow(node) {
  if (node.value !== undefined || node.jsonError) return;
  if (node.loading) return node.loading;
  node.loading = (async () => {
    const { blob, start, end } = node.span;
    let v;
    try {
      v = JSON.parse(await blob.slice(start, end).text());
    } catch {
      v = null;
    }
    if (!v || typeof v !== "object" || Array.isArray(v)) {
      node.jsonError = `Not valid JSONL: line ${node.vpath}`;
      node.dir = false;
      node.kids = undefined;
    } else {
      node.value = v;
      node.kids = jsonKids(node, v);
    }
    node.loading = null;
  })();
  return node.loading;
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
        /* A server-listed row (a SQLite table row) carries its cells as a
           record; it browses like a JSONL record. CSV rows keep their own view. */
        if (!k.dir && k.record && !k.csv) {
          Object.assign(k, jsonValue(node, k.name, k.record, k.vpath));
        }
      }
      return;
    }
    if (node.span) return loadRow(node);
    if (node.json) {
      node.jsonRoot ||= node;
      node.jsonPath ||= [];
      if (node.value !== undefined) {
        if (node.kids === null) node.kids = jsonKids(node, node.value);
        return;
      }
      if (node.loading) return node.loading;
      node.loading = (async () => {
        try {
          if ((node.meta?.size ?? 0) > JSON_MAX) {
            node.jsonTooLarge = true;
            throw new Error("Too large to browse (over 8 MiB)");
          }
          const blob = await fs.blob({ ...node, dir: false, vpath: "" });
          if (!blob) throw new Error("Cannot read file");
          if (blob.size > JSON_MAX) {
            node.jsonTooLarge = true;
            throw new Error("Too large to browse (over 8 MiB)");
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
        /* The node is a directory to core; the port still reads it as the
           file it is (FSA.loadMeta skips directories). */
        const blob = await fs.blob({ ...node, dir: false });
        if (!blob) throw new Error("Cannot read file");
        node.kids = blob.size > TEXT_MAX
          ? jsonlLazyRows(node, blob, await jsonlIndex(blob))
          : jsonlRows(node, jsonlParse(await blob.text()));
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
  async render(n) {
    if (n.span && n.value === undefined) {
      await loadRow(n);
      if (n.jsonError) throw new Error(n.jsonError);
    }
    if (n.jsonTooLarge) throw new Error(n.jsonError);
    if (!n.json || n.value === undefined) return provider.render(n);
    let text;
    try {
      text = typeof n.value === "string" ? n.value : JSON.stringify(n.value);
    } catch {
      return provider.render({ ...n, dir: false });
    }
    if (n.value !== null && typeof n.value === "object") {
      const html = jsonHTML(text, n);
      return Promise.resolve(
        `<pre class="pv-text${html === null ? "" : " pv-json"}">${
          html ?? esc(text)
        }</pre>`,
      );
    }
    return Promise.resolve(
      `<pre class="pv-text pv-json-value">${esc(text)}</pre>`,
    );
  },
});

/* JSON documents use the same virtual-node contract as JSONL and SQLite. The
   value stays on each node so the preview can answer locally; vpath is only a
   stable address for the shared router and server-shaped nodes. */
function jsonValue(parent, name, value, vpath, key = name) {
  const container = value !== null && typeof value === "object";
  return {
    name,
    dir: container,
    kids: container ? null : undefined,
    vpath,
    icon: container ? (Array.isArray(value) ? "[]" : "{}") : "◻",
    json: true,
    jsonRoot: parent.jsonRoot || parent,
    jsonPath: [...(parent.jsonPath || []), key],
    value,
    rel: parent.rel,
    ordered: true,
    meta: { virtual: true },
  };
}

function jsonKids(node, value) {
  const entries = Array.isArray(value)
    ? value.map((v, i) => [String(i), v])
    : Object.entries(value);
  return entries.map(([name, value], i) =>
    jsonValue(node, name, value, node.vpath ? `${node.vpath}/${i}` : String(i))
  );
}
