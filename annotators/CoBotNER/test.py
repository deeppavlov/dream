import requests


def main():
    url = "http://0.0.0.0:8102/entities"

    request_data = {
        "sentences": ["i like baseball but my favorite sportsman is michail jordan who is a basketballist."],
        "nounphrases": [["baseball", "sportsman", "michail jordan", "basketballist"]],
    }

    result = requests.post(url, json=request_data).json()[0]
    gold_result = {
        "entities": ["baseball", "sportsman", "michail jordan", "basketballist"],
        "labelled_entities": [
            {"text": "baseball", "label": "sport"},
            {"text": "sportsman", "label": "misc"},
            {"text": "michail jordan", "label": "person"},
            {"text": "basketballist", "label": "sport"},
        ],
    }

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
