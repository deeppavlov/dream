import pytest
import requests

@pytest.mark.parametrize(
    "request_data, gold_results",
    [({"last_utterances": [["кто написал войну и мир?"]]},
        [
            {
                "entities": ["войну и мир"],
                "labelled_entities": [{"label": "literary_work", "offsets": [12, 23], "text": "войну и мир"}],
            }
        ]
      )
    ]
)
def test_entity_detection_rus(url: str, request_data: dict, gold_results: list[dict]):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert result == gold_results
