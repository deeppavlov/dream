import argparse
import os
import random
from time import sleep

import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def test_bot():
    user_id = random.randint(0, 100)
    res = requests.post(
        "http://0.0.0.0:4242",
        json={
            "user_id": f"test-user-{user_id}",
            "payload": "Who are you? who built you? what can you do?",
        },
    ).json()["active_skill"]
    if "prompted" in res:
        print("Success!")
    else:
        raise ValueError(f"\nERROR: assistant returned `{res}`\n")


prompt = """TASK: Your name is Baby Sitting Assistant. You were made by Babies & Co.
Help the human to get busy a baby. Do not discuss other topics. Respond with empathy.
Ask open-ended questions to help the human understand what to do with a baby.
"""

LM_SERVICES_MAPPING = {
    "Open-Assistant SFT-1 12B": "http://transformers-lm-oasst12b:8158/respond",
    "GPT-JT 6B": "http://transformers-lm-gptjt:8161/respond",
    "GPT-3.5": "http://openai-api-davinci3:8131/respond",
    "ChatGPT": "http://openai-api-chatgpt:8145/respond",
    "ChatGPT 16k": "http://openai-api-chatgpt-16k:8167/respond",
    "GPT-4 32k": "http://openai-api-gpt4-32k:8160/respond",
    "GPT-4": "http://openai-api-gpt4:8159/respond",
}


def check_universal_assistant(lm_services):
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is None!")
    for lm_service in lm_services:
        print(f"Checking `Universal Assistant` with `{lm_service}`")

        result = requests.post(
            "http://0.0.0.0:4242",
            json={
                "user_id": f"test-user-{random.randint(100, 1000)}",
                "payload": "I want an article about quantum physics for children.",
                "prompt": prompt,
                "lm_service_url": LM_SERVICES_MAPPING[lm_service],
                "openai_api_key": OPENAI_API_KEY,
            },
        ).json()["active_skill"]

        if "prompted" in result:
            print("Success!")
        else:
            raise ValueError(f"\nERROR: `Universal Assistant` returned `{result}` with lm service {lm_service}\n")
        sleep(5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("assistant", help="assistant to test")
    args = parser.parse_args()
    assistant = args.assistant
    if assistant == "multiskill_ai_assistant":
        test_bot()
    elif assistant == "universal_prompted_assistant":
        check_universal_assistant(["ChatGPT", "GPT-3.5"])  # TODO: add "GPT-4 32k", "GPT-4" and "ChatGPT 16k"


if __name__ == "__main__":
    main()
