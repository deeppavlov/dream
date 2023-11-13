import json

import pytest

import sys
from os import path

import requests

PARENT_DIR = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(PARENT_DIR)


@pytest.mark.parametrize(
    "sentences, gold_result",
    [
        (
            {
                "last_utterances": [
                    ["john peterson is my brother.", "he lives in New York."],
                    ["my laptop was broken.", "could you show me the nearest store in Moscow where i can fix it."],
                ]
            },
            [
                [
                    [{"confidence": 1, "end_pos": 2, "start_pos": 0, "text": "john peterson", "type": "PER"}],
                    [{"confidence": 1, "end_pos": 5, "start_pos": 3, "text": "New York", "type": "LOC"}],
                ],
                [
                    [],
                    [{"confidence": 1, "end_pos": 9, "start_pos": 8, "text": "Moscow", "type": "LOC"}],
                ],
            ],
        )
    ],
)
def test_ner(url: str, sentences: dict, gold_result: list):
    response = requests.post(url, json=sentences, headers={"Content-Type": "application/json"})
    result = json.loads(response.text)
    assert response.status_code == 200
    assert result == gold_result
