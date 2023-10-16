import pytest
import requests

from typing import Dict, List


@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {"last_utterances": [["кто написал войну и мир?"]]},
            [
                {
                    "entities": ["войну и мир"],
                    "labelled_entities": [{"label": "literary_work", "offsets": [12, 23], "text": "войну и мир"}],
                }
            ],
        )
    ],
)
def test_entity_detection_rus(url: str, request_data: Dict, gold_results: List[Dict]):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert result == gold_results
