"""Only the Playwright operations used by static/test-ui.py, over WebDriver."""

import asyncio
import base64
import json
import re
import shutil
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

from webdriver import application

KEYS = {
    "ArrowLeft": "\ue012",
    "ArrowUp": "\ue013",
    "ArrowRight": "\ue014",
    "ArrowDown": "\ue015",
    "Home": "\ue011",
    "End": "\ue010",
    "PageUp": "\ue00e",
    "PageDown": "\ue00f",
    "Enter": "\ue007",
    "Escape": "\ue00c",
    "Backspace": "\ue003",
    "Delete": "\ue017",
    "Tab": "\ue004",
    "F5": "\ue035",
    "Control": "\ue009",
    "Shift": "\ue008",
    "Alt": "\ue00a",
    "Meta": "\ue03d",
}
QUERY = r"""(selector) => {
  const match = selector.match(/^(.*?):(?:has-text|text-is)\("(.*?)"\)(.*)$/);
  if (!match) return [...document.querySelectorAll(selector)];
  return [...document.querySelectorAll(match[1])].filter(e => e.textContent.includes(match[2]))
    .flatMap(e => match[3].trim() ? [...e.querySelectorAll(match[3])] : [e]);
}"""


class Locator:
    def __init__(self, page, selector):
        self.page, self.selector = page, selector

    async def evaluate(self, fn):
        return await self.page.evaluate(
            f"({fn})(({QUERY})({json.dumps(self.selector)})[0])"
        )

    async def count(self):
        return await self.page.evaluate(
            f"({QUERY})({json.dumps(self.selector)}).length"
        )

    async def inner_text(self):
        return await self.evaluate("(e) => e.innerText")

    async def input_value(self):
        return await self.evaluate("(e) => e.value")

    async def is_visible(self):
        return await self.page.evaluate(
            f"({QUERY})({json.dumps(self.selector)}).some(e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length))"
        )

    async def get_attribute(self, name):
        return await self.evaluate(f"(e) => e.getAttribute({json.dumps(name)})")

    async def wait_for(self, state="visible", timeout=30000):
        until = time.monotonic() + timeout / 1000
        while time.monotonic() < until:
            visible = await self.is_visible()
            if visible if state == "visible" else not visible:
                return self
            await asyncio.sleep(0.05)
        raise TimeoutError(self.selector)

    async def click(self, **kwargs):
        await self.wait_for()
        element = self.page.raw.call(
            "/execute/sync",
            {"script": f"return ({QUERY})(arguments[0])[0]", "args": [self.selector]},
        )
        try:
            self.page.raw.call(
                "/element/" + element["element-6066-11e4-a52e-4f735466cecf"] + "/click",
                {},
            )
            return
        except RuntimeError as error:
            if "element not interactable" not in str(error):
                raise
        await self.evaluate("e => e.scrollIntoView({block:'nearest',inline:'nearest'})")
        await self.page.evaluate(
            "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
        )
        point = await self.evaluate("""e => {
const r = e.getBoundingClientRect();
const x = Math.floor((Math.max(0,r.left) + Math.min(innerWidth,r.right))/2);
const y = Math.floor((Math.max(0,r.top) + Math.min(innerHeight,r.bottom))/2);
if (!e.contains(document.elementFromPoint(x,y))) throw new Error('Click target is covered: ' + JSON.stringify({x,y,rect:r.toJSON(),target:e.outerHTML.slice(0,150),hit:document.elementFromPoint(x,y)?.outerHTML.slice(0,150)}));
return {x,y};
}""")
        self.page.raw.call(
            "/actions",
            {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "mouse",
                        "parameters": {"pointerType": "mouse"},
                        "actions": [
                            {"type": "pointerMove", **point},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ]
            },
        )

    async def fill(self, text):
        await self.evaluate(
            f'e => {{ e.focus(); e.value = {json.dumps(text)}; e.dispatchEvent(new InputEvent("input", {{bubbles:true, inputType:"insertText"}})); }}'
        )

    async def dispatch_event(self, event):
        await self.evaluate(
            f"e => e.dispatchEvent(new Event({json.dumps(event)}, {{bubbles:true}}))"
        )


