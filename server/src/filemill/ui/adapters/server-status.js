/* ═══════════════════════════════════════════════════════════════════════════
   Server status — whether the Filemill server answers. Server build only.

   The page learns that its server is gone from its own requests, never from
   navigator.onLine: a browser without internet still reaches a server on
   127.0.0.1, and a headless one can say "offline" while that server answers.
   Every read and write in adapters/http.js goes through serverFetch. While the
   server is away, the service worker answers reads with the copies it kept,
   marked X-Filemill-Offline (server/src/filemill/static/sw.js), and the
   indicator in the top bar says that the server is offline. A click, a tap,
   Enter or Space expands it into what that means and what to do. ADR 0089.

       online        hidden
       offline       no answer, a 502–504 from a proxy, or an offline copy
       reconnecting  a probe is out
       refused       the server answered 403 to a change
       recovered     answering again after being offline; brief

   The probe fetches the shell, past the worker, and takes its mutation token:
   a restarted server has a new one, and the old one would refuse every save.
   ═══════════════════════════════════════════════════════════════════════════ */

const OFFLINE_HEADER = "X-Filemill-Offline";
/* What a proxy answers when the Filemill server behind it does not. */
const UNAVAILABLE = [502, 503, 504];
const ONLINE_PROBE_MS = 30_000;
const OFFLINE_PROBE_MS = 5_000;
const RECOVERED_MS = 4_000;

const AWAY =
  "Filemill cannot reach its server. Folders and files from the server " +
  "that are on screen were loaded earlier and may be out of date. Nothing " +
  "can be saved or deleted until the server is back.";
const HELP = "Start Filemill on the machine that serves it, for example with " +
  "<code>uv run filemill [ROOT]</code>, then choose Retry now. Filemill " +
  "also retries every few seconds. The installed app can connect to the " +
  "server but cannot start it. If someone else runs the server, it returns " +
  "when they restart it.";
const TEXT = {
  offline: ["Server offline", AWAY, HELP],
  reconnecting: ["Reconnecting…", AWAY, HELP],
  refused: [
    "Change refused",
    "The server is running but refused the last change. If it restarted " +
    "since this page loaded, Retry now fetches a new session; then make the " +
    "change again. If it keeps refusing, the server may not accept this " +
    "address: see FILEMILL_ORIGINS in its documentation.",
    "",
  ],
  recovered: ["Server back online", "Filemill reaches its server again.", ""],
};

export class ServerOffline extends Error {
  constructor() {
    super("Server offline");
    this.name = "ServerOffline";
  }
}

let state = "online";
/* A read was answered offline since the last recovery, so what is on
   screen may be older than the server's files. */
let readOffline = false;
let probing = null;
let probeTimer = 0;
let hideTimer = 0;
let onRecover = () => {};
let ui = null;

export const serverOffline = () =>
  state === "offline" || state === "reconnecting";

/* True when the worker answered with a copy kept from an earlier read. */
export const offlineCopy = (response) =>
  response.headers.get(OFFLINE_HEADER) === "copy";

/* fetch, for the Filemill server: reports what the answer says about the
   server, and throws ServerOffline when there is no answer to use. */
export async function serverFetch(url, init = {}) {
  let response;
  try {
    response = await fetch(url, init);
  } catch (err) {
    if (err.name === "AbortError") throw err;
    unreachable(init);
    throw new ServerOffline();
  }
  if (
    response.headers.has(OFFLINE_HEADER) ||
    UNAVAILABLE.includes(response.status)
  ) {
    unreachable(init);
    if (!response.ok) throw new ServerOffline();
  } else if (response.status === 403) {
    set("refused");
  } else if (serverOffline()) {
    void probe();
  }
  return response;
}

function unreachable(init) {
  if ((init.method || "GET") === "GET") readOffline = true;
  set("offline");
}

/* Ask the server, past the service worker, and take a fresh mutation token. */
export function probe() {
  if (probing) return probing;
  if (state === "offline") set("reconnecting");
  probing = (async () => {
    try {
      const base = document.documentElement.dataset.base || "/";
      const response = await fetch(`${base}?filemill=render`, {
        cache: "no-store",
      });
      if (UNAVAILABLE.includes(response.status)) throw new ServerOffline();
      const shell = new DOMParser().parseFromString(
        await response.text(),
        "text/html",
      );
      const token = shell.documentElement.dataset.mutationToken;
      if (token) document.documentElement.dataset.mutationToken = token;
      answered();
    } catch {
      set("offline");
    } finally {
      probing = null;
      schedule();
    }
  })();
  return probing;
}

function answered() {
  if (state === "online" || state === "recovered") return;
  if (state === "refused") return set("online");
  const refresh = readOffline;
  readOffline = false;
  set("recovered");
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    if (state === "recovered") set("online");
  }, RECOVERED_MS);
  onRecover(refresh);
}

function schedule() {
  clearTimeout(probeTimer);
  probeTimer = setTimeout(
    () => document.hidden ? schedule() : probe(),
    serverOffline() ? OFFLINE_PROBE_MS : ONLINE_PROBE_MS,
  );
}

function set(next) {
  if (next === state) return;
  state = next;
  if (!probing) schedule();
  if (!ui) return;
  const [label, text, help] = TEXT[next] || ["", "", ""];
  ui.root.hidden = next === "online";
  ui.root.dataset.state = next;
  ui.label.textContent = label;
  ui.text.textContent = text;
  ui.help.innerHTML = help;
  ui.help.hidden = !help;
  ui.retry.disabled = next === "reconnecting";
  if (next === "online") expand(false);
}

function expand(open) {
  ui.toggle.setAttribute("aria-expanded", String(open));
  ui.details.hidden = !open;
}

/* Put the indicator in the top bar and start watching. `recover(refresh)`
   runs when the server answers again; `refresh` says that reads were
   answered offline in the meantime, so their content needs reading again. */
export function initServerStatus(recover) {
  onRecover = recover;
  document.getElementById("gear").insertAdjacentHTML(
    "beforebegin",
    `<div id="server-status" hidden><button type="button" class="tb" id="server-status-toggle" aria-expanded="false" aria-controls="server-status-details"><span class="dot" aria-hidden="true"></span><span id="server-status-label" aria-live="polite"></span></button><div id="server-status-details" hidden><p id="server-status-text"></p><p id="server-status-help" hidden></p><button type="button" id="server-status-retry">Retry now</button></div></div>`,
  );
  const $ = (id) => document.getElementById(id);
  ui = {
    root: $("server-status"),
    toggle: $("server-status-toggle"),
    label: $("server-status-label"),
    details: $("server-status-details"),
    text: $("server-status-text"),
    help: $("server-status-help"),
    retry: $("server-status-retry"),
  };
  ui.toggle.onclick = () =>
    expand(ui.toggle.getAttribute("aria-expanded") !== "true");
  ui.retry.onclick = () => probe();
  /* Enter and Space press these buttons; the finder's keyboard model, which
     listens on the document, would otherwise take them as "open" and
     type-ahead. Escape closes the details. */
  ui.root.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !ui.details.hidden) {
      e.preventDefault();
      expand(false);
      ui.toggle.focus();
    }
    if (["Enter", " ", "Escape"].includes(e.key)) e.stopPropagation();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) probe();
  });
  /* The connectivity flag is a hint to ask, not an answer. */
  addEventListener("online", () => probe());
  addEventListener("offline", () => probe());
  schedule();
}
