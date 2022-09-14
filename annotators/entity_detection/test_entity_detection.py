import requests


def main():
    url = "http://0.0.0.0:8103/respond"

    request_data = [
        {"sentences": [["what is the capital of russia?"]]},
        {"sentences": [["let's talk about politics."]]},
    ]

    gold_results = [
        [
            {
                "entities": ["capital", "russia"],
                "labelled_entities": [
                    {"text": "capital", "offsets": [12, 19], "label": "misc", "finegrained_label": [["misc", 1.0]]},
                    {
                        "text": "russia",
                        "offsets": [23, 29],
                        "label": "location",
                        "finegrained_label": [["country", 0.953]],
                    },
                ],
            }
        ],
        [
            {
                "entities": ["politics"],
                "labelled_entities": [
                    {"text": "politics", "offsets": [17, 25], "label": "misc", "finegrained_label": [["misc", 1.0]]}
                ],
            }
        ],
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