class Keyboard:
    def __init__(self, page):
        self.page = page

    async def press(self, key):
        parts = key.split("+")
        actions = [{"type": "keyDown", "value": KEYS.get(k, k)} for k in parts]
        actions += [{"type": "keyUp", "value": KEYS.get(k, k)} for k in reversed(parts)]
        self.page.raw.call(
            "/actions",
            {"actions": [{"type": "key", "id": "keyboard", "actions": actions}]},
        )

    async def type(self, text):
        for char in text:
            await self.press(char)


class NativePage:
    def __init__(self, raw, root):
        self.raw, self.root = raw, root
        self.listeners = {}
        self.raw.evaluate(
            """() => {
window.__nativeErrors = [];
window.__nativeConsole = [];
addEventListener("error", e => __nativeErrors.push(e.message));
addEventListener("unhandledrejection", e => __nativeErrors.push(String(e.reason)));
const error = console.error.bind(console);
console.error = (...args) => {
  __nativeConsole.push({type: 'error', text: args.map(String).join(' ')});
  error(...args);
};
}"""
        )
        self.keyboard = Keyboard(self)
        self.mouse = SimpleNamespace(move=self.move)

    def on(self, event, callback):
        self.listeners[event] = callback

    async def move(self, x, y):
        self.raw.call(
            "/actions",
            {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "mouse",
                        "parameters": {"pointerType": "mouse"},
                        "actions": [{"type": "pointerMove", "x": x, "y": y}],
                    }
                ]
            },
        )

    async def goto(self, url):
        return None  # The host has already loaded its embedded resource.

    async def evaluate(self, script, arg=None):
        mounting = re.fullmatch(r"mount\(__mk\((\d+)\)\)", script)
        if mounting:
            return await self.mount(int(mounting[1]))
        adding = re.fullmatch(r"__add\(__(live|race), '([^']+)'\)", script)
        removing = re.fullmatch(r"__rm\(__(live|race), '([^']+)'\)", script)
        if adding or removing:
            match = adding or removing
            file = (
                self.root / ("refresh" if match[1] == "live" else "racing") / match[2]
            )
            if adding:
                file.write_text(match[2])
            else:
                file.unlink()
        result = self.raw.evaluate(script, arg)
        for error in self.raw.evaluate("__nativeErrors.splice(0)"):
            if "pageerror" in self.listeners:
                self.listeners["pageerror"](error)
        for message in self.raw.evaluate("__nativeConsole.splice(0)"):
            if "console" in self.listeners:
                self.listeners["console"](SimpleNamespace(**message))
        if "window.__mk = " in script:
            self.raw.evaluate("""() => {
if (window.__nativeInstrumented) return;
window.__nativeInstrumented = true;
const meta = NativeFS.loadMeta;
NativeFS.loadMeta = async n => { if (!n.dir && !n.meta) window.__gets++; return meta(n); };
const load = NativeFS.ensureLoaded;
NativeFS.ensureLoaded = async n => {
  if (!['slow', 'racing'].includes(n.rel) || n.kids !== null) return load(n);
  if (n.loading) return n.loading;
  const pending = (async () => {
    await load(n); const kids = n.kids; n.kids = null;
    await new Promise(r => setTimeout(r, n.rel === 'slow' ? 500 : 400));
    n.kids = kids; n.loading = null;
  })();
  n.loading = pending; return pending;
};
}""")
        return result

    async def mount(self, count):
        files = self.raw.evaluate(
            """async n => {
const tree = __mk(n), files = [];
async function walk(node, path) {
  if (node.kind === 'directory') {
    files.push({path, dir:true});
    try { for await (const [name, child] of node.entries()) await walk(child, path ? path + '/' + name : name); } catch {}
  } else {
    try {
      const file = await node.getFile();
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = ''; for (let i=0;i<bytes.length;i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192));
      files.push({path, data:btoa(binary), mod:file.lastModified});
    } catch { files.push({path, data:'', denied:true}); }
  }
}
await walk(tree, ''); window.__gets = 0; return files;
}""",
            count,
        )
        for file in self.root.rglob("*"):
            if file.is_dir():
                file.chmod(0o700)
            else:
                file.chmod(0o600)
        for file in self.root.iterdir():
            if file.is_dir():
                shutil.rmtree(file)
            else:
                file.unlink()
        import os

        for item in files:
            file = self.root / item["path"]
            if item.get("dir"):
                file.mkdir(exist_ok=True)
            else:
                file.write_bytes(base64.b64decode(item["data"]))
                if item.get("mod"):
                    os.utime(file, (item["mod"] / 1000, item["mod"] / 1000))
                if item.get("denied"):
                    file.chmod(0)
        (self.root / "locked").chmod(0)
        self.raw.evaluate("mount()")

    def locator(self, selector):
        return Locator(self, selector)

    async def click(self, selector):
        return await self.locator(selector).click()

    async def fill(self, selector, value):
        return await self.locator(selector).fill(value)

    async def focus(self, selector):
        return await self.locator(selector).evaluate("e => e.focus()")

    async def press(self, selector, key):
        await self.focus(selector)
        await self.keyboard.press(key)

    async def type(self, selector, text):
        await self.focus(selector)
        await self.keyboard.type(text)

    async def inner_text(self, selector):
        return await self.locator(selector).inner_text()

    async def text_content(self, selector):
        return await self.locator(selector).evaluate("e => e.textContent")

    async def input_value(self, selector):
        return await self.locator(selector).input_value()

    async def is_visible(self, selector):
        return await self.locator(selector).is_visible()

    async def is_hidden(self, selector):
        return not await self.is_visible(selector)

    async def get_attribute(self, selector, name):
        return await self.locator(selector).get_attribute(name)

    async def query_selector(self, selector):
        return self.locator(selector) if await self.locator(selector).count() else None

    async def eval_on_selector(self, selector, fn):
        return await self.locator(selector).evaluate(fn)

    async def eval_on_selector_all(self, selector, fn):
        return await self.evaluate(f"({fn})(({QUERY})({json.dumps(selector)}))")

    async def wait_for_selector(self, selector, **kwargs):
        return await self.locator(selector).wait_for(**kwargs)

    async def wait_for_timeout(self, ms):
        await asyncio.sleep(ms / 1000)

    async def wait_for_function(self, fn, timeout=30000):
        until = time.monotonic() + timeout / 1000
        while time.monotonic() < until:
            if await self.evaluate(fn):
                return
            await asyncio.sleep(0.05)
        raise TimeoutError(fn)

    async def set_viewport_size(self, size):
        self.raw.call("/window/rect", size)


class Browser:
    def __init__(self, stack, scheme=None):
        self.stack, self.scheme = stack, scheme

    async def new_context(self, color_scheme):
        return Browser(self.stack, color_scheme)

    async def new_page(self, viewport=None):
        temporary = self.stack.enter_context(
            tempfile.TemporaryDirectory(prefix="filemill-ui-")
        )
        root = Path(temporary) / "workspace"
        root.mkdir()
        raw = self.stack.enter_context(application(root, self.scheme))
        page = NativePage(raw, root)
        if viewport:
            await page.set_viewport_size(viewport)
        return page

    async def close(self):
        pass


class NativePlaywright:
    native = True

    def async_playwright(self):
        return self

    async def __aenter__(self):
        self.stack = ExitStack()
        return SimpleNamespace(chromium=SimpleNamespace(launch=self.launch))

    async def launch(self, **kwargs):
        return Browser(self.stack)

    async def __aexit__(self, *args):
        self.stack.close()
