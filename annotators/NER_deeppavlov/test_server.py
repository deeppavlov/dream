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
            {'confidence': 1, 'end_pos': 3, 'start_pos': 2, 'text': 'ивана', 'type': 'PER'},
            {'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'москве', 'type': 'LOC'}
        ],
        [
            {'confidence': 1, 'end_pos': 3, 'start_pos': 2, 'text': 'Ивана', 'type': 'PER'},
            {'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'Москве', 'type': 'LOC'}
        ],
        [
            {'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'justin', 'type': 'ORG'},
            {'confidence': 1, 'end_pos': 11, 'start_pos': 9, 'text': 'sahara desert', 'type': 'LOC'}
        ],
        [
            {'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'Justin', 'type': 'PER'},
            {'confidence': 1, 'end_pos': 11, 'start_pos': 9, 'text': 'Sahara Desert', 'type': 'LOC'}
        ],
        [
            {'confidence': 1, 'end_pos': 5, 'start_pos': 3, 'text': 'Bob Smith', 'type': 'PER'},
            {'confidence': 1, 'end_pos': 8, 'start_pos': 6, 'text': 'Las Vegas', 'type': 'LOC'}
        ]
    ]

    result = requests.post(url, json=request_data).json()
    assert result == gold_results, print(result)
    print("Success")


if __name__ == "__main__":
    main()
