# 92. Shared content search capability

Date: 2026-10-22

Status: Accepted

## Context

[ADR 0091] temporarily disabled search for browser-owned roots. [The task]
requires the same search control and interactions for both sources. The static
edition must also keep granted file contents in the browser.

## Decision

The optional filesystem capability `search(root, query, focused, signal)`
returns `{matches, partial?}`. Each match has a root-relative `path`, one-based
`line` and plain-text `context`. The mounted root binds the capability. The
shared UI owns input, a 250 ms debounce, messages, escaped result buttons and
path sorting. It accepts one trimmed literal, case-sensitive line of at most
200 UTF-16 code units. Each file contributes its first matching line, with a
240-character context. Enter, Space and pointer activation use shared path
navigation; router writes are optional.

Input changes abort the previous search immediately, before the next debounce.
Every mount clears the timer, query and results and aborts the old controller.
Late success/error responses and detached result buttons cannot act after
invalidation. An empty query cancels and hides results. Pending work shows
“Searching…”, an empty result shows “No matches”, and failures show “Search
error”. A filesystem without the capability hides the control.

HTTP owns the search endpoint. Its server operation feeds bounded file
snapshots to ripgrep. FSA visits only the selected handle and descendants;
it does not upload bytes or call the search endpoint. Both scan real files,
skip hidden entries, `node_modules`, `__pycache__` and NUL-containing binary
files, and decode UTF-8 with replacement. Ignore files do not affect search.
An explicitly focused hidden folder can be searched in private mode. Virtual
containers and document sections are outside content search. Server
traversal skips symlinks; a directly focused server bookmark remains governed
by the existing path policy. Browser handles expose no symlink traversal API.

## Bounds and cancellation

Both implementations cap traversal at 2,000 entries, recursion at 32 levels
below the focused folder, each snapshot at 1 MiB, total snapshots at 16 MiB and
results at 100 files. Limits include skipped entries. FSA also counts entries
used to resolve the focused path. Oversized files are skipped before reading.
Reads are sequential. Reaching a limit or skipping an oversized file sets
`partial`, displayed as “Partial results — search limit reached”, including
when no matches have been found. Result subsets at a limit can differ with
filesystem enumeration order. Focus a narrower folder to reduce work.

Each operation has a ten-second deadline. FSA races pending handle reads
against cancellation and the deadline. Browser APIs cannot cancel an already
issued OS read; its late settlement starts no further traversal. A timeout or
permission failure reports an error rather than claiming complete results.
HTTP abort prevents stale UI updates; it does not stop an already running
server operation. The server deadline bounds that remaining work. Ripgrep
receives at most one 1 MiB snapshot per process, so captured output is bounded
before result truncation. This uses a process per text file; revisit batching
if measured workloads fail the deadline within these byte/entry bounds.

## Validation

Browser regressions cover equivalent fixtures in both modes, literal queries,
first-line context, focused-folder scope, Enter and Space, empty/error states,
partial results and local requests staying off the server search endpoint.
Controlled reads cover delayed local success and failure across query changes,
local root changes and return to served mode. Existing controlled server
responses cover the reverse transition. Capability checks exercise entry,
byte, depth and match limits. Static checks exercise result activation in the
bundle and development editions. The task record contains commands, observed
counts and resource measurements; these bounds are policy, not a throughput
benchmark.

[ADR 0091]: 0091-server-search-stops-at-local-folder-mounts.md
[The task]: ../tasks/130-give-served-and-browser-owned-folders-the-same-content-search.md
