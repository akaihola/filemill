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

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
put passwords, tokens, private files, or other secrets in the report. Give the
affected version or commit, the steps to reproduce, and the impact.
