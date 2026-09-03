/* ═══════════════════════════════════════════════════════════════════════════
   Syntax highlighting — in the browser, so one copy serves both builds.

   The Python side can already colour source with Pygments, and does for its
   own pages. The shared UI deliberately does not use it: a preview that is
   coloured only when a Python process is behind it would have to be written
   twice — once here for the single file, once there for the served page.
   Colouring the text in the browser instead means both builds run *this*
   file, and a folder reached through "Open local folder…" is coloured on the
   server build too, though the server has never seen a byte of it.

   This is not a parser. Four token classes — comment, string, number, keyword
   — one regular expression per language, and the leftmost match wins, which is
   what keeps a `#` inside a string out of the comment class with no state to
   carry from one token to the next. That is enough to read a file by and well
   short of a language front end: what it gets wrong is mis-coloured, never
   mangled, because every character of the input is escaped and emitted exactly
   once — see hlHTML.

   A language is one line in HL_LANGS. An extension that is not listed previews
   as plain text, the way every file did before this existed. Markdown, SVG and
   HTML are absent on purpose: the pane has something better than source for
   them already.
   ═══════════════════════════════════════════════════════════════════════════ */

/* Written as plain strings rather than literals because they are assembled:
   a regex literal cannot be pasted into another one without going through its
   .source anyway, and doubling the backslashes once here is the smaller cost. */
const HL_NUM = "\\b(?:0[xXbBoO][0-9a-fA-F_]+|\\d[\\d_]*(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)\\b";

/* A quoted run ends at the first unescaped quote of the same kind; `\\[\\s\\S]`
   rather than `\\.` so a backslash before a newline does not end the string. */
const HL_STR    = "\"(?:\\\\[\\s\\S]|[^\"\\\\])*\"|'(?:\\\\[\\s\\S]|[^'\\\\])*'";
const HL_TICK   = "`(?:\\\\[\\s\\S]|[^`\\\\])*`|" + HL_STR;   /* + JS template */
const HL_TRIPLE = "\"\"\"[\\s\\S]*?\"\"\"|'''[\\s\\S]*?'''|" + HL_STR;   /* + Python */

const HL_SLASH = "//[^\\n]*|/\\*[\\s\\S]*?\\*/";
const HL_HASH  = "#[^\\n]*";
const HL_DASH  = "--[^\\n]*";
const HL_BLOCK = "/\\*[\\s\\S]*?\\*/";

const hlWords = s => "\\b(?:" + s.trim().split(/\s+/).join("|") + ")\\b";

const K_JS = `as async await break case catch class const continue debugger default delete do
  else export extends false finally for from function if import in instanceof let new null of
  return static super switch this throw true try typeof undefined var void while with yield`;
const K_TS = K_JS + ` abstract declare enum implements interface is keyof namespace never
  private protected public readonly type unknown satisfies`;
const K_PY = `and as assert async await break class continue def del elif else except False
  finally for from global if import in is lambda None nonlocal not or pass raise return self
  True try while with yield`;
const K_C = `auto break bool case char const continue default do double else enum extern false
  float for goto if inline int long NULL register return short signed sizeof static struct
  switch true typedef union unsigned void volatile while`;
const K_CPP = K_C + ` catch class constexpr delete explicit friend mutable namespace new
  noexcept nullptr operator override private protected public template this throw try typename
  using virtual`;
const K_SQL = `add all alter and as asc begin between by case check column commit constraint
  count create cross default delete desc distinct drop else end exists foreign from full group
  having in index inner insert into is join key left like limit max min not null offset on or
  order outer primary references returning right rollback select set sum table then transaction
  union unique update values view when where with`;

/* One entry per language; `k` is a finished pattern so that a language whose
   keywords are not words — a TeX macro, a CSS at-rule, an XML tag — can say so
   without a second mechanism. `n: false` turns the number class off. */
