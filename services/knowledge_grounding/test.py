import allure
import pytest
import requests


@allure.description("""Knowledge grounding multi-language test""")
@pytest.mark.parametrize(
    "checked_sentence, knowledge, text, expected",
    [
        (
            "When Mabel visited their home to play the piano, "
            "she occasionally glimpsed a flitting swirl of white in the next room, "
            "sometimes even received a note of thanks for calling, but she never actually "
            "spoke with the reclusive, almost spectral Emily.",
            "The real-life soap opera behind the publication of Emily Dickinson’s poems\n"
            "When Mabel visited their home to play the piano, she occasionally glimpsed "
            "a flitting swirl of white in the next room, sometimes even received a note of "
            "thanks for calling, but she never actually spoke with the reclusive, almost spectral Emily.",
            "Yeah she was an icon she died in 1886 at the tender age of 55.",
            True,
        ),
        (
            "Penguins are a group of aquatic flightless birds.",
            "Penguins are a group of aquatic flightless birds.",
            "Who are penguins?",
            True,
        ),
    ],
)
def test_knowledge_grounding(url: str, checked_sentence, knowledge, text, expected):
    history = (
        "Do you know who Emily Dickson is?\n"
        'Emily Dickinson? The poet? I do! "Tell all the truth, but tell it slant" '
        "she once said. Do you like her poetry?"
    )

    request_data = {
        "batch": [
            {"checked_sentence": checked_sentence, "knowledge": knowledge, "text": text, "history": history},
        ]
    }
    results = requests.post(url, json=request_data).json()
    assert all(results)
