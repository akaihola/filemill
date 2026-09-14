const CSV_MAX = 512 * 1024;

function csvParse(text) {
  const rows = [], row = [];
  let cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') cell += '"', i++;
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"' && !cell) quoted = true;
    else if (c === ",") row.push(cell), cell = "";
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell), rows.push(row.splice(0)), cell = "";
    } else cell += c;
  }
  if (quoted) throw new Error("Malformed CSV: unterminated quoted field");
  if (cell || row.length) row.push(cell), rows.push(row);
  if (!rows.length) return { headers: [], records: [] };
  const headers = rows.shift().map((v, i) => v || `column ${i + 1}`);
  if (new Set(headers).size !== headers.length) {
    throw new Error("Malformed CSV: duplicate header");
  }
  const records = rows.filter((r) => r.some(Boolean)).map((r, i) => {
    if (r.length !== headers.length) {
      throw new Error(`Malformed CSV: row ${i + 2}`);
    }
    return Object.fromEntries(headers.map((h, j) => [h, r[j]]));
  });
  return { headers, records };
}

const isCsv = (n) => /\.csv$/i.test(n.name);

function csvLabels(records, key) {
  const seen = new Set();
  const labels = [];
  for (const record of records) {
    const label = record[key];
    if (!label || seen.has(label)) return null;
    seen.add(label);
    labels.push(label);
  }
  return labels;
}

function csvRows(node, records, headers) {
  const key = headers.find((header) => csvLabels(records, header));
  const labels = key
    ? csvLabels(records, key)
    : records.map((_, i) => `row ${i + 1}`);
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

const withCsv = (fs) => ({
  ...fs,
  async ensureLoaded(node) {
    if (!node.csv) {
      await fs.ensureLoaded(node);
      for (const k of node.kids || []) {
        if (!k.dir && isCsv(k)) {
          Object.assign(k, { dir: true, kids: null, csv: true, ordered: true });
        }
      }
      return;
    }
    if (node.kids !== null || node.loading) return node.loading;
    node.loading = (async () => {
      try {
        if ((node.meta?.size ?? 0) > CSV_MAX) {
          throw new Error("Too large to browse (over 512 KB)");
        }
        const blob = await fs.blob({ ...node, dir: false });
        if (!blob || blob.size > CSV_MAX) {
          throw new Error("Too large to browse (over 512 KB)");
        }
        const parsed = csvParse((await blob.text()).replace(/^\uFEFF/, ""));
        node.headers = parsed.headers;
        if (!parsed.records.length) {
          node.dir = false;
          node.csvEmpty = true;
        }
        node.kids = csvRows(node, parsed.records, parsed.headers);
      } catch (err) {
        node.denied = String(err.message || err);
        node.dir = false;
        node.csvError = true;
        node.kids = [];
      }
      node.loading = null;
    })();
    return node.loading;
  },
});

const withCsvPreview = (provider) => ({
  revoke() {
    provider.revoke?.();
  },
  async render(n) {
    if (n.csv && !n.record) {
      await FS.ensureLoaded(n);
      if (n.csvEmpty) {
        return '<div class="preview-empty">CSV file is empty.</div>';
      }
      if (n.csvError) return provider.render(n);
    }
    if (!n.record) return provider.render(n);
    const rows = Object.entries(n.record).map(([k, v]) =>
      `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`
    ).join("");
    return Promise.resolve(
      `<div class="pv-rich"><table class="pv-kv">${rows}</table></div>`,
    );
  },
});
