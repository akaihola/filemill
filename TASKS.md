# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Unverified proposals

- [125] Clarify network consent scope from docs question 11
  <!-- hai:{"id":"simple-76bc63bc-236d-4bb7-8eaf-45ad44c96212","labels":["steward"],"createdAt":"2026-10-20T07:12:47.626Z","updatedAt":"2026-10-20T08:15:29.716Z"} -->

- [121] Separate internal requests from real file and folder paths
  <!-- hai:{"id":"simple-4495517f-2546-4750-93e8-47dac424ae2a","labels":["steward"],"createdAt":"2026-10-20T07:12:44.051Z","updatedAt":"2026-10-20T08:12:08.283Z"} -->

- [116] Sandbox the Raw view of HTML files inside archives with a
  Content-Security-Policy header
  <!-- hai:{"id":"simple-2569b382-eaf4-4d64-8db1-ecd76cccca46","labels":["steward"],"createdAt":"2026-10-20T02:10:36.825Z","updatedAt":"2026-10-20T02:10:36.825Z"} -->

## Ordered backlog

- [130] Give served and browser-owned folders the same content search
    - Depends on: [120]

  <!-- hai:{"id":"simple-d1776999-2a2c-4870-936a-9620915aee07","labels":["steward"],"createdAt":"2026-10-20T08:12:02.201Z","updatedAt":"2026-10-20T08:12:29.949Z"} -->

## Scheduled

## In Progress

- [~] [141] Finish browser fixture isolation and qualify independent test roots
      <!-- hai:{"id":"simple-e978cab5-98e2-43f3-80a4-8a56695f8ac3","labels":["steward"],"createdAt":"2026-10-21T11:20:40.877Z","updatedAt":"2026-10-21T15:01:55.354Z"} -->

## Completed / Accepted

- [ ] [120] Disable server search in local folders from docs question 5
      <!-- hai:{"id":"simple-a4b4e43a-fd0b-4a48-a78c-52a850f38e2b","labels":["steward"],"createdAt":"2026-10-20T07:12:43.204Z","updatedAt":"2026-10-22T02:21:17.973Z"} -->

- [ ] [148] Say in --bind's help that an explicit flag wins over FILEMILL_BIND
      <!-- hai:{"id":"simple-7e2f615f-1902-49fd-b0be-0cf3fe8b7ead","labels":["steward"],"createdAt":"2026-10-21T21:59:19.762Z","updatedAt":"2026-10-21T23:12:08.340Z"} -->

- [ ] [147] Allow only known elements and attributes in reStructuredText previews
      <!-- hai:{"id":"simple-88cfaa62-ec67-4090-a023-c53f20d3b2e4","labels":["steward","security"],"createdAt":"2026-10-21T20:34:29.661Z","updatedAt":"2026-10-21T23:11:22.493Z"} -->

- [ ] [146] Check filemill's README, contributor docs, goals and roadmap against
  current main
      <!-- hai:{"id":"simple-a4858f85-f357-497a-a1d3-f32ee93767e7","labels":["steward","review"],"createdAt":"2026-10-21T19:48:01.758Z","updatedAt":"2026-10-21T21:14:20.860Z"} -->

- [ ] [144] Make the full static suites pass reliably: the wide-folder wait and
  test_rst's release count
      <!-- hai:{"id":"simple-0eccd583-2747-4244-95a8-321980b45c28","labels":["steward"],"createdAt":"2026-10-21T14:15:31.702Z","updatedAt":"2026-10-21T18:38:54.893Z"} -->

- [x] [145] Add three missing browser regressions: focused search scope, HTTP entry
  order, duplicate CSV rows
      <!-- hai:{"id":"simple-de8a2439-b587-4816-9dea-f158c5a0bf70","labels":["steward"],"createdAt":"2026-10-21T14:15:34.877Z","updatedAt":"2026-10-21T19:49:47.063Z"} -->

- [x] [143] Check whether the demo instances show up in the development dashboard
      <!-- hai:{"id":"simple-5d0a1fa0-5647-4a21-a6c8-f0050c6de2c7","labels":["steward","review"],"createdAt":"2026-10-21T11:20:51.060Z","updatedAt":"2026-10-21T19:49:51.651Z"} -->

- [x] [142] Recover the revision and failing tests of the old server browser
  baseline
      <!-- hai:{"id":"simple-7e0cfc0d-56d3-479e-ac6b-e6ce359a174b","labels":["steward","review"],"createdAt":"2026-10-21T11:20:46.465Z","updatedAt":"2026-10-21T19:49:57.067Z"} -->

- [x] [140] Reuse the preview element across resizes and folding
      <!-- hai:{"id":"simple-e05f5d48-cda2-4c6e-971b-79425d2fa5ad","labels":["steward"],"createdAt":"2026-10-21T11:20:37.089Z","updatedAt":"2026-10-21T19:50:03.033Z"} -->

- [x] [133] Protect saves from truncation and stale overwrites (architecture review
  A4)
      <!-- hai:{"id":"simple-7fc0721d-e6cf-4c12-91b0-2758fd68f09c","labels":["steward"],"createdAt":"2026-10-20T19:37:48.890Z","updatedAt":"2026-10-21T19:50:08.919Z"} -->

- [ ] [138] Make public instances read-only and check Host on every route (security
  review S1, S3)
    - Depends on: [137]

      <!-- hai:{"id":"simple-14481238-0336-4adf-a3ce-bc5aeadaf3a2","labels":["steward"],"createdAt":"2026-10-20T23:39:29.669Z","updatedAt":"2026-10-21T10:39:02.981Z"} -->

- [ ] [139] Stop RST previews and search results from injecting live markup
  (security review S2, S4)
    - Depends on: [137]

      <!-- hai:{"id":"simple-28e033e1-3498-4fc4-bb30-8ccfad7e134a","labels":["steward"],"createdAt":"2026-10-20T23:39:32.779Z","updatedAt":"2026-10-21T08:12:34.496Z"} -->

- [x] [137] Fix the intermittent Back failure in
  test_back_retraces_the_folders_that_were_opened
      <!-- hai:{"id":"simple-67d7be8a-d50f-4a7e-a079-ca6a43ab338b","labels":["steward"],"createdAt":"2026-10-20T22:52:05.894Z","updatedAt":"2026-10-21T11:12:41.181Z"} -->

- [ ] [136] Security scan of filemill: served roots, mutations, previews, caches and
  history
      <!-- hai:{"id":"simple-2987e143-caeb-4d71-9d71-d4ad75a184de","labels":["steward","security"],"createdAt":"2026-10-20T19:38:07.298Z","updatedAt":"2026-10-20T23:06:40.487Z"} -->

- [x] [122] Clarify deliberate test delays from docs question 8
      <!-- hai:{"id":"simple-e47a58f3-193e-4296-83a9-cfa00f27371b","labels":["steward"],"createdAt":"2026-10-20T07:12:44.920Z","updatedAt":"2026-10-21T11:12:45.066Z"} -->

- [x] [135] Keep bundle repositories alive through active reads (architecture review
  A14)
      <!-- hai:{"id":"simple-ad2e83e1-1884-4c57-afb0-fc279fdbafd6","labels":["steward"],"createdAt":"2026-10-20T19:38:05.190Z","updatedAt":"2026-10-21T05:16:00.868Z"} -->

- [x] [134] Refresh JSON columns from the current file (architecture review A13)
      <!-- hai:{"id":"simple-fc2b70cd-7598-47b9-8b82-4004d374afcd","labels":["steward"],"createdAt":"2026-10-20T19:38:03.173Z","updatedAt":"2026-10-21T05:16:05.864Z"} -->

- [x] [132] Re-check the architecture review against current main
      <!-- hai:{"id":"simple-2a087add-53a0-4c65-9b64-6b413aae4b4f","labels":["steward","review"],"createdAt":"2026-10-20T17:18:18.462Z","updatedAt":"2026-10-21T05:16:10.851Z"} -->

- [x] [131] Close the gaps found in five older review items
      <!-- hai:{"id":"simple-c79b828d-b1d0-4776-82e2-0e9bdf1d6bed","labels":["steward"],"createdAt":"2026-10-20T14:12:31.533Z","updatedAt":"2026-10-21T05:16:15.459Z"} -->

- [x] [127] Correct icon generator claims from docs question 13
      <!-- hai:{"id":"simple-c28a4f20-6a8c-44e7-a484-b78ac1731e99","labels":["steward"],"createdAt":"2026-10-20T07:12:49.393Z","updatedAt":"2026-10-21T05:16:21.478Z"} -->

