import allure
import pytest
import requests

from typing import Dict, List


@allure.description("""Test entities detection and labeling""")
@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {"sentences": [["what is the capital of russia?"]]},
            [
                {
                    "entities": ["capital", "russia"],
                    "labelled_entities": [
                        {
                            "finegrained_label": [["misc", 0.871]],
                            "label": "misc",
                            "offsets": [12, 19],
                            "text": "capital",
                        },
                        {
                            "finegrained_label": [["loc", 0.9927]],
                            "label": "location",
                            "offsets": [23, 29],
                            "text": "russia",
                        },
                    ],
                }
            ],
        ),
        (
            {"sentences": [["let's talk about politics."]]},
            [
                {
                    "entities": ["politics"],
                    "labelled_entities": [
                        {
                            "finegrained_label": [["misc", 0.9984]],
                            "label": "misc",
                            "offsets": [17, 25],
                            "text": "politics",
                        }
                    ],
                }
            ],
        ),
    ],
)
def test_entity_detection(url: str, request_data: Dict[str, list], gold_results: List[Dict]):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert "entities" in result[0]
    assert "labelled_entities" in result[0]
    assert result == gold_results
