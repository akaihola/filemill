from pathlib import Path

import pytest

from filemill.providers.vtt_provider import VTTProvider
from filemill.vfs import REGISTRY


@pytest.mark.parametrize("name", ["captions.vtt", "captions.VTT"])
def test_vtt_provider_is_registered(tmp_path: Path, name: str):
    path = tmp_path / name
    provider = REGISTRY.get(path)
    assert isinstance(provider, VTTProvider)
    assert provider.list_entries(path, "") == []
    assert provider.list_entries(path, "unused/child") == []
    assert not provider.handles(tmp_path / "captions.txt")


def test_vtt_provider_http_contract(client, tmp_root):
    source = b"WEBVTT\r\n\r\n00:00.000 --> 00:01.000\r\nHello\r\n"
    (tmp_root / "captions.vtt").write_bytes(source)
    entries = client.get("/api/dir?p=").json()["entries"]
    entry = next(e for e in entries if e["name"] == "captions.vtt")
    assert entry["dir"] is False
    assert client.get("/captions.vtt").content == source
    assert client.get("/captions.vtt?filemill=raw").content == source
    for vpath in ("", "unused/child"):
        response = client.get("/api/dir", params={"p": "captions.vtt", "v": vpath})
        assert response.status_code == 200
        assert response.json() == {"entries": [], "denied": None}
    response = client.get("/captions.vtt/unused/child")
    assert response.status_code == 200
    assert 'data-filemill="render"' in response.text