- [x] [126] Align decision timing rules from docs question 12
      <!-- hai:{"id":"simple-c51c3fbe-451d-4e29-8e42-9474e4e8d838","labels":["steward"],"createdAt":"2026-10-20T07:12:48.486Z","updatedAt":"2026-10-21T05:16:25.658Z"} -->

- [x] [124] Explain dependency constraints from docs question 10
      <!-- hai:{"id":"simple-d36f5057-cc6b-4c43-aaf5-45532393af26","labels":["steward"],"createdAt":"2026-10-20T07:12:46.777Z","updatedAt":"2026-10-21T05:16:29.850Z"} -->

- [x] [123] Clarify conditional test skips from docs question 9
      <!-- hai:{"id":"simple-c33756b3-3ea8-4a89-9352-60eaf73faf0e","labels":["steward"],"createdAt":"2026-10-20T07:12:45.801Z","updatedAt":"2026-10-21T05:16:35.373Z"} -->

- [x] [119] Offer manual copying in a pop-up when clipboard access fails
      <!-- hai:{"id":"simple-ee263a83-cc2f-41ec-9040-d4a5c0a8e93b","labels":["steward"],"createdAt":"2026-10-20T07:12:42.185Z","updatedAt":"2026-10-21T05:16:38.972Z"} -->

- [x] [117] Show an expandable server-offline indicator with cached content
      <!-- hai:{"id":"simple-2815036e-03d8-491d-a901-3794c92f18de","labels":["steward"],"createdAt":"2026-10-20T07:12:40.437Z","updatedAt":"2026-10-21T05:16:43.173Z"} -->

- [ ] [118] Hide the ineffective server preview switch from docs question 3
      <!-- hai:{"id":"simple-1161fe2f-92b3-4ea4-99a6-9b511726259b","labels":["steward"],"createdAt":"2026-10-20T07:12:41.306Z","updatedAt":"2026-10-20T11:15:39.997Z"} -->

- [x] [129] Remove the obsolete /w/ and /n/ URL routes
      <!-- hai:{"id":"simple-0ee9510c-1d58-4841-a0ec-bad006c0fd85","labels":["steward"],"createdAt":"2026-10-20T08:11:59.096Z","updatedAt":"2026-10-20T10:24:38.620Z"} -->

- [ ] [128] Never list or serve hidden files on a public instance
      <!-- hai:{"id":"simple-9104b865-c208-4bfe-bc8c-92ac37a361d3","labels":["steward"],"createdAt":"2026-10-20T07:26:36.286Z","updatedAt":"2026-10-20T08:46:16.991Z"} -->

- [x] [115] Propose plain answers to the docs check's twelve remaining questions
      <!-- hai:{"id":"simple-e25533eb-a765-42e3-8e41-b1e7e16d1b0e","labels":["steward","review"],"createdAt":"2026-10-19T17:58:46.533Z","updatedAt":"2026-10-21T05:16:48.660Z"} -->

- [x] [94] Move the CI workflows to action versions that run on Node.js 24
    - Depends on: [96]

      <!-- hai:{"id":"simple-28def403-6427-4ff6-aea8-3643a19d1a61","labels":["steward"],"createdAt":"2026-10-16T16:48:54.367Z","updatedAt":"2026-10-17T08:00:57.885Z"} -->

- [ ] [114] Sandbox HTML previews of archive members as SECURITY.md promises
      <!-- hai:{"id":"simple-19e1170a-8c5b-4b30-935e-64b054b39407","labels":["steward","security"],"createdAt":"2026-10-19T17:58:36.228Z","updatedAt":"2026-10-20T00:11:48.739Z"} -->

- [x] [113] Fix the five tests that failed in GitHub CI after the history push
      <!-- hai:{"id":"simple-633e3e56-0c80-48dc-940c-9c4d23e9ebb8","labels":["steward"],"createdAt":"2026-10-19T17:55:35.768Z","updatedAt":"2026-10-21T19:50:20.604Z"} -->

- [x] [112] Section links and heading fragments don't open the heading
      <!-- hai:{"id":"simple-7c134768-10d6-422d-87d7-0354b53e8de5","labels":["steward"],"createdAt":"2026-10-19T16:06:43.116Z","updatedAt":"2026-10-19T20:47:32.805Z"} -->

- [x] [93] Make main's CI green again: static bundle test failing since 06792cb
    - Depends on: [96]

      <!-- hai:{"id":"simple-08939b57-cc97-400c-bce7-e77ff1e462c5","labels":["steward"],"createdAt":"2026-10-16T16:48:53.101Z","updatedAt":"2026-10-19T18:13:46.054Z"} -->

- [x] [110] Confusing diagonal scroll
      <!-- hai:{"id":"simple-03b8dad8-ef8f-463e-a43d-6e54a152efdd","priority":"none","labels":[],"createdAt":"2026-10-19T15:11:32.244Z","updatedAt":"2026-10-19T18:14:16.303Z"} -->

- [x] [111] Renders HTML comments in Markdown documents
      <!-- hai:{"id":"simple-6a0e8d6a-4429-4924-bff3-b5437909a311","priority":"none","labels":[],"createdAt":"2026-10-19T15:48:38.147Z","updatedAt":"2026-10-19T18:18:03.621Z"} -->

- [x] [109] Check filemill's docs and ADR statuses against the code, and fix what
  disagrees
      <!-- hai:{"id":"simple-b148aec7-49a8-44df-88c0-13a18617b1d3","labels":["steward"],"createdAt":"2026-10-19T08:08:26.389Z","updatedAt":"2026-10-20T08:17:54.276Z"} -->

- [x] [107] Date superseded roadmap and ADR claims (roadmap Phase 0)
    - Depends on: [105]

      <!-- hai:{"id":"simple-c54d6a4c-5bfc-417e-bb9c-250b2b875076","labels":["steward"],"createdAt":"2026-10-18T20:07:24.425Z","updatedAt":"2026-10-19T09:55:42.505Z"} -->

- [x] [108] Wait for PageDown scrolling in the static keyboard test
      <!-- hai:{"id":"simple-e9360e81-e2ed-419a-8061-7e3136ecbb92","createdAt":"2026-10-18T21:43:30.456Z","updatedAt":"2026-10-19T09:55:41.941Z"} -->

- [x] [104] Make preview content inert: wikilink text and DOCX output (A2)
      <!-- hai:{"id":"simple-fdfa185d-6944-4b3b-acc4-f7b3b2114168","labels":["steward"],"createdAt":"2026-10-18T20:07:21.877Z","updatedAt":"2026-10-19T19:03:24.424Z"} -->

- [x] [106] Link or remove every lint suppression and the obsolete PPTX skip
  (roadmap Phase 1)
    - Depends on: [102]

      <!-- hai:{"id":"simple-bf3779d1-478d-46a3-858d-498dde815c5f","labels":["steward"],"createdAt":"2026-10-18T20:07:23.528Z","updatedAt":"2026-10-19T14:05:45.290Z"} -->

- [x] [105] Correct the current edition and renderer documentation (roadmap Phase 0)
    - Depends on: [102]

      <!-- hai:{"id":"simple-a03688ad-b2e9-4885-b18d-eaa33c6adb90","labels":["steward"],"createdAt":"2026-10-18T20:07:22.740Z","updatedAt":"2026-10-19T14:05:45.809Z"} -->

- [ ] [103] Close the directory-index path escape and authorize save and delete (A1,
  A3)
      <!-- hai:{"id":"simple-ffe76e04-123e-46db-8436-f5563ac5b5d7","labels":["steward"],"createdAt":"2026-10-18T20:07:14.696Z","updatedAt":"2026-10-18T21:55:15.099Z"} -->

- [x] [102] Audit the technical roadmap against main and draft the next phase's
  issues
    - Depends on: [101]

      <!-- hai:{"id":"simple-4062970c-4d67-4774-b6d9-969613643e7c","labels":["steward"],"createdAt":"2026-10-18T02:12:21.766Z","updatedAt":"2026-10-18T19:44:21.344Z"} -->

- [x] [101] Make the browser keyboard tests wait for each opened folder before the
  next key
      <!-- hai:{"id":"simple-52f039e0-e22b-4c63-95c2-21d6afb06983","labels":["steward"],"createdAt":"2026-10-18T02:12:12.913Z","updatedAt":"2026-10-19T09:55:41.397Z"} -->

