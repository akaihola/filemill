# Vendored renderer modules

The server edition serves these from `/ui/vendor/` so that Markdown and `.docx`
render in the browser with nothing fetched from a CDN. `_ui_shell` in
`server/src/filemill/app.py` points `window.FILEMILL_CDN` at them; the static
edition keeps the CDN URLs in `ui/adapters/preview-rich.js`. Same versions, same
pins, in both editions. Files are named `.js` because `/ui/{path}` serves only
`.js`, `.css` and `.woff` with a module-safe media type.

| File | Version | Source URL | sha256 |
| --- | --- | --- | --- |
| `markdown-it.js` | 14.1.0 | https://esm.sh/markdown-it@14.1.0/es2022/markdown-it.bundle.mjs | `2812c3ed8c99108de4686948c1f4502522466f9a0a230b5249804182fa8471b5` |
| `markdown-it-footnote.js` | 4.0.0 | https://esm.sh/markdown-it-footnote@4.0.0/es2022/markdown-it-footnote.bundle.mjs | `65e39cb32b7be7f92290e853ca47d17b8c48cebe9bafbc4386b12ae62592a6aa` |
| `markdown-it-deflist.js` | 3.0.0 | https://esm.sh/markdown-it-deflist@3.0.0/es2022/markdown-it-deflist.bundle.mjs | `984de6876e6d907a426cf21d81e7b78ca99851e5bb59409f69cf9f3530d2c725` |
| `markdown-it-task-lists.js` | 2.1.1 | https://esm.sh/markdown-it-task-lists@2.1.1/es2022/markdown-it-task-lists.bundle.mjs | `bf883a408925b43e38f410bb174c7d18aa45e92137a970532b5839f828bd18ad` |
| `markdown-it-anchor.js` | 9.2.0 | https://cdn.jsdelivr.net/npm/markdown-it-anchor@9.2.0/dist/markdownItAnchor.mjs | `7f7f9dee35c787915cd7bc3c13ba43ab8caef59a737e94dbac107c6a6a6607ea` |
| `mammoth.browser.min.js` | 1.8.0 | https://cdn.jsdelivr.net/npm/mammoth@1.8.0/mammoth.browser.min.js | `deb07bf230d1cb3e190bc5adc6743f35c6531b6571d1e5469b24f452a7f0f4ab` |
| `mammoth.js` | — | wrapper written here | — |

Why two are not esm.sh bundles: the esm.sh build of markdown-it-anchor imports
`/node/process.mjs`, and every ESM build of mammoth pulls a chain of Node
polyfills (`buffer`, `process`, `events`, `async_hooks`, `tty`) by absolute
path, which cannot be served from `/ui/vendor/`. The anchor package's own ESM
file has no imports and guards `typeof process`; mammoth's browserify build is
self-contained and assigns `globalThis.mammoth`, so `mammoth.js` imports it and
re-exports that global as the default export the loader expects.

Refresh: download the URL, keep the file name, update the hash, and check that
`grep -l 'from "/' ui/vendor/*.js` prints nothing.
