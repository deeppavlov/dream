import requests
from os import getenv


# ATTENTION!!! This test is only working if you assign `GIGACHAT_CREDENTIALS` env variable
GIGACHAT_CREDENTIALS = getenv("GIGACHAT_CREDENTIALS", None)
GIGACHAT_SCOPE = getenv("GIGACHAT_SCOPE", None)
assert GIGACHAT_CREDENTIALS, print("No GigaChat credentials is given in env vars")
DEFAULT_CONFIG = {"max_tokens": 64, "temperature": 0.4, "top_p": 1.0, "frequency_penalty": 0, "presence_penalty": 0}
SERVICE_PORT = int(getenv("SERVICE_PORT"))


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    contexts = [
        [
            "Привет! Я Маркус. Как ты сегодня?",
            "Привет, Маркус! Я в порядке. Как у тебя?",
            "У меня все отлично. Какие у тебя планы на сегодня?",
        ],
        ["Привет, Маркус! Я в порядке. Как у тебя?", "У меня все отлично. Какие у тебя планы на сегодня?"],
    ]
    prompts = [
        "Отвечай как дружелюбный чатбот.",
        "Отвечай как дружелюбный чатбот.",
    ]
    result = requests.post(
        url,
        json={
            "dialog_contexts": contexts,
            "prompts": prompts,
            "configs": [DEFAULT_CONFIG] * len(contexts),
            "gigachat_credentials": [GIGACHAT_CREDENTIALS] * len(contexts),
            "gigachat_scopes": [GIGACHAT_SCOPE] * len(contexts),
        },
    ).json()
    print(result)

    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
