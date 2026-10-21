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

## Root-relative file URLs

Files use their own paths below `/`, including direct-root symlink bookmarks.
`/w/` and `/n/` are ordinary resource paths, not aliases. Every resource passes
containment and public-mode checks. See
[ADR 0088](docs/adr/0088-remove-named-mount-and-alternate-shell-routes.md).
The server sends no CORS headers. This prevents browser scripts on another
origin from reading responses, but does not authorize writes or prevent requests.

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
clients. Tokens change on process restart. When the server answers again
after being offline, an open page fetches the shell and takes the new token
from it. After a restart the page did not notice, a save gets 403 and the page
shows "Change refused" with a Retry now button that fetches the token.

## Offline copies in the browser

The server edition's service worker keeps copies of what the browser read:
the shell, the UI files, folder listings, file bytes up to 2 MiB and server
previews, at most 200 of the last three. It shows them only when the server
cannot be reached, with a "Server offline" indicator, and never in place of a
server answer. See
[ADR 0089](docs/adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md).

These copies stay in the browser profile's Cache Storage after the page
closes, including for files deleted or changed since, until a newer read
replaces them or the limit drops them. Anyone who can read that browser
profile can read them. A public instance's visitors keep copies of the visible
files they opened. To remove them, clear the site's data in the browser
settings. The worker does not keep search results, requests for parts of a
file, or user HTML pages opened at their own URLs. Files that such a page
embeds are kept like other reads.

## HTML files at the server root

The server serves a `.html` file under the root as a web page at its own URL,
and a folder's `index.html` at the folder's URL. These pages are what lets a
built site or an HTML report in the root work as a website. They come from the
same origin as Filemill, and Filemill does not sandbox them. A script in such a
page can do anything the web interface can: read every file through `/api/*`,
root URLs, fetch the shell for its token, and save or delete files.
Only serve a root whose HTML you trust, as you would for any static web server.
The Raw link of an HTML member of an archive opens it the same way, from
`/api/raw`.

The preview pane is a different boundary. It shows an HTML file, or an HTML
member of an archive, in an iframe with `sandbox=""`, so the page's scripts do
not run there. Markdown, reStructuredText, `.docx` and `.desktop` previews are
inserted into the page as inert markup. Markup in their text stays text.
reStructuredText and `.docx` output loses its event-handler, `xlink:href` and
`data` attributes. The server removes them from its reStructuredText output,
and the browser checks every preview the server renders again before
inserting it. A
reStructuredText image stays a link, `:loading: embed` included: the server
never reads or inlines the image file, and the browser fetches it through the
root check. In reStructuredText, `.docx` and `.desktop` previews a link keeps
its target only for `http:`, `https:`, `mailto:` or a scheme-less address, and
a `.desktop` URL with any other protocol is shown and not linked. Markdown
links keep markdown-it's validation, and `markdownHref` also rejects
`javascript:`, `vbscript:`, `file:` and `data:` targets. Search results show a
file's name and matching line as text. See
[ADR 0082](docs/adr/0082-previews-link-only-to-safe-protocols.md).

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
put passwords, tokens, private files, or other secrets in the report. Give the
affected version or commit, the steps to reproduce, and the impact.
