# ADR 0067: Drop the no-columns layout

Date: 2026-09-25.

## Context

The URL contract in `server/src/filemill/urls.py` offered three layouts:
`full-columns`, `compressed-columns` and `no-columns`. `no-columns` existed so a
dashboard could embed a bare document at the file's own path. That embedding
was never built. No page, dashboard or site generator requests the value. After
the resource route began serving the shared shell for every non-raw view, the
layout survived only as client CSS and a `render.js` toggle. The Fullscreen
button already hides the bar, trail, status line and columns.

## Decision

Remove `no-columns`. The layout query accepts `full-columns` (default) and
`compressed-columns`. `?filemill=raw|render|highlight` is unchanged.

## Consequences

A stale `?layout=no-columns` link is an unrecognised value. It falls back to
`full-columns` and opens the normal finder on the same path; tests pin this.
Asking for a chrome-free document from the URL is no longer possible. If an
embedding need appears, add a layout value with a failing test and its users.
