/* Headings — the outline of a Markdown or reStructuredText file.

   outline(text, kind) returns the sections as a tree of {name, level, start,
   end, kids}. start and end are 0-based line indexes, end exclusive, of the
   section's source: its heading, its body and its subsections. A section ends
   where the next heading of its own level or a shallower one begins. Names are
   unique among siblings, because a column, the selection and the URL all name
   a row by it; a repeat gets " (2)", " (3)" and so on.

   Markdown: ATX (`# Title`, optional closing hashes) and setext (a paragraph
   underlined with `===` or `---`) headings, skipping fenced code and a leading
   YAML front matter block. reStructuredText: a title underlined, or overlined
   and underlined, with one repeated punctuation character; levels follow the
   order in which the adornment styles first appear, as docutils assigns them.
   Only the label is read from inline markup: code spans, emphasis and links
   are reduced to their text. */

const FENCE = /^ {0,3}(`{3,}|~{3,})/;
const ATX = /^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$/;
const SETEXT = /^ {0,3}(=+|-+)[ \t]*$/;
const FRONT_MATTER = /^(?:---|\.\.\.)\s*$/;
/* A line that cannot be a setext heading's paragraph: a block start, indented
   code, a thematic break or an empty line. */
const NOT_PARAGRAPH =
  /^(?:\s*$|(?: {4}|\t)| {0,3}(?:>|[-*+][ \t]|\d{1,9}[.)][ \t]|([-*_])(?:[ \t]*\1){2,}[ \t]*$))/;
const ADORNMENT = /^([!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~])\1*[ \t]*$/;
const SHORT_UNDERLINE =
  4; /* docutils: shorter than this and the title is text */

const label = (raw) => {
  const text = raw
    .replace(/:[\w.+-]+:`([^`]*)`/g, "$1")
    .replace(/`+([^`]*?)(?:\s*<[^>]*>)?`+_{0,2}/g, "$1")
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/!?\[([^\]]*)\]\[[^\]]*\]/g, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/(\*\*|__)(.+?)\1/g, "$2")
    .replace(/(\*|_)(.+?)\1/g, "$2")
    .replace(/\s*\{#[^}]*\}\s*$/, "")
    .replace(/\s+/g, " ")
    .trim();
  return text || "Untitled";
};

const paragraph = (line) =>
  !NOT_PARAGRAPH.test(line) && !ATX.test(line) &&
  !FENCE.test(line) && !SETEXT.test(line);

/* The line after a leading YAML front matter block, or 0. */
function afterFrontMatter(lines) {
  if (lines[0] === undefined || !/^---\s*$/.test(lines[0])) return 0;
  const close = lines.findIndex((l, j) => j > 0 && FRONT_MATTER.test(l));
  return close > 0 ? close + 1 : 0;
}

function markdownHeadings(lines) {
  const found = [];
  let fence = null;
  for (let i = afterFrontMatter(lines); i < lines.length; i++) {
    const line = lines[i];
    if (fence) {
      if (line.trim().startsWith(fence) && !line.trim().replace(/^[`~]+/, "")) {
        fence = null;
      }
      continue;
    }
    const open = FENCE.exec(line);
    if (open) {
      fence = open[1];
      continue;
    }
    const atx = ATX.exec(line);
    if (atx) {
      found.push({ name: label(atx[2] || ""), level: atx[1].length, start: i });
      continue;
    }
    const under = i + 1 < lines.length && paragraph(line) &&
      SETEXT.exec(lines[i + 1]);
    if (under) {
      let start = i;
      while (start > 0 && paragraph(lines[start - 1])) start--;
      found.push({
        name: label(lines.slice(start, i + 1).join(" ")),
        level: under[1][0] === "=" ? 1 : 2,
        start,
      });
      i++;
    }
  }
  return found;
}

function rstHeadings(lines) {
  const found = [];
  const styles = [];
  const level = (style) => {
    if (!styles.includes(style)) styles.push(style);
    return styles.indexOf(style) + 1;
  };
  const blankBefore = (i) => i === 0 || !lines[i - 1].trim();
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (ADORNMENT.test(line)) {
      const title = lines[i + 1], under = lines[i + 2];
      if (
        blankBefore(i) && title?.trim() && !ADORNMENT.test(title) &&
        under !== undefined && ADORNMENT.test(under) && under[0] === line[0]
      ) {
        found.push({
          name: label(title),
          level: level(`over${line[0]}`),
          start: i,
        });
        i += 2;
      }
      continue;
    }
    const under = lines[i + 1];
    if (
      !line.trim() || /^\s/.test(line) || under === undefined ||
      !ADORNMENT.test(under) || !blankBefore(i)
    ) continue;
    const width = under.trimEnd().length;
    if (width < line.trimEnd().length && width < SHORT_UNDERLINE) continue;
    found.push({
      name: label(line),
      level: level(`under${under[0]}`),
      start: i,
    });
    i++;
  }
  return found;
}

function unique(kids) {
  const seen = new Set();
  for (const kid of kids) {
    let name = kid.name;
    for (let n = 2; seen.has(name); n++) name = `${kid.name} (${n})`;
    seen.add(name);
    kid.name = name;
    unique(kid.kids);
  }
  return kids;
}

export function outline(text, kind) {
  return build(String(text ?? "").split("\n"), kind);
}

/* The outline as a column browses it. A file that opens with its one title,
   and nothing before it but blank lines or front matter, is named by that
   title already: its subsections are the first column. A file with fewer than
   two sections in all has no hierarchy to browse and returns []. */
export function sections(text, kind) {
  const lines = String(text ?? "").split("\n");
  let tree = build(lines, kind);
  const first = kind === "rst" ? 0 : afterFrontMatter(lines);
  const top = lines.findIndex((l, i) => i >= first && l.trim());
  if (tree.length === 1 && tree[0].start === top) tree = tree[0].kids;
  const count = (list) => list.reduce((n, s) => n + 1 + count(s.kids), 0);
  return count(tree) < 2 ? [] : tree;
}

function build(lines, kind) {
  const headings = kind === "rst"
    ? rstHeadings(lines)
    : markdownHeadings(lines);
  const root = { level: 0, kids: [] };
  const open = [root];
  for (const h of headings) {
    while (open.length > 1 && open.at(-1).level >= h.level) {
      open.pop().end = h.start;
    }
    const node = { ...h, end: lines.length, kids: [] };
    open.at(-1).kids.push(node);
    open.push(node);
  }
  return unique(root.kids);
}
