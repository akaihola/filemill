# 88. Remove named-mount and alternate-shell routes

Date: 2026-10-20

Status: Accepted

## Context

Task [35](../tasks/35-decide-web-mounts.md) kept `/w/` for same-origin links
and removed its CORS middleware. That decision was implemented. Later, task
[42](../tasks/42-tilde-link-mount-prefix.md) changed the last UI consumer to
root-relative links. `/n/` remained an alternate shell base, while ordinary
resource URLs already served the same shell with `?filemill=render`.

The user approved removal of both aliases on 2026-10-20 in
[129](../tasks/129-remove-the-obsolete-w-and-n-url-routes.md). Old links do
not need compatibility support. Alias routes hide real folders with those
names and give one file several addresses.

## Decision

Delete both route handlers and the named-mount resolution helpers. Use the
resource route for every `w` and `n` path. Do not redirect old aliases or deny
these prefixes. A missing real path returns 404, even if an old alias would
have resolved it. The path router reads and writes root-relative file URLs. A JSON file opened
as a column keeps its render query, so a reload returns the shell rather than
raw JSON. Virtual JSON containers retain their member URLs.

Keep `resolve_safe`, direct-root symlink bookmark zones, public-mode checks
and directory-index containment. These rules apply equally to `w`, `n` and
other resource paths. A bare file serves bytes; `?f`, `?filemill=render` and
`?filemill=highlight` select the shell. Directories follow the existing index
rule: a bare directory serves its index, if present, and a query opens Filemill.

## Collision matrix

This is the boundary shared with question 6 and
[121](../tasks/121-clarify-api-path-collisions-from-docs-question-6.md).
That issue still needs a transport design decision. This change does not
reserve new paths or change internal request dispatch.

| Request | Result now |
| --- | --- |
| `/w`, `/n`, and their children | Normal resource routing, including real files, folders and bookmarks |
| Old `/w/<root-name>/file` or `/n/file` without that real path | 404; no compatibility redirect |
| `/api/dir`, `/api/raw`, other registered API endpoints | API handler takes priority |
| `/api/note.txt` without a matching endpoint | Normal resource routing |
| `/ui/<path>`, `/icons/<name>` | Registered asset handler takes priority |
| `/sw.js`, `/manifest.json` | PWA handler takes priority |

## Validation

Route tests first failed for both real folders, missing old aliases and
bookmarks. They now cover bare and rendered files, folder indexes, directory
shells, missing paths and bookmark escapes. Existing virtual-file, public-mode,
PWA and browser checks use root-relative URLs. The static build is checked
against the shared sources; it does not include the server path router.
