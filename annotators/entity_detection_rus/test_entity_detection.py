import pytest
import requests

@pytest.mark.parametrize(
    "request_data", "gold_results",
    request_data=[{"last_utterances": [["кто написал войну и мир?"]]}],
    gold_results=[
        [
            {
                "entities": ["войну и мир"],
                "labelled_entities": [{"label": "literary_work", "offsets": [12, 23], "text": "войну и мир"}],
            }
        ]
    ]
)
def test_entity_detection_rus(url: str, request_data, gold_results):
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1

    assert count == len(request_data)
