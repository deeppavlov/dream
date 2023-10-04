from deeppavlov_kg import TerminusdbKnowledgeGraph


def main():
    TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
    TERMINUSDB_SERVER_TEAM = "admin"
    TERMINUSDB_SERVER_DB = "user_knowledge_db"
    TERMINUSDB_SERVER_PASSWORD = "root"

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
