import os
from dotenv import load_dotenv
from deeppavlov_kg import TerminusdbKnowledgeGraph

load_dotenv("./.env")
load_dotenv("./.env_secret")


def main():
    TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
    TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")
    assert TERMINUSDB_SERVER_PASSWORD, "TerminusDB server password is not specified in env"
    TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
    TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM")

    graph = TerminusdbKnowledgeGraph(
        db_name=TERMINUSDB_SERVER_DB,
        team=TERMINUSDB_SERVER_TEAM,
        server=TERMINUSDB_SERVER_URL,
        password=TERMINUSDB_SERVER_PASSWORD,
    )

    entity_kind_details = graph.ontology.get_all_entity_kinds()
    entity_kinds = [entity_kind for entity_kind, _ in entity_kind_details.items()]
    print(f"Entity kinds in db: {entity_kinds}")
    print("Success")


if __name__ == "__main__":
    main()
