# Remove the tailnet hostname from all files and from history

Antti asked for this on 2026-10-17. Hai removed the same name from its own
repository in `80ee4c4`. filemill is public on GitHub, and its gogo tailnet
hostname (the private DNS name that `HAI_ALLOWED_HOSTS` in `~/.config/hai/hai.env`
holds) appears in current files and in about 200 commits. Never write the name
itself into a file, commit message, task doc or closing message; refer to it as
`<tailnet-host>`.

Current files: `TASKS.md` (the title of the large-JSON-preview issue) and
`docs/tasks/51-raw-url-redirect.md`, `55-favicon-deeplink-error.md` and
`60-content-search-timeout.md`. Find all of them with `git grep -n 'ts[.]net'`, and
history with `git log --all --oneline -S'ts[.]net'`.

## Work

1. Precondition: issues [93], [94] and [95] depend on this one, so no other
   pacer work should be under way in filemill. Check `git worktree list`; report
   any worktree whose branch has commits that are not on `main`. Those include
   the Kandev worktrees under `~/.kandev/tasks/`, which Antti may still want.
2. Replace the name in current files with `<tailnet-host>`, or with a phrase
   that reads well. Commit this on `main` first.
3. Back up: `git -C ~/prg/filemill bundle create ~/backups/filemill-before-tailnet-rewrite-YYYYMMDD.bundle --all`.
4. Rewrite every ref with `git filter-repo --replace-text`. Keep the mapping
   file out of the repository, for example in `$TMPDIR`; it contains the name.
   Do the rewrite in a fresh clone, then make `~/prg/filemill` match it
   (`main` and the branches that still exist). Keep the worktrees working, or
   name the ones that can't be kept.
5. Verify: `git log --all -S'ts[.]net'` and `git grep 'ts[.]net' $(git rev-list --all)`
   find nothing, and the tests that ran before still pass.
6. Write in this description file the old→new hashes of every commit that a
   `docs/tasks/` file or `TASKS.md` cites (`.git/filter-repo/commit-map`), so
   that citations can be followed.

Do not push, and do not touch atom or GitHub.

## For Antti (after this lands)

- Force-push to GitHub: `git -C ~/prg/filemill push --force --all origin` and
  `--tags`.
- On atom, discard the old history: `git fetch` and then `git reset --hard origin/main`.
  Rebase or recreate any local branches there.
- GitHub keeps old commits reachable through pull request refs (PR #2) and its
  caches. Only GitHub Support can purge those.

Acceptance: steps 2–6 done, nothing pushed, and the closing message lists what
Antti has to do.
