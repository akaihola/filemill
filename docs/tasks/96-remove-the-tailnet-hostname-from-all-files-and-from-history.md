# Remove the tailnet hostname from all files and from history

Antti asked for this on 2026-10-17. Hai removed the same name from its own
repository in `80ee4c4`. filemill is public on GitHub, and its private tailnet
hostname (the private DNS name that `HAI_ALLOWED_HOSTS` in the private Hai environment file
holds) appears in current files and in about 200 commits. Never write the name
itself into a file, commit message, task doc or closing message; refer to it as
`<tailnet-host>`.

Current files: `TASKS.md` (the title of the large-JSON-preview issue) and
`docs/tasks/51-raw-url-redirect.md`, `55-favicon-deeplink-error.md` and
`60-content-search-timeout.md`. Find all of them with `git grep -n 'ts[.]net'`, and
history with `git log --all --oneline -S'ts[.]net'`.

## Work

Set `FILEMILL_REPO` to the repository checkout and `BACKUP_DIR` to a private
backup directory before using the commands below. Mirror names in angle
brackets are placeholders for the affected clone's remotes.

1. Precondition: issues [93], [94] and [95] depend on this one, so no other
   pacer work should be under way in filemill. Check `git worktree list`; report
   any worktree whose branch has commits that are not on `main`. Those include
   the Kandev-managed worktrees, which Antti may still want.
2. Replace the name in current files with `<tailnet-host>`, or with a phrase
   that reads well. Commit this on `main` first.
3. Back up: `git -C "$FILEMILL_REPO" bundle create "$BACKUP_DIR/filemill-before-tailnet-rewrite-YYYYMMDD.bundle" --all`.
4. Rewrite every ref with `git filter-repo --replace-text`. Keep the mapping
   file out of the repository, for example in `$TMPDIR`; it contains the name.
   Do the rewrite in a fresh clone, then make `"$FILEMILL_REPO"` match it
   (`main` and the branches that still exist). Keep the worktrees working, or
   name the ones that can't be kept.
5. Verify: `git log --all -S'ts[.]net'` and `git grep 'ts[.]net' $(git rev-list --all)`
   find nothing, and the tests that ran before still pass.
6. Write in this description file the old→new hashes of every commit that a
   `docs/tasks/` file or `TASKS.md` cites (`.git/filter-repo/commit-map`), so
   that citations can be followed.

Do not push, and do not touch the maintainer host or GitHub.

## For Antti (after this lands)

- Force-push to GitHub only the two branches it has. The rewrite also rewrote
  the remote-tracking refs, and the steward found both clean on 2026-10-17:
  `git -C "$FILEMILL_REPO" push --force origin main refs/remotes/origin/ci/hai91-durations-all:refs/heads/ci/hai91-durations-all`.
  The repository has no tags. (This replaces `push --force --all origin`, which
  would also publish 34 local `pacer-*`, `backup/*` and `feature/*` branches.)
- On the maintainer host, discard the old history: `git fetch` and then `git reset --hard origin/main`.
  Rebase or recreate any local branches there. On 2026-10-17 at 07:48 UTC, a
  minute after the rewrite, a push put the development host's `refs/remotes/<mirror>/main` and
  `refs/remotes/<mirror>/pacer-dbb29e55-…` back on the old history, which still
  carries the name. No T3 thread ran it; it may have come from the maintainer host. Those refs
  are local and not published, but delete them on the development host once the maintainer clone is reset
  (`git -C "$FILEMILL_REPO" update-ref -d <ref>`).
