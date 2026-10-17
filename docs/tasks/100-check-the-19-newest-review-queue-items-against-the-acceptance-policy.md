---
depends-on: [99]
---

# Check the 19 newest review-queue items against the acceptance policy

Steward issue, 2026-10-17 (decisions D7 and D10 in
`<steward-vault>/agents/steward/decisions.md`). It takes over vault
[18], whose tracker is blocked. The verdicts feed the steward's next digest,
so that Antti can accept or reject these items with less checking of his own.
Antti's first calibration lesson: run the tests a packet names before offering
an item.

## Items

The `- [ ]` items under `## Completed / Accepted` whose Hai `updatedAt` is from
2026-10-17, except [96], a history rewrite left to Antti, and this issue's
prerequisite [99]. Most moved there through [95]'s reconciliation; read [95]'s
notes in `docs/tasks/95-*.md` for them. [95] itself, [97], [98], [30] and the
`wait_for_timeout` `[*]` are among them.

## Work

Run after [99], so that `main` carries [25]'s pytest migration and, ideally,
green suites. Read each item's description and the commits that delivered it.
Run the tests the description names on current `main`, in bundle and dev mode
where static tests apply. If a suite fails on `main`, name the failure, whether
an item caused it, and whether an issue covers it; don't count it against an
item that didn't cause it. Check criterion 3 with `git revert --no-commit` of
an item's commits in a temporary worktree (`git worktree add --detach
"$TMPDIR/revert-check" main`, removed afterwards); conflicts only in `TASKS.md`
and `docs/tasks/` don't count.

For each item, record one line: issue, a one-line outcome, the evidence
(commits, files, test command with pass and fail counts) and a verdict under
`<steward-vault>/agents/steward/acceptance-policy.md`:

- **would accept:** all four criteria hold; give the revert command;
- **left to Antti:** name the criterion or the "Always left to Antti" class;
- **not done:** say what is missing.

## Deliverable

A section `## Evidence, YYYY-MM-DD` in this description file, with the lines
grouped by verdict and the counts per verdict at the end.

## Ground rules

- Change no other issue's state or text, and never change `[ ]` to `[x]`: only
  Antti accepts.
- Don't push, and don't touch the vault.

## Acceptance

- Every listed item has a line with evidence and a verdict.
- Nothing outside this file and the issue's own tracker moves changed.

## Evidence, 2026-10-17

Checked on `main` at `defedeb2`. This branch adds only tracker commits. The
runs used Python 3.14.7, Playwright 1.63.0, pytest 9.0.2 and Nix Chromium.
The verdicts follow `<steward-vault>/agents/steward/acceptance-policy.md` in
shadow mode. Nothing here accepts an item.

The 19 items are the `[ ]` entries under Completed / Accepted whose Hai
`updatedAt` was 2026-10-17 when this issue was written, without [96] and
[99]. [25] moved there afterwards, together with [99], and [99]'s validation
covers it. It is not among the 19.

### Suites on main

The three suites ran in parallel:

| Suite | Command | Result |
| --- | --- | --- |
| server | `uv run pytest server/tests -q --tb=short --durations=10` | 851 passed, 2 failed, 701.49 s |
| bundle | `uv run pytest static/tests --bundle -q --tb=short --durations=10` | 147 passed, 473.61 s |
| dev | `uv run pytest static/tests --dev -q --tb=short --durations=10` | 147 passed, 493.90 s |

Neither server failure counts against an item:

- `test_docs.py::test_documentation_uses_portable_development_examples`
  could not read `.claude/loop.md`, a placeholder that the agent sandbox
  mounts into the checkout. Outside the sandbox, `uv run pytest
  server/tests/test_docs.py server/tests/test_pytest_config.py
  server/tests/test_file_kind.py -q` passed 32 tests. This is an artifact of
  the environment and needs no issue.
- `test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor`
  timed out at `focusCol === 1 && path.length >= 2` under suite load. It
  passed five isolated reruns in 2.25–2.61 s. It presses ArrowRight before
  the folder opened by ArrowDown has loaded. [99]'s `88766300` added that
  wait to the sibling `test_arrow_navigation_keeps_fold_animation_running`,
  but not to this test. The test comes from `6c08d447` ([48]). None of the 19
  items caused the failure, and no issue covers it.

