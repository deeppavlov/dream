import requests
import json

pizza = json.load(open("common/prompts/pizza.json", "r"))["prompt"]
spacex = json.load(open("common/prompts/spacex.json", "r"))["prompt"]
ielts = json.load(open("common/prompts/ielts.json", "r"))["prompt"]


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
            "prompt": [pizza, spacex, ielts],
        },
        {
            "max_similarity": 0.7275472283363342,
            "prompt": [spacex, ielts, pizza],
        },
    ]

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
