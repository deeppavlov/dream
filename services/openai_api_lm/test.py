import requests
from os import getenv


# ATTENTION!!! This test is only working if you assign `OPENAI_API_KEY` env variable
OPENAI_API_KEY = getenv("OPENAI_API_KEY", None)
OPENAI_ORGANIZATION = getenv("OPENAI_ORGANIZATION", None)
assert OPENAI_API_KEY, print("No OpenAI API key is given in env vars")


def test_respond():
    url = "http://0.0.0.0:8131/respond"

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
            "OPENAI_API_KEY_list": [OPENAI_API_KEY] * len(contexts),
            "OPENAI_ORGANIZATION_list": [OPENAI_ORGANIZATION] * len(contexts),
            "prompts": prompts,
            "configs": ["openai-text-davinci-003.json"] * len(contexts),
        },
    ).json()
    print(result)

    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
