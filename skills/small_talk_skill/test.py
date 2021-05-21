import requests


def test_one_step_responses():
    url = 'http://0.0.0.0:8062/respond'

    response = requests.post(url, json={"dialogs": [
        {"human_utterances": [{"text": "can we talk about my grandmother.", "annotations": {}}],
         "utterances": [{"text": "can we talk about my grandmother.", "annotations": {}}],
         "bot_utterances": [],
         "human": {"attributes": {}}},
        {"human_utterances": [{"text": "i like cars", "annotations": {}}],
         "utterances": [{"text": "i like cars", "annotations": {}}],
         "bot_utterances": [],
         "human": {"attributes": {}}},
        {"human_utterances": [{"text": "switch topic", "annotations": {}}],
         "utterances": [{"text": "switch topic", "annotations": {}}],
         "bot_utterances": [],
         "human": {"attributes": {}}}
    ]}).json()
    assert response[0][:2] == ["Do you have a family?", 1.0], print(response)
    assert response[1][:2] == ["Can you drive a car?", 0.9], print(response)
    assert response[2][1] == 0.98, print(response)

    print("SUCCESS!")


if __name__ == '__main__':
    test_one_step_responses()
