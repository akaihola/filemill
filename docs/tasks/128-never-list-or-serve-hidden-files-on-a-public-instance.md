Steward issue, 2026-10-20 10:40, from part Q2 of the steward's decision 30, "The public Filemill site shows hidden files" ([agent@hopeli:~/my-knowledge/agents/steward/asks/30-public-filemill-shows-hidden-files.md](http://hopeli/my-knowledge/agents/steward/asks/30-public-filemill-shows-hidden-files.md?f)), which Antti approved on 2026-10-20 ("30 yes"). Goal: agentic-leverage. The nixos-config issue [Publish only filemill's committed files on the public Filemill site](http://hopeli/repos/nixos-config/docs/tasks/67-publish-only-filemill-s-committed-files-on-the-public-filemill-site.md?f) is the other half.

## Why

`filemill-public.service` serves `~/menu-public` on `127.0.0.1:8336`, published without a login as filemill.vempai.men. A security check on 2026-10-20 found that adding `?hidden=show` to an address there lists hidden files, and that hidden files are served too: the whole `.git/` folder, `.serena/`, `.claude/` and `.scratch/`. Filemill has no notion of a public instance, so the same code serves Antti's private homes and the public site alike.

## Work

1. Add a public mode, switched on by a command-line option and an environment variable in the style of `--bind` and `FILEMILL_BIND` in [cli.py](../../server/src/filemill/cli.py).
2. In public mode, never list, preview, download or serve a path with any component that starts with `.`, whatever the query string says (`?hidden=show` included). Answer such paths with 404, so their existence isn't confirmed. Don't follow a symlink that resolves to a hidden path either.
3. Cover every route that touches files: the UI shell, the API's listing and file routes, previews, downloads and static file serving.
4. Document the option in [the server README](../../server/README.md), and say that a public instance must use it.

## Acceptance

- Tests: in public mode a listing with `?hidden=show` shows no hidden entries, and direct requests for `.git/config`, `.claude/settings.json` and a nested `a/.b/c` answer 404 on each file route. Private mode is unchanged.
- The focused tests and the full suite pass.
- No pushes, deploys or service restarts. The nixos-config issue turns the option on for `filemill-public`.

## Plan

- `--public` and `FILEMILL_PUBLIC` set `app.state.public`. `env.py` gains a
  flag reader: any value except empty, `0`, `false`, `no` or `off` turns the
  mode on, so a typo fails closed. `--live` passes the mode to the reloaded
  app through the variable.
- `paths.py` holds the rule. `hidden(rel)` rejects a request path, unquoted
  the way `resolve_safe` unquotes it, with any component starting with `.`.
  `public_zones` drops bookmarks with a hidden name or a hidden component in
  their target path. `visible(path, zones)` requires the resolved path to lie
  in a zone and under no hidden name in any zone that holds it.
  `resolve_safe` and `resolve_web_mount` take `public=`.
- `app.py` checks `p`, `v`, `?vpath=` and the resource, `/n/` and `/w/` paths,
  and resolves through the public rule. A public listing keeps only entries it
  would serve, archive members included; search drops matches it would not
  serve; the shell ignores `?hidden=show`.
- Answers stay one 404, as for paths outside the root. Save and delete check
  authorization first, as ADR 0081 requires.
- ADR 0087 records the rule. `server/README.md`, `SECURITY.md`, `CHANGELOG.md`
  and `docs/ARCHITECTURE-REVIEW.md` describe it.
