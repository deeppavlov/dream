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
        {
            "max_similarity": 0.766472339630127,
            "prompts": ["pizza", "spacex", "ielts"],
        },
        {
            "max_similarity": 0.7275472283363342,
            "prompts": ["spacex", "ielts", "pizza"],
        },
    ]

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
