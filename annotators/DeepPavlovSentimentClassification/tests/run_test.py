import requests


def get_input_json(text: str):
    return {"sentences": [text]}


selected_classes = [
    "positive",
    "positive",
    "negative",
    "positive",
    "neutral",
    "positive",
    "neutral",
    "neutral",
    "positive",
]


def test_one_step_responses():
    url = "http://0.0.0.0:8024/model"
    input_data = {
        "sentences": [
            "ok",
            "i love you",
            "i hate you",
            "yes",
            "no",
            "please",
            "tell me something",
            "let's talk about something else",
            "let's talk about it",
        ]
    }
    response = requests.post(url, json=input_data).json()
    for tgt, pred in zip(selected_classes, response):
        assert tgt == pred[0][0]
    print("SUCCESS!")


if __name__ == "__main__":
    test_one_step_responses()
