---
depends-on: []
---

# Fill the preview width with reStructuredText paragraphs

## Original report and requirements

reStructuredText paragraphs are rendered very narrow. For example
in`/home/agent/prg/feedtask/README.rst`, a the source for a paragraph is:

  ```rst
  A command-line tool to capture stdin and command output for AI tools
  (like `Roo Code`_, an AI-powered coding assistant for VSCode).
  ```

  and it's rendered as

  ```
  A command-line tool to capture stdin and command output for AI tools (like
  Roo Code, an AI-powered coding assistant for VSCode).
  ```

  even when there's ample horizontal space available. Paragraphs should be filled out
  to the available width just like in Markdown rendering.
