import requests


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
            {},
            {},
        ],
    }

    result = requests.post(url, json=input_data).json()
    assert all([isinstance(element, dict) and "prompts" in element for element in result]), print(result)
    print("Success!")


if __name__ == "__main__":
    main()
