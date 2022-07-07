import requests


def main():
    url = "http://0.0.0.0:8103/respond"

    request_data = [{"last_utterances": [["кто написал войну и мир?"]]}]

    gold_results = [
        [
            {
                "entities": ["войну и мир"],
                "labelled_entities": [{"label": "literary_work", "offsets": [12, 23], "text": "войну и мир"}],
            }
        ]
    ]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
