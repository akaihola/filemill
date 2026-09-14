from pathlib import Path

import pytest


@pytest.fixture
def bundle(request):
    name = "index-dev.html" if request.config.getoption("--dev") else "index.html"
    return Path(__file__).parent / name


@pytest.fixture
def fake_handle():
    return "__mk"


@pytest.fixture
def opfs_root():
    return "navigator.storage.getDirectory()"


def pytest_addoption(parser):
    parser.addoption("--dev", action="store_true", help="test modular static sources")
