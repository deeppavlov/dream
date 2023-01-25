import requests


def test_respond():
    url = "http://0.0.0.0:8136/respond"
    contexts = [
        [
            "Respond like a friendly chatbot",
            "Human: Hi! I am Marcus. How are you today?",
        ]
    ]
    result = requests.post(url, json={"dialog_contexts": contexts}).json()
    print(result)
    assert [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
