import os
import requests


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    contexts = [
        [
            "Hi! I am Marcus. How are you today?",
            "Hi Marcus! I am fine. How are you?",
            "I am great. What are your plans for today?",
        ],
        ["Привет, Маркус! Я в порядке. Как дела?", "Я отлично. Какие у тебя планы на сегодня?"],
    ]
    prompts = [
        "Respond like a friendly chatbot. \n Dialog:\n",
        "Отвечай как дружелюбный бот.",
    ]
    result = requests.post(
        url,
        json={
            "dialog_contexts": contexts,
            "prompts": prompts,
        },
    ).json()
    print(result)

    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
