from pathlib import Path
import os
import uuid
import requests
from deeppavlov_kg import TerminusdbKnowledgeGraph


TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
TERMINUSDB_SERVER_TEAM = "admin"
TERMINUSDB_SERVER_DB = "bot_knowledge_db"
TERMINUSDB_SERVER_PASSWORD = "root"
INDEX_LOAD_PATH = Path(os.path.expanduser("annotators/user_knowledge_memorizer"))
USER_KG_PORT = 8027

USER_KG_URL = f"http://0.0.0.0:{USER_KG_PORT}/respond"

graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
    index_load_path=INDEX_LOAD_PATH,
)

# graph.drop_database()

print(graph.ontology.get_all_entity_kinds())
print(graph.get_all_entities())
# # graph.ontology.create_entity_kind("Bot")
# bot_id = graph.create_entity("Bot", "/".join(["Bot", str(uuid.uuid4())]))
# print(bot_id)
user_existing_entities = graph.get_properties_of_entity(entity_id="Bot/514b2c2d-bb72-4294-9486-04f9e099825e")
print(user_existing_entities.keys())
# # graph.ontology.create_entity_kind("Hobby")
# graph.ontology.create_relationship_kind("Bot", "like_activity", "Hobby")
# # graph.create_entities(["Bot", "Hobby"], ["Bot/5f205630-a516-4d26-b89c-30f07eab98f0", "Hobby/reading"])
# graph.create_entities(["Hobby"], ["Hobby/reading"])
graph.create_relationships(["Bot/514b2c2d-bb72-4294-9486-04f9e099825e"], ["like_activity"], ["Hobby/reading"])
print(user_existing_entities.keys())
