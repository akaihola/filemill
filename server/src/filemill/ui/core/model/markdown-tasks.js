/* A rendered task checkbox names its 0-based source line. The line must still
   start with a list marker and the mark the render showed; anything else means
   the source moved on, and nothing is rewritten. */
const TASK = /^((?:[ \t]*>)*[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+\[)([ xX])(\] )/;

export function toggleTask(text, line, checked) {
  const lines = text.split("\n");
  if (!Number.isInteger(line) || line < 0 || line >= lines.length) return null;
  const match = TASK.exec(lines[line]);
  if (!match || (match[2] !== " ") === checked) return null;
  lines[line] = match[1] + (checked ? "x" : " ") +
    lines[line].slice(match[1].length + 1);
  return lines.join("\n");
}
