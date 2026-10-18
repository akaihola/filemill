# Security

## Supported threat model

Filemill is a local file browser. The person who starts the server must trust
its users and the files in the root directory.

The server binds to `127.0.0.1` by default. It checks each path against the
root, symlinks included, before it reads or serves a file. Do not expose
Filemill to an untrusted network without access control. Review the bind and
mount settings first.

Filemill has no user authentication, encryption, or tenant isolation. A user
who can reach an exposed server can read files within the root and its direct
bookmark symlink targets, subject to the server process permissions. A network
client can also fetch the UI token and authorize writes.

## Named mounts under `/w/`

`/w/<root-name>/...` serves the raw bytes of a file under the root directory,
and `/w/<symlink-name>/...` does the same for each symlink that sits directly in
the root. Every path still passes the root check above. The route exists for the
web interface's own `~/` links. The server sends no CORS headers, so browser
scripts on another origin cannot read the responses. This does not prevent
requests from reaching the server or authorize writes. If you need cross-origin reads, put a reverse proxy that adds the headers in
front of a bind you trust.

## Save and delete authorization

Both endpoints require a matching Origin and Host plus the per-process
X-Filemill-Token header before resolving paths or reading a body. Missing,
opaque, unrelated or unauthorized origins and missing or incorrect tokens
receive 403. The Filemill shell supplies the token to the shipped HTTP adapter;
raw HTML files do not receive it automatically.

Loopback origins work by default. For reverse proxies or a LAN bind, configure
exact space-separated public origins with FILEMILL_ORIGINS, for example
`https://files.example https://files.example:8443`. Preserve the public Host
header at the proxy. Explicit HTTPS origins work over HTTP backend connections.
No wildcard origins are accepted and no CORS access is granted. See
[ADR 0081](docs/adr/0081-authorize-server-mutations.md) for the complete policy.

The token authorizes browser requests, not users. Root HTML executes on the
Filemill origin and can fetch the shell to obtain the token. Only serve trusted
HTML on that origin. Preview injection remains an open risk under A2; the token
does not protect against same-origin scripts. Use authenticated access control
before exposing the server to untrusted clients. Tokens change on process
restart; a stale cached shell fails authorization until refreshed. Service
worker document caching remains open under A5.

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
put passwords, tokens, private files, or other secrets in the report. Give the
affected version or commit, the steps to reproduce, and the impact.
