import os
import requests


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
LANGUAGE = os.getenv("LANGUAGE", "EN")


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    if LANGUAGE == "RU":
        contexts = [
            [
                "Здарова, Миша, как дела?",
                "Привет! Все в порядке. А у тебя как?",
                "По-тихоньку. Есть планы на сегодня?",
            ],
            ["Здарова, Миша, как дела?", "Все в порядке. Есть планы на сегодня?"],
        ]
        prompts = [
            "Отвечай на диалог как дружелюбный чат-бот.",
            "Отвечай на диалог как дружелюбный чат-бот.",
        ]
    else:
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
        },
    ).json()
    print(result)

    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
