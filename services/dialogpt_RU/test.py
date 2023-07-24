import requests


def test_respond():
    url = "http://0.0.0.0:8125/respond"

    dialog_contexts = [
        [
            {"speaker": "human", "text": "Привет, как день прошел?"},
            {"speaker": "bot", "text": "Хорошо, а у тебя как?"},
            {"speaker": "human", "text": "Нормально, посоветуй фильм посмотреть"},
        ]
    ]

    request_data = {"dialog_contexts": dialog_contexts, "num_return_sequences": 5}
    result = requests.post(url, json=request_data).json()[0]
    print(result)
    assert len(result) == 5 and len(result[0]) > 0, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
