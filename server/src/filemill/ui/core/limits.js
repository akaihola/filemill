export const TEXT_MAX = 512 * 1024;
export const JSON_MAX = 8 * 1024 * 1024;
/* Deeper JSON is shown as source. Engines differ by orders of magnitude in
   how deep they recurse before giving up, and how long that takes. */
export const JSON_FOLD_DEPTH = 1000;
export const IMAGE_EXTENSIONS = [
  "png",
  "jpg",
  "jpeg",
  "gif",
  "webp",
  "avif",
  "bmp",
  "ico",
  "svg",
];
