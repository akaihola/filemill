export function editorUndo(ta, changed) {
  const past = [], future = [];
  let previous = ta.value;
  let selection = [ta.selectionStart, ta.selectionEnd];
  let composing = false;
  const remember = () => {
    const text = ta.value;
    if (text === previous) return;
    let start = 0, end = previous.length, nextEnd = text.length;
    while (start < end && start < nextEnd && previous[start] === text[start]) {
      start++;
    }
    while (
      end > start && nextEnd > start && previous[end - 1] === text[nextEnd - 1]
    ) {
      end--;
      nextEnd--;
    }
    past.push({
      start,
      removed: previous.slice(start, end),
      text: text.slice(start, nextEnd),
      before: selection,
      after: [ta.selectionStart, ta.selectionEnd],
    });
    future.length = 0;
    previous = text;
    selection = [ta.selectionStart, ta.selectionEnd];
  };
  const restore = (redo) => {
    if (ta.readOnly || composing) return;
    const from = redo ? future : past, to = redo ? past : future;
    const change = from.pop();
    if (!change) return;
    const remove = redo ? change.removed : change.text;
    const insert = redo ? change.text : change.removed;
    ta.setRangeText(insert, change.start, change.start + remove.length);
    selection = redo ? change.after : change.before;
    ta.setSelectionRange(...selection);
    previous = ta.value;
    to.push(change);
    changed();
  };
  ta.addEventListener("beforeinput", (e) => {
    if (e.inputType === "historyUndo" || e.inputType === "historyRedo") {
      e.preventDefault();
      restore(e.inputType === "historyRedo");
    } else if (!composing) selection = [ta.selectionStart, ta.selectionEnd];
  });
  ta.addEventListener("compositionstart", () => {
    selection = [ta.selectionStart, ta.selectionEnd];
    composing = true;
  });
  ta.addEventListener("compositionend", () => {
    composing = false;
    remember();
    changed();
  });
  ta.addEventListener("input", () => {
    if (!composing) remember();
    changed();
  });
  ta.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === "z") {
      e.preventDefault();
      restore(e.shiftKey);
    }
  });
}
