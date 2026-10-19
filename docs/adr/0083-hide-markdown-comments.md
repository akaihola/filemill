# ADR 0083: Hide Markdown comments

Date: 2026-10-19. Issue: [111].

## Context

The shared Markdown renderer disables raw HTML to keep previews inert. This
also escapes HTML comments, which makes private notes and tracker metadata
visible in rendered documents.

## Decision

Add inline and block comment rules to the existing markdown-it instance.
Consume comments without emitting HTML or changing the source. Keep raw HTML
disabled, as required by [ADR 0082](0082-previews-link-only-to-safe-protocols.md).
Do not remove comments from the source with a regular expression: that would
also change code examples and task checkbox source line numbers.

Block comments start at a block's first non-indented-code position. They end
after the line with the closing delimiter, or at the block's end if unclosed.
Inline comments end at the closing delimiter. Code and escaped delimiters
keep their normal Markdown meaning.

## Consequences

Both editions and all callers of the shared renderer hide comments. Source,
Raw and edits retain the original text. Other raw HTML stays escaped. No new
dependency is needed. Browser tests cover the bundle, shared modules and server.

[111]: ../tasks/111-renders-html-comments-in-markdown-documents.md
