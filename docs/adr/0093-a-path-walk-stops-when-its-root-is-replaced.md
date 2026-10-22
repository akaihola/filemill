# ADR 0093: A path walk stops when its root is replaced

Date: 2026-10-22. Issue: [153].

Status: Accepted

## Context

`applyPath` walks a link, a refresh or a remembered folder down from the root
and awaits a read at each folder ([ADR 0057]). A mount replaces the root; the
server build's local-folder mode also replaces the filesystem port. A walk
released after such a mount appended its old folders to the new root, moved
focus, read the next folder through the new port and wrote its old location to
the URL. Its boolean URL guard also held back the new root's own URL until the
stale walk ended.

## Decision

A walk owns the root it started from. After each read it checks that this root
is still mounted. If not, it returns `false` and changes no path, selection or
focus; it also skips its final render and scroll. It reads through the
filesystem port it captured when it started. The URL guard holds the root being
walked, so it suppresses URL writes only while that root is mounted, and only
the walk that set it clears it.

## Consequences

The new root's state and URL belong to the mount that installed it. A caller
sees an abandoned walk as an incomplete one. Walks on one root still share
global state across awaits; choose and refresh keep their own sequence guards.
General navigation and preview ownership remain architecture finding A9.

[153]: ../tasks/153-stop-a-deep-link-walk-when-its-root-is-replaced-architecture-review-a9.md
[ADR 0057]: 0057-applypath-restores-refresh-links-and-remembered-folders-alike.md
