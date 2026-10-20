# ADR 0073: Git bundles browse by their refs and trees

Date: 2026-10-10.

## Context

A Git `.bundle` is a backup of a repository in one file: a header naming refs,
then a packfile. Tar and zip archives already open as columns of their members
([ADR 0072]); a bundle holds files too, but behind commits and trees that only
Git can read. There is no Python packfile reader in the standard library, and
writing one (delta chains, both delta kinds, SHA-1 and SHA-256) is more code
than this feature is worth while `git` is on every host that makes bundles.

## Decision

A `.bundle` opens as a column of its refs in the server edition, through
`providers/gitbundle.py`, and only when a `git` executable is on the path. The
first columns follow the ref names with `refs/` dropped: `heads` → `main`,
`tags` → `v1`, and `HEAD` when the bundle carries it. A ref is a folder of its
commit's tree, one level per column; a blob is a file member, so it previews
and serves through `/api/preview` and `/api/raw` with its virtual path as `v`,
exactly like an archive member. Submodule entries are not listed.

The refs come from the bundle's text header, which the provider reads itself:
a root listing asks every bundle whether it is non-empty, and that must cost a
header read, not a process and a copy of the pack. `git` reads the rest. At
the first tree listing the provider unbundles the file into a temporary bare
repository, then lists with `git ls-tree` and reads with `git cat-file`. The
eight-entry cache is keyed by path, size and mtime. Each tree or blob read
also holds the temporary-directory owner through its last Git call. Eviction
releases only the cache's ownership. The directory is removed after the last
active read releases it; nothing else is written. Concurrent reads can share
an owner. Every call runs with the user's Git configuration hidden and
prompting off, with the existing 60-second deadline.

Git execution failures and timeouts propagate to the existing provider error
path. A failed listing reports `denied`, rather than an empty successful tree.
Blob metadata uses `cat-file --batch-check` with NUL-delimited input. A missing
object remains a missing member; a command failure raises an error.

The work is bounded. A bundle over `BUNDLE_MAX` (512 MiB) is a plain file,
because unbundling copies the pack. A blob over `MEMBER_MAX` (16 MiB) is
listed and named but not read, the same contract as an archive member. A
broken bundle, an incremental one (its header names prerequisites, so its
objects are elsewhere) and any bundle on a host without `git` are plain
files.

## Consequences

The server edition shells out to `git`, as it already does to ripgrep for
search. The static edition does not open bundles. A ref level and a tree level
are told apart by the ref names, which Git keeps prefix-free, so a path is
never ambiguous. `clean_member_path` moves from the archive provider to
`vfs.py` so both providers refuse the same escaping names.

[ADR 0072]: 0072-archives-browse-by-their-members.md
