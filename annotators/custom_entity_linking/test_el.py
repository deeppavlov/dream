import requests

use_context = True


def main():
    url = "http://0.0.0.0:8153"
    inserted_data = {
        "user_id": "1234",
        "entity_info": {
            "entity_substr": ["forrest gump"],
            "entity_ids": ["film/123"],
            "tags": ["film"],
        },
    }
    requests.post(f"{url}/add_entities", json=inserted_data)

    request_data = [
        {
            "user_id": ["1234"],
            "entity_substr": [["forrest gump"]],
            "entity_tags": [[[("film", 1.0)]]],
            "context": [["who directed forrest gump?"]],
        }
    ]
    gold_results = [["film/123"]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(f"{url}/model", json=data).json()
        print(result)

        entity_ids = []
        for entity_info_list in result:
            for entity_info in entity_info_list:
                entity_ids = entity_info.get("entity_ids")

        if entity_ids == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
