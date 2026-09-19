# `.py.j2` highlighting

## Original request

`.py.j2` are templates for Python files that are rendered by Jinja2. Does our
highlighting library support syntax highlighting for such hybrid files? If so,
implement that. If not, consider alternatives and write a report.

## Finding on 2026-09-14

This report from `21fd4db` predates removal of the server's Pygments path and
relocation of the shared UI to `ui/`. Paths and commands below record the
original investigation. The separate scheduled task "Treat `.py.j2` as Python"
in [TASKS.md](../../TASKS.md) selects the Python-only fallback, not a hybrid lexer.

At the time of the investigation, Filemill did not support hybrid `.py.j2` highlighting.

The shared browser highlighter in `server/src/filemill/ui/core/syntax.js` selects a language from the final filename suffix. `x.py.j2` therefore resolves to `j2`, which is unknown and falls back to escaped plain text. The same source is used by the static build.

The server's Pygments path also does not provide this support. With the pinned Pygments 2.19.2, `get_lexer_for_filename()` selects `PythonLexer` for `x.py`, but raises `ClassNotFound` for both `x.j2` and `x.py.j2`. Pygments' `jinja` alias selects `DjangoLexer`, which is not a Python/Jinja hybrid lexer.

## Alternatives

1. Add a small browser tokenizer that recognizes Jinja delimiters and applies the existing Python rules to the remaining text. This keeps the current architecture and bundle, but only gives partial correctness. Nested or complex Jinja expressions can be misclassified.
2. Add a maintained Jinja/Python lexer and integrate it into the browser path and any server fallback. This gives better language coverage, but adds dependency, bundle, and maintenance cost. The current architecture intentionally avoids a third-party browser highlighter.
3. Treat `.py.j2` as Python. This is the smallest fallback and keeps Python code readable, but Jinja directives and expressions receive Python-only coloring.

## Recommendation

Keep `.py.j2` as plain text until partial highlighting is an explicitly accepted product behavior. If useful partial highlighting is required, implement option 3 in the shared suffix classifier and add browser coverage for `.py.j2`; do not add speculative lexer infrastructure.

Focused validation completed:

- `deno check src/filemill/ui/core/syntax.js`
- Pygments filename probes for `x.py`, `x.j2`, and `x.py.j2`
- Pygments alias probes for `jinja`, `jinja2`, `python`, and `py`
