import requests


def test_respond():
    url = "http://0.0.0.0:8131/respond"

    persona = [
        [["I like ice-cream.", "I hate onions."], 0.5],
        [["I like watching people swimming.", "I like travelling."], 0.6],
    ]
    utterances_histories = [
        ["What do you like?"],
        ["What do you like?"],
    ]
    test_data = {"persona": persona, "utterances_histories": utterances_histories}

    result = requests.post(url, json=test_data).json()

    assert len(result[0][0]) > 0, "Empty response"
    print("Success")


if __name__ == "__main__":
    test_respond()
