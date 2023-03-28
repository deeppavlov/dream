import os
import requests


DEFAULT_CONFIG = {
    "max_length": 60,
    "min_length": 8,
    "top_p": 0.9,
    "temperature": 0.9,
    "do_sample": True,
    "num_return_sequences": 2,
}
SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
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
    result = requests.post(
        url,
        json={
            "dialog_contexts": contexts,
            "prompts": prompts,
            "configs": [DEFAULT_CONFIG] * len(contexts),
        },
    ).json()
    print(result)

    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
