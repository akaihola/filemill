"""Small WebDriver client for native contract and renderer tests."""

import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path


class Page:
    def __init__(self, url):
        self.url = url

    def call(self, path, data=None, method=None):
        request = urllib.request.Request(
            self.url + path,
            data=None if data is None else json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                return json.load(response)["value"]
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error

    def evaluate(self, script, arg=None):
        result = self.call(
            "/execute/async",
            {
                "script": """
const done = arguments[arguments.length - 1];
try {
  let value = (0, eval)(arguments[0]);
  if (typeof value === 'function') value = value(arguments[1]);
  Promise.resolve(value).then(v => done({value: v ?? null}), e => done({error: String(e)}));
} catch(e) { done({error: String(e)}); }
""",
                "args": [script, arg],
            },
        )
        if "error" in result:
            raise RuntimeError(result["error"])
        return result["value"]

    def wait(self, expression, timeout=15):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            try:
                result = self.evaluate(expression)
                if result:
                    return result
            except RuntimeError:
                pass
            time.sleep(0.05)
        raise TimeoutError(expression)


@contextmanager
def application(root, scheme=None):
    binary = Path(
        os.environ.get(
            "FILEMILL_NATIVE_BINARY", Path(__file__).parent / "webview/build/filemill"
        )
    ).resolve()
    assert binary.is_file(), f"Build the native host first: {binary}"
    processes = []
    with (
        tempfile.TemporaryDirectory(prefix="filemill-native-") as temporary,
        open(Path(temporary) / "process.log", "w+") as log,
    ):

        def start(args, env):
            process = subprocess.Popen(
                args,
                env=env,
                cwd=temporary,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            processes.append(process)
            return process

        env = dict(os.environ, FILEMILL_ROOT=str(root))
        if scheme:
            env["FILEMILL_TEST_THEME"] = scheme
        try:
            if not env.get("DISPLAY"):
                read, write = os.pipe()
                process = subprocess.Popen(
                    [
                        "Xvfb",
                        "-dpi",
                        "96",
                        "-displayfd",
                        str(write),
                        "-screen",
                        "0",
                        "1600x1000x24",
                    ],
                    pass_fds=(write,),
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
                processes.append(process)
                os.close(write)
                with os.fdopen(read) as stream:
                    env["DISPLAY"] = ":" + stream.readline().strip()
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            start(
                [
                    os.environ.get("WEBKIT_WEBDRIVER", "WebKitWebDriver"),
                    f"--port={port}",
                ],
                env,
            )
            client = Page(f"http://127.0.0.1:{port}")
            for _ in range(100):
                try:
                    client.call("/status")
                    break
                except urllib.error.URLError:
                    time.sleep(0.05)
            session = client.call(
                "/session",
                {
                    "capabilities": {
                        "alwaysMatch": {
                            "webkitgtk:browserOptions": {
                                "binary": str(binary),
                                "args": ["--automation"],
                            }
                        }
                    }
                },
            )
            client.url += "/session/" + session["sessionId"]
            client.wait(
                'typeof FS !== "undefined" && path.length && path[0].kids !== null'
            )
            yield client
            # Terminate the driver process group, including the application.
            # WebKit's DELETE session can hang while closing the last window.
        finally:
            for process in reversed(processes):
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            log.seek(0)
            output = log.read()
            if "Traceback" in output:
                print(output)
