"""Host authorization applies before every route, including loopback peers."""

import pytest
from starlette.testclient import TestClient

from filemill.app import app

READ_ROUTES = [
    "/?f",
    "/api/dir",
    "/api/search?q=Hello",
    "/api/raw?p=.hidden",
    "/api/preview?p=readme.md",
    "/.hidden",
    "/readme.md?f",
    "/ui/entry-server.js",
    "/manifest.json",
    "/sw.js",
    "/icons/icon-192.png",
]


@pytest.mark.parametrize("url", READ_ROUTES)
@pytest.mark.parametrize("public", [False, True])
def test_foreign_host_refused(tmp_root, monkeypatch, url, public):
    monkeypatch.setattr(app.state, "public", public)
    monkeypatch.delenv("FILEMILL_ORIGINS", raising=False)
    with TestClient(
        app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 43210)
    ) as client:
        response = client.get(url, headers={"Host": "rebound.example:8000"})
    assert response.status_code == 403
    assert app.state.mutation_token not in response.text
    assert "hidden" not in response.text


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1:8000", "[::1]:8000"])
def test_loopback_reads_work(tmp_root, host):
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/.hidden", headers={"Host": host}).text == "hidden"


@pytest.mark.parametrize(
    "host,expected",
    [
        ("files.example", 200),
        ("files.example:443", 200),
        ("files.example:8443", 200),
        ("files.example:444", 403),
        ("files.example.evil", 403),
        ("evil.example", 403),
    ],
)
def test_proxy_hosts_use_configured_origins(tmp_root, monkeypatch, host, expected):
    monkeypatch.setenv(
        "FILEMILL_ORIGINS", "https://files.example https://files.example:8443 invalid"
    )
    with TestClient(app, base_url="http://127.0.0.1") as client:
        response = client.get(
            "/.hidden",
            headers={
                "Host": host,
                "X-Forwarded-Host": "localhost",
                "Forwarded": "host=localhost",
            },
        )
    assert response.status_code == expected


@pytest.mark.parametrize(
    "hosts",
    [
        [],
        ["localhost", "localhost"],
        ["localhost", "evil.example"],
        ["localhost/path"],
        ["user@localhost"],
        ["localhost:bad"],
        ["localhost?query"],
        ["localhost#fragment"],
        ["["],
    ],
)
async def test_missing_ambiguous_or_invalid_host_refused(tmp_root, hosts):
    import httpx

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        request = client.build_request("GET", "/.hidden")
        del request.headers["host"]
        for host in hosts:
            request.headers = httpx.Headers(
                [*request.headers.multi_items(), ("host", host)]
            )
        assert (await client.send(request)).status_code == 403
