import requests
import json


def make_input_data(curr_sent, bot_sent, human_attributes=None, emotion=None, intents=None):
    human_attributes = {} if human_attributes is None else human_attributes
    emotion = {"neutral": 0} if emotion is None else emotion
    intents = {"yes": {"confidence": 0, "detected": 0}} if intents is None else intents
    input_data = {
        "dialogs": [
            {
                "id": "test",
                "bot": {"attributes": {}},
                "human": {"attributes": human_attributes},
                "human_attributes": human_attributes,
                "bot_attributes": {},
                "human_utterances": [
                    {
                        "user_telegram_id": "test",
                        "text": curr_sent,
                        "annotations": {
                            "emotion_classification": {
                                "text": {
                                    "anger": 0,
                                    "fear": 0,
                                    "joy": 0,
                                    "disgust": 0,
                                    "sadness": 0.9,
                                    "surprise": 0,
                                    "neutral": 0,
                                }
                            },
                            "intent_catcher": {
                                "no": {"confidence": 0.0, "detected": 0},
                                "yes": {"confidence": 0.0, "detected": 0},
                            },
                        },
                    }
                ],
                "bot_utterances": [{"text": bot_sent, "active_skill": "emotion_skill" if bot_sent else ""}],
            }
        ],
    }
    input_data["dialogs"][-1]["human_utterances"][-1]["annotations"]["emotion_classification"]["text"].update(emotion)
    input_data["dialogs"][-1]["human_utterances"][-1]["annotations"]["intent_catcher"].update(intents)
    return input_data


#
#
# def test_it_returns_empty_for_some_random_text():
#     data = make_input_data('hey', '')
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert response[0][0] == '', print(response)
#     assert response[0][1] == 0, print(response)
#
#
# def test_it_returns_joke_for_negative_emotion():
#     data = make_input_data('i am feeling depressed', '', {'sadness': 0.9})
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert 'joke' in response[0][0], print(response)
#     assert response[0][1] > 0, print(response)
#
#
# def test_it_returns_7minute_for_positive_emotion():
#     data = make_input_data('i am feeling joyful', '', {'joy': 0.9})
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert '7 minute' in response[0][0], print(response)
#     assert response[0][1] > 0, print(response)
#
#
# def test_positive_scenario():
#     data = make_input_data('yes', 'can i tell you a joke?', intents={"yes": {"confidence": 1, "detected": 1}})
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert 'feel better now?' in response[0][0], print(response)
#     assert response[0][1] == 1.0, print(response)
#
#     data = make_input_data('yes', 'do you feel better now?', intents={"yes": {"confidence": 1, "detected": 1}})
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert '7 minute' in response[0][0], print(response)
#     assert response[0][1] == 1.0, print(response)
#
#     data = make_input_data('yes', 'heard about 7 minute workout', intents={"yes": {"confidence": 1, "detected": 1}})
#     url = 'http://0.0.0.0:8049/respond'
#     response = requests.post(url, json=data).json()
#     assert 'workout' in response[0][0], print(response)
#     assert response[0][1] == 1.0, print(response)


if __name__ == "__main__":
    url = "http://0.0.0.0:8049/respond"
    with open("tests.json") as fp:
        tests = json.load(fp)
    for test in tests:
        expected_results = test.pop("results")
        test = make_input_data(
            test.get("curr_sent", ""),
            test.get("bot_sent", ""),
            test.get("human_attributes", {}),
            test.get("emotion", {"neutral": 0}),
            test.get("intents", {"yes": {"confidence": 0, "detected": 0}}),
        )
        try:
            phrase, confidence, human_attributes, bot_attributes, attributes = requests.post(url, json=test).json()[0]
        except Exception as e:
            print(f"Exception:\n test: {test}\nresult: {expected_results}")
            raise e
        state = human_attributes.get("emotion_skill_attributes", {}).get("state", "")
        emotion = human_attributes.get("emotion_skill_attributes", {}).get("emotion", "")
        try:
            if "text" in expected_results:
                print("Check text")
                assert expected_results["text"] in phrase, print(phrase)
            if "confidence" in expected_results:
                print("Check confidence")
                assert expected_results["confidence"] == confidence, print(confidence)
            if "states" in expected_results:
                print("Check states")
                assert state in expected_results["states"], print(state)
            if "emotion" in expected_results:
                print("Check emotion")
                assert expected_results["emotion"] == emotion, print(emotion)
        except AssertionError as e:
            print(f"AssertionError at test: \n{test}\n")
            print("-" * 30)
            print(f"expected_results: {expected_results}")
            print(
                f"state: {state} phrase: {phrase}; confidence: {confidence}; "
                f"bot_attributes: {bot_attributes}; human_attributes: {human_attributes}; "
                f"attributes: {attributes}"
            )
            raise e
    print("EMO SKILL TESTS: SUCCESS")
