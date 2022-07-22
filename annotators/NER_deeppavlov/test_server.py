import requests


def main():
    url = "http://0.0.0.0:8021/ner"

    request_data = {
        "last_utterances": [
            ["я видела ивана в москве"],
            ["Я видела Ивана в Москве"],
            ["i have heard about justin. he is in sahara desert"],
            ["I have heard about Justin. He is in Sahara Desert"],
        ]
    }

    gold_results = [
        [
            [
                {"confidence": 1, "end_pos": 14, "start_pos": 9, "text": "ивана", "type": "PER"},
                {"confidence": 1, "end_pos": 23, "start_pos": 17, "text": "москве", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 14, "start_pos": 9, "text": "Ивана", "type": "PER"},
                {"confidence": 1, "end_pos": 23, "start_pos": 17, "text": "Москве", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 25, "start_pos": 19, "text": "justin", "type": "ORG"},
                {"confidence": 1, "end_pos": 42, "start_pos": 36, "text": "sahara", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 25, "start_pos": 19, "text": "Justin", "type": "PER"},
                {"confidence": 1, "end_pos": 42, "start_pos": 36, "text": "Sahara", "type": "ORG"},
                {"confidence": 1, "end_pos": 50, "start_pos": 43, "text": "Desert", "type": "ORG"},
            ]
        ],
    ]

    result = requests.post(url, json=request_data).json()
    assert result == gold_results, print(result)
    print("Success")


if __name__ == "__main__":
    main()
