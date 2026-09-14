# Security

## Supported threat model

Filemill is a local file browser. It assumes that the person who starts the
server trusts its users and the files in the configured root directory.

The server binds to `127.0.0.1` by default. It checks paths against the root,
including symlinks, before it reads or serves a file. Do not expose Filemill to
an untrusted network without adding access control and reviewing the bind and
mount settings.

Filemill does not provide user authentication, authorization, encryption, or
tenant isolation. A user who can reach an exposed server may read files that the
server process can read.

## Report a vulnerability

Report security issues through [GitHub private vulnerability
reporting](https://github.com/akaihola/filemill/security/advisories/new). Do not
include passwords, tokens, private files, or other secrets in the report. Give
the affected version or commit, the steps to reproduce, and the impact.
