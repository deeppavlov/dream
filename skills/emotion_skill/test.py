import requests


def make_input_data(curr_sent, bot_sent, emotion={'neutral': 0}, intents={"yes": {"confidence": 0, "detected": 0}}):
    input_data = {
        "dialogs": [
            {
                "id": "test",
                'utterances': [
                    {
                        "user_telegram_id": "test", "text": curr_sent,
                        "annotations": {
                            "emotion_classification": {
                                "text": {"anger": 0, "fear": 0,
                                         "joy": 0, "love": 0,
                                         "sadness": 0, "surprise": 0,
                                         "neutral": 0}},
                            "intent_catcher": {"no": {"confidence": 0.0, "detected": 0},
                                               "yes": {"confidence": 0.0, "detected": 0}}
                        }
                    }
                ],
                'bot_utterances': [{'text': bot_sent}]
            }
        ]
    }
    input_data['dialogs'][-1]['utterances'][-1]['annotations']['emotion_classification']['text'].update(emotion)
    input_data['dialogs'][-1]['utterances'][-1]['annotations']['intent_catcher'].update(intents)
    return input_data


def test_it_returns_empty_for_some_random_text():
    data = make_input_data('hey', '')
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert response[0][0] == '', print(response)
    assert response[0][1] == 0, print(response)


def test_it_returns_joke_for_negative_emotion():
    data = make_input_data('i am feeling depressed', '', {'sadness': 0.9})
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert 'joke' in response[0][0], print(response)
    assert response[0][1] == 1.0, print(response)


def test_it_returns_7minute_for_positive_emotion():
    data = make_input_data('i am feeling joyful', '', {'joy': 0.9})
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert '7 minute' in response[0][0], print(response)
    assert response[0][1] == 1.0, print(response)


def test_positive_scenario():
    data = make_input_data('yes', 'can i tell you a joke?', intents={"yes": {"confidence": 1, "detected": 1}})
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert 'feel better now?' in response[0][0], print(response)
    assert response[0][1] == 1.0, print(response)

    data = make_input_data('yes', 'do you feel better now?', intents={"yes": {"confidence": 1, "detected": 1}})
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert '7 minute' in response[0][0], print(response)
    assert response[0][1] == 1.0, print(response)

    data = make_input_data('yes', 'heard about 7 minute workout', intents={"yes": {"confidence": 1, "detected": 1}})
    url = 'http://0.0.0.0:8049/respond'
    response = requests.post(url, json=data).json()
    assert 'power of this workout' in response[0][0], print(response)
    assert response[0][1] == 1.0, print(response)


if __name__ == '__main__':
    test_it_returns_empty_for_some_random_text()
    test_it_returns_joke_for_negative_emotion()
    test_it_returns_7minute_for_positive_emotion()
    test_positive_scenario()
    print("EMO SKILL TESTS: SUCCESS")
