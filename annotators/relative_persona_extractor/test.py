import requests


def main():
    url = "http://0.0.0.0:8133/respond"
    input_data = {
        "contexts": [
            [
                "How do you spend your spare time?",
                "I like to watch movies and eat pizza.",
                "Cool! What else do you like?",
            ],
            [
                "I like to go to the cinema on fridays",
                "great. how do you spend your spare time?",
                "I like to watch movies",
            ],
        ]
    }
    gold = [
        {
            "max_similarity": 0.6948127746582031,
            "persona": [
                "I like Italian food especially pasta and pizza.",
                "I like to watch football and basketball on TV.",
                "I like watching travel video blogs.",
            ],
        },
        {
            "max_similarity": 0.6451027989387512,
            "persona": [
                "I like watching travel video blogs.",
                "I like to watch football and basketball on TV.",
                "I like Italian food especially pasta and pizza.",
            ],
        },
    ]

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
