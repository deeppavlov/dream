import pytest
import requests


@pytest.mark.parametrize(
    "sentences, gold, segments_gold",
    [({"sentences": ["привет как дела"]}, "привет. как дела?", ["привет.", "как дела?"])],
)
def test_sentseg(url: str, sentences: dict, gold: str, segments_gold: list):
    response = requests.post(url, json=sentences)
    result = response.json()
    assert response.status_code == 200
    assert result[0]["punct_sent"] == gold
    assert result[0]["segments"] == segments_gold
