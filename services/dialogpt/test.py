import os
import requests


N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))


def test_respond():
    url = "http://0.0.0.0:8128/respond"

    sentence_pairs = [["hi", "hi. how are you?"],
                      ["let's chat about movies", "cool. what movies do you like?"]]

    result = requests.post(url, json={"sentence_pairs": sentence_pairs}).json()
    assert [
        len(sample[0]) > 0 and all([len(text) > 0 for text in sample[0]]) and all([conf > 0.0 for conf in sample[1]])
        for sample in result
    ], f"Got\n{result}\n, but expected:\n"
    print("Success")


if __name__ == "__main__":
    test_respond()
