import requests
from typing import List


def get_input_json(last_utterance: str, human_utterance_history_batch: List):
    return {"last_utterance_batch": [last_utterance], "human_utterance_history_batch": [human_utterance_history_batch]}


selected_classes = ["Why do you ask ?", "Does that question interest you ?"]


def test_skill():
    url = "http://0.0.0.0:8047/respond"
    input_data = {
        "last_utterance_batch": ["what do you like", "what do you like"],
        "human_utterance_history_batch": [["hi"], ["hi", "what do you like"]],
    }
    response = requests.post(url, json=input_data).json()
    for tgt, pred in zip(selected_classes, response):
        assert tgt == pred[0]
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
