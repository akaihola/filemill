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

## Public instances

Start a server that publishes its root without a login with `--public` or
`FILEMILL_PUBLIC=1`. It then answers 404 for every path with a component that
starts with `.`, such as `.git/`, on every route that reads files, and does not
follow a symlink into one. Listings and search leave such entries out, and
`?hidden=show` changes nothing. Visible files remain readable by anyone who can
reach the server. See
[ADR 0087](docs/adr/0087-a-public-instance-never-lists-or-serves-hidden-paths.md)
for the rule and what it does not hide.

## Named mounts under `/w/`

`/w/<root-name>/...` serves the raw bytes of a file under the root directory,
and `/w/<symlink-name>/...` does the same for each symlink that sits directly in
the root. Every path still passes the root check above. The route stays for
existing links; the web interface no longer makes them, because a Markdown `~/`
link now resolves against the root at `/`. The server sends no CORS headers, so
browser scripts on another origin cannot read the responses. This does not
prevent requests from reaching the server or authorize writes. If you need
cross-origin reads, put a reverse proxy that adds the headers in front of a
bind you trust.

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

The token authorizes browser requests, not users, and does not protect against
same-origin scripts; see [HTML files at the server root](#html-files-at-the-server-root).
Use authenticated access control before exposing the server to untrusted
clients. Tokens change on process restart; a stale cached shell fails
authorization until refreshed. Service worker caching remains open under A5.

## HTML files at the server root

The server serves a `.html` file under the root as a web page at its own URL,
and a folder's `index.html` at the folder's URL. These pages are what lets a
built site or an HTML report in the root work as a website. They come from the
same origin as Filemill, and Filemill does not sandbox them. A script in such a
page can do anything the web interface can: read every file through `/api/*`,
`/w/` and root URLs, fetch the shell for its token, and save or delete files.
Only serve a root whose HTML you trust, as you would for any static web server.
The Raw link of an HTML member of an archive opens it the same way, from
`/api/raw`.

The preview pane is a different boundary. It shows an HTML file, or an HTML
member of an archive, in an iframe with `sandbox=""`, so the page's scripts do
not run there. Markdown, reStructuredText, `.docx` and `.desktop` previews are
inserted into the page as inert markup. Markup in their text stays text. In reStructuredText, `.docx` and
`.desktop` previews a link keeps its target only for `http:`, `https:`,
`mailto:` or a scheme-less address, and a `.desktop` URL with any other
protocol is shown and not linked. Markdown links keep markdown-it's validation,
and `markdownHref` also rejects `javascript:`, `vbscript:`, `file:` and `data:`
targets. See [ADR 0082](docs/adr/0082-previews-link-only-to-safe-protocols.md).

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
put passwords, tokens, private files, or other secrets in the report. Give the
affected version or commit, the steps to reproduce, and the impact.
