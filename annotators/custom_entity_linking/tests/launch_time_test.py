import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from deeppavlov_kg import TerminusdbKnowledgeGraph


load_dotenv("./.env")

INDEX_LOAD_PATH = Path(os.path.expanduser("~/.deeppavlov/downloads/entity_linking_eng/custom_el_eng_dream"))
TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
TERMINUSDB_SERVER_TEAM = "admin"
TERMINUSDB_SERVER_DB = "user_knowledge_db"
TERMINUSDB_SERVER_PASSWORD = "root"


graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
    index_load_path=INDEX_LOAD_PATH,
)


def main():
    start_time = time.time()
    CUSTOM_ENTITY_LINKING_PORT = 8153

    CUSTOM_ENTITY_LINKING_URL = f"http://0.0.0.0:{CUSTOM_ENTITY_LINKING_PORT}/model"

    inserted_data = {
        "user_id": "User/Jack",
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

    request_data = {
        "user_id": ["User/Jack"],
        "entity_substr": [["forrest gump"]],
        "entity_tags": [[[("film", 1.0)]]],
        "contexts": [["who directed forrest gump?"]],
    }

    trials = 0
    response = None
    while response != 200:
        try:
            response = requests.post(CUSTOM_ENTITY_LINKING_URL, json=request_data).status_code

        except Exception:
            time.sleep(2)
            trials += 1
            if trials > 30:
                raise TimeoutError("Couldn't build the component")

    total_time = time.time() - start_time
    print("Success")
    print(f"custom entity linking launch time = {total_time:.3f}s")


if __name__ == "__main__":
    main()
