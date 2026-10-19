# ADR 0078: Delete waits for active preview reads

Date: 2026-10-17. Issue: [97].

## Context

A preview reads bytes to render content and again to check editability. Delete
could remove the selected file between these reads. The later read returned
HTTP 404. Removing a folder could also race with a child preview. Preview
generation checks protect the DOM but do not protect the file during a read.

## Decision

Track active preview fills in the shared core by filesystem root and entry
path. After confirmation, mark the deletion path as pending. Block new fills
for that path and its children. Wait for existing fills under that path before
calling `FS.remove`. Keep the pending mark until refresh or error handling ends.

## Consequences

Both editions use the same ordering without a change to the filesystem port.
An active preview can delay deletion until its reads finish. Previews outside
the deletion path continue as before. Failed reads and failed deletion requests
remain visible to error checks. Preview caching and general cancellation remain
part of architecture finding A9.

[97]: ../tasks/97-fix-intermittent-preview-404-after-deleting-the-selected-file.md
