import pytest
import requests

use_context = True


@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {
                "entity_substr": [["форрест гамп"]],
                "entity_tags": [["film"]],
                "context": [["кто снял фильм форрест гамп?"]],
            },
            ["Q134773"],
        ),
        (
            {
                "entity_substr": [["роберт левандовский"]],
                "entity_tags": [["per"]],
                "context": [["за какую команду играет роберт левандовский?"]],
            },
            ["Q151269"],
        ),
    ],
)
def test_entity_linking(url: str, request_data: dict[str, list], gold_results: list[str]):
    response = requests.post(url, json=request_data)
    result = response.json()
    entity_ids = result[0][0]["entity_ids"]
    assert response.status_code == 200
    assert entity_ids == gold_results
