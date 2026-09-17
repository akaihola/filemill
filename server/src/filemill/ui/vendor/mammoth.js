/* mammoth 1.8.0 ships its browser build as a classic script that sets
   globalThis.mammoth; this wrapper gives it the default export the loader in
   ui/adapters/preview-rich.js expects. See README.md. */
import "./mammoth.browser.min.js";
export default globalThis.mammoth;
