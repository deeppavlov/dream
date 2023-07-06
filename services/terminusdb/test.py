import os
from pathlib import Path
from dotenv import load_dotenv
from deeppavlov_kg import TerminusdbKnowledgeGraph

load_dotenv("./.env")
load_dotenv("./.env_secret")


def main():
    TERMINUSDB_SERVER_URL = os.getenv("TERMINUSDB_SERVER_URL")
    TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")
    assert TERMINUSDB_SERVER_PASSWORD, "TerminusDB server password is not specified in env"
    TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
    TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM")
    INDEX_LOAD_PATH = Path(os.path.expanduser("services/terminusdb"))

    graph = TerminusdbKnowledgeGraph(
        db_name=TERMINUSDB_SERVER_DB,
        team=TERMINUSDB_SERVER_TEAM,
        server=TERMINUSDB_SERVER_URL,
        password=TERMINUSDB_SERVER_PASSWORD,
        index_load_path=INDEX_LOAD_PATH,
    )

    entity_kind_details = graph.ontology.get_all_entity_kinds()
    entity_kinds = [entity_kind for entity_kind, _ in entity_kind_details.items()]
    print(f"Entity kinds in db: {entity_kinds}")
    print("Success")


if __name__ == "__main__":
    main()
