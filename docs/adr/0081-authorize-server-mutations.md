# ADR 0081: Authorize server mutations

Date: 2026-10-19. Issue: [103].

## Context

Removing CORS headers prevents browser scripts on other origins from reading
responses. It does not prevent a simple POST from overwriting a file. Save
and delete previously accepted any caller that could reach the server.

## Decision

Updated 2026-10-21 for [the public and Host authorization repair][138].
Every route first passes shared Host middleware, including read, UI and PWA
routes. Exactly one valid Host is required. Loopback names are allowed;
otherwise its host and effective port must match a valid `FILEMILL_ORIGINS`
entry, using that entry's scheme so HTTPS proxies over HTTP backends work.
Forwarded headers and loopback peers grant no additional Host permission.
Rejected requests receive 403 before dispatch.

Public instances always refuse save and delete with 403 before reading a body
or resolving a path. Their shells omit the mutation token. The HTTP adapter
omits its optional write and remove capabilities, so the shared UI offers no
mutation controls for the served root. Locally opened folders keep their own
filesystem capabilities.

On private instances, before resolving a mutation path or consuming request
bytes, both endpoints require exactly one Origin, Host and X-Filemill-Token
header. Invalid requests
receive the same 403 response. The Origin must be an HTTP or HTTPS origin
without credentials, path, query or fragment. Its authority must match Host.
Default ports compare by their effective port.

Loopback hosts 127.0.0.1, localhost and [::1] are allowed when the origin scheme
matches the request scheme. Other origins must appear in the space-separated
FILEMILL_ORIGINS environment variable, for example:

```sh
FILEMILL_ORIGINS='https://files.example https://files.example:8443' filemill .
```

A reverse proxy must preserve the public Host. An explicit configured origin
may use HTTPS while the backend connection uses HTTP, without trusting
Forwarded or X-Forwarded-Host. Binding to a LAN address requires configuring
its browser origin too. Wildcards and the opaque Origin `null` are rejected.

Each server process generates a 256-bit random token at import. The server
puts it in data-mutation-token on its private UI shell, served with Cache-Control:
no-store. The HTTP filesystem adapter sends it in X-Filemill-Token on saves
and deletes. Raw documents and API read responses do not contain the token.
The adapter never puts it in a URL, cookie or browser persistent storage.
Restarting invalidates old tokens; clients must reload the shell. API clients must send
both an allowed Origin and the token obtained from the shell.

## Consequences

An unrelated page cannot read the token through the browser's same-origin
policy, and its simple POST is rejected before body consumption. Cross-origin
DELETE or token headers require preflight; no CORS permission is granted.
The shared Host allowlist rejects an arbitrary DNS name resolving to loopback
on reads and writes alike. Before upgrading, proxy and LAN operators must set
`FILEMILL_ORIGINS` for every deployed browser origin.

This is browser request authorization, not user authentication. A network
client can fetch a private shell and authorize writes. Trusted same-origin HTML
can also fetch the shell and obtain its token. Serve only trusted root HTML;
use separate origins or authenticated access control for untrusted content
and networks. A2's preview injection fix remains separate.

The existing service worker can cache shell responses despite no-store.
Cache policy remediation remains A5. A stale shell after a server restart
fails closed until refreshed from the network. Saves remain non-atomic and
without conflict checks until A4.

## File response audit

The implicit directory index is resolved against the same request zones as
its explicit URL before FileResponse. Nested escapes are denied; direct-root
bookmark links remain allowed. Resource raw responses, /api/raw, /api/preview
and /w/ already resolve their real file before reading it. Archive and bundle
members use provider virtual paths rather than filesystem child paths.
Bundled UI and PWA files are package assets, not children of the browsed root;
their route names cannot select arbitrary paths outside those asset trees.
Filesystem replacement races between validation and opening remain outside
this change; the local filesystem and its owner are trusted.

[103]: ../tasks/103-close-the-directory-index-path-escape-and-authorize-save-and-delete-a1.md
[138]: ../tasks/138-make-public-instances-read-only-and-check-host-on-every-route-security.md
