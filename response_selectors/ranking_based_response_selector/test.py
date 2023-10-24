import requests
import json


def test_selector(url: str):
    with open("test_data.json", "r") as f:
        data = json.load(f)
    # To skip "Oh, and remember this dialog's id" that raises error due to absence of 'dialog_id' field in test_data.
    data["dialogs"][0]["human_utterances"].append(data["dialogs"][0]["human_utterances"][0])
    result = requests.post(url, json=data).json()
    assert result[0][0] == "program_y"
