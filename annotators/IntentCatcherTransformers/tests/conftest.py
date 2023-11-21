import json

import pytest

from os import getenv

INTENT_PHRASES_PATH = getenv("INTENT_PHRASES_PATH")


def pytest_addoption(parser):
    parser.addoption("--uri", action="store", default="http://0.0.0.0")
    parser.addoption("--port", action="store", default="8014")
    parser.addoption("--handle", action="store", default="detect")


@pytest.fixture
def uri(request) -> str:
    return request.config.getoption("--uri")


@pytest.fixture
def port(request) -> str:
    return request.config.getoption("--port")


@pytest.fixture
def handle(request) -> str:
    return request.config.getoption("--handle")


@pytest.fixture
def url(uri, port, handle) -> str:
    return f"{uri}:{port}/{handle}"


@pytest.fixture
def tests():
    if "RU" in INTENT_PHRASES_PATH and "commands" in INTENT_PHRASES_PATH:
        tests = json.load(open("tests_commands_RU.json"))
    elif "RU" in INTENT_PHRASES_PATH:
        tests = json.load(open("tests_RU.json"))
    elif "commands" in INTENT_PHRASES_PATH:
        tests = json.load(open("tests_commands.json"))
    else:
        tests = json.load(open("tests.json"))
    return tests
