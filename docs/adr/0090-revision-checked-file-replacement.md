# ADR 0090: Revision-checked file replacement

Date: 2026-10-20

## Context

The [save-safety task] addresses architecture review A4. A direct write can
truncate the old file before a disk error. A draft can also overwrite a file
that another writer changed after the editor read it.

## Decision

The [filesystem port] returns an opaque `revision` on each editable Blob.
`write(node, text, expected)` checks that revision. The editor pins the revision
of its draft, even if another preview reads the node later. Document wrappers
pass it through. Checkbox changes read a fresh snapshot and use its revision.
A conflict rejects the write and keeps the editor text. Explicit navigation
still discards the draft, as specified by [the editor task].

The HTTP port requests `/api/raw?snapshot=1` and receives an ETag with a
bounded snapshot from the same open file. Ordinary raw downloads keep
FileResponse streaming and Range support. The revision is a SHA-256 content
hash, independent of filesystem timestamps. Save requires `If-Match`; no
revision returns 428,
and a different revision returns 409. Origin, host and mutation-token checks
still run before the server reads the body. The handler stops receiving when
the body exceeds 8 MiB. A worker thread runs the blocking save.

Server saves share a process lock. The server writes a temporary file in the
same directory, flushes it, calls `fsync`, checks the revision again, then
renames it over the target. A write, flush, metadata or rename failure before
the rename leaves the old bytes intact. Temporary files are removed on failure.
The rename is the commit point. The directory is not fsynced; this does not
promise persistence of the rename after power loss.

Server replacement has these filesystem rules:

- **Symlinks:** follow the target authorized by the root resolver. Keep the
  symlink and replace its target's directory entry.
- **Hard links:** replace only the selected directory entry. Other links keep
  the old inode and old bytes.
- **Ownership:** preserve the original owner and group. If the process cannot
  set them on the temporary file, fail before replacement.
- **Permissions:** require write access to the old file and preserve its mode
  bits. Replacement also needs write access to its directory. ACLs and extended
  attributes are not copied to the new inode.

The browser-owned adapter hashes the read bytes with SHA-256. It reads the
current file again after permission approval and before opening a write stream.
It checks again after writing and before closing. It explicitly aborts the
stream after a write, close or conflict failure. Equal size and modification
time do not hide changed content.

The native bridge returns bytes and a stat revision from the same descriptor.
It rejects a changed or missing revision with `ESTALE`. It rechecks the named
entry before its existing GLib consistent, durable replacement. Native paths
still reject symlinks. GLib replacement leaves other hard links on the old
inode and preserves mode bits. Ownership, ACLs and other metadata follow
[GLib's replacement contract], which does not guarantee their preservation.
This differs from the server's explicit owner-preservation requirement.

## Limits

Unrelated programs do not use Filemill's lock. POSIX rename and the browser
picker API have no atomic compare-and-swap operation for these files. A writer
can still race the final revision check and commit. Native stat revisions assume ordinary local filesystem timestamp behavior.
Server and browser hashes identify content, so rewriting the same bytes is not
a conflict.

The server lock covers one process. Run one server worker. A multi-worker
configuration needs a shared save lock before it can offer the same guarantee.
These revisions protect ordinary stale drafts; they do not provide database
transactions against arbitrary external writers.

## Validation

Regressions cover partial temporary writes, failed fsync and rename, external
changes during flush, concurrent saves, missing and stale revisions, streamed
body limits, worker-thread execution, symlinks, hard links, owner/group/mode
preservation and metadata failure. Browser checks cover same-size external
changes, stream abort and draft retention through a document wrapper. Native
contract checks cover stale writes. [A4 validation] records the suite results
and the unchanged-main history failure that blocks the full-suite gate.

[save-safety task]: ../tasks/133-protect-saves-from-truncation-and-stale-overwrites-architecture-review.md
[filesystem port]: ../../server/src/filemill/ui/core/ports.js
[the editor task]: ../tasks/28-editor-features.md

[GLib's replacement contract]: https://docs.gtk.org/glib/func.file_set_contents_full.html

[A4 validation]: ../ARCHITECTURE-REVIEW.md#a4-saves-can-truncate-or-overwrite-newer-content
