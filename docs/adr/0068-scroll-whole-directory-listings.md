# ADR 0068: Scroll whole directory listings

Date: 2026-09-26.

## Context

`/api/dir` sliced listings at 500 entries and the column showed a
`< Page N of NN >` control. Only page one was ever loaded unless the user
paged, so a deep link, a refresh, sort and type-ahead could not reach later
entries (A6 in `docs/ARCHITECTURE-REVIEW.md`). The server already enumerated,
stat()ed and sorted the whole directory for every page, so paging bounded the
response, not the work. The shared UI already virtualises a column of 1 000 or
more rows: it positions rows absolutely in a layer of the full height and
creates only the rows near the viewport.

## Decision

`/api/dir` returns every entry in one response and takes no `page` parameter.
The column has one vertical scrollbar. No pager exists. Virtualisation stays in
`ui/core/render.js`; no third-party list library is added. The existing one is
a few dozen lines, already serves keyboard navigation, type-ahead and deep
links, and the static edition inlines every module into one file.

## Consequences

Every entry is addressable: a deep link or refresh restores any entry, and sort
and type-ahead see the whole directory. A very large directory costs one larger
JSON response instead of several requests that each listed the whole directory.
A row's vertical position is arithmetic, so the row pitch must match the
stylesheet's `--row-h` and `--row-gap` at every density.
