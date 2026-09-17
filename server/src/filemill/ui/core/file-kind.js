import { IMAGE_EXTENSIONS } from "./limits.js";

const RICH = new Set(["md", "markdown", "rst", "docx", "pptx"]);
const image = new RegExp(`^(?:${IMAGE_EXTENSIONS.join("|")})$`, "i");

export function classifyFile(name, { dir = false, vpath = "", csv = false,
  jsonl = false } = {}) {
  if (dir) return { kind: "folder", preview: "none", editable: false };
  if (vpath || csv || jsonl) {
    return { kind: "vfs", preview: "virtual", editable: false };
  }
  const match = String(name || "").toLowerCase().match(/\.([^.]+)$/);
  const ext = match?.[1] || "";
  if (image.test(ext)) return { kind: "file", preview: "image", editable: false };
  if (ext === "pdf") return { kind: "file", preview: "pdf", editable: false };
  if (ext === "html" || ext === "htm") {
    return { kind: "file", preview: "html", editable: false };
  }
  if (ext === "desktop") return { kind: "link", preview: "desktop", editable: false };
  if (ext === "vtt") return { kind: "file", preview: "vtt", editable: true };
  if (RICH.has(ext)) {
    return { kind: "file", preview: ext, editable: ["md", "markdown", "rst"].includes(ext) };
  }
  return { kind: "file", preview: "text", editable: true };
}
