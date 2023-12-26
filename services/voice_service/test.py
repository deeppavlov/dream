import requests


def test_respond():
    url = "http://0.0.0.0:8333/respond"

    # voice_path = "..."

    contexts = [["hi", "hi. how are you?"], ["let's chat about movies", "cool. what movies do you like?"]]
    gold_result = [["Reacting to a voice message "]]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [
        len(sample[0]) > 0 and all([len(text) > 0 for text in sample[0]]) and all([conf > 0.0 for conf in sample[1]])
        for sample in result
    ], f"Got\n{result}\n, but expected:\n{gold_result}"


if __name__ == "__main__":
    test_respond()
