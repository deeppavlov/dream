import requests


def main():
    url = f"http://0.0.0.0:8133/respond"
    input_data = {
        "contexts": [
            [
                "How do you spend your spare time?",
                "I like to watch movies and eat pizza.",
                "Cool! What else do you like?"
            ],
            [
                "I like to go to the cinema on fridays"
                "great. how do you spend your spare time?",
                "I like to watch movies and eat pizza.",
            ],
        ]
    }
    gold = []

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
