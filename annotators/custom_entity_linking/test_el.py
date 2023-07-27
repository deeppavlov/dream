import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from deeppavlov_kg import TerminusdbKnowledgeGraph

load_dotenv("./.env")

TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
INDEX_LOAD_PATH = Path(os.path.expanduser("annotators/user_knowledge_memorizer"))

graph = TerminusdbKnowledgeGraph(db_name=TERMINUSDB_SERVER_DB, index_load_path=INDEX_LOAD_PATH)


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
    graph.index.set_active_user_id(inserted_data["user_id"])
    graph.index.add_entities(
        inserted_data["entity_info"]["entity_substr"],
        inserted_data["entity_info"]["entity_ids"],
        inserted_data["entity_info"]["tags"],
    )

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
