import allure
import pytest
import requests

use_context = True


@allure.description("""Test linking entities to tags, context""")
@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {
                "entity_substr": [["forrest gump"]],
                "entity_tags": [[[("film", 0.9)]]],
                "context": [["who directed forrest gump?"]],
            },
            ["Q134773", "Q552213"],
        ),
        (
            {
                "entity_substr": [["robert lewandowski"]],
                "entity_tags": [[[("per", 0.9)]]],
                "context": [["what team does robert lewandowski play for?"]],
            },
            ["Q151269", "Q215925"],
        ),
    ],
)
def test_entity_linking(url: str, request_data, gold_results):
    result = requests.post(url, json=request_data).json()
    entity_ids = result[0][0]["entity_ids"]
    assert entity_ids == gold_results