- GitHub keeps old commits reachable through pull request refs (PR #2) and its
  caches. Only GitHub Support can purge those.

Acceptance: steps 2–6 done, nothing pushed, and the closing message lists what
Antti has to do.

## Local completion, 2026-10-17

Sanitized current documents on main before the rewrite. Rewrote all 285
original refs, including remote-tracking, Kandev recovery and T3 checkpoint
refs. Preserved all 27 worktrees and their untracked files. The iPad-folder
Kandev branch has 3 commits outside main; the browser-test Kandev branch has
2. Both remain available. All 5 stash entries remain in their original order,
with additional rewritten refs under `refs/stash-archive/`.

Verified backup: `$BACKUP_DIR/filemill-before-tailnet-rewrite-20261017.bundle`.
A supplemental `$BACKUP_DIR/filemill-before-tailnet-rewrite-20261017-with-stashes.bundle`
also preserves older stash entries that the standard all-refs bundle omits.
These private backups retain the original sensitive history.

History pickaxe and tracked-tree scans found no unescaped private DNS suffix
across all 1,925 rewritten commits. The 11 documentation tests, DOM-free model
checks and static bundle check passed before the rewrite and were rerun after it.
No application behavior or architecture changed. Nothing was pushed; neither
the maintainer host nor GitHub was accessed. Antti still needs to perform the steps above.

### Commit citation map

Resolved commit citations in `TASKS.md` and `docs/tasks/` across every original
ref before rewriting. The table includes unchanged hashes. Foreign-repository
hashes, such as the Hai citation above, are outside this rewrite. The full
rewrite map is also retained in `.git/filter-repo/commit-map`.

| Old commit | New commit |
| --- | --- |
| `01836d3b8599851179c6531d4a99b8771755be69` | `9c7c8427f3201c1af161d95067e93bfe020fd719` |
| `05f44fcc179f49e6366f1a64aeb3882a9e31206e` | `1f8a8e608f4c9017ae72cd0bf1775108609b8110` |
| `06792cb871c7ab16b23c85eddd197c409f342eea` | `ed6ed24fee181d77d1fc71445f10694354e1dfd0` |
| `0ac460c3132a1c253853f7a8053ea2979fdef6bf` | `78beebf17e5b6d58decf89d4a2244f9b6fd60082` |
| `1b698a7284ac0a07944e7a27f45acc2caed97f6d` | `98adbd48e2dd10464713602e5befc5f18bb328eb` |
| `1c179ef34356a2a82aced8f7e02894b77d902765` | `d1e98b467e7b83f582346468ed83695677c51bf8` |
| `20acff4c86e5318ba57ef4087a81c8d2d2a3d728` | `60f36c577f53bc8119f9f42e73b6cf9e73f48fad` |
| `21fd4db2ad4701fed8441982a53079bc5b95e2e3` | `e3143ad51530ff3e0af5f9b44ab355c8b972d47a` |
| `263288ff031f6e4454538b8be982f09b12572dae` | `023c2450f8c1840419022fadfefa424a6eba53aa` |
| `32a5a6c663a6da0b52d5e626752b06848d31c5ac` | `c7b7f38b13bd30e0c47a1df216597b1ab26d2fe4` |
| `3470ea911e1800e813b5377c3262a30fa8395dcb` | `ab6c5d05da5204dc8764e7088d13ac8ad4c2f407` |
| `37238544a4907eadcfaee7c17d6ab62afc048576` | `25f8e36660526303592368ce6c56711664a5e86c` |
| `3764d302542d77ccc662fba81bd48d3f2e3e19e8` | `eb18340ca533abf1b2cceeb4884de8d27d869e65` |
| `3d505c53457802a2725e7e63e82d5e5e953c1d6a` | `980d366491f91e5e65f0a011d7af391e23b939c0` |
| `3d830e73902d105b96365c1a86b13e19c6b6987b` | `b7757a6cc49bedd2cd741abb77b39eb24e262dd9` |
| `45dbcce597d6793863dca2dc83b2cdb9af21383a` | `0d917dd413cfe2cfa0ff1b5e4ed66e7b2129694b` |
| `4851e83153d67f9e615fd7e60f4f8d0bf0d68be4` | `af9168e7fbeeba6eb5f6c3546b0de8570337678d` |
| `57ddbe148088f5008e217de6e39ee8ef1a5fa763` | `1d5f729cfce55cd1c82948186f8510de17a6c3ad` |
| `5aa3f32ca985056c1ae553bf2323ffed740ef016` | `cfc345e065319ba3a4896a65ba09803a69788e41` |
| `5d55bd417a3ae81f2774b944b436a481ad1d3239` | `a275ab89c439fe25d2d66141e4f8c16550e7dccb` |
| `5ee500f21fd2d6187b1f514c7fe3ba22fb6da50e` | `9585f8b7c5d8107b026fdc4772efe809c9bd59ad` |
| `68eae0d70391011554707d5c7ac7b57248affb89` | `f08928fecb385b0f8054427ae44a9217ed31d4ff` |
| `72e16aad8d6d3ba11371dc67392e45559e6cd15f` | `cd3687b3c9419f294f88f864a25c275d579f991c` |
| `7ff1fd2ae5d441194bbc74d004d5d78c9d05c04e` | `fc4f0d521d46ce1d77b3bbd4890796c63e0b063e` |
| `83c44ad787b960802d1f3a407a523efcb5fff1f1` | `3bd91e00022b8d56fdc5a4661429a79a67fcdecd` |
| `85ffe6d4453ac8a630822a5e78906b7ac7e82dac` | `b780fad27dbd05a3f2423ed6176194cd2dfa49c2` |
| `9502cded9ab82e63fbc85f3a07673e2397c3d01d` | `a7ab526b7c330c7bd9bf0fb150c7f58c1c44a79a` |
| `95ea18b1c0bb66cc4957a4fe28289e6e2767305a` | `9d90ed3fde4a05f85ed39ab50a382744b059ed88` |
| `9a4c3a0221b6105a43c8dbe04ed9dbd3807b10be` | `003a082eeaa35380ce96f19bbafed0441f130d85` |
| `9c67d665098875b01da5b7b14be7dc897ad65dd4` | `04262ad2294880de8c7515845becdfc7f5aaa805` |
| `9e46ede7160069abac5694f6219b37d58503ced4` | `26778f7ef18de1df32b63b8c14cefea822c19331` |
| `a4c77073bf4a43bd10b4981f7a76aed285cf41ee` | `1bf99afae7d19f6ec874bb539333b845272e7dc3` |
| `a61e4ebd29f3b1a50140dc67199aace86335d47d` | `3b5730fc58aa127f29b4bf50d0b439f7cdf0c069` |
| `ac44066e53f9c91e160075482c3c64727f13dce4` | `7df84cda44e655e953d7e658f8cfe6a08f641e00` |
| `b210f9aa884bb1ff1ad54095499999af0579192d` | `c486a8daeb57b93c6071403f1c90d350afab8bb5` |
| `b96d84e2d0e9782553584e935f7cbae0dd650097` | `9f9a50716fa4943f857f19cfc5f82ac0808b6c32` |
| `c10c1e3611a0e065c5d7cc4f7abb3abe8ec65ec1` | `db21b97e5d249980d75174cc81644caeb332852f` |
| `ca1446b7172a9cd6d7af17f943b2eafe2fc89bad` | `9522af500758cfff48b2e39deb80e446f5beed1a` |
| `d3de46ca591d9be597a7e09fc9342ca344332fcb` | `075f617703388f5177b835c523ef181cccdef9f3` |
| `de104f58958db68045a777536817553189ac2197` | `357c7c80c5103d849cd6545a529794a87e83231c` |
| `e61aaad9e5d956e4cf012ee62449de8ef8df0c6b` | `875b032b653b27814e959145128130c0e74c3729` |
| `e89f974d9907f586b805aa494626969c3de2f807` | `16ff8558494cbc6ca07d6f979ed5a9a035a56a37` |
| `ea20d27dad8dd2153e6185e418b7aa2bf0de1edd` | `6b25f1e84b27f2b6c278dc3a1265bf35b99992f8` |
| `efa92fdeb2cf8124d42231e79c666a30f79f61ae` | `c37b3e72e5feedd7023b5be032d0ce1cce0ae5ee` |
| `effac316b36ca78d9fea060aa0ecbf5e2f3cb0a1` | `1c8408179683d8af5c101b038bc3491f4812b801` |
| `fbd49aeddda9f842a65425907fc38e31a20dc246` | `87bc1f5d728840efd91341e894f8a80c283ee579` |
| `ff11672c5961428a03f41707250c610b1b929593` | `5863968c7e29bdfa2270ce4ad445981a1d0fc9f5` |
| `ff773fc058f0b01e2cbb6351e16ac2f77793d80c` | `55350300b46f9ba232d57274017e2448155e8dfa` |
