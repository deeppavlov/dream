from deeppavlov_kg import TerminusdbKnowledgeGraph
import json
from scenario.config import KG_DB_NAME, KG_TEAM_NAME, KG_PASSWORD, KG_SERVER


terminus_kg = TerminusdbKnowledgeGraph(
    team=KG_TEAM_NAME, db_name=KG_DB_NAME, server=KG_SERVER, password=KG_PASSWORD
    )

# terminus_kg.drop_database()

print(terminus_kg.get_all_entities())
