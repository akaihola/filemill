# Changelog

This file records all notable changes to Filemill.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Filemill uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Contribution, security, and release documents.
- Browsing of `.jsonl` files over 512 KB. Rows are indexed by line and parsed
  one at a time when opened.
- Tar archives (plain, gzip, bzip2, xz, zstd) and zip files open as columns of
  their members in the server edition, and a member previews as the file it is.
- Git `.bundle` files open as columns of their refs and trees in the server
  edition when `git` is installed, and a blob previews as the file it is.

### Changed

- Large directories scroll in one virtualized column instead of paging.

### Removed

- The `Access-Control-Allow-Origin: *` header on `/w/` named-mount responses.
  Browser scripts on other origins cannot read those responses. Removing CORS
  headers did not prevent cross-origin writes.

### Fixed

- Implicit directory indexes now pass the same containment check as explicit
  file URLs, including nested symlinks and bookmark mounts.
- Save and delete now require matching Origin/Host and a per-process mutation
  token before reading request bodies. The shipped UI sends the token;
  FILEMILL_ORIGINS configures public reverse-proxy and LAN origins.

- Resizing remaps widened columns to the available fold-dial stops. Fractional
  column widths reach each stop with one fling instead of requiring an extra swipe.
- Back and Forward retrace the columns that were entered. Opening sibling
  folders with ↑/↓ or a click in the same column no longer adds a history entry
  per folder ([ADR 0050]).
- `Alt`+`←`/`→` and `⌘`+`←`/`→` reach the browser as Back and Forward instead of
  moving the finder's focus.
- Markdown and WebVTT previews show one Raw link. The per-type Rendered/Raw
  and Transcript/Raw groups duplicated the Raw link and the Source toggle.
- A Markdown or `.docx` member of an archive renders in the browser like the
  same file on disk, and a Markdown member opens as columns of its headings.
  The server had returned a member's coloured source ([ADR 0072]).
- Relative Markdown links in archive members and their heading sections open
  siblings inside the archive instead of unrelated files at the server root.
- JSON keys and CSV labels ending in `.md` or `.markdown` remain data values
  and records instead of advertising document heading columns.

### Security

- Previews no longer run markup or links from the files they show. Text beside
  a Markdown wikilink stays text. Links in `.docx`, reStructuredText and
  `.desktop` previews keep their targets only for `http:`, `https:`, `mailto:`
  or a scheme-less address ([ADR 0082]).
- An HTML member of an archive previews in a sandboxed iframe, as an HTML file
  on disk does. Its scripts had run with Filemill's origin.

## [0.1.0] - 2026-09-15

### Added

- A static, single-file edition that browses a local folder.
- A Python server edition with a local web interface.
- Miller-column navigation, previews, deep links, keyboard navigation, and PWA
  support.
- Previews for Markdown, DOCX, PPTX, PDF, images, plain text, and source code.
- SQLite and JSON virtual filesystem views.

[ADR 0050]: docs/adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
[ADR 0072]: docs/adr/0072-archives-browse-by-their-members.md
[ADR 0082]: docs/adr/0082-previews-link-only-to-safe-protocols.md
