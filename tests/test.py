import argparse
import os
import random
from time import sleep
from urllib import parse

import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_PORT = os.getenv("BOT_PORT")
PORTAINER_URL = os.getenv("PORTAINER_URL")

if BOT_PORT and PORTAINER_URL:
    print("testing in portainer")
    BOT_URL = f"http://{parse.urlparse(PORTAINER_URL).hostname}:{BOT_PORT}"
else:
    BOT_URL = "http://0.0.0.0:4242"

host = parse.urlparse(PORTAINER_URL).hostname


def test_bot():
    user_id = random.randint(0, 100)
    res = requests.post(
        BOT_URL,
        json={
            "user_id": f"test-user-{user_id}",
            "payload": "Help me with an article about penguins.",
        },
    ).json()["active_skill"]
    if "prompted" in res:
        print("Success!")
    else:
        raise ValueError(f"\nERROR: assistant returned `{res}`\n")


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
            BOT_URL,
            json={
                "user_id": f"test-user-{random.randint(100, 1000)}",
                "payload": "What song should I sing to my baby?",
                "api_keys": {"openai_api_key": OPENAI_API_KEY},
                "skills": [
                    {
                        "name": "dff_baby_sitting_prompted_skill",
                        "display_name": "Baby Sitting Assistant",
                        "prompt": """TASK: Your name is Baby Sitting Assistant. You were made by Babies & Co.
Help the human to get busy a baby. Do not discuss other topics. Respond with empathy.
Ask open-ended questions to help the human understand what to do with a baby.
""",
                        "lm_service": {
                            "url": LM_SERVICES_MAPPING[lm_service],
                            "kwargs": None,
                        },
                    }
                ],
            },
        ).json()["active_skill"]

        if result == "dff_baby_sitting_prompted_skill":
            print("Success!")
        else:
            raise ValueError(f"\nERROR: `Universal Assistant` returned `{result}` with lm service {lm_service}\n")
        sleep(5)


def check_universal_selectors_assistant(lm_services):
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is None!")

    for lm_service in lm_services:
        print(f"Checking `Universal Selectors Assistant` with `{lm_service}`")
        skills_full_input = [
            {
                "name": "dff_mathematician_prompted_skill",
                "display_name": "Mathematician Skill",
                "description": "Mathematician Skill imitating an intelligent person.",
                "prompt": "Answer like you are mathematician.",
                "lm_service": {
                    "url": LM_SERVICES_MAPPING[lm_service],
                    "config": {
                        "max_tokens": 64,
                        "temperature": 0.9,
                        "top_p": 1.0,
                        "frequency_penalty": 0,
                        "presence_penalty": 0,
                    },
                    "kwargs": None,
                },
            },
            {
                "name": "dff_blondy_prompted_skill",
                "display_name": "Blondy skill",
                "description": "Skill for stupid funny responses imitating a blondy girl.",
                "prompt": "Answer like you are a stupid Blondy Girl.",
                "lm_service": {
                    "url": LM_SERVICES_MAPPING[lm_service],
                    "config": None,
                    "kwargs": None,
                },
            },
        ]

        print("Checking debugging `Skill Selector`")
        result = requests.post(
            BOT_URL,
            json={
                "user_id": f"test-user-{random.randint(100, 1000)}",
                "payload": "How much is two plus two?",
                "api_keys": {"openai_api_key": OPENAI_API_KEY},
                "skills": skills_full_input,
                # skill selector     ----------------------------
                "skill_selector": {
                    "prompt": """Select up to 1 the most relevant to the dialog context skills.
LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS
Return only names of the selected skills divided by comma. Do not respond to the dialog context.""",
                    "lm_service": {
                        "url": LM_SERVICES_MAPPING[lm_service],
                        "config": {
                            "max_tokens": 128,
                            "temperature": 0.4,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                        },
                        "kwargs": None,
                    },
                },
                "debug_output": True,
            },
        ).json()

        if result["active_skill"] != "dummy_skill" and "hypotheses" in result.get("debug_output", {}):
            print("Success!")
        else:
            raise ValueError(
                f"\nERROR: `Universal Selectors Assistant` returned `{result['response']}` "
                f"with lm service {lm_service}\n"
            )
        sleep(5)

        print("Checking debugging `Response Selector`")
        result = requests.post(
            BOT_URL,
            json={
                "user_id": f"test-user-{random.randint(100, 1000)}",
                "payload": "How much is two plus two?",
                "api_keys": {"openai_api_key": OPENAI_API_KEY},
                "skills": skills_full_input,
                # response selector     ----------------------------
                "response_selector": {
                    "prompt": "Select the most funny answer.\nLIST_OF_HYPOTHESES\n",
                    "lm_service": {
                        "url": LM_SERVICES_MAPPING[lm_service],
                        "config": {
                            "max_tokens": 64,
                            "temperature": 0.9,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                        },
                        "kwargs": None,
                    },
                },
                # skill selector     ----------------------------
                "selected_skills": "all",
            },
        ).json()

        if result["active_skill"] in ["dff_mathematician_prompted_skill", "dff_blondy_prompted_skill"]:
            print("Success!")
        else:
            raise ValueError(
                f"\nERROR: `Universal Selectors Assistant` returned `{result['text']}` with lm service {lm_service}\n"
            )
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
    elif assistant == "universal_selectors_assistant":
        check_universal_selectors_assistant(["ChatGPT"])  # TODO: add "GPT-4 32k", "GPT-4" and "ChatGPT 16k"


if __name__ == "__main__":
    main()
