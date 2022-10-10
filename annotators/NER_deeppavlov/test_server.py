import requests


def main():
    url = "http://0.0.0.0:8021/ner"

    request_data = {
        "last_utterances": [
            ["я видела ивана в москве"],
            ["Я видела Ивана в Москве"],
            ["i have heard about justin. he is in sahara desert"],
            ["I have heard about Justin. He is in Sahara Desert"],
            ["can john smith move forward for 15 meters, then for fifteen meters, and get back to las vegas then"],
            ["я бы проехала на 30 метров вперед, а потом повернула на сорок пять градусов по часовой стрелке"],
        ]
    }

    gold_results = [
        [
            [
                {"confidence": 1, "end_pos": 3, "start_pos": 2, "text": "ивана", "type": "PER"},
                {"confidence": 1, "end_pos": 5, "start_pos": 4, "text": "москве", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 3, "start_pos": 2, "text": "Ивана", "type": "PER"},
                {"confidence": 1, "end_pos": 5, "start_pos": 4, "text": "Москве", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 5, "start_pos": 4, "text": "justin", "type": "PER"},
                {"confidence": 1, "end_pos": 11, "start_pos": 9, "text": "sahara desert", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 5, "start_pos": 4, "text": "Justin", "type": "PER"},
                {"confidence": 1, "end_pos": 11, "start_pos": 9, "text": "Sahara Desert", "type": "LOC"},
            ]
        ],
        [
            [
                {"confidence": 1, "end_pos": 3, "start_pos": 1, "text": "john smith", "type": "PER"},
                {"confidence": 1, "end_pos": 8, "start_pos": 6, "text": "15 meters", "type": "QUANTITY"},
                {"confidence": 1, "end_pos": 13, "start_pos": 11, "text": "fifteen meters", "type": "QUANTITY"},
                {"confidence": 1, "end_pos": 20, "start_pos": 18, "text": "las vegas", "type": "LOC"},
            ]
        ],
        [[]],
    ]

    result = requests.post(url, json=request_data).json()
    assert result == gold_results, print(result)
    print("Success")


if __name__ == "__main__":
    main()
