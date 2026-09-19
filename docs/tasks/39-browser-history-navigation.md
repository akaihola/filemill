---
depends-on: []
---

# Fix Back/Forward navigation across folders, previews and raw files

## Original report and requirements

Bug: Back and Forward navigation doesn't work correctly. Fix browser history
management so that navigating back and forward works as expected when moving between
folders and files and raw files. Also make sure `Alt`+`ArrowLeft`/`ArrowRight` works
as expected.

## Related work

[58] records the earlier Raw-to-preview URL regression. This report also covers
folder navigation and Alt+ArrowLeft/ArrowRight, so it remains a separate task.

[58]: 58-raw-history-preview-mode.md
