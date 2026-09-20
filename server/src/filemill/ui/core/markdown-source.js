import { esc } from "./icons.js";
import { markdownDestination, markdownHref } from "./markdown-links.js";

const mdSpan = (text, kind) => `<span class="hl-${kind}">${esc(text)}</span>`;
const mdReference = (label) => label.trim().replace(/\s+/g, " ").toUpperCase();

/* Find the end of a balanced label/destination without treating escaped
   punctuation as a delimiter. A broken link stays literal source. */
function mdClosing(text, start, open, close) {
  let depth = 1;
  for (let i = start + 1; i < text.length; i++) {
    if (text[i] === "\\") i++;
    else if (
      open === "(" &&
      ((text[i] === "<" && i === start + 1) ||
        ((text[i] === '"' || text[i] === "'") && /\s/.test(text[i - 1])))
    ) {
      const delimiter = text[i] === "<" ? ">" : text[i];
      while (++i < text.length) {
        if (text[i] === "\\") i++;
        else if (text[i] === delimiter) break;
      }
    } else if (text[i] === open) {
      // Bound malformed nesting as well as the work spent searching for an end.
      if (++depth > 32) return -1;
    } else if (text[i] === close && --depth === 0) return i;
  }
  return -1;
}

function mdTarget(text) {
  const match =
    /^(?:<([^<>\n]*)>|((?:\\.|[^\\\s])+?))(?:\s+(?:"[^"\n]*"|'[^'\n]*'|\([^\n]*\)))?\s*$/
      .exec(text.trim());
  return match ? markdownDestination(match[1] ?? match[2]) : null;
}

function mdInline(text, references, dir, links) {
  const tokens =
    /\\[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]|`+|!?\[|<[^<>\n]+>|(?:https?:\/\/|www\.)[^\s<>]+/g;
  let out = "", last = 0, match;
  while ((match = tokens.exec(text))) {
    let end = tokens.lastIndex, href = null, kind = null;
    const token = match[0];
    if (token[0] === "`") {
      const runs = /`+/g;
      runs.lastIndex = end;
      let close;
      while ((close = runs.exec(text))) {
        if (close[0] === token) {
          end = runs.lastIndex;
          kind = "str";
          break;
        }
      }
    } else if (token === "[" || token === "![") {
      const start = match.index + token.length - 1;
      const close = mdClosing(text, start, "[", "]");
      if (close >= 0) {
        const label = text.slice(start + 1, close);
        end = close + 1;
        if (text[end] === "(") {
          const finish = mdClosing(text, end, "(", ")");
          if (finish >= 0) {
            href = mdTarget(text.slice(end + 1, finish));
            end = finish + 1;
          }
        } else {
          const ref = /^\[([^\]\n]*)\]/.exec(text.slice(end));
          href = references.get(mdReference(ref?.[1] || label)) ?? null;
          if (ref) end += ref[0].length;
        }
        if (token === "![") href = null;
      }
    } else if (token[0] === "<") {
      const url = token.slice(1, -1);
      if (/^(?:https?:\/\/|mailto:)/i.test(url)) {
        href = markdownDestination(url);
      }
    } else if (token[0] !== "\\") {
      // Sentence punctuation is not part of a bare URL. Balanced URL brackets are.
      let url = token.replace(/[.,!?;:]+$/, "");
      for (const [open, close] of [["(", ")"], ["[", "]"]]) {
        while (
          url.endsWith(close) &&
          url.split(close).length > url.split(open).length
        ) {
          url = url.slice(0, -1);
        }
      }
      end = match.index + url.length;
      href = markdownDestination(
        url.startsWith("www.") ? "http://" + url : url,
      );
    }
    const raw = text.slice(match.index, end);
    out += esc(text.slice(last, match.index));
    const target = href === null ? null : markdownHref(href, dir);
    out += target !== null
      ? links
        ? `<a class="hl-link" href="${esc(target)}">${esc(raw)}</a>`
        : mdSpan(raw, "link")
      : kind
      ? mdSpan(raw, kind)
      : esc(raw);
    last = tokens.lastIndex = end;
  }
  return out + esc(text.slice(last));
}

export function markdownSource(text, node) {
  const lines = text.match(/[^\n]*\n|[^\n]+$/g) || [];
  const blocks = [], references = new Map();
  for (let i = 0; i < lines.length; i++) {
    let source = lines[i], kind = "text";
    const fence = /^ {0,3}(`{3,}|~{3,})([^\n]*)/.exec(source);
    if (fence && !(fence[1][0] === "`" && fence[2].includes("`"))) {
      const close = new RegExp(
        `^ {0,3}${fence[1][0]}{${fence[1].length},}\\s*$`,
      );
      while (++i < lines.length) {
        source += lines[i];
        if (close.test(lines[i])) break;
      }
      kind = "str";
    } else if (/^(?: {4}|\t)/.test(source)) kind = "str";
    else if (/^ {0,3}#{1,6}(?:\s|$)/.test(source)) kind = "heading";
    else if (source.trim() && /^ {0,3}(?:=+|-+)\s*$/.test(lines[i + 1] || "")) {
      source += lines[++i];
      kind = "heading";
    } else {
      const ref = /^ {0,3}\[([^\]\n]+)\]:\s*(.+)/.exec(source);
      if (ref) {
        const href = mdTarget(ref[2]);
        if (href !== null) {
          const key = mdReference(ref[1]);
          if (!references.has(key)) references.set(key, href);
          kind = "link";
        }
      }
    }
    if (kind === "text" && blocks.at(-1)?.kind === "text") {
      blocks.at(-1).source += source;
    } else blocks.push({ source, kind });
  }
  const dir = typeof node?.rel === "string"
    ? node.rel.replace(/\/?[^/]*$/, "")
    : undefined;
  return blocks.map(({ source, kind }) => {
    if (kind === "str" || kind === "link") return mdSpan(source, kind);
    const html = mdInline(source, references, dir, node !== undefined);
    return kind === "heading"
      ? `<span class="hl-heading">${html}</span>`
      : html;
  }).join("");
}