const HL_SPECS = {
  js:    { c: HL_SLASH, s: HL_TICK,   k: hlWords(K_JS) },
  ts:    { c: HL_SLASH, s: HL_TICK,   k: hlWords(K_TS) },
  py:    { c: HL_HASH,  s: HL_TRIPLE, k: hlWords(K_PY) },
  c:     { c: HL_SLASH, s: HL_STR,    k: hlWords(K_C) },
  cpp:   { c: HL_SLASH, s: HL_STR,    k: hlWords(K_CPP) },
  cs:    { c: HL_SLASH, s: HL_STR,    k: hlWords(K_CPP + ` base checked decimal event foreach
           get in interface internal is lock object out params readonly ref sealed set string
           unchecked unsafe var where yield`) },
  java:  { c: HL_SLASH, s: HL_STR,    k: hlWords(K_C + ` abstract assert catch class extends
           final finally implements import instanceof interface native new package private
           protected public super synchronized this throw throws transient try var`) },
  kt:    { c: HL_SLASH, s: HL_STR,    k: hlWords(`as break by class companion const continue
           data do else enum false for fun if import in infix init inline interface internal is
           lateinit null object open operator out override package private protected public
           reified return sealed super suspend this throw true try typealias val var vararg when
           where while`) },
  go:    { c: HL_SLASH, s: HL_TICK,   k: hlWords(`break case chan const continue default defer
           else fallthrough false for func go goto if import interface map nil package range
           return select struct switch true type var`) },
  rs:    { c: HL_SLASH, s: HL_STR,    k: hlWords(`as async await break const continue crate dyn
           else enum extern false fn for if impl in let loop match mod move mut pub ref return
           self Self static struct super trait true type unsafe use where while`) },
  swift: { c: HL_SLASH, s: HL_STR,    k: hlWords(`as associatedtype async await break case catch
           class continue default defer deinit do else enum extension fallthrough false
           fileprivate final for func guard if import in init internal is lazy let mutating nil
           open operator private protocol public repeat rethrows return self Self static struct
           subscript super switch throw throws true try typealias var weak where while`) },
  php:   { c: HL_SLASH + "|" + HL_HASH, s: HL_STR, k: hlWords(`abstract and array as break case
           catch class clone const continue declare default do echo else elseif empty enum
           extends false final finally fn for foreach function global if implements include
           instanceof interface isset list match namespace new null or print private protected
           public readonly require return static switch throw trait true try unset use var
           while yield`) },
  rb:    { c: HL_HASH,  s: HL_STR,    k: hlWords(`alias and begin break case class def defined
           do else elsif end ensure false for if in module next nil not or redo require rescue
           retry return self super then true undef unless until when while yield`) },
  pl:    { c: HL_HASH,  s: HL_STR,    k: hlWords(`and bless defined do else elsif eq foreach ge
           gt if last le local lt my ne next no not or our package print qw redo ref require
           return sub undef unless until use while`) },
  sh:    { c: HL_HASH,  s: HL_STR,    k: hlWords(`alias break case cd continue declare do done
           elif else esac eval exec exit export fi for function if in local read readonly return
           select set shift source then trap unset until while`) },
  lua:   { c: "--\\[\\[[\\s\\S]*?\\]\\]|" + HL_DASH, s: HL_STR, k: hlWords(`and break do else
           elseif end false for function goto if in local nil not or repeat return then true
           until while`) },
  r:     { c: HL_HASH,  s: HL_STR,    k: hlWords(`break else FALSE for function if in Inf NA
           NaN next NULL repeat return TRUE while`) },
  sql:   { c: HL_DASH + "|" + HL_BLOCK, s: HL_STR, k: hlWords(K_SQL), i: true },
  nix:   { c: HL_HASH + "|" + HL_BLOCK, s: HL_TRIPLE, k: hlWords(`assert builtins else false if
           import in inherit let null or rec then true with`) },
  json:  { c: HL_SLASH, s: HL_STR,    k: hlWords("true false null") },
  yaml:  { c: HL_HASH,  s: HL_STR,    k: hlWords("true false null yes no on off") },
  toml:  { c: HL_HASH,  s: HL_TRIPLE, k: hlWords("true false") },
  ini:   { c: HL_HASH + "|;[^\\n]*", s: HL_STR, k: hlWords("true false yes no on off") },
  css:   { c: HL_BLOCK, s: HL_STR,    k: "@[a-zA-Z-]+" },
  xml:   { c: "<!--[\\s\\S]*?-->", s: HL_STR, k: "</?[A-Za-z_][\\w.:-]*" },
  tex:   { c: "%[^\\n]*", n: false,   k: "\\\\[A-Za-z@]+" },
};

