import pytest


def pytest_addoption(parser):
    parser.addoption("--uri", action="store", default="http://0.0.0.0")
    parser.addoption("--port", action="store", default="8153")


@pytest.fixture
def uri(request) -> str:
    return request.config.getoption("--uri")


@pytest.fixture
def port(request) -> str:
    return request.config.getoption("--port")


@pytest.fixture
def url(uri, port) -> str:
    return f"{uri}:{port}"
