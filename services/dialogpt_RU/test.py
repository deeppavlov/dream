import requests


def test_respond():
    url = "http://0.0.0.0:8091/respond"

    dialog_contexts = [[
        {"speaker": "human", "text": "Привет, как день прошел?"},
        {"speaker": "bot", "text": "Хорошо, а у тебя как?"},
        {"speaker": "human", "text": "Нормально, посоветуй фильм посмотреть"},
    ]]

    request_data = {"dialog_contexts": dialog_contexts}

    result = requests.post(url, json=request_data).json()
    print(result)

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
