import requests


def test():
    test_config = {
        "sentences": ["I am so sad"],
        "user_emotion": "distress",
        "sentiment": "negative",
        "bot_mood": [0.75, 0.25, 0.44],
    }
    response = requests.post("http://0.0.0.0:8051/model", json=test_config)
    assert response.status_code == 200
    print("SUCCESS")


if __name__ == "__main__":
    test()