Focused runs repeat each item's own tests on the same tree. Static tests ran
in both bundle and development mode.

Revert checks used `git worktree add --detach "$TMPDIR/hai100/revert-check"
main`, then `git revert --no-commit` of each item's commits, newest first,
with `-m 1` for merges. Conflicts in `TASKS.md` and `docs/tasks/` took
`main`'s side and are not counted. The lines below name only the counted
conflict files. I removed the worktree afterwards.

### Would accept

- **[*] Clarify `[~]`.** The Rules section defines `[~]` as actively in
  progress. Evidence: `00dd2c69` (merge `c9e024ec`, `TASKS.md` only) added
  the definition. Later rule changes replaced its completion clause ("replace
  it with `[x]`") with today's "move it to Completed / Accepted with `[ ]`".
  No record shows the Kandev session review, but the meaning is settled and
  current. No tests apply. Revert: `git revert -m 1 c9e024ec`, which
  conflicts only in `TASKS.md`; resolve it by dropping the `[~]` Rules bullet.

### Left to Antti

**Criterion 3 only.** Criteria 1, 2 and 4 hold, but reverting on today's
`main` conflicts outside the tracker files. [97] and [98] conflict only in
`docs/ARCHITECTURE-REVIEW.md`, which `AGENTS.md` asks every task to keep
current.
The older items conflict because later work changed the same lines, or
because [25] moved `static/test-*.py` to `static/tests/`.

- **[97] Preview 404 after deletion.** A confirmed delete now blocks new
  preview reads under its path and waits for the active ones before
  `FS.remove`. Evidence: `84214e2f` (`ui/core/render.js`, bundle, ADR 0078,
  regression). `uv run pytest
  server/tests/test_browser_new_ui.py::test_delete_waits_for_active_preview_reads
  server/tests/test_browser_new_ui.py::test_delete_key_deletes_selected_files_and_directories_but_not_editors -q`:
  5 passed in each of three runs, 7.44–8.56 s. The revert conflicts in
  `docs/ARCHITECTURE-REVIEW.md`, where [30] later extended the same A9
  paragraph and ADR link list.
- **[98] Mobile landscape navigation timeout.** The keyboard harness writes
  server logs to a file instead of an unread pipe, and mobile pages use
  touch input. No UI code changed. Evidence: `9fa13dbe`, `f8cec8ab`,
  `e36a43e3` (`server/tests/test_browser_keyboard.py`,
  `docs/ARCHITECTURE-REVIEW.md`). `uv run pytest` of
  `test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen`,
  `test_mobile_landscape_wide_folder_with_small_server_log_pipe` and
  `test_mobile_tap_uses_touch_input` in `server/tests/test_browser_keyboard.py`:
  3 passed in each of three runs, 29.03–29.64 s. The revert conflicts in
  `docs/ARCHITECTURE-REVIEW.md`.
- **[*] Replace every `wait_for_timeout`.** `grep -r wait_for_timeout static
  server/tests` exits 1 with no matches. Evidence: `ffc5dbf4` replaced 288
  fixed waits. Its guard `server/tests/test_browser_waits.py` passed (1 test),
  and both static suites passed. The revert conflicts in
  `server/tests/test_browser_keyboard.py`, `server/tests/test_browser_waits.py`,
  `docs/ARCHITECTURE-REVIEW.md` and the moved `static/test-ui.py`,
  `test-url.py` and `test-rich.py`.
- **[*] `Delete` key shortcut.** Delete removes the selected file or folder
  after confirmation, but not in editors or with an empty selection.
  Evidence: `fe2d904c`, `2e9fb1bc` (merge `6c78f2d8`). [97] fixed the later
  preview 404. `uv run pytest
  server/tests/test_browser_new_ui.py::test_delete_key_deletes_selected_files_and_directories_but_not_editors -q`:
  1 passed. The revert conflicts in `ui/core/model/keyboard.js`,
  `ui/core/nav.js` and `server/tests/test_browser_new_ui.py`.
- **[*] Left arrow from preview keeps ancestor folds.** Evidence: `847671f6`
  (merge `6b6f4d5d`). `uv run pytest
  static/tests/test_model.py::test_preview_left_preserves_ancestor_folds`:
  1 passed in each mode. The revert conflicts in `ui/core/nav.js`,
  `static/index.html` and `static/tests/test_model.py`.
- **[*] Left arrow with all columns folded expands the parent.** Evidence:
  `01f8071f`, `2edc4b59` (merge `7ab2a3b0`). `uv run pytest
  static/tests/test_model.py::test_preview_left_expands_parent_when_all_columns_are_folded`:
  1 passed in each mode. The revert conflicts in `static/tests/test_model.py`.
- **[*] `.py.j2` as Python.** Evidence: `3a18660c`, `fae72c0f` (merge
  `cf366caa`). `uv run pytest
  server/tests/test_browser_new_ui.py::test_jinja_python_source_is_highlighted_in_the_browser
  server/tests/test_preview.py::test_jinja_python_file_is_syntax_highlighted -q`:
  2 passed. The revert conflicts in `server/tests/test_browser_new_ui.py`.
- **[*] `.jsonl` over 512 KB.** Large JSONL files are indexed by line and
  parse one row at a time. Evidence: `3eca819c`, `8dbd28a7`, `2880dbf3`
  (merge `aca1c222`), ADR 0068. `uv run pytest
  server/tests/test_browser_new_ui.py -k large_jsonl -q`: 3 passed.
  `uv run pytest static/tests/test_ui.py::test_jsonl_rows`: 1 passed in each
  mode.
  The revert conflicts in `CHANGELOG.md`, `ui/adapters/vfs-json.js`,
  `ui/core/ports.js`, `static/index.html` and `static/test-ui.py`.
- **[64] Stable widths during Up/Down.** Evidence: `c95582a2`, `4a9d2d99`
  (merge `6b84f417`). `uv run pytest` of
  `test_vertical_navigation_keeps_focused_column_whole`,
  `test_vertical_navigation_preserves_rounded_fold_boundary` and
  `test_vertical_navigation_preserves_full_fold_with_equal_widths` in
  `server/tests/test_browser_keyboard.py`: 11 passed.
  `static/tests/test_ui.py::test_keyboard_vertical` keeps the original width
  check: 1 passed in each mode. The revert conflicts in `ui/core/render.js`
  and `static/test-ui.py`.
- **[*] Delete the JSON and CSV providers.** Neither provider file nor its
  registration in `vfs.py` remains. JSON and CSV are browser adapters.
  Evidence: `44f4241f` (merge `8e6eba1e`), `59d95e15` (merge `77d74f19`).
  The CSV provider was removed inside the CSV preview merge `cdfda09c`
  (`b82a09eb`). `uv run pytest server/tests/test_vfs.py
  server/tests/test_api.py server/tests/test_browser_new_ui.py -k csv -q`:
  8 passed. The revert conflicts in `server/src/filemill/vfs.py`,
  `docs/ARCHITECTURE-REVIEW.md` and 11 files of the CSV merge.
- **[*] Remove development-setup references.** Documentation, docstrings and
  comments no longer name private hosts or paths. Evidence: `bdaac0d6`
  (33 files, with the guard in `server/tests/test_docs.py`). The guard passed
  outside the sandbox. A `git grep` for host names and home paths finds them
  only in two link fixtures in browser tests. The revert conflicts in
  `README.md` and `server/pyproject.toml`.
- **[*] Keep `test-e2e.py` manual.** `static/FSA-TEST-CHECKLIST.md` says when
  and how to run it, and the script stays out of the automated suites.
  Evidence: `6e7ee5be` (merge `8c10a648`). `python3 -m py_compile
  static/test-e2e.py` passes, and the script has a `__main__` guard. The
  manual run needs a desktop and two folder picks, so it was not repeated.
  The revert conflicts in `static/FSA-TEST-CHECKLIST.md`, which `b279fdcf`,
  `ffc5dbf4` and `587752b4` edited later.

**Other reasons.**

- **[*] Default `--bind` to `127.0.0.1`.** A security fix, one of the
  "Always left to Antti" classes. The default and `SECURITY.md` are in
  place. Evidence: the default came in `499222cf` inside the PWA merge
  `8243ef81`. The bind issue's own merge `eb89451d` (`88c597b7`) only
  adjusted tests. `SECURITY.md` came from `7dd91c3e` (merge `6eafc128`).
  `uv run pytest server/tests/test_cli.py -q`: 9 passed. Reverting these
  merges also conflicts.
- **[*] `.py` not highlighted.** Criteria 2 and 3, because no delivering
  commit exists. Python source is highlighted in browser and server
  previews. `uv run pytest
  server/tests/test_browser_new_ui.py::test_source_is_highlighted_in_the_browser
  server/tests/test_preview.py::test_python_file_is_syntax_highlighted -q`:
  2 passed. [95] cites `f05a6f89` (2026-08-30), which predates the report in
  `9aa929d1` (2026-09-17), and no later commit names a fix. Reverting
  `f05a6f89` conflicts in 11 files.
- **[43] The 11 server browser failures.** Criteria 1 and 3. The original 11
  test names and revision were never recorded. [43]'s description says not to
  infer completion from another task's baseline, yet its evidence is the
  red-test inventory of L020 (merge `92d131fe`, `7945a0e6`, `e0349caa`). The
  inventory lists 1 legacy-query test and 8 mobile restore tests, not the
  reported 2 and 9. `uv run pytest server/tests/test_browser_keyboard.py -k
  restore -q`: 8 passed. Reverting `92d131fe` conflicts in 25 files and would
  undo L020.
- **[41] RST in Source and Rendered modes.** Criteria 1 and 3. Evidence:
  `9fba9118` (merge `b43eae83`) renders served RST through Docutils. `uv run
  pytest server/tests/test_browser_new_ui.py -k rst -q`: 15 passed. Finding
  A8 in `docs/ARCHITECTURE-REVIEW.md` records that a browser-owned RST file in
  local-folder mode still requests `/api/preview?p=undefined`, and cites
  [41]. The revert conflicts in `server/src/filemill/app.py`,
  `ui/adapters/app-http.js` and `server/tests/test_browser_new_ui.py`.
- **[95] Tracker reconciliation.** Criterion 1, for one row. Evidence:
  `9d562520` (`TASKS.md` and its description). The table has 127 unique rows
  (A01–A18, L001–L109). Its named tests passed (32, see above). The revert
  conflicts only in `TASKS.md`. Row A14 moved [43] to Completed on another
  task's inventory, which [43]'s description rules out. The other 126 rows
  and moves hold, so the decision is [95] with or without the A14 move.
- **[30] Native shell.** Criteria 1, 2 and 3. Evidence: merges `cd3687b3`
  (2026-09-21 prototype) and `bb581be8`, ADR 0079. A fresh build reproduced
  the recorded 444,520-byte executable with a 334,651-byte UI. Outside the
  sandbox, `nix-shell native/shell.nix --run 'uv run --project server
  pytest native/test_host.py -q'` passed 18 tests, and the same with
  `static/tests/test_ui.py --native` passed 58 tests in 281.61 s after
  [25]'s migration. That was one run. The worker reports that four of five
  full runs pass, and one fails at a known `scroll_settled` timeout. The merge also adds the shared JSON
  fold-depth limit (`75da49f0`, ADR 0080) outside the issue's scope
  (`native/`, `ui/core/ports.js`, `docs/adr/`, `README.md`). Tauri was
  measured on 2026-09-21 and not rebuilt. Reverting `bb581be8` conflicts in
  `native/README.md` and the moved `static/test-ui.py`.

### Not done

None.

### Counts

| Verdict | Items |
| --- | ---: |
| Would accept | 1 |
| Left to Antti, criterion 3 only | 12 |
| Left to Antti, other reasons | 6 |
| Not done | 0 |
| Total | 19 |

For the steward: 12 of the 18 items left to Antti fail only criterion 3,
because a revert on today's `main` conflicts. Two decisions would settle most
of them. Should `docs/ARCHITECTURE-REVIEW.md` count like the tracker files?
That would clear [97] and [98]. Should criterion 3 apply to items finished
weeks ago, which later work has built on?
