import requests


def test_one_step_responses():
    url = "http://0.0.0.0:8062/respond"

    response = requests.post(
        url,
        json={
            "dialogs": [
                {
                    "human_utterances": [{"text": "let's talk about marvel", "annotations": {}}],
                    "utterances": [{"text": "let's talk about marvel", "annotations": {}}],
                    "bot_utterances": [],
                    "human": {"attributes": {}},
                },
                {
                    "human_utterances": [{"text": "switch topic", "annotations": {}}],
                    "utterances": [{"text": "switch topic", "annotations": {}}],
                    "bot_utterances": [],
                    "human": {"attributes": {}},
                },
            ]
        },
    ).json()
    assert response[0][:2] == ["Do you like superheroes?", 1.0], print(response)
    assert response[1][1] == 0.9, print(response)

    print("SUCCESS!")


if __name__ == "__main__":
    test_one_step_responses()
