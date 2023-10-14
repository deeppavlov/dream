import allure
import pytest
import requests

from typing import Dict, List


@allure.description("""Base response test""")
def test_response(url):
    data = {"sentences": ["Hello how are you", "I am fine", "Alexa what is the weather today"]}
    response = requests.post(url, json=data)
    response_data = response.json()
    assert response.status_code == 200
    assert len(response_data) == 3
    assert "punct_sent" in response_data[0]
    assert "segments" in response_data[0]


@allure.description("""Base response test: pass wrong json""")
def test_response_wrong_structure(url: str):
    data = {"wrong": ["Hello how are you", "I am fine", "Alexa what is the weather today"]}
    response = requests.post(url, json=data)
    assert response.status_code == 500


@allure.description("""Test punctuation""")
@pytest.mark.parametrize(
    "sentences, gold",
    [
        ({"sentences": ["hey alexa how are you"]}, "hey alexa. how are you?"),
        ({"sentences": [""]}, ""),
    ],
)
def test_sentseg_punctuation(url: str, sentences: Dict, gold: str):
    response = requests.post(url, json=sentences)
    data = response.json()
    assert response.status_code == 200
    assert data[0]["punct_sent"] == gold


@allure.description("""Test sentence split""")
@pytest.mark.parametrize(
    "sentences, gold",
    [
        ({"sentences": ["hey alexa how are you"]}, ["hey alexa.", "how are you?"]),
        ({"sentences": [""]}, [""]),
        ({"sentences": ["Hello. How are you? I am fine!"]}, ["Hello.", "How are you?", "I am fine!"]),
    ],
)
def test_sentseg_split(url: str, sentences: Dict, gold: List[str]):
    response = requests.post(url, json=sentences)
    data = response.json()
    assert response.status_code == 200
    assert data[0]["segments"] == gold


@allure.description("""Test preprocessing""")
@pytest.mark.parametrize(
    "sentences, gold",
    [
        ({"sentences": ["Fred ai n't going."]}, "Fred is not going."),
        ({"sentences": ["I'm hungry."]}, "I am hungry."),
        ({"sentences": ["You're funny."]}, "You are funny."),
        ({"sentences": ["I've done it."]}, "I have done it."),
        ({"sentences": ["I'll be there."]}, "I will be there."),
        ({"sentences": ["She's reading."]}, "She is reading."),
        ({"sentences": ["he's running."]}, "he is running."),
        ({"sentences": ["it's raining."]}, "it is raining."),
        ({"sentences": ["that's interesting."]}, "that is interesting."),
        ({"sentences": ["y'all come back now."]}, "you all come back now."),
        ({"sentences": ["yall come back now."]}, "you all come back now."),
        ({"sentences": ["I'd like a coffee."]}, "I would like a coffee."),
        ({"sentences": ["I'm gon na study."]}, "I am going to study."),
        ({"sentences": ["I wan na play."]}, "I want to play."),
    ],
)
def test_sentseg_preprocessing(url: str, sentences: Dict, gold: str):
    response = requests.post(url, json=sentences)
    data = response.json()
    assert response.status_code == 200
    assert data[0]["punct_sent"] == gold