- [x] [100] Check the 19 newest review-queue items against the acceptance policy
    - Depends on: [99]

      <!-- hai:{"id":"simple-89e06a37-5045-45d1-be1f-dc45abf1ced6","labels":["steward"],"createdAt":"2026-10-17T17:06:24.317Z","updatedAt":"2026-10-21T17:11:50.770Z"} -->

- [ ] [99] Rebase [25]'s pytest migration onto main and merge it once the full suite
  passes
      <!-- hai:{"id":"simple-008dfc0f-048f-4de3-9845-bedc6e858c47","labels":["steward"],"createdAt":"2026-10-17T14:10:56.295Z","updatedAt":"2026-10-17T18:08:57.189Z"} -->

- [ ] [25] Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under pytest with
  fixtures for the fake handle, the OPFS root and the bundle. Split `main()` by section.
    - Depends on: [12]

      <!-- hai:{"updatedAt":"2026-10-17T18:08:34.601Z"} -->

- [ ] [30] Prototype one native shell that hosts the DOM renderer in a WebView and supplies
  the three ports natively. Choose the smallest binary that passes `test-ui.py`.
    - Depends on: [29]

      <!-- hai:{"updatedAt":"2026-10-17T16:24:16.554Z"} -->

- [x] [98] Investigate mobile landscape wide-folder navigation timeout
      <!-- hai:{"id":"simple-eae59ddd-5222-4dbd-972d-d23258c6db71","createdAt":"2026-10-17T07:56:11.253Z","updatedAt":"2026-10-21T14:12:50.766Z"} -->

- [ ] [97] Fix intermittent preview 404 after deleting the selected file
      <!-- hai:{"id":"simple-5b65e45b-f3ef-448e-85b3-ca938f67c989","createdAt":"2026-10-17T07:51:46.441Z","updatedAt":"2026-10-17T11:53:09.416Z"} -->

