from deeppavlov_kg import TerminusdbKnowledgeGraph
import json


DB = "test_italy_skill"
# TEAM = ""
TEAM = "yashkens|c77b"

PASSWORD = ""  #insert your password here

terminus_kg = TerminusdbKnowledgeGraph(
    team=TEAM, db_name=DB, server="https://7063.deeppavlov.ai/", password=PASSWORD
    )

# terminus_kg.drop_database()

# print(terminus_kg.get_all_entities())
# user_existing_entities = terminus_kg.get_properties_of_entity(entity_id="User/")
# print(user_existing_entities.keys())
print(user_existing_entities['FAVORITE_FOOD/AbstractFood'])



# with open("skills/dff_travel_italy_skill/new.json", "r") as file:
#     user_info = json.load(file)
#     print(user_info["dialog"]["human_utterances"][-1]["user"]["id"])

# to retrieve user_id
# user_id = ctx.misc["agent"]["dialog"]["human_utterances"][-1]["user"]["id"]
# user_id = "User/" + user_id