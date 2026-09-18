# Security

## Supported threat model

Filemill is a local file browser. The person who starts the server must trust
its users and the files in the root directory.

The server binds to `127.0.0.1` by default. It checks each path against the
root, symlinks included, before it reads or serves a file. Do not expose
Filemill to an untrusted network without access control. Review the bind and
mount settings first.

Filemill has no user authentication, authorization, encryption, or tenant
isolation. A user who can reach an exposed server can read every file that the
server process can read.

## Named mounts under `/w/`

`/w/<root-name>/...` serves the raw bytes of a file under the root directory,
and `/w/<symlink-name>/...` does the same for each symlink that sits directly in
the root. Every path still passes the root check above. The route exists for the
web interface's own `~/` links, so it answers same-origin pages only: the server
sends no CORS headers, and a page on another origin cannot read files through
it. If you need cross-origin reads, put a reverse proxy that adds the headers in
front of a bind you trust.

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
put passwords, tokens, private files, or other secrets in the report. Give the
affected version or commit, the steps to reproduce, and the impact.
