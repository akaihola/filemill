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
- [ ] `<file>.md?f#<slug>` opens the file and scrolls its preview to the heading whose
      GitHub slug is `<slug>` (lowercase, punctuation dropped, spaces as hyphens), so
      one anchor works on both GitHub and Filemill. Where markdown-it-anchor's id
      differs, such as for "Q1: scope", both forms work.
- [ ] A heading that doesn't exist falls back to the whole file, not to an error page.
- [ ] Browser tests cover a fresh load of both forms.

## Implementation plan (2026-10-19)

1. Test section URLs through the resource route and fresh browser loads.
   The current `api.split_vfs` already accepts document sections. Keep its
   containment checks and use regression tests to preserve this behavior.
2. Keep existing heading IDs. Add GitHub fragment aliases during Markdown
   rendering. Resolve fragments after the asynchronous preview is ready.
   Scroll only the preview body, so the column layout does not move.
3. Test missing headings, punctuation, duplicate headings, and both fragment
   forms. Run the local quality gate and the affected browser suites.
4. Merge into main. Move the canonical issue to Completed / Accepted with
   user acceptance unchecked.

## Implementation and validation (2026-10-19)

The current source already serves document section URLs through `api.split_vfs`.
Nine new HTTP cases preserve this behavior for Markdown and reStructuredText.
Fresh browser loads also verify nested sections in both formats.

Markdown previews now accept GitHub fragments and existing renderer fragments.
They keep the whole file open and scroll only the preview body. Duplicate
headings receive numbered GitHub aliases. Unknown and malformed fragments keep
the file open. A missing section at any path depth now restores the whole file.

Red-green evidence: fragment scroll checks failed before the change. Nested
missing-section browser and model checks also failed before the model fix.
The final focused browser run passed all 12 cases, including punctuation,
Unicode, duplicate headings, both fragment forms, and missing headings.

Validation:

- Full server suite: 963 passed.
- Static bundle and development suites: 151 passed each. Each initial run also
  found two renderer-stub failures. Changing rule registration from `after`
  to the existing `push` API fixed both. Both tests passed on rerun in each mode.
- Shared model checks passed.
- The full pre-commit gate passed: Ruff, formatting, mypy, Deno formatting and
  lint, suppression-link checks, and the generated static bundle check.

[ADR 0085](../adr/0085-markdown-heading-fragments-scroll-the-preview.md) records
fragment routing and preview scrolling. Completion awaits user acceptance.

## Firefox follow-up (2026-10-19)

The user reported that Firefox 157 on NixOS scrolled only after a hard reload.
Normal address-bar navigation kept the preview at the top. Fresh Firefox 155
checks passed, including the original example links against the live server.

The running server advertised startup asset hashes that did not match its
updated UI files. A hard reload bypassed the old cached modules. Restarting the
local server refreshed the version URLs. The user then confirmed that all
example links scrolled correctly. The scrolling implementation did not change.

Fragment checks now run in Chromium and Firefox. Each case checks a fresh load,
a service-worker-controlled load, and a load with a warm cache. CI installs
Firefox for the server suite. README now states that a running server must
restart after UI updates.

Validation: 14 cross-browser fragment cases passed, 30 documentation and pytest
configuration checks passed, and the pre-commit gate passed.
