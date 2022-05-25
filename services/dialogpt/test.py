import requests


def test_respond():
    url = "http://0.0.0.0:8125/respond"

    contexts = [["hi", "hi. how are you?"], ["let's chat about movies", "cool. what movies do you like?"]]
    gold_result = [["I'm good, how are you?", 0.9], ["I like the new one.", 0.9]]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [
        len(sample[0]) > 0 and sample[1] > 0.0 for sample in result
    ], f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
