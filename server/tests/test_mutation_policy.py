"""Mutation authorization must finish without consuming request bytes."""

import re

import pytest
from starlette.requests import Request
from starlette.testclient import TestClient

from filemill import app as app_module


def shell_token(client):
    response = client.get("/?f")
    match = re.search(r'data-mutation-token="([^"]+)"', response.text)
    assert match, "the shipped shell must supply the mutation token"
    assert response.headers["cache-control"] == "no-store"
    return match[1]


@pytest.mark.parametrize("method,endpoint", [("POST", "save"), ("DELETE", "delete")])
@pytest.mark.parametrize(
    "failure",
    ["origin", "missing-origin", "null-origin", "token", "missing-token", "host"],
)
async def test_denied_before_body(tmp_root, method, endpoint, failure):
    headers = {
        "host": "127.0.0.1:8000",
        "origin": "http://127.0.0.1:8000",
        "x-filemill-token": getattr(app_module.app.state, "mutation_token", "missing"),
    }
    if failure == "origin":
        headers["origin"] = "https://unrelated.example"
    elif failure == "missing-origin":
        del headers["origin"]
    elif failure == "null-origin":
        headers["origin"] = "null"
    elif failure == "token":
        headers["x-filemill-token"] = "wrong"
    elif failure == "missing-token":
        del headers["x-filemill-token"]
    else:
        headers["host"] = "rebound.example:8000"
        headers["origin"] = "http://rebound.example:8000"

    async def receive():
        pytest.fail("unauthorized request read its body")

    request = Request(
        {
            "type": "http",
            "app": app_module.app,
            "method": method,
            "scheme": "http",
            "path": f"/api/{endpoint}",
            "query_string": b"p=readme.md",
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
            "server": ("127.0.0.1", 8000),
        },
        receive,
    )
    handler = app_module.api_save if endpoint == "save" else app_module.api_delete
    response = handler(request, p="readme.md")
    if endpoint == "save":
        response = await response
    assert response.status_code == 403
    assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"


@pytest.mark.parametrize(
    "origin",
    [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://[::1]:8000",
        "https://files.example",
    ],
)
def test_authorized_mutations(tmp_root, monkeypatch, origin):
    monkeypatch.setenv("FILEMILL_ORIGINS", "https://files.example")
    with TestClient(
        app_module.app,
        base_url=origin if "[::1]" not in origin else "http://127.0.0.1:8000",
    ) as client:
        token = shell_token(client)
        headers = {
            "Origin": origin,
            "Host": origin.split("://", 1)[1],
            "X-Filemill-Token": token,
            "If-Match": client.get("/api/raw?p=readme.md&snapshot=1").headers["etag"],
        }
        assert (
            client.post(
                "/api/save?p=readme.md", content="changed", headers=headers
            ).status_code
            == 200
        )
        assert (tmp_root / "readme.md").read_text() == "changed"
        assert (
            client.delete("/api/delete?p=readme.md", headers=headers).status_code == 200
        )
        assert not (tmp_root / "readme.md").exists()


def test_proxy_does_not_require_forwarded_headers(tmp_root, monkeypatch):
    monkeypatch.setenv("FILEMILL_ORIGINS", "https://files.example")
    with TestClient(app_module.app, base_url="http://files.example") as client:
        token = shell_token(client)
        assert (
            client.post(
                "/api/save?p=readme.md",
                content="changed",
                headers={
                    "Origin": "https://files.example",
                    "X-Filemill-Token": token,
                    "If-Match": client.get("/api/raw?p=readme.md&snapshot=1").headers[
                        "etag"
                    ],
                },
            ).status_code
            == 200
        )


@pytest.mark.parametrize(
    "origin",
    [
        "https://files.example.evil",
        "http://files.example",
        "https://files.example:444",
        "http://localhost:9999",
    ],
)
def test_origin_must_match_host_and_configuration(tmp_root, monkeypatch, origin):
    monkeypatch.setenv("FILEMILL_ORIGINS", "https://files.example")
    with TestClient(app_module.app, base_url="https://files.example") as client:
        token = shell_token(client)
        assert (
            client.post(
                "/api/save?p=readme.md",
                content="changed",
                headers={
                    "Origin": origin,
                    "X-Filemill-Token": token,
                    "If-Match": client.get("/api/raw?p=readme.md&snapshot=1").headers[
                        "etag"
                    ],
                },
            ).status_code
            == 403
        )
        assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"


@pytest.mark.parametrize("header", ["Origin", "Host", "X-Filemill-Token"])
def test_ambiguous_headers_are_denied(tmp_root, header):
    with TestClient(app_module.app, base_url="http://localhost") as client:
        token = shell_token(client)
        headers = [
            ("Origin", "http://localhost"),
            ("Host", "localhost"),
            ("X-Filemill-Token", token),
        ]
        headers.append((header, dict(headers)[header]))
        assert (
            client.post(
                "/api/save?p=readme.md", content="changed", headers=headers
            ).status_code
            == 403
        )
        assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"


@pytest.mark.parametrize(
    "origin",
    [
        "null",
        "file://localhost",
        "http://localhost/path",
        "http://user@localhost",
        "http://localhost?query",
        "http://localhost#fragment",
        "http://localhost:invalid",
        "http://localhost:0",
    ],
)
def test_invalid_origins_are_denied(tmp_root, origin):
    with TestClient(app_module.app, base_url="http://localhost") as client:
        token = shell_token(client)
        assert (
            client.post(
                "/api/save?p=readme.md",
                content="changed",
                headers={
                    "Origin": origin,
                    "X-Filemill-Token": token,
                    "If-Match": client.get("/api/raw?p=readme.md&snapshot=1").headers[
                        "etag"
                    ],
                },
            ).status_code
            == 403
        )


def test_token_changes_invalidate_existing_shells(tmp_root, monkeypatch):
    import secrets

    with TestClient(app_module.app, base_url="http://localhost") as client:
        token = shell_token(client)
        monkeypatch.setattr(
            app_module.app.state, "mutation_token", secrets.token_urlsafe(32)
        )
        headers = {"Origin": "http://localhost", "X-Filemill-Token": token}
        assert (
            client.post(
                "/api/save?p=readme.md", content="changed", headers=headers
            ).status_code
            == 403
        )
        assert (
            client.delete("/api/delete?p=readme.md", headers=headers).status_code == 403
        )
        assert shell_token(client) != token
        assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"