/* Extensions that are the same language under another name. */
const HL_ALIAS = {
  mjs: "js", cjs: "js", jsx: "js", tsx: "ts", h: "c", hpp: "cpp", cc: "cpp", cxx: "cpp",
  bash: "sh", zsh: "sh", fish: "sh", yml: "yaml", jsonc: "json", cfg: "ini", conf: "ini",
  scss: "css", less: "css", gitignore: "sh", env: "sh",
  /* what a Markdown fence calls the language, when that is not an extension */
  python: "py", javascript: "js", typescript: "ts", shell: "sh", rust: "rs", ruby: "rb",
};

/* Comment, then string, then number, then keyword. The order only settles ties
   at one position — `exec` takes the leftmost match either way, which is what
   puts a quote inside a comment in the comment and not in a string of its own. */
const HL_LANGS = Object.fromEntries(Object.entries(HL_SPECS).map(([key, sp]) => {
  const alts = [];
  if (sp.c) alts.push(`(?<com>${sp.c})`);
  if (sp.s) alts.push(`(?<str>${sp.s})`);
  if (sp.n !== false) alts.push(`(?<num>${HL_NUM})`);
  if (sp.k) alts.push(`(?<kw>${sp.k})`);
  return [key, new RegExp(alts.join("|"), sp.i ? "gi" : "g")];
}));

/* The language for a file name, or null for "no highlighting known". Starting
   at index 0 so a dotfile is its own extension: .gitignore is a shell-comment
   file and has nothing else to go on. */
function hlLang(name) {
  const i = name.lastIndexOf(".");
  if (i < 0) return null;
  const ext = name.slice(i + 1).toLowerCase();
  const key = HL_ALIAS[ext] || ext;
  return key in HL_LANGS ? key : null;
}

/* Escaped HTML for `text`, with the recognised tokens wrapped in spans. Every
   character reaches the output exactly once: the gap before a match is escaped
   and copied, the match itself is escaped inside its span, and the tail after
   the last match is escaped and copied. Nothing here interpolates unescaped
   input, which is what makes the output safe to assign to innerHTML. */
function hlHTML(text, key) {
  const re = HL_LANGS[key];
  let out = "", last = 0, m;
  re.lastIndex = 0;
  while ((m = re.exec(text)) !== null) {
    /* No alternative can match the empty string today; the guard is what keeps
       that from becoming an infinite loop if one ever does. */
    if (!m[0]) { re.lastIndex++; continue; }
    const cls = Object.keys(m.groups).find(g => m.groups[g] !== undefined);
    out += esc(text.slice(last, m.index)) + `<span class="hl-${cls}">${esc(m[0])}</span>`;
    last = re.lastIndex;
  }
  return out + esc(text.slice(last));
}

/* Colour the fenced code inside a rendered Markdown fragment. Both markdown-it
   and markdown-it-py emit <pre><code class="language-x"> with no highlighter
   configured, so this one function is what makes "fenced code is coloured" true
   in both builds. Only code nodes are touched: paragraphs and their soft line
   breaks stay exactly as the renderer left them. */
function hlFences(host) {
  for (const code of host.querySelectorAll('pre > code[class*="language-"]')) {
    const m = /(?:^|\s)language-(\S+)/.exec(code.className);
    const key = m && hlLang("x." + m[1]);
    if (key) code.innerHTML = hlHTML(code.textContent, key);
  }
}
