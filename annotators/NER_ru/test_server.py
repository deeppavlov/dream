import requests


def main():
    url = "http://0.0.0.0:8021/ner"

    request_data = [{"last_utterances": [["я видела ивана в москве"]]}]

    gold_results = [
        [
            [
                {"confidence": 1, "end_pos": 14, "start_pos": 9, "text": "ивана", "type": "PER"},
                {"confidence": 1, "end_pos": 23, "start_pos": 17, "text": "москве", "type": "LOC"},
            ]
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
