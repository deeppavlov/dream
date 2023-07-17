import pytest
import requests


@pytest.mark.parametrize(
    "sentences", "gold",
    {"sentences": ["hey alexa how are you"]}, "hey alexa. how are you?"
)
def test_sentseg(url: str, sentences: dict, gold: str):
    response = requests.post(url, json=sentences).json()
    assert response[0]["punct_sent"] == gold, print(response)
