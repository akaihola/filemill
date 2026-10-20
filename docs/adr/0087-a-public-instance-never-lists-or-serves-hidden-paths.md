# ADR 0087: A public instance never lists or serves hidden paths

Date: 2026-10-20. Issue: [128].

## Context

The server lists every entry in a folder and leaves dotfiles to the client,
which hides them unless the user, or `?hidden=show`, asks for them. It serves
any path inside the root and its direct bookmark symlinks. On 2026-10-20 a
check of the demo instance, which publishes a root without a login, listed
hidden files with `?hidden=show` and served the whole `.git/` folder,
`.claude/`, `.serena/` and `.scratch/`. The server had no notion of a public
instance; one code path served private homes and the public site alike.

## Decision

`--public`, or `FILEMILL_PUBLIC` set to anything but empty, `0`, `false`, `no`
or `off`, starts a public instance. A misspelt value turns the mode on. No
command-line option turns off what the variable turned on. `--live` passes the
mode to the reloaded application through the variable, and direct ASGI loading
reads it at import.

A path is hidden when one of its components starts with `.`, `.` and `..`
included. A public instance never lists, previews, downloads or serves one:

- The path a request names is checked before resolution, stripped and
  unquoted first the way `api.rel_to_abs` and `paths.resolve_safe` treat it,
  so `%2egit`, or `.git` after leading whitespace, counts as `.git`. This
  covers the resource route, `/n/`, `/w/`, and the `p`, `v` and `vpath` values
  of the API, resource and `/n/` routes. A hidden name is refused even when it
  leads to a visible path, because answering would confirm that it exists.
- The path a request resolves to is checked too. `paths.public_zones` drops a
  bookmark whose name or any component of whose target path is hidden. The
  root's own path is the operator's choice and is not checked, but a bookmark
  named like the root, which replaces the root's zone, gets no exemption. The
  resolved path must lie in a remaining zone under no hidden name there, so a
  symlink into `.git/` is refused like a symlink out of the root. A root below
  a bookmark's hidden folder still serves its own files.
- A listing keeps only the entries the instance would serve, so a symlink into
  a hidden folder is not listed, and its `abs` field cannot reveal the target.
  An archive or bundle listing drops members with a hidden virtual path. Names
  on disk and member paths are checked as they are, not unquoted.
- A folder's `index.html` that the instance would not serve counts as absent:
  the folder opens the shell, whether or not the index's target exists.
- Search answers 404 for a hidden focus folder and drops matches the instance
  would not serve, whatever a ripgrep configuration file says. A configuration
  that searches hidden files can still fill the 100-match limit with matches
  that are then dropped.
- The shell ignores `?hidden=show`.

Every other refusal is the same 404 as a path outside the root. Save and delete
check authorization first, as [ADR 0081] requires, then refuse a hidden path
with 404.

Private instances are unchanged.

## Consequences

A public instance cannot serve `/.well-known/`, a site's `.htaccess`, or a
bookmark into a folder such as `~/.config`. A reverse proxy has to answer
`/.well-known/` itself.

The rule errs towards refusing. Under a root below a hidden folder, a bookmark
into the root has a hidden component in its target path, so `/w/<bookmark>/`
answers 404 even where the resource route serves the same file through the
root. A member whose
name starts with `%2e` or with whitespace before a dot is listed, but a request
for it is refused.

An archive or Git bundle is still downloadable whole, members included, so
hiding its hidden members is consistency, not protection. The same holds for a
JSON key or Markdown heading that starts with `.`: the virtual path is refused,
but the file's bytes are served.

The mode does not hide visible paths. Listings still carry each entry's absolute
path in `abs`, the shell carries the root's in `data-absolute`, and a visible
folder that holds hidden files can still be deleted by an authorized client.
Bundled assets under `/ui/` and `/icons/` are the application's own files and
are not checked.

[ADR 0081]: 0081-authorize-server-mutations.md
[128]: ../tasks/128-never-list-or-serve-hidden-files-on-a-public-instance.md
