# Changelog

This file records all notable changes to Filemill.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Filemill uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Contribution, security, and release documents.

### Removed

- The `Access-Control-Allow-Origin: *` header on `/w/` named-mount responses.
  Other origins can no longer read files through the server.

## [0.1.0] - 2026-09-15

### Added

- A static, single-file edition that browses a local folder.
- A Python server edition with a local web interface.
- Miller-column navigation, previews, deep links, keyboard navigation, and PWA
  support.
- Previews for Markdown, DOCX, PPTX, PDF, images, plain text, and source code.
- SQLite and JSON virtual filesystem views.
