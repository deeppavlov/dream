import requests


def main():
    url = "http://0.0.0.0:8002/dialogact"

    request_data = {
        "utterances_histories": [
            [
                ["let's chat about jesus"],
                ["no", "let's chat about animals"],
                ["okay", "i love cats", "my cat is named putin"],
            ]
        ]
    }

    result = requests.post(url, json=request_data).json()
    gold_result = [
        [
            ["General_ChatIntent", "Information_RequestIntent", "Information_RequestIntent"],
            ["Other", "Science_and_Technology", "Science_and_Technology"],
        ]
    ]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
