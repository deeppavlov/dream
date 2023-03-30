# import json 

from deeppavlov_kg import TerminusdbKnowledgeGraph
import json
from scenario.config import KG_DB_NAME, KG_TEAM_NAME, KG_PASSWORD, KG_SERVER


terminus_kg = TerminusdbKnowledgeGraph(
    team=KG_TEAM_NAME, db_name=KG_DB_NAME, server=KG_SERVER, password=KG_PASSWORD
    )

# to get a list of sugar ingredients
PARENT = "Gluten"
NUMBER_OF_GENERATIONS=2

all_entities = terminus_kg.ontology.get_all_entity_kinds()
children = []
children += [k for k,v in all_entities.items() if v.get("@inherits")==PARENT]
print(len(children))
for _ in range(NUMBER_OF_GENERATIONS):
    children += [k for k,v in all_entities.items() if v.get("@inherits") in children]

# print(children)

# get a list of desserts
all_entities = terminus_kg.ontology.get_all_entity_kinds()
desserts = []
desserts += [k for k,v in all_entities.items() if v.get("@inherits")=="Dessert"]

# print(desserts)

sugar_free_desserts = []
for des in desserts:
    lst_ing = []
    ingredients = terminus_kg.ontology.get_entity_kind(des)
    for k, v in ingredients.items():
        if isinstance(v, dict):
            lst_ing.append(v["@class"])
    # print(des, len(list(set(lst_ing) & set(children))))
    sugar_ingredient_intersection = list(set(lst_ing) & set(children))
    if len(sugar_ingredient_intersection) < 1:
        sugar_free_desserts.append(des)

print(len(sugar_free_desserts), sugar_free_desserts)


# print(terminus_kg.get_all_entities())
# print(terminus_kg.ontology.get_all_entity_kinds("Dessert"))
# if terminus_kg.ontology.get_entity_kind("Pecan_pie"):
#     print("True")
    
slot_value = []
ingredients = terminus_kg.ontology.get_entity_kind("chocolat_fondant")
# print(ingredients.items())
# for k, v in ingredients.items():
#     if isinstance(v, dict):
#         slot_value.append(v["@class"])

# print(slot_value)
# food = ", ".join(slot_value) # TO_DO: code to check underscore in names and delete it
# print(food)
# print("This dessert consists of: {}.".format(food))

# desserts = ["apple pie", "pudding"]

# # To capitalize and underscore dessert_id
# for i in range(len(desserts)):
#     desserts[i] = desserts[i].replace(" ", "_")
#     desserts[i] = desserts[i].capitalize()

# print(desserts)
# with open("pr_ex.json", "r") as file:
#      data = json.load(file)
#      print(data["dialog"]["human_utterances"][-1]["annotations"]["entity_detection"]["entities"][-1])