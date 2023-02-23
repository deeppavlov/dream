import requests


def test_respond():
    url = "http://0.0.0.0:8130/respond"
    contexts = [
        [
            "Hi! I am Marcus. How are you today?",
            "Hi Marcus! I am fine. How are you?",
            "I am great. What are your plans for today?",
        ],
        ["Hi Marcus! I am fine. How are you?", "I am great. What are your plans for today?"],
    ]
    prompts = [
        "Respond like a friendly chatbot.",
        "Respond like a friendly chatbot.",
    ]
    result = requests.post(url, json={"dialog_contexts": contexts, "prompts": prompts}).json()
    print(result)
    assert [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success")
    print(result)


if __name__ == "__main__":
    test_respond()
