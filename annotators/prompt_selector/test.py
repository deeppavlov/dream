import requests
from os import getenv


def main():
    url = "http://0.0.0.0:8135/respond"
    input_data = {
        "contexts": [
            [
                "Hello! I would like to order pizza.",
            ],
            [
                "What is SpaceX?",
            ],
        ],
        "prompts_goals": [
            {
                "pizza": "Assists the user in ordering food and providing answers based on a pre-defined FAQ list.",
                "dream_persona": "Responds in a friendly and caring manner to engage and connect with the user.",
            },
        ],
        "last_human_utterances": [
            {
                "text": "What is SpaceX?",
                "attributes": {"openai_api_key": getenv("OPENAI_API_KEY")},
            },
        ],
    }

    result = requests.post(url, json=input_data).json()
    assert all([isinstance(element, dict) and "prompts" in element for element in result]), print(result)
    print("Success!")


if __name__ == "__main__":
    main()
