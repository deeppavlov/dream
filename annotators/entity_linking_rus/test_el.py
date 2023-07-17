import pytest
import requests

use_context = True


@pytest.mark.parametrize(
    "request_data", "gold_results",
    [
        {
            "entity_substr": [["форрест гамп"]],
            "entity_tags": [["film"]],
            "context": [["кто снял фильм форрест гамп?"]],
        },
        {
            "entity_substr": [["роберт левандовский"]],
            "entity_tags": [["per"]],
            "context": [["за какую команду играет роберт левандовский?"]],
        },
    ],
    [["Q134773"], ["Q151269"]]
)
def test_entity_linking(url: str, request_data, gold_results):
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        entity_ids = result[0][0]["entity_ids"]
        if entity_ids == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
