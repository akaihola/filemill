---
depends-on: []
---

# Fix portrait horizontal overflow potentially caused by the fold hint

## Original report and requirements

Bug: Task 511f90cc-2725-4ef1-a8d8-ed67c4eddb0f failed to fix the portrait mobile
scroll to the right problem. I suspect the extra space at the right side of the page
is caused by the `⇧+wheel fold` label flowing outside the right edge of the page.
