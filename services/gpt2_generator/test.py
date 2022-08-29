import requests


def test_respond():
    url = "http://0.0.0.0:8132/respond"

    contexts = [["hi", "hi. how are you?"], ["let's chat about movies", "cool. what movies do you like?"]]
    results = requests.post(url, json={"utterances_histories": contexts}).json()
    assert len(results) == 2
    assert [
        len(sample[0]) > 0 and all([len(text) > 0 for text in sample[0]]) and all([conf > 0.0 for conf in sample[1]])
        for sample in results
    ]
    print("Success")


if __name__ == "__main__":
    test_respond()