- [ ] [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with
  `wait_for_function` or `expect`. Done when `grep -r wait_for_timeout` finds nothing.
      <!-- hai:{"id":"simple-1a46227e658d855f","updatedAt":"2026-10-17T11:30:59.992Z"} -->

- [x] [95] Reconcile TASKS.md with the code: 16 In Progress and 109 legacy completions
    - Depends on: [96]

      <!-- hai:{"id":"simple-fe5c93cd-f67b-45d1-8352-57667238abe6","labels":["steward"],"createdAt":"2026-10-16T16:48:55.733Z","updatedAt":"2026-10-21T17:11:54.393Z"} -->

- [x] [*] `.py` files are not highlighted at all.
      <!-- hai:{"id":"simple-5a544fc442d3d2ca","updatedAt":"2026-10-21T14:12:54.678Z"} -->

- [x] [*] Keep `static/test-e2e.py` as a manual check. Describe when and how to run it in
  `static/FSA-TEST-CHECKLIST.md`.
      <!-- hai:{"id":"simple-d27ac8852cc5e629","updatedAt":"2026-10-21T05:16:52.764Z"} -->

- [x] [*] Clarify the meaning of `[~]` in this file. Review Kandev task sessions to find out
  what it means.
      <!-- hai:{"id":"simple-78caa9fe22d090fa","updatedAt":"2026-10-21T17:11:57.851Z"} -->

- [ ] [43] Investigate the 11 server browser failures also reproduced on main.
      <!-- hai:{"updatedAt":"2026-10-17T08:24:54.209Z"} -->

- [ ] [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in
  `SECURITY.md`.
      <!-- hai:{"id":"simple-d0a68dc82549f87f","updatedAt":"2026-10-17T08:24:53.222Z"} -->

- [x] [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their
  registration in `vfs.py`. JSON is a browser virtual filesystem. CSV comes in phase 8.
      <!-- hai:{"id":"simple-8cc5cb10b6db5cb0","updatedAt":"2026-10-21T19:50:30.028Z"} -->

- [x] [41] Fix plain-text reStructuredText previews in Source and Rendered modes.
      <!-- hai:{"updatedAt":"2026-10-21T14:12:57.477Z"} -->

- [x] [64] Keep subfolder and folded parent widths stable during Up/Down navigation.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:00.460Z"} -->

- [x] [*] Add the `Delete` key as a shortcut to delete the current file or directory.
      <!-- hai:{"id":"simple-733e4b4bae09fdf7","updatedAt":"2026-10-21T14:13:03.475Z"} -->

- [x] [*] When returning focus back to the containing folder from the preview pane using the
  left arrow key, always keep all ancestor folder columns in the same expanded/collapsed
  state as they are. Currently expanded ancestor folders are collapsed if I hit the left
  arrow key.
      <!-- hai:{"id":"simple-e604b54e598da82b","updatedAt":"2026-10-21T14:13:05.486Z"} -->

- [x] [*] Treat `.py.j2` as Python.
      <!-- hai:{"id":"simple-2ff9c56170d9a118","updatedAt":"2026-10-21T14:13:06.879Z"} -->

- [x] [*] When all folder columns are collapsed, exiting the preview pane using the arrow
  left key doesn't currently expand the parent folder column (rightmost folder column
  just before the preview pane). Make sure left arrow always expands the parent folder
  column.
      <!-- hai:{"id":"simple-ab72d7c18c51fff6","updatedAt":"2026-10-21T14:13:09.171Z"} -->

- [ ] [*] `.jsonl` files larger than 512 KB aren't previewed or made navigable in a contents
  column. Instead, the message `⚠ Too large to browse (over 512 KB)` appears in the
  column. Solve handling of large `.jsonl` files. Use Fable Medium to solve this. Use
  3rd party libraries if that helps.
      <!-- hai:{"id":"simple-0f26b9b92836a26f","updatedAt":"2026-10-17T08:24:49.361Z"} -->

- [x] [*] From documentation, docstrings and comments, remove references to specific
  development setups which include e.g. server names and local paths.
      <!-- hai:{"id":"simple-ea7f9f2b5da73868","updatedAt":"2026-10-21T19:50:34.172Z"} -->

- [x] [96] Remove the tailnet hostname from all files and from history
      <!-- hai:{"id":"simple-67027c02-b019-474e-a497-05db579c17c2","labels":["steward"],"createdAt":"2026-10-17T07:08:55.437Z","updatedAt":"2026-10-19T21:04:02.635Z"} -->

- [x] [90] Run the static bundle, static development and server CI suites in parallel
  <!-- hai:{"id":"simple-8b926d81-b116-4839-987a-c05a6e7930a0","createdAt":"2026-10-12T13:32:52.839Z","updatedAt":"2026-10-17T07:09:36.159Z"} -->

- [x] [*] Share Chromium, and the server where tests allow, across `server/tests/test_browser_new_ui.py`. Per-test startup and teardown cost about 200s of the 611s server suite in run 38630672866 (see [91]). Measure pytest workers afterwards.
  <!-- hai:{"id":"simple-adb180cf-7f03-46bb-86ca-b374139716ab","createdAt":"2026-10-14T20:37:41.753Z","updatedAt":"2026-10-15T20:17:19.776Z"} -->

- [x] [*] `static/test-rich.py::test_markdown_viewport` counts `td` cells without waiting after viewport and fullscreen changes; it failed `assert 0 == 20` in the `--dev` suite of run 38630672866.
  <!-- hai:{"id":"simple-e983b058-8891-4280-9712-04ba9dcbfb61","createdAt":"2026-10-14T20:37:42.533Z","updatedAt":"2026-10-15T20:16:19.320Z"} -->

- [x] [91] Report the slowest tests in each CI suite
  <!-- hai:{"id":"simple-80260468-7074-4230-adda-ff1ce00e1fe5","createdAt":"2026-10-12T13:32:53.680Z","updatedAt":"2026-10-17T07:09:37.860Z"} -->

- [x] [87] Make CI green so GitHub Pages publishes
  <!-- hai:{"updatedAt":"2026-10-14T13:16:05.732Z"} -->

- [x] [92] Scope CI cancellation to the same branch or pull request
  <!-- hai:{"id":"simple-e40d6c02-1029-4f85-b7d6-3189430599b8","createdAt":"2026-10-12T13:32:54.478Z","updatedAt":"2026-10-14T20:15:31.951Z"} -->

- [x] [89] Markdown previews show two Raw buttons
  <!-- hai:{"updatedAt":"2026-10-11T19:28:33.081Z"} -->

- [x] [80] Left arrow doesn't preview the whole document after returning from per-section preview
  <!-- hai:{"id":"simple-c4d74fd6-cd42-426e-9cda-819fbf9965c3","priority":"none","labels":[],"createdAt":"2026-10-08T16:24:33.129Z","updatedAt":"2026-10-11T19:27:12.770Z"} -->

- [x] [84] JSON member in an archive shows a chevron but does not open
  <!-- hai:{"updatedAt":"2026-10-11T19:03:14.084Z"} -->

- [x] [78] Wide document scrolls instead of expanding the preview
  <!-- hai:{"id":"simple-78e15d9a-0d90-4186-953f-46fdddf6fe5c","priority":"none","labels":[],"createdAt":"2026-10-08T16:19:43.075Z","updatedAt":"2026-10-11T19:05:34.107Z"} -->

- [x] [79] Remove § signs and redundant headings from document section previews
  <!-- hai:{"id":"simple-e6ef425c-e474-4559-b792-1e21478c71bb","priority":"none","labels":[],"createdAt":"2026-10-08T16:21:55.597Z","updatedAt":"2026-10-11T18:53:20.045Z"} -->

- [x] [81] Horizontal scrolling fold "stops"
  <!-- hai:{"id":"simple-d01a5118-704f-4133-953c-ead294dbc119","priority":"none","labels":[],"createdAt":"2026-10-08T19:19:18.607Z","updatedAt":"2026-10-11T19:28:58.545Z"} -->

- [x] [82] Update stale Playwright 1.61 pins and the server renderer note in docs
  <!-- hai:{"updatedAt":"2026-10-11T19:06:17.369Z"} -->

- [x] [86] Markdown in archives is not rendered
  <!-- hai:{"updatedAt":"2026-10-11T19:04:16.821Z"} -->

- [x] [85] Images in archives are not scaled to the preview pane
  <!-- hai:{"updatedAt":"2026-10-11T18:27:58.921Z"} -->

- [x] [88] Status bar hints wrap and get clipped
  <!-- hai:{"updatedAt":"2026-10-11T19:18:11.203Z"} -->

- [x] [83] Screen-reader search label shows on screen
  <!-- hai:{"updatedAt":"2026-10-11T19:00:25.515Z"} -->

- [x] [*] Make Git `.bundle` files navigable hierarchically, and if they contain previewable
  files, show them in the preview pane when navigated to.
  <!-- hai:{"id":"simple-ca7153b94516ed5f","updatedAt":"2026-10-11T08:10:30.642Z"} -->

- [x] [*] Make `.tar.zst` (and other compressed archive) files navigable hierarchically, and
  if they contain previewable files, show them in the preview pane when navigated to.
  <!-- hai:{"id":"simple-8f807623b9f707fd","updatedAt":"2026-10-11T08:09:29.993Z"} -->

- [x] [*] A 528 kB JSON file like
      https://filemill.example/backups/example/backup-manifest.json?f= isn't
      previewed nor navigable hierarchically.
      <!-- hai:{"id":"simple-fec4c3e94daf7040","updatedAt":"2026-10-17T08:20:01.188Z"} -->

- [x] [*] Similar to JSON and SQLite files, allow hierarchical navigation of Markdown
      and reStructuredText documents based on their headings.
  <!-- hai:{"id":"simple-f8626c1613849773","updatedAt":"2026-10-17T07:09:42.979Z"} -->

- [x] [77] .md tight bullet list line spacing
      <!-- hai:{"id":"simple-f6220ff8-98cd-48a2-b2ab-4744392be4a7","priority":"none","labels":[],"createdAt":"2026-10-06T18:33:12.894Z","updatedAt":"2026-10-07T15:05:44.592Z"} -->

- [x] [39] Fix Back/Forward navigation across folders, previews and raw files.
      <!-- hai:{"updatedAt":"2026-10-07T15:04:51.317Z"} -->
- [x] [*] On iPad, two touches on a folder name are required to open its contents in the
      next column. Only one touch should do it.
      <!-- hai:{"id":"simple-63ca4fc48e67d49a","updatedAt":"2026-10-07T15:03:32.602Z"} -->

- [x] [65] [*] Bug: PNG and JPEG preview doesn't work reliably. Sometimes the text
      `No inline preview for this file type.` is displayed instead of the image.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:11.059Z"} -->

- [x] [*] For hierarchical nested view of JSON, don't use the folder icon. Use the JSON
      icon for the whole file, and `{}` and `[]` icons for objects and arrays.
      <!-- hai:{"id":"simple-d79a2589a64cd338","updatedAt":"2026-10-21T14:13:11.967Z"} -->

- [x] [67] Use the vertical scrollbar to browse large directories instead of pagination.
      Virtualize directory contents efficiently.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:12.754Z"} -->

- [x] [*] Per recommendation from task dd6897a9-b54e-4ad4-b9b5-b2372292f4b1, remove
      ?no-columns, wants_columns, and url_for_state. Keep documentation up-to-date.
      <!-- hai:{"id":"simple-fbf40aa94751de5e","updatedAt":"2026-10-21T19:50:38.266Z"} -->

- [x] [68] Fix server test fixture discovery from the repository root and document the
      working pytest command.
      <!-- hai:{"updatedAt":"2026-10-21T05:16:57.569Z"} -->

- [x] [*] Do issues [38], [39], [40] and [42] each currently sit under both Scheduled
      and In Progress in the tracker? Should they be deduplicated and corrected to sit
      in the correct section so they reflect the implementation?
      <!-- hai:{"id":"simple-25a6f43e328c61c9","updatedAt":"2026-10-21T05:17:01.969Z"} -->

- [x] [*] Fix the extra mount prefix in rendered `~/...` Markdown links.
    - Depends on: [42]

      <!-- hai:{"id":"simple-5424d9c1649ac2ea","updatedAt":"2026-10-21T19:50:43.386Z"} -->

- [ ] [*] Check the two architecture reviews (`docs/2026-09-05-ARCHITECTURE-REVIEW.md`
      and `docs/2026-09-19-architecture-review-and-remediation-plan.md`). Remove
      everything that isn't valid any more. De-duplicate and refine. Write into a new
      file and remove the old ones. Use GPT-6-Astra Medium.

- [x] [*] Implement highlighting of reStructuredText (not actually properly implemented
      by [50]). Ensure unintended highlighting doesn't happen between aposthrophes in
      words. Ensure special roles are highlighted similar to how Pygments does.
      <!-- hai:{"id":"simple-69b9d05bc6cbd5cf","updatedAt":"2026-10-21T14:13:14.152Z"} -->

- [x] [42] Render `~/...` Markdown links relative to the root mount, with `?f`, instead
      of deprecated `/w/...` paths.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:15.476Z"} -->

- [ ] [37] Make the installed PWA show its server-not-running recovery page when opened
      while the server is stopped.

- [x] [69] Show copied paths in the status bar. Repeat `Ctrl+C` within 5 seconds, with
      no intervening interaction, to cycle relative path, full path and item name.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:17.677Z"} -->

- [x] [70] In preview focus, ArrowRight folds the leftmost expanded folder column, then
      enters fullscreen once columns are hidden. ArrowLeft exits fullscreen.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:19.272Z"} -->

- [x] [31] Evaluate AppKit, GTK and WinUI against the WebView prototype. Record the
      comparison in an ADR. Do not start a native toolkit before the ADR exists.
    - Depends on: [30]

      <!-- hai:{"updatedAt":"2026-10-21T05:17:06.677Z"} -->

- [x] [71] Let reStructuredText paragraphs fill the available preview width, as Markdown
      paragraphs do.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:20.207Z"} -->

- [x] [*] The `Delete` button in the preview pane gives the red error
      `Delete failed: actions.render is not a function` on the bottom status line (after
      confirming deletion).
      <!-- hai:{"id":"simple-fef3685dc982ab7b","updatedAt":"2026-10-21T14:13:20.970Z"} -->

- [x] [72] Make the browser Back button exit mobile fullscreen preview like Exit
      fullscreen, without leaving an empty preview.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:22.851Z"} -->

- [x] [*] There's no way to access the file context menu on desktop browsers. On touch
      devices, a long touch does show it. Also, the context menu is transparent and very
      hard to read. And the `Delete` item is missing from the menu.
      <!-- hai:{"id":"simple-ecb8969c9a740d42","updatedAt":"2026-10-21T14:13:25.528Z"} -->

- [x] [*] On a portrait mobile phone, Markdown preview is wider than the screen.
      Contents overflow horizontally both at the left and right edges.
      <!-- hai:{"id":"simple-9738df645fc3082f","updatedAt":"2026-10-21T14:13:26.952Z"} -->

- [ ] [*] Fix all remaining red tests (listed in project memory), including the one-line
      cause of the newest root-column regression.

- [x] [73] Fix Markdown source highlighting for headings, URLs and links without
      treating word apostrophes as delimiters. Make links clickable.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:27.871Z"} -->

- [x] [74] Remember collapsed JSON paths and apply the same collapse pattern to similar
      objects at the same depth.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:28.783Z"} -->

- [x] [*] In hierarchical navigation of `.json`, `.jsonl`, and SQLite `.db` files, when
      the key of a scalar value is highlighted, show its value in the preview pane
      instead of rendering the parent JSON structure. If the value is a string and has
      `\n` characters, display it with line breaks.
      <!-- hai:{"id":"simple-0ba6747d436ce10a","updatedAt":"2026-10-21T14:13:30.086Z"} -->

- [x] [*] Bug: The `Fullscreen` button causes a full screen view of the file to briefly
      flash, and then immediately returns to the main Filemill UI.
      <!-- hai:{"id":"simple-d66cbaa914926ffd","updatedAt":"2026-10-21T14:13:32.168Z"} -->

- [x] [*] When navigating to the parent directory using the left arrow key, make sure
      the highlighted file or directory is scrolled into view.
      <!-- hai:{"id":"simple-5fca1830a0ffbefd","updatedAt":"2026-10-21T14:13:33.951Z"} -->

- [ ] [75] Use stable folder widths in em units and let previews fill the remaining
      space. Tune automatic folding and column/preview ratios for desktop and
      portrait/landscape phones.

- [x] [*] Bug: Arrow Right into the preview pane works inconasistently. Sometimes it
      focuses the preview pane without changing the layout. Sometimes it hides the
      folder columns and stretches the preview pane to full width.
      <!-- hai:{"id":"simple-d7d4c2e34d1abfcf","updatedAt":"2026-10-21T14:13:35.273Z"} -->

- [x] [76] Keep the focused folder column's width stable during Up/Down navigation,
      without partial folding, dimmed text or overlaid folder names.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:36.082Z"} -->

- [x] [*] Feature: Clicking on a content search result now opens the raw file. Open the
      rendered file in the UI preview pane instead.
      <!-- hai:{"id":"simple-31175d0fe86ffbc4","updatedAt":"2026-10-21T14:13:37.387Z"} -->

- [x] [29] Make `ui/core/` a model package with no DOM: nodes, selection, folding
      arithmetic, keyboard map and deep links. Keep a thin DOM renderer beside it.
    - Depends on: [21]

      <!-- hai:{"updatedAt":"2026-10-21T19:50:49.551Z"} -->

- [x] [*] Delete `_document_page` — document representations, including
      `layout=no-columns`, now return the shared client shell.
      <!-- hai:{"id":"simple-8b040fc456862500","updatedAt":"2026-10-21T05:17:10.450Z"} -->

- [x] [13] Correct the stale claims that review finding 15 lists in `server/README.md`,
      `server/CONTRIBUTING.md`, `server/TASKS.md`, `docs/tasks/2-*.md` and root
      `TASKS.md`.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:39.450Z"} -->

- [x] [*] Split `applyScroll` in `ui/core/layout.js` into `foldFromScroll`,
      `applyWidths`, `panFocus` and `slideTail`. Each function is under 25 lines.
      <!-- hai:{"id":"simple-3719edde73c010f9","updatedAt":"2026-10-21T05:17:15.483Z"} -->

- [ ] [15] Split the decisions table in `static/AGENTS.md` into one dated ADR file per
      decision in `docs/adr/`. Each file has context, decision, measurement,
      consequences.

- [x] [10] Toggling `Source` / `Rendered` reloads the whole page and causes an
      uncomfortable blink and a delay. Just the preview pane should be reloaded, and the
      URL and history updated.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:42.057Z"} -->

- [x] [*] Delete the `/raw?path=` route in `app.py`. The client builds `${API}/raw?p=`
      URLs for images, PDF and HTML. Done when `grep -r raw?path server/src` prints
      nothing.
    - Depends on: [33]

      <!-- hai:{"id":"simple-6e2f3140d42e50d0","updatedAt":"2026-10-21T05:17:19.758Z"} -->

- [x] [*] Virtualise column rows. `content-visibility` made layout cheap, but a 100
      k-entry directory still builds 100 k DOM nodes. Do this only if such folders show
      up.
      <!-- hai:{"id":"simple-239d177742cf7f08","updatedAt":"2026-10-21T14:13:43.093Z"} -->

- [x] [6] Centralize file-kind classification across filesystem producers and
      preview/edit consumers. Add one test table per language that both sides share.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:43.867Z"} -->

- [ ] [44] Document demo instances matching each browser test setup.

- [x] [*] Delete `/open-link` and `_parse_desktop_url` in `app.py`. `desktopCard` in
      `ui/adapters/preview-local.js` already handles `.desktop` files in both editions.
      <!-- hai:{"id":"simple-dc3759a81ca7da4c","updatedAt":"2026-10-21T17:12:01.555Z"} -->

- [x] [*] Give each magic number in `ui/core/state.js`, `layout.js`, `nav.js`,
      `render.js` a name and a one-line comment that says why the value is what it is.
      <!-- hai:{"id":"simple-c4f050c41d8042de","updatedAt":"2026-10-21T17:12:05.776Z"} -->

- [ ] [21] Cache the preview element keyed on the previewed node and its `meta`, the
      same way `colCache` keys columns. A resize must cause zero `PREVIEW.render` calls.

- [x] [*] Delete `/sse/reload` and `LIVE_MODE` in `app.py`, `LIVE_RELOAD_JS` in
      `styles.py` and the `watchfiles` dependency. Delete their tests.
      <!-- hai:{"id":"simple-a784513db6a55664","updatedAt":"2026-10-21T17:12:10.158Z"} -->

- [ ] [*] Run the static and server browser tests through one root `conftest.py` and one
      Playwright fixture. Delete the CDN proxy plumbing in `test_browser_keyboard.py`.
    - Depends on: [25]

- [x] [*] Add a preview for `.mp4` files with a `<video controls>` element, as one
      registry entry plus one test.
    - Depends on: [26]

      <!-- hai:{"id":"simple-0add5f8e086d4935","updatedAt":"2026-10-21T14:13:45.094Z"} -->

- [ ] [*] Implement CSV as a browser virtual filesystem in `ui/adapters/vfs-csv.js`,
      like JSONL: one entry per row, a key/value preview per row. No Python. Closes
      legacy server issue #49.
    - Depends on: [26]

- [x] [*] Compute the symlink zone map one time per request in `paths.py`. Delete the
      three other walks of the root that build the same map.
    - Depends on: [24]

      <!-- hai:{"id":"simple-cb5dad9619411b8b","updatedAt":"2026-10-21T05:17:24.077Z"} -->

- [ ] [*] Stop `server/tests/conftest.py` from changing the module global `ROOT`. Done
      when `uv run pytest -n auto` passes at the repository root.

- [ ] [*] Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell becomes
      one string template. Done when `dependencies` has starlette, uvicorn, typer,
      python-pptx.
    - Depends on: [24]

- [x] [*] On mobile, long-pressing a file or directory should open a menu of actions to
      copy its base name, relative path or absolute path.
      <!-- hai:{"id":"simple-8db4dd9add33b575","updatedAt":"2026-10-21T14:13:46.970Z"} -->

- [ ] [*] Delete `server/src/filemill/styles.py`. The shell links `/ui/core/styles.css`,
      and no other server route emits HTML. Delete the tests that pin `APP_CSS`.
    - Depends on: [33], [34]

- [x] [*] Delete `/api/render` in `app.py`, `render_upload` in `api.py` and
      `ui/adapters/preview-upload.js`. Local folders in the server edition use
      PreviewRich.
    - Depends on: [32], [34]

      <!-- hai:{"id":"simple-3aedf96e37dbfa74","updatedAt":"2026-10-21T14:13:49.158Z"} -->

- [ ] [*] Each row of a JSONL file must be presented exactly like a hierarchical nested
      view of a JSON file.

- [ ] [45] Show JSON children beside a foldable preview of the selected value.

- [x] [46] Fix ancestor columns unfolding during down-arrow navigation.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:50.284Z"} -->

- [ ] [*] Keyboard navigation using arrows still doesn't animate
      folding/unfolding/resizing of columns. Do systematic debugging to identify the
      cause, and fix it.

- [ ] [7] Make entry ordering an adapter-owned contract.
    - Depends on: [6]

- [ ] [47] Fold folder columns on preview entry and restore the containing column on
      exit.

- [x] [48] Keep ancestor folding unchanged during Up/Down navigation.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:51.025Z"} -->

- [x] [*] Add a PWA manifest and service worker to the static bundle so
      `static/index.html` installs as a standalone window. The server edition already
      serves `/manifest.json`.
      <!-- hai:{"id":"simple-ed3e53b5b075f345","updatedAt":"2026-10-21T19:50:54.195Z"} -->

- [ ] [49] Fix content search errors and restrict search to the focused directory tree.

- [ ] [*] The `Fullscreen` button in the preview pane doesn't do anything. No errors
      seen on the JavaScript console either.

- [x] [50] Fix missing reStructuredText rendering and highlighting after the initial
      implementation.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:52.154Z"} -->

- [x] [51] Return raw file bytes for URLs without query parameters.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:53.368Z"} -->

- [x] [52] Return focus to the parent column when leaving the preview with ArrowLeft.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:55.780Z"} -->

- [ ] [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`.
      Quote identifiers with `"` and replace `"` inside them with `""`, or check
      `sqlite_master`.

- [x] [53] Let Markdown paragraphs wrap to the preview width instead of preserving
      linefeeds.
      <!-- hai:{"updatedAt":"2026-10-21T19:50:59.076Z"} -->

- [x] [*] Typing a right arrow when the rightmost column before the preview is focused
      should focus the preview and let the user scroll it up/down using the arrow and
      PgUp/PgDn keys.
      <!-- hai:{"id":"simple-ed61b251d476c9b7","updatedAt":"2026-10-21T14:13:58.157Z"} -->

- [x] [*] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and
      `PYGMENTS_FORMATTER` and the second `FRIENDLY_CSS` in
      `server/src/filemill/styles.py`.
      <!-- hai:{"id":"simple-d9099b5f33858c5e","updatedAt":"2026-10-21T19:51:03.482Z"} -->

- [x] [54] Keep all Markdown previews within the portrait screen width.
      <!-- hai:{"updatedAt":"2026-10-21T14:13:59.668Z"} -->

- [x] [55] Fix the favicon 404 and `renderPage is not a function` error.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:02.073Z"} -->

- [x] [*] In `ui/adapters/vfs-json.js`, merge `withJsonl` and `withJson` into
      `withVirtual`, and `withJsonlPreview` and `withJsonPreview` into
      `withVirtualPreview`.
      <!-- hai:{"id":"simple-f0abe28f8ba0a6df","updatedAt":"2026-10-21T19:51:08.377Z"} -->

- [ ] [20] Create `ui/core/limits.js` with one `TEXT_MAX` and one image extension list.
      Create one `mountRoot()` and one `currentPath()`. Delete the copies and
      `pathParts`.

- [x] [22] Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model:
      `sel[i]` is the selected name. Derive the row index when needed.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:03.562Z"} -->

- [ ] [*] Add root `CONTRIBUTING.md` (setup, tests, commit style, STE rule),
      `SECURITY.md` (threat model, how to report) and `CHANGELOG.md` (Keep a Changelog
      format).

- [x] [*] Document the full port contract in `ui/core/ports.js`: `FS.node`, `FS.blob`,
      `ROUTER.write(state, replace)`, `RouterPath.base` and every node field.
      <!-- hai:{"id":"simple-c4226038e8e9f0f4","updatedAt":"2026-10-21T17:12:13.685Z"} -->

- [ ] [*] Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and
      `server/lmt/`. Move a paragraph only if it is still true and is not elsewhere.

- [x] [*] Make root `README.md` the one explanation of the two editions and their ports.
      `server/README.md` and `static/AGENTS.md` link to it and keep edition-specific
      text.
      <!-- hai:{"id":"simple-4f48aa6ce563577e","updatedAt":"2026-10-21T05:17:29.563Z"} -->

- [ ] [*] Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`,
      `server/.claude/commands/` and `architecture-review-20260904.html`.

- [ ] [56] Add a Rendered / highlighted Source toggle beside Raw and Fullscreen.

- [x] [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno
      lint and `static/build-index.py --check`. Run `pre-commit run --all-files` until
      it passes.
      <!-- hai:{"id":"simple-aae954c8c6879d22","updatedAt":"2026-10-21T05:17:35.072Z"} -->

- [ ] [57] Fix portrait horizontal overflow potentially caused by the fold hint.

- [ ] [*] Feature: ability to delete a file or a directory from the file manager.

- [x] [*] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight`
      view.
      <!-- hai:{"id":"simple-5e3b16344b7db1cd","updatedAt":"2026-10-21T14:14:05.094Z"} -->

- [x] [58] Preserve preview mode in file URLs so Back from Raw restores the finder.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:06.795Z"} -->

- [x] [59] Fix the missing-timestamp error for YouTube WebVTT files.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:09.267Z"} -->

- [x] [*] In an installed PWA, there is no way to get back from raw file view to the
      file manager view.
      <!-- hai:{"id":"simple-2fc7af9cb8de6116","updatedAt":"2026-10-21T19:51:12.294Z"} -->

- [x] [60] Fix content searches failing with `Search timed out`.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:10.988Z"} -->

- [ ] [61] Choose unique CSV row keys and keep duplicate values independently
      selectable.

- [x] [66] Evaluate hybrid Python/Jinja highlighting and report supported alternatives.
      <!-- hai:{"updatedAt":"2026-10-21T05:17:40.274Z"} -->

- [x] [62] Prevent further left swipes from exposing a margin beside a fullscreen
      portrait preview.
      <!-- hai:{"updatedAt":"2026-10-21T19:51:16.172Z"} -->

- [x] [*] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project).
      Format `ui/` one time and commit the result as its own commit.
      <!-- hai:{"id":"simple-52ea810a3c949145","updatedAt":"2026-10-21T19:51:20.356Z"} -->

- [x] [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add
      `[tool.ruff]` with `line-length = 88`. Fix all findings. Run `ruff format`.
      <!-- hai:{"id":"simple-8ef4c9ecd63ddbd2","updatedAt":"2026-10-21T17:12:18.864Z"} -->

- [x] [63] Add Raw, Source / Rendered and Fullscreen controls to the preview toolbar.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:12.360Z"} -->

- [ ] [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail:
      the `.pv-content` timeout and the two "edit starts at the top" checks.

- [x] [*] In `ui/core/state.js`, replace `node.jsonl ? kids : sortKids(kids)` with a
      `node.ordered` flag. Each virtual provider (JSON, JSONL, SQLite) sets the flag.
      <!-- hai:{"id":"simple-0b3c8f5e45edb60a","updatedAt":"2026-10-21T19:51:25.039Z"} -->

- [x] [28] Grow the editor behind the `FS.write` port: undo, find, a line gutter and a
      "modified" mark. Each addition is one file in `ui/editor/`.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:13.966Z"} -->

- [x] [27] Try reStructuredText rendering in the browser with Pyodide or a WASM tool,
      behind the rich renderer consent switch. Record size and first-load time in an
      ADR.
    - Depends on: [26]

      <!-- hai:{"updatedAt":"2026-10-21T14:14:16.708Z"} -->

- [ ] [*] Render `.pptx` in the browser: unzip the file and show the slide text, as one
      registry entry. Then delete `_preview_pptx`, `python-pptx` and `/api/preview`.
    - Depends on: [26]

- [x] [24] Reduce `app.py` to routing: move `_resolve_safe` and the symlink map to
      `paths.py` and the PWA routes to `pwa.py`. No imports inside functions.
    - Depends on: [33], [34]

      <!-- hai:{"updatedAt":"2026-10-21T17:12:25.076Z"} -->

- [ ] [33] Keep the URL contract, drop the server-side representations: the server sends
      bytes for `?filemill=raw` and the shell for all else. The client renders the view.
    - Depends on: [32]

- [ ] [35] Decide the fate of the `/w/` named mounts and their CORS middleware: delete
      them, or make CORS opt-in and document it in `SECURITY.md`.
    - Depends on: [32]

- [x] [32] Render Markdown and `.docx` in the browser in the server edition too. Serve
      the pinned renderer modules from `ui/vendor/`. Then delete `rendering.py` and its
      deps.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:17.991Z"} -->

- [x] [34] Make the SQLite provider return JSON only. The client renders tables and rows
      with the JSON hierarchical view. Delete the HTML in `providers/sqlite.py`. Close
      [9].
      <!-- hai:{"updatedAt":"2026-10-21T14:14:19.600Z"} -->

- [x] [9] Close the conditional `ViewSpec` proposal: [34] removed the six-argument
      interface.
      <!-- hai:{"updatedAt":"2026-10-21T05:17:46.482Z"} -->

- [x] [26] Create one renderer registry, a list of `{kind, render, fallback}`. Both
      editions fill it from the same core list plus their own adapters.
      <!-- hai:{"updatedAt":"2026-10-21T14:14:21.483Z"} -->

- [x] [36] Decide how the installed PWA gets a running server: a systemd or launchd
      unit, a launcher, a desktop shell, or only a better "server not running" page.
      <!-- hai:{"updatedAt":"2026-10-21T19:51:32.874Z"} -->

- [x] [*] Add a `LICENSE` file with the MIT license text. `README.md` already says MIT.
      Use the current year and "Antti Kaihola" as the copyright holder.
      <!-- hai:{"id":"simple-e92b763f3b4733a5","updatedAt":"2026-10-21T05:17:51.357Z"} -->

- [ ] [*] Feature: Move to using `pptx-vanilla-viewer` from a CDN for previewing
      PowerPoint files. Current PPTX support was implemented in task
      38ab06e2-c607-4d4a-9978-67847e70d27d.

- [x] [*] Even in non-editing Markdown previews, let the user check/uncheck rendered
      checkboxes and edit the Markdown source to correspond to the checkbox status with
      `- [ ]` or `- [x]`.

- [x] [*] Expand `~/path` links in rendered Markdown to the mount that resolves to
      `$HOME`. Today `[text](~/note.md)` is a dead link although the file exists.

- [x] [38] Fix PPTX previews that show unspaced slide text in both modes.

- [x] [40] Return preview focus to the containing folder and selected file.

[6]: docs/tasks/6-file-kind-classification.md
[7]: docs/tasks/7-adapter-owned-entry-order.md
[9]: docs/tasks/9-vfs-viewspec.md
[10]: docs/tasks/10-preview-mode-toggle.md
[12]: docs/tasks/12-test-ui-runs-to-end.md
[13]: docs/tasks/13-correct-stale-documents.md
[15]: docs/tasks/15-split-decisions-into-adrs.md
[20]: docs/tasks/20-one-limits-one-path.md
[21]: docs/tasks/21-cache-preview-element.md
[22]: docs/tasks/22-one-selection-model.md
[24]: docs/tasks/24-split-app-py.md
[25]: docs/tasks/25-static-tests-under-pytest.md
[26]: docs/tasks/26-renderer-registry.md
[27]: docs/tasks/27-rst-in-browser.md
[28]: docs/tasks/28-editor-features.md
[29]: docs/tasks/29-core-without-dom.md
[30]: docs/tasks/30-webview-shell.md
[31]: docs/tasks/31-native-toolkit-evaluation.md
[32]: docs/tasks/32-browser-markdown-in-server-edition.md
[33]: docs/tasks/33-shell-for-every-representation.md
[34]: docs/tasks/34-sqlite-json-only.md
[35]: docs/tasks/35-decide-web-mounts.md
[36]: docs/tasks/36-pwa-start-server.md
[37]: docs/tasks/37-pwa-startup-offline-recovery.md
[66]: docs/tasks/66-py-j2-highlighting.md
[38]: docs/tasks/38-pptx-rendered-preview.md
[39]: docs/tasks/39-browser-history-navigation.md
[40]: docs/tasks/40-preview-return-containing-folder.md
[41]: docs/tasks/41-rst-rendering-regression.md
[42]: docs/tasks/42-tilde-link-mount-prefix.md
[43]: docs/tasks/43-server-browser-baseline-failures.md
[44]: docs/tasks/44-browser-test-demo-instances.md
[45]: docs/tasks/45-json-selected-value-preview.md
[46]: docs/tasks/46-down-arrow-ancestor-unfolding.md
[47]: docs/tasks/47-preview-focus-folding.md
[48]: docs/tasks/48-preserve-ancestor-fold-state.md
[49]: docs/tasks/49-content-search-scope.md
[50]: docs/tasks/50-rst-rendering-first-regression.md
[51]: docs/tasks/51-raw-url-redirect.md
[52]: docs/tasks/52-preview-left-arrow-focus.md
[53]: docs/tasks/53-markdown-paragraph-wrapping.md
[54]: docs/tasks/54-portrait-markdown-width.md
[55]: docs/tasks/55-favicon-deeplink-error.md
[56]: docs/tasks/56-rendered-source-toggle.md
[57]: docs/tasks/57-portrait-fold-hint-overflow.md
[58]: docs/tasks/58-raw-history-preview-mode.md
[59]: docs/tasks/59-youtube-webvtt-timestamps.md
[60]: docs/tasks/60-content-search-timeout.md
[61]: docs/tasks/61-csv-unique-row-keys.md
[62]: docs/tasks/62-portrait-preview-swipe-overflow.md
[63]: docs/tasks/63-preview-toolbar-controls.md
[64]: docs/tasks/64-column-width-stability.md
[65]: docs/tasks/65-image-preview-unreliability.md
[67]: docs/tasks/67-scroll-large-directories.md
[68]: docs/tasks/68-server-pytest-fixture-discovery.md
[69]: docs/tasks/69-copy-path-status-cycle.md
[70]: docs/tasks/70-preview-arrow-fullscreen.md
[71]: docs/tasks/71-rst-paragraph-wrapping.md
[72]: docs/tasks/72-mobile-fullscreen-back.md
[73]: docs/tasks/73-markdown-source-highlighting.md
[74]: docs/tasks/74-json-collapse-patterns.md
[75]: docs/tasks/75-standard-column-widths.md
[76]: docs/tasks/76-focused-column-width-stability.md
[*]: TASKS.md

---

[77]: docs/tasks/77-md-tight-bullet-list-line-spacing.md

<!-- hai:reserved-numbers:6,7,9,10,12,13,15,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148 -->

[78]: docs/tasks/78-wide-document-scrolls-instead-of-expanding-the-preview.md

[79]: docs/tasks/79-remove-signs-and-redundant-headings-from-document-section-previews.md

[80]: docs/tasks/80-left-arrow-doesn-t-preview-the-whole-document-after-returning-from-per.md

[81]: docs/tasks/81-horizontal-scrolling-fold-stops.md

[82]: docs/tasks/82-stale-playwright-pins-and-server-renderer-note.md

[83]: docs/tasks/83-screen-reader-search-label-shows-on-screen.md

[84]: docs/tasks/84-json-member-in-archive-shows-chevron-but-does-not-open.md

[85]: docs/tasks/85-images-in-archives-are-not-scaled.md

[86]: docs/tasks/86-markdown-in-archives-is-not-rendered.md

[87]: docs/tasks/87-make-ci-green-so-pages-publishes.md

[88]: docs/tasks/88-status-bar-hints-wrap-and-get-clipped.md

[89]: docs/tasks/89-markdown-previews-show-two-raw-buttons.md

[90]: docs/tasks/90-run-the-static-bundle-static-development-and-server-ci-suites-in-paral.md

[91]: docs/tasks/91-report-the-slowest-tests-in-each-ci-suite.md

[92]: docs/tasks/92-scope-ci-cancellation-to-the-same-branch-or-pull-request.md

[93]: docs/tasks/93-make-main-s-ci-green-again-static-bundle-test-failing-since-06792cb.md

[94]: docs/tasks/94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md

[95]: docs/tasks/95-reconcile-tasks-md-with-the-code-16-in-progress-and-109-legacy-complet.md

[96]: docs/tasks/96-remove-the-tailnet-hostname-from-all-files-and-from-history.md

[97]: docs/tasks/97-fix-intermittent-preview-404-after-deleting-the-selected-file.md

[98]: docs/tasks/98-investigate-mobile-landscape-wide-folder-navigation-timeout.md

[99]: docs/tasks/99-rebase-25-s-pytest-migration-onto-main-and-merge-it-once-the-full-suit.md

[100]: docs/tasks/100-check-the-19-newest-review-queue-items-against-the-acceptance-policy.md

[101]: docs/tasks/101-make-the-browser-keyboard-tests-wait-for-each-opened-folder-before-the.md

[102]: docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md

[103]: docs/tasks/103-close-the-directory-index-path-escape-and-authorize-save-and-delete-a1.md

[104]: docs/tasks/104-make-preview-content-inert-wikilink-text-and-docx-output-a2.md

[105]: docs/tasks/105-correct-the-current-edition-and-renderer-documentation-roadmap-phase-0.md

[106]: docs/tasks/106-link-or-remove-every-lint-suppression-and-the-obsolete-pptx-skip-roadm.md

[107]: docs/tasks/107-date-superseded-roadmap-and-adr-claims-roadmap-phase-0.md

[108]: docs/tasks/108-wait-for-pagedown-scrolling-in-the-static-keyboard-test.md

[109]: docs/tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md

[110]: docs/tasks/110-confusing-diagonal-scroll.md

[111]: docs/tasks/111-renders-html-comments-in-markdown-documents.md

[112]: docs/tasks/112-section-links-and-heading-fragments-don-t-open-the-heading.md

[113]: docs/tasks/113-fix-the-five-tests-that-failed-in-github-ci-after-the-history-push.md

[114]: docs/tasks/114-sandbox-html-previews-of-archive-members-as-security-md-promises.md

[115]: docs/tasks/115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md

[116]: docs/tasks/116-sandbox-the-raw-view-of-html-files-inside-archives-with-a-content-secu.md

[117]: docs/tasks/117-clarify-cache-and-recovery-claims-from-docs-question-2.md

[118]: docs/tasks/118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md

[119]: docs/tasks/119-document-the-menu-copy-exception-from-docs-question-4.md

[120]: docs/tasks/120-disable-server-search-in-local-folders-from-docs-question-5.md

[121]: docs/tasks/121-clarify-api-path-collisions-from-docs-question-6.md

[122]: docs/tasks/122-clarify-deliberate-test-delays-from-docs-question-8.md

[123]: docs/tasks/123-clarify-conditional-test-skips-from-docs-question-9.md

[124]: docs/tasks/124-explain-dependency-constraints-from-docs-question-10.md

[125]: docs/tasks/125-clarify-network-consent-scope-from-docs-question-11.md

[126]: docs/tasks/126-align-decision-timing-rules-from-docs-question-12.md

[127]: docs/tasks/127-correct-icon-generator-claims-from-docs-question-13.md

[128]: docs/tasks/128-never-list-or-serve-hidden-files-on-a-public-instance.md

[129]: docs/tasks/129-remove-the-obsolete-w-and-n-url-routes.md

[130]: docs/tasks/130-give-served-and-browser-owned-folders-the-same-content-search.md

[131]: docs/tasks/131-close-the-gaps-found-in-five-older-review-items.md

[132]: docs/tasks/132-re-check-the-architecture-review-against-current-main.md

[133]: docs/tasks/133-protect-saves-from-truncation-and-stale-overwrites-architecture-review.md

[134]: docs/tasks/134-refresh-json-columns-from-the-current-file-architecture-review-a13.md

[135]: docs/tasks/135-keep-bundle-repositories-alive-through-active-reads-architecture-revie.md

[136]: docs/tasks/136-security-scan-of-filemill-served-roots-mutations-previews-caches-and-h.md

[137]: docs/tasks/137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md

[138]: docs/tasks/138-make-public-instances-read-only-and-check-host-on-every-route-security.md

[139]: docs/tasks/139-stop-rst-previews-and-search-results-from-injecting-live-markup-securi.md

[140]: docs/tasks/140-reuse-the-preview-element-across-resizes-and-folding.md

[141]: docs/tasks/141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md

[142]: docs/tasks/142-recover-the-revision-and-failing-tests-of-the-old-server-browser-basel.md

[143]: docs/tasks/143-check-whether-the-demo-instances-show-up-in-the-development-dashboard.md

[144]: docs/tasks/144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md

[145]: docs/tasks/145-add-three-missing-browser-regressions-focused-search-scope-http-entry-.md

[146]: docs/tasks/146-check-filemill-s-readme-contributor-docs-goals-and-roadmap-against-cur.md

[147]: docs/tasks/147-allow-only-known-elements-and-attributes-in-restructuredtext-previews.md

[148]: docs/tasks/148-say-in-bind-s-help-that-an-explicit-flag-wins-over-filemill-bind.md

## Rules

Here are the rules for TASKS.md usage:

### TASKS.md maintenance sessions

- In `## Completed / Accepted`, `- [ ] [N] summary` or `- [ ] [*] summary` means
  completed work awaiting user acceptance. `- [x] [N] summary` or `- [x] [*] summary`
  means the user has accepted it. Only user acceptance, or the steward's under its acceptance policy, changes `[ ]` to `[x]`;
  completion, tests and deployment do not.
- Move newly completed issues into `## Completed / Accepted` with `[ ]`.
- During the next maintenance run, remove only `[x]` issues from this section, plus
  their unused description files and reference-style links. Keep `[ ]` issues and any
  files or links still referenced by another issue.
- Each issue must retain either
    - a numbered reference-style link (e.g. `[1]`) to a description file, or
    - `[*]` to indicate no description file is needed for a simple task.
- `[~]` marks an issue that is actively in progress. When the issue is complete, move it
  to `## Completed / Accepted` with `[ ]`, pending user acceptance.
- Link references are listed between `## Completed / Accepted` and `## Rules`.
- Keep summaries concise. Move detailed requirements, rationale, examples and acceptance
  criteria into `docs/tasks/N-issue-description.md`; preserve simple tasks inline. Reuse
  an existing description for the same issue.
- For a new description, use the first unused number, checking both this file and
  description filenames in Git history. Do not reuse numbers of accepted issues.
- The section records work status; the checkbox in `## Completed / Accepted` records
  user acceptance. Completed descriptions retain historical requirements, paths and
  validation results; they are not current implementation instructions. Date later
  corrections and distinguish regressions from earlier work.
- Any completed tasks which haven't yet been moved from `## In Progress` to
  `## Completed / Accepted` should be moved there.
- Any in progress tasks which haven't yet been moved from `## Ordered backlog` or
  `## Scheduled` to `## In Progress` should be moved there.
- Ensure there are no duplicate sections, and that they are in the correct order:
  `## Unverified proposals` -> `## Ordered backlog` -> `## Scheduled` ->
  `## In Progress` -> `## Completed / Accepted` -> `## Rules`.

### Modifying issues

- Ensure dependencies between issues are correctly updated.
- State dependencies using
    - indented `- Depends on: [N]` bullets in TASKS.md, and
    - YAML frontmatter in description files.
- Ensure backlog order respects dependencies.
- When you move an issue, preserve its identifier, text and line wrapping. Change only
  the status checkbox when completion or user acceptance requires it. This keeps moves
  identifiable in Git and reduces avoidable conflicts.

### Workflow for new issue completion

Below, `<filename>@<branch>` means you must operate on the file in the specified branch.

1. Choose issue and schedule work (typically by a heartbeat)

- Pick a backlog issue from `TASKS.md@main`. Pick the first issue that has no dependency
  to any uncompleted issue.
- Move it under `## Scheduled` in `TASKS.md@main` and remove it from
  `## Ordered backlog` and commit `main`.

2. Work on the issue (typically by a task workflow)

- Move the issue under `## In Progress` in `TASKS.md@<worktree-branch>`, ensure no copy
  is left in `## Ordered backlog`.
- Create or update, review and refine a plan in
  `docs/tasks/<N-issue-description>.md@<worktree-branch>`, if more description is needed
  than nicely fits in a bullet point. If you created a plan document, link to it using a
  new `[N]` reference-style link.
- If needed, reword the issue in `TASKS.md@<worktree-branch>` to be more accurate.
- Commit description file (if any) and `TASKS.md@<worktree-branch>`.
- Implement the plan, and lint, test, review and refine the implementation in the
  worktree feature branch.

3. Merge and deploy (typically by last steps of a task workflow)

- Rebase the worktree feature branch on `main` and resolve any conflicts.
- Merge the rebased branch on `main`.
- Keep the worktree and branch after merging. Remove them only when the user
  explicitly requests it.
- Move the issue from `## In Progress` to `## Completed / Accepted` in `TASKS.md@main`
  with `[ ]`, pending user acceptance, and commit.
- Do any deployment steps if defined in the general development worklow.
