# ADR 0064: Keep browser RST rendering behind rich-preview consent

Status: accepted, 2026-09-18. Issue [27], after registry issue [26].

## Context

The repository already contains docutils on Pyodide and an `rst` entry in
`RICH_RENDERERS`. [ADR 0002](0002-rst-in-browser.md) records the original
experiment, but its statements that the registry does not exist and the server
never imports the rich adapter are obsolete. This evaluation verifies the
current browser bundle and supplies a repeatable measurement command.

The static edition registers the RST renderer. The server imports the shared
rich adapter but excludes RST from its registry. At the original measurement
baseline, served RST used `PreviewHTTP`. Main's subsequent PPTX change removed
that adapter; both served and browser-local RST now fall back to plain text.
This task preserves the rebased main behavior rather than restoring a removed
server preview route.

## Decision

Keep the pinned Pyodide 0.29.4 distribution and its docutils 0.21.2 package.
Reuse the existing lazy loader, remembered default-on rich-preview switch,
512 KiB text limit and source fallback. No interpreter bytes enter the app
bundle, and file contents are not uploaded. Turning rich previews off prevents
the default CDN-backed RST runtime from loading. The existing exemption for
root-relative vendored modules is unchanged.

Give each `runPythonAsync` call its own Python globals and destroy that proxy
in `finally`. A delayed interpreter stub reproduced the old shared `src`
being overwritten by another preview. Both deterministic tests and the real
runtime now verify distinct output for simultaneous sources.

Docutils still disables `raw` and file insertion. The real-runtime check renders
a heading, emphasis, a note directive, a table and a footnote, and checks that
raw script markup and an include of `/etc/passwd` do not appear in the DOM.
No additional parser was evaluated: the existing Pyodide implementation meets
this bounded experiment's rendering requirements. ADR 0002 remains the record
of the earlier JavaScript alternative.

## Measurement

Measured on the gogo development host on 2026-09-18, Linux 6.12.91 x86_64,
glibc 2.42, Playwright 1.61.0, headless Chromium 149.0.7827.55. Requests went to
the pinned jsDelivr URLs without a configured browser proxy or network/CPU
throttling. No proxy environment variables were present. Upstream CDN caches
were not cleared. Other browser test suites were stopped for this run; shared
host load and public network latency remain uncontrolled.

The first measured bundle, based on main `048b2ed`, was **231,465 bytes**,
versus 231,303 before the
per-render globals fix, an increase of 162 bytes. Runtime assets remain lazy.
Sizes below come from Chromium Resource Timing. Encoded body sizes exclude
HTTP headers; decoded sizes are asset bytes after HTTP decompression, not
Python heap usage or the expanded wheel contents.

| Asset | Encoded body bytes | Decoded body bytes |
| --- | ---: | ---: |
| pyodide.mjs | 7,170 | 17,616 |
| pyodide-lock.json | 26,288 | 122,027 |
| python_stdlib.zip | 2,386,400 | 2,424,002 |
| pyodide.asm.wasm | 2,672,378 | 8,647,684 |
| pyodide.asm.js | 226,426 | 1,074,322 |
| docutils-0.21.2-py3-none-any.whl | 566,702 | 587,408 |
| Total | **5,885,364** | **12,873,059** |

The runtime download is 5.89 MB encoded and 12.87 MB decoded, using decimal MB.
All three runs returned the same sizes. Resource Timing also reported
5,887,164 total `transferSize` bytes, which includes its header-size accounting.

| Fresh context | First selection to rendered table, ms | Warm selection, ms |
| --- | ---: | ---: |
| 1 | 18,546.8 | 150.7 |
| 2 | 14,908.4 | 96.9 |
| 3 | 11,449.9 | 188.0 |
| Median | **14,908.4** | **150.7** |

