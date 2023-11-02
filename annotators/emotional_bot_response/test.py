import requests


def test():
    test_config = {
        "sentences": ["I will eat pizza"],
        "bot_mood_labels": ["angry"],
        "bot_emotions": ["anger"],
    }
    response = requests.post("http://0.0.0.0:8050/respond_batch", json=test_config)
    assert response.status_code == 200
    print("SUCCESS")


if __name__ == "__main__":
    test()
