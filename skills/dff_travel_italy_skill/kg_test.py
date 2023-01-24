from deeppavlov_kg import TerminusdbKnowledgeGraph
from dotenv import load_dotenv

load_dotenv()

DB = "test_italy_skill"
# TEAM = ""
TEAM = "yashkens|c77b"

PASSWORD = ""  #insert your password here

terminus_kg = TerminusdbKnowledgeGraph(
    team=TEAM, db_name=DB, server="https://7063.deeppavlov.ai/", password=PASSWORD
    )

# terminus_kg= TerminusdbKnowledgeGraph(team=TEAM, db_name=DB)

# terminus_kg.drop_database()

print(terminus_kg.get_all_entities())