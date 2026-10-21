Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1.5 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[21] (cache the preview element) waits in the review queue because its central guarantee is missing: resizing the window or folding the tree still renders the preview again. Triage section "Prepare the specific repairs", item "Filemill preview reuse".

## Work

1. Keep the rendered preview for the same file and metadata across resizes and folding.
2. Invalidate it when the file is edited, its metadata changes or the selection moves.
3. Add tests that count preview renders.

## Acceptance

- Resizing and folding cause no extra preview rendering; an edit or a selection change renders once.
- The existing rendering budgets and editor invalidation checks pass, with the suites the Rules name.
- Add a dated pointer to this issue's evidence in [21]'s task file. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.

## Plan, 2026-10-21

1. Add failing provider-render counts for resize, folding and pending reads.
2. Retain one preview pane with explicit node, metadata and view identity.
   Invalidate pending work when selection leaves, including empty selections.
3. Check edits, metadata changes, mode changes and selection changes.
4. Run the model checks, pre-commit gate, both static suites and server suite
   one at a time under the memory guard. Record results before merging.

## Evidence, 2026-10-21

- **Red before the repair:** the new [UI regressions] counted three provider
  renders after resize and layout work, instead of one. Repeated renders also
  replaced a pane while its metadata read was pending.
- **Corrections during implementation:** retaining DOM exposed Left-arrow's
  dependence on losing focus when the pane was replaced. The [model checks]
  caught that regression and a JSON placeholder retained after its content
  became available. Left-arrow now leaves the preview explicitly, and the
  cache distinguishes placeholders from available previews. The old [Markdown
  viewport check] required a replacement after each resize. It now keeps its
  geometry checks and asserts pane identity and one slow initial render.
  A controlled delayed-outline test also caught a second render when a document
  declined its outline after its preview was visible. Content availability now
  supplies the cache distinction, without keying on the document's directory
  flag. A further failing test forced resize during the metadata read after Save; the refill now
  updates its key before that await.
- **Pending revision correction:** a controlled provider test populated a
  revision before its render resolved. A resize then replaced the pending pane.
  Pending fills now hold their incoming revision and publish the completed key
  only if their token still owns the pane. This covers HTTP providers that read
  their revision with the bytes.
- **Server readiness:** the full covered server run stopped after 415 passes
  when Firefox's fresh Markdown preview was still empty at the default
  five-second assertion timeout. The exact case passed in isolation. That
  condition-based assertion now allows 15 seconds for the real renderer,
  as other Markdown readiness checks do. It still requires the same content.
- **Implementation:** retain one pane, with node/root/port identity and a key
  for metadata values, revision, representation and relevant settings. Preserve
  raw URLs and content nodes across resize and folding. Save and Cancel refill
  the pane. Selection changes, including an empty selection, invalidate old
  async fills. The [lifetime decision] records the boundary.
- **Coverage:** provider render counts cover resize, folding, Save, metadata
  mutation/replacement, selection changes and pending fills. [Mode checks]
  count Source/Rendered changes for Markdown and WebVTT. Existing editor and
  performance budgets remain intact.

[UI regressions]: ../../static/tests/test_ui.py
[model checks]: ../../static/tests/test_model.py
[Mode checks]: ../../static/tests/test_preview_views.py
[Markdown viewport check]: ../../static/tests/test_rich.py
[lifetime decision]: ../adr/0020-pvtoken-guards-preview-fills.md
