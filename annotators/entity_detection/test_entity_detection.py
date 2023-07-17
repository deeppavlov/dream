import pytest
import requests


@pytest.mark.parametrize(
    "request_data", "gold_results",
    request_data=[
        {"sentences": [["what is the capital of russia?"]]},
        {"sentences": [["let's talk about politics."]]},
    ],
    gold_results=[
        [
            {
                "entities": ["capital", "russia"],
                "labelled_entities": [
                    {"finegrained_label": [["misc", 0.871]], "label": "misc", "offsets": [12, 19], "text": "capital"},
                    {
                        "finegrained_label": [["loc", 0.9927]],
                        "label": "location",
                        "offsets": [23, 29],
                        "text": "russia",
                    },
                ],
            }
        ],
        [
            {
                "entities": ["politics"],
                "labelled_entities": [
                    {"finegrained_label": [["misc", 0.9984]], "label": "misc", "offsets": [17, 25], "text": "politics"}
                ],
            }
        ],
    ]
)
def test_entity_detection(url: str, request_data, gold_results):
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1
    assert count == len(request_data)
