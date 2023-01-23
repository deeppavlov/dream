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
        ]
    }
    gold = [
        {"prompts": ["pizza", "dream_persona"], "max_similarity": 0.7664722204208374},
        {"prompts": ["pizza", "dream_persona"], "max_similarity": 0.277923583984375},
    ]

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
