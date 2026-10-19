Filemill writes a section URL but cannot open it, and it ignores heading fragments. So nobody can link to a heading inside a Markdown file.

## Observed (2026-10-19, hopeli, `daf2bafe`)

For [link-paths-in-documents-written-for-reading-not-only-in-replies.md](http://hopeli/repos/nixos-config/docs/backlog/link-paths-in-documents-written-for-reading-not-only-in-replies.md?f):

1. Selecting its "Work" section changes the address to
   `…/link-paths-in-documents-written-for-reading-not-only-in-replies.md/Work?f=&filemill=render`.
2. Loading that address in a new tab returns HTTP 404 with the bare text "Not found".
   The server serves the app shell only for paths that exist on disk.
3. `…/link-paths-in-documents-written-for-reading-not-only-in-replies.md?f#work`
   opens the whole file at the top. markdown-it-anchor gives the heading `id="work"`,
   but nothing scrolls to it.

The README says a section can be previewed "and linked to alone", but such a link
works only within the current tab.

## Why

Antti asked agents to deep-link headings in Markdown files (steward, 2026-10-19).
The steward's writing guide has had to say "Filemill doesn't scroll to heading
fragments" since D67.

## Acceptance criteria

- [ ] A section address that Filemill writes (`<file>.md/<heading>/…?f…`) opens the
      same section preview when loaded fresh, in the server edition. Any path whose
      first missing segment comes after an existing `.md` or `.rst` file gets the app
      shell, not a 404.
- [ ] `<file>.md?f#<slug>` opens the file and scrolls its preview to the heading with
      that id (markdown-it-anchor's slug), so agents can write GitHub-style anchors.
- [ ] A heading that doesn't exist falls back to the whole file, not to an error page.
- [ ] Browser tests cover a fresh load of both forms.
