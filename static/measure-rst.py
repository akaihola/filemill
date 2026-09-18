#!/usr/bin/env python3
"""Measure real CDN-backed RST rendering in the committed browser bundle.

uv run --with 'playwright==1.61.0' python3 static/measure-rst.py
Outputs JSON; no stubs, local mirrors or timing assertions.
"""
import asyncio
import json
import platform
import runpy
import statistics
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
SAMPLE = """Evaluation
==========

Some *rst* text and a footnote [1]_.

.. note:: Browser-rendered directive.

===== =====
Name  Value
===== =====
one   two
===== =====

.. [1] Browser-rendered footnote.

.. raw:: html

   <script>window.rstInjected = true</script>

.. include:: /etc/passwd
"""


async def main():
    fixture = runpy.run_path(str(HERE / 'test-rich.py'))
    httpd, port = fixture['serve']()
    base = f'http://127.0.0.1:{port}/static/index.html'
    runs = []
    try:
        async with async_playwright() as p:
            async with await p.chromium.launch() as browser:
                for _ in range(3):
                    async with await browser.new_context(service_workers='block') as context:
                        page = await context.new_page()
                        cdp = await context.new_cdp_session(page)
                        await cdp.send('Network.enable')
                        await cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
                        await page.goto(base)
                        await page.evaluate("localStorage.setItem('filemill.rich', 'on')")
                        await page.evaluate("""sample => {
                          const file = (name, text) => ({kind: 'file', name,
                            getFile: async () => new File([text], name)});
                          const files = [file('evaluation.rst', sample), file('plain.txt', 'plain')];
                          return mount({kind: 'directory', name: 'measurement',
                            entries: async function*() { for (const f of files) yield [f.name, f]; }});
                        }""", SAMPLE)
                        await page.evaluate('performance.clearResourceTimings()')
                        await page.evaluate("""() => {
                          window.rstStarted = performance.now();
                          [...document.querySelectorAll('.row')].find(
                            e => e.textContent.includes('evaluation.rst')).click();
                        }""")
                        await page.wait_for_selector('#pv-content .pv-rich table', timeout=120000)
                        cold_ms = await page.evaluate('performance.now() - window.rstStarted')
                        assert await page.locator('#pv-content .note').count() == 1
                        assert await page.locator('#pv-content [role="doc-footnote"]').count() == 1
                        assert not await page.evaluate('!!window.rstInjected')
                        assert not await page.locator('#pv-content script').count()
                        assert 'root:' not in await page.inner_text('#pv-content')
                        assets = await page.evaluate("""() => performance.getEntriesByType('resource')
                          .filter(e => e.name.includes('/pyodide/')).map(e => ({
                            url: e.name, transfer_bytes: e.transferSize,
                            encoded_bytes: e.encodedBodySize, decoded_bytes: e.decodedBodySize
                          }))""")
                        assert assets and all(a['encoded_bytes'] > 0 for a in assets), assets
                        await page.click('.row:has-text("plain.txt")')
                        await page.wait_for_selector('#pv-content .pv-text')
                        await page.evaluate("""() => {
                          window.rstStarted = performance.now();
                          [...document.querySelectorAll('.row')].find(
                            e => e.textContent.includes('evaluation.rst')).click();
                        }""")
                        await page.wait_for_selector('#pv-content .pv-rich table')
                        warm_ms = await page.evaluate('performance.now() - window.rstStarted')
                        assert len(await page.evaluate("performance.getEntriesByType('resource').filter(e => e.name.includes('/pyodide/'))")) == len(assets)
                        outputs = await page.evaluate("""async () => Promise.all(
                          ['First source', 'Second source'].map(text => renderNode(
                            {name: 'parallel.rst'}, new Blob([text]), 'rst')))
                        """)
                        assert 'First source' in outputs[0] and 'Second source' not in outputs[0]
                        assert 'Second source' in outputs[1] and 'First source' not in outputs[1]
                        runs.append({'cold_ms': cold_ms, 'warm_ms': warm_ms, 'assets': assets,
                                     'encoded_bytes': sum(a['encoded_bytes'] for a in assets),
                                     'decoded_bytes': sum(a['decoded_bytes'] for a in assets)})
                print(json.dumps({'browser': browser.version, 'host': platform.platform(),
                                  'bundle_bytes': (HERE / 'index.html').stat().st_size,
                                  'sample': SAMPLE, 'runs': runs,
                                  'median_cold_ms': statistics.median(r['cold_ms'] for r in runs)}, indent=2))
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == '__main__':
    asyncio.run(main())