The first-load measurement includes runtime/package download, initialization,
conversion, DOM insertion and browser-automation detection of the table. It
excludes initial app navigation and folder mounting. Warm selections reuse the
interpreter, with no additional runtime asset requests. These are observed
end-to-end times, not a benchmark threshold or pure conversion timings.

A review repeat after rebasing onto main `abcab66` measured a **232,097-byte**
bundle. Runtime sizes were unchanged. Cold selections took 7,547.5, 6,110.7
and 5,505.2 ms, a **6,110.7 ms median**. Warm selections took 62.6, 59.7 and
60.9 ms. The same Chromium version and command were used without concurrent
browser suites. The difference from the earlier run illustrates uncontrolled
host/network variance; it does not establish a renderer speed improvement.

The final review on main `05f44fc`, after its editor changes, measured a
**238,914-byte** bundle with unchanged runtime asset sizes. Cold
selections took 9,035.8, 6,471.6, 6,586.1 ms, median
**6,586.1 ms**; warm selections took 67.0, 58.6, 57.3 ms.
All real-runtime safety and concurrent-source checks passed again.

### Reproduce

From the repository root, with the pinned Playwright Chromium installed:

```bash
python3 static/build-index.py
python3 static/build-index.py --check
uv run --with 'playwright==1.61.0' python3 static/measure-rst.py > /tmp/rst-measure.json
```

`measure-rst.py` includes the exact RST sample and emits browser/host details,
bundle bytes, all asset URLs and sizes, individual timings and the cold median
as JSON. It serves the built page on loopback with a fake read-only folder,
uses real CDN assets without `FILEMILL_CDN` overrides, creates three fresh
browser contexts, blocks service workers and disables Chromium's HTTP cache.
Each context starts without an interpreter. A plain-text selection separates
the cold and warm RST selections. The command fails if safety/concurrency
checks fail or asset body sizes are unavailable, rather than reporting zeros.
It closes Chromium and the loopback server on exit. Run without other browser
test suites for a comparable sample. Network access is required.

## Consequences

The full parser costs several megabytes and seconds on first use. Keeping the
existing opt-out switch and readable failure fallback makes that cost bounded
to users opening RST with rich previews enabled. The UI already warns of the
approximately 13 MB renderer. Offline, initialization/package/conversion
failures show source; oversized files keep the existing absent-preview result.

The interpreter remains in memory and conversion runs on the main thread.
Heap usage was not measured in this evaluation. A worker or another parser
would need a separate performance justification; this task adds neither.
Pinned assets reduce version drift but still require CDN availability on a
cold load. Browser caching can improve later visits without being assumed in
the measurements above.

Run the focused checks with `static/test-rich.py --dev --rst` and
`static/test-rich.py --bundle --rst`, using the same pinned Playwright command
above. They cover failures, retry, consent changes, initialization reuse,
source isolation and size limits. The generated bundle freshness check and
changed-renderer lint also pass. The full rich suite still expects main's
removed PPTX viewer; the server RST test still expects the removed server
renderer. These upstream failures, and broader UI/formatting failures, are
recorded in the review handoff rather than changing unrelated contracts.

## Manual acceptance check

Serve the repository root with `python3 -m http.server 8000` and open
`http://localhost:8000/static/index.html` in Chrome or Chromium. Use a local
browser on that host, or forward port 8000 to your browser's localhost.
Select a folder containing two `.rst` documents with different headings,
a note directive and a table.

- Leave Settings → Rich previews on and select an RST file. After the first
  runtime download, its heading, directive and table should render.
- Switch rapidly between the two files. The selected file must never show
  the other file's text.
- Turn Rich previews off. RST shows source, and the setting survives reload.
  Turn it on again to restore rendering.
- In a fresh browser context, block `cdn.jsdelivr.net` in developer tools,
  then select RST with Rich previews on. The source remains readable with
  an offline note. Remove the block and reload the page to retry.

The server edition at `filemill.vempai.men` retains current main's source
preview for RST; use the static edition above to test this renderer.
Performance reproduction and interpretation are in Measurement above.
