from deeppavlov_kg import TerminusdbKnowledgeGraph
from dotenv import load_dotenv

load_dotenv()

DB = "test_italy_skill"
TEAM = "yashkens|c77b"

terminus_kg = TerminusdbKnowledgeGraph(team=TEAM, db_name=DB)

print(terminus_kg.ontology.get_all_entity_kinds())

print(terminus_kg.get_all_entities())