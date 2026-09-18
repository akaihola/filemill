export function editorGutter(ta, gutter) {
  let count = 0;
  const sync = () => {
    gutter.style.transform = `translateY(${-ta.scrollTop}px)`;
  };
  ta.addEventListener("scroll", sync);
  return () => {
    const lines = ta.value.split("\n").length;
    if (lines !== count) {
      gutter.textContent = Array.from({ length: lines }, (_, i) => i + 1).join(
        "\n",
      );
      count = lines;
    }
    sync();
  };
}
