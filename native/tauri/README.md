# Tauri comparison candidate

This temporary candidate is not qualified for release. Its filesystem check
passes, but the same WebKit scrolled-row interaction blocks the UI suite.
The direct WebKit host also has root-picker and navigation isolation work
that this comparison candidate does not yet have. Sizes are provisional,
not evidence of a passing winner.

Build from the repository root after building the shared native resource:

```bash
nix-shell -p webkitgtk_4_1 gtk3 pkg-config openssl --run 'cargo build --manifest-path native/tauri/Cargo.toml --release --locked -j 2'
TAURI_WEBVIEW_AUTOMATION=true \
FILEMILL_NATIVE_BINARY=native/tauri/target/release/filemill-tauri-comparison \
nix-shell native/shell.nix --run 'uv run --project server pytest static/test-ui.py::test_ui --native -q'
```

Cargo.lock pins Tauri 2.11.6. The initial stripped executable measured
3,053,312 bytes, with a 288,920-byte embedded UI input. Later shared native
changes require rebuilding before a final comparison. The build does not
include the system WebKitGTK runtime in the executable size.
