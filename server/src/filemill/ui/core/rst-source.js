/* reStructuredText source, coloured the way Pygments' RstLexer colours it:
   section titles, directives, comments, targets, field markers, literal
   blocks, and the inline markup docutils recognises. Inline markup follows the
   docutils recognition rules — a start-string needs whitespace or punctuation
   before it and an end-string needs it after — so `2*3*4`, `snake_case_name`
   and the apostrophes in "don't" stay plain text. Every character of the input
   is escaped and emitted exactly once. */
import { esc } from "./icons.js";

const rsSpan = (text, kind) => `<span class="hl-${kind}">${esc(text)}</span>`;
const rsIndent = (line) => /^[ \t]*/.exec(line)[0].length;
const rsBlank = (line) => !line.trim();

/* One punctuation character repeated: a section title's under- or overline. */
const RS_ADORN = /^([!-\/:-@[-\x60{-~])\1*[ \t]*\n?$/;

const RS_START = String
  .raw`(?<=^|[\s\-:/'"<(\[{\p{Ps}\p{Pi}\p{Pf}\p{Pd}\p{Po}])`;
const RS_END = String
  .raw`(?=$|[\s\-.,:;!?\\/'")\]}>\p{Pe}\p{Pi}\p{Pf}\p{Pd}\p{Po}])`;
const RS_TICK = String.raw`\x60(?![\s\x60])(?:\\[\s\S]|[^\x60\\])*?(?<!\s)\x60`;
const RS_ROLE = String.raw`:[A-Za-z0-9]+(?:[\-_.+:][A-Za-z0-9]+)*:`;
const rsMarkup = (name, source) => `(?<${name}>${RS_START}${source}${RS_END})`;

/* The leftmost match wins; at one position the first alternative does. */
const RS_INLINE = new RegExp(
  [
    String.raw`(?<esc>\\[\s\S])`,
    String
      .raw`(?<fld>(?<=(?:^|\n)[ \t]*):(?![\s:])(?:\\.|[^:\n\\\x60])*?(?<!\s):(?=\s|$))`,
    rsMarkup("lit", String.raw`\x60\x60(?!\s)[\s\S]*?(?<!\s)\x60\x60`),
    rsMarkup("roleL", RS_ROLE + RS_TICK),
    rsMarkup("roleR", RS_TICK + RS_ROLE),
    rsMarkup("ref", RS_TICK + "__?"),
    rsMarkup("interp", RS_TICK),
    rsMarkup("note", String.raw`\[(?:#[\w.\-]*|\*|\d+|[A-Za-z][\w.\-]*)\]__?`),
    rsMarkup("sub", String.raw`\|(?![\s|])[^|\n]*?(?<!\s)\|(?:__?)?`),
    rsMarkup("strong", String.raw`\*\*(?![\s*])[\s\S]*?(?<!\s)\*\*`),
    rsMarkup("emph", String.raw`\*(?![\s*])(?:\\[\s\S]|[^*\\])*?(?<!\s)\*`),
    rsMarkup("name", String.raw`[A-Za-z0-9](?:\w|[\-.+:](?=\w))*(?<!_)__?`),
  ].join("|"),
  "gu",
);
const RS_KIND = {
  fld: "attr",
  lit: "str",
  ref: "link",
  interp: "var",
  note: "link",
  sub: "link",
  strong: "strong",
  emph: "emph",
  name: "link",
};

/* A role and its interpreted text are two tokens in Pygments, and here. */
function rsInline(text) {
  let out = "", last = 0;
  for (const m of text.matchAll(RS_INLINE)) {
    const kind = Object.keys(m.groups).find((g) => m.groups[g] !== undefined);
    if (kind === "esc") continue;
    const token = m[0];
    out += esc(text.slice(last, m.index));
    if (kind === "roleL") {
      const cut = token.indexOf("\x60");
      out += rsSpan(token.slice(0, cut), "attr") +
        rsSpan(token.slice(cut), "var");
    } else if (kind === "roleR") {
      const cut = token.lastIndexOf("\x60") + 1;
      out += rsSpan(token.slice(0, cut), "var") +
        rsSpan(token.slice(cut), "attr");
    } else out += rsSpan(token, RS_KIND[kind]);
    last = m.index + token.length;
  }
  return out + esc(text.slice(last));
}

/* `highlight(code, lang)` colours a code-block directive's body; it is passed
   in rather than imported so that this module does not import syntax.js. */
export function rstSource(text, highlight) {
  const lines = text.match(/[^\n]*\n|[^\n]+$/g) || [];
  /* The lines from `from` indented deeper than `indent`, without the blank
     lines that trail them. */
  const blockEnd = (from, indent) => {
    let j = from;
    while (
      j < lines.length && (rsBlank(lines[j]) || rsIndent(lines[j]) > indent)
    ) j++;
    while (j > from && rsBlank(lines[j - 1])) j--;
    return j;
  };
  let out = "", literal = -1;
  for (let i = 0; i < lines.length;) {
    const line = lines[i];
    if (rsBlank(line)) {
      out += esc(line);
      i++;
      continue;
    }
    const indent = rsIndent(line);
    /* The indented block after a paragraph that ends in "::". */
    if (literal >= 0) {
      const base = literal;
      literal = -1;
      if (indent > base) {
        const end = blockEnd(i, base);
        out += rsSpan(lines.slice(i, end).join(""), "str");
        i = end;
        continue;
      }
    }
    if (/^[ \t]*\.\.(?=\s|$)/.test(line)) {
      const end = blockEnd(i + 1, indent);
      const body = lines.slice(i + 1, end).join("");
      const directive = /^([ \t]*\.\.[ \t]+)(\w[\w:+.\-]*?)(::)(?=\s|$)(.*\n?)$/
        .exec(line);
      const target =
        /^([ \t]*\.\.[ \t]+)(__?(?:\\.|[^:\n\\])*:|\[[^\]\n]+\]|\|[^|\n]+\|)(?=\s|$)(.*\n?)$/
          .exec(line);
      if (directive) {
        const [, lead, name, colons, rest] = directive;
        const lang = rest.trim();
        out += esc(lead) + rsSpan(name, "kw") + esc(colons) + rsInline(rest) +
          (/^(?:code|code-block|sourcecode)$/.test(name) && lang
            ? highlight(body, lang)
            : rstSource(body, highlight));
      } else if (target) {
        out += esc(target[1]) + rsSpan(target[2], "link") + esc(target[3]) +
          esc(body);
      } else out += rsSpan(line + body, "com");
      i = end;
      continue;
    }
    const next = lines[i + 1] || "";
    if (
      RS_ADORN.test(line) && lines[i + 2]?.trim() === line.trim() &&
      !rsBlank(next) && !RS_ADORN.test(next)
    ) {
      out += rsSpan(line + next + lines[i + 2], "heading");
      i += 3;
      continue;
    }
    if (
      !indent && !RS_ADORN.test(line) && RS_ADORN.test(next) &&
      next.trim().length >= Math.min(line.trim().length, 4)
    ) {
      out += rsSpan(line + next, "heading");
      i += 2;
      continue;
    }
    let end = i;
    while (end < lines.length && !rsBlank(lines[end])) end++;
    const paragraph = lines.slice(i, end).join("");
    out += rsInline(paragraph);
    if (/::\s*$/.test(paragraph)) literal = indent;
    i = end;
  }
  return out;
}
