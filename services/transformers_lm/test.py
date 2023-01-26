import os
import requests


N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))


def test_respond():
    url = "http://0.0.0.0:8130/respond"
    contexts = [
        [
            "Respond like a friendly chatbot",
            "Human: Hi! I am Marcus. How are you today?",
        ]
    ]
    result = requests.post(url, json={"dialog_contexts": contexts}).json()
    print(result)
    assert [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success")
    print(result)


if __name__ == "__main__":
    test_respond()
