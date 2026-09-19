---
depends-on: []
---

# Fix the missing-timestamp error for YouTube WebVTT files

## Original report and requirements

Bug: For `.vtt` files from YouTube, this error is always displayed instead of the
content: `Malformed WebVTT: cue is missing a timestamp`. You may test using `.vtt`
files found on the filesystem.
