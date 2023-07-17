import pytest
import requests


@pytest.mark.parametrize(
    "sentences", "gold", "segments_gold",
    {"sentences": ["привет как дела"]}, "привет. как дела?", ["привет.", "как дела?"]
)
def test_sentseg(url: str, sentences: dict, gold: str, segments_gold: list):
    response = requests.post(url, json=sentences).json()

    assert response[0]["punct_sent"] == gold, print(response)
    assert response[0]["segments"] == segments_gold, print(response)
