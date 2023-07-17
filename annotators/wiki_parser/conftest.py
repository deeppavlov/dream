import pytest


def pytest_addoption(parser):
    parser.addoption('--url', action='store', default="http://0.0.0.0:8077/model")


@pytest.fixture
def url(request) -> str:
    return request.config.getoption('--url')