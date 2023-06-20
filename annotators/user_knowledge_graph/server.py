# pylint: disable=W1203

import os
import json
import logging
from typing import List, Dict, Tuple
from pathlib import Path
from uuid import uuid4
from flask import Flask, jsonify, request
from deeppavlov_kg import TerminusdbKnowledgeGraph


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)

with open('rel_list.json') as file:
    rel_kinds_dict = json.load(file)

TERMINUSDB_SERVER_URL = os.getenv("TERMINUSDB_SERVER_URL")
TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")
assert TERMINUSDB_SERVER_PASSWORD, "TerminusDB server password is not specified in env"
TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM")
INDEX_LOAD_PATH=Path(os.path.expanduser(os.getenv("INDEX_LOAD_PATH")))

graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
    index_load_path=INDEX_LOAD_PATH
)
logger.info('Graph Loaded!')

# [
#     {
#         'triplets': [
#             {'object': '2 dog', 'relation': 'have pet', 'subject': 'user'}, {'object': 'travel', 'relation': 'like activity', 'subject': 'user'}
#         ]
#     }
# ]
def check_property_vs_relationship(utterances_info: List[dict]) -> Tuple[list, list]:
    """Checks if the prop_ex triplets are relationship or property triplets."""
    if isinstance(utterances_info, dict):
        utterances_info = [utterances_info]

    relationships, properties = [], []
    for utterance_info in utterances_info:
        for _, value in utterance_info.items():
            for triplet in value:
                if "relation" in triplet:
                    relationships.append(triplet)
                elif "property" in triplet:
                    properties.append(triplet)
    return relationships, properties


# [
#     {
#         'confidences': [1.0, 1.0],
#         'entity_id_tags': ['Misc', 'AbstractBook'],
#         'entity_ids': ['Misc/c4076d20-769b-4812-ba27-a5d88d2dc2f9', 'AbstractBook/3fd23b02-604d-4846-8dc7-018c716d7f5a'],
#         'entity_substr': 'travel',
#         'tokens_match_conf': [1.0, 1.0]
#     }, {
#         'confidences': [1.0],
#         'entity_id_tags': ['Misc'],
#         'entity_ids': ['Misc/6ca7c2b7-2af9-4e9a-b485-27df1c63a4d0'],
#         'entity_substr': 'venice',
#         'tokens_match_conf': [1.0]
#     }
# ]

def get_entity_type(attributes):
    #TODO: this doesn't work. Most likely it should get output of entity-detection not prop-ex
    """Extracts DBPedia type from property extraction annotator."""
    if not isinstance(attributes, dict):
        return 'Misc'
    entity_info = attributes.get('entity_info', [])
    if not entity_info:
        return 'Misc'
    exact_entity_info = entity_info[list(entity_info.keys())[0]]
    finegrained = exact_entity_info.get('finegrained_types', [])
    if finegrained:
        entity_type = finegrained[0].capitalize()
        logger.info(f'Fine-grained type: {entity_type}')
        return entity_type
    return 'Misc'


def check_entities_in_index(custom_el_annotations: list, prop_ex_triplets: list) -> Tuple[dict, list]:
    entities_in_index, entities_not_in_index = {}, []
    logger.info(f"custom_el_annotations -- {custom_el_annotations}")
    for triplet in prop_ex_triplets:
        in_index = False
        for entity_info in custom_el_annotations:
            if triplet["object"] == entity_info["entity_substr"]:
                in_index = True
                entities_in_index[(entity_info["entity_substr"], entity_info["entity_id_tags"][0])] = entity_info["entity_ids"][0]
                break
        if not in_index:
            # relation = '_'.join(triplet['relation'].split(' '))
            logger.debug(f"triplet['relation'] -- {triplet['relation']}")
            if triplet["relation"] in rel_kinds_dict:
                entity_kind = rel_kinds_dict[triplet["relation"]]
            else:
                logger.debug(f"triplet['object'] -- {triplet['object']}")
                entity_kind = get_entity_type(triplet["object"])
            entities_not_in_index.append((triplet["object"], entity_kind))
    return entities_in_index, entities_not_in_index


def check_entities_in_kg(graph, entities: list) -> Tuple[list, list]:
    entities_in_kg, entities_not_in_kg = [], []

    all_entities_in_kg = graph.get_all_entities()

    for (entity_substr, entity_kind) in entities:
        in_kg = False
        for entity_props in all_entities_in_kg:
            if entity_substr == entity_props.get("substr") and entity_kind == entity_props["@type"]:
                entities_in_kg.append(entity_props)
                in_kg = True
        if not in_kg:
            entities_not_in_kg.append((entity_substr, entity_kind))
    return entities_in_kg, entities_not_in_kg


def add_entities_to_index(graph, user_id, entities_info_lists):

    substr_list = entities_info_lists["substr_list"]
    ids_list = entities_info_lists["ids_list"]
    kinds_list = entities_info_lists["kinds_list"]
    logger.debug(f"Adding to index user_id '{user_id}' - entity_info: "
                    f"'entity_substr': {substr_list}, 'entity_ids': {ids_list},"
                    f" 'tags': {kinds_list}")
    graph.index.set_active_user_id("2700259bdcd44")
    graph.index.add_entities(substr_list, ids_list, kinds_list)


def create_entities(graph, entities_info: List[Tuple[str, str]]):
    # entity_substr, entity_kinds, entity_ids = [], [], []
    entities_info_lists = {
        "substr_list": [],
        "kinds_list": [],
        "ids_list": []
    }

    for entity_info in entities_info:
        entities_info_lists["substr_list"].append(entity_info[0])
        entities_info_lists["kinds_list"].append(entity_info[1])
        entities_info_lists["ids_list"].append("/".join([entity_info[1], str(uuid4())]))
    
    try:
        graph.ontology.create_entity_kinds(entities_info_lists["kinds_list"])
    except ValueError:
        logger.info(f"All entity kinds '{entities_info_lists['kinds_list']}' are already in KG")
    
    property_kinds = [["substr"]]*len(entities_info_lists["substr_list"])
    property_values = [[substr] for substr in entities_info_lists["substr_list"]]
    graph.ontology.create_property_kinds_of_entity_kinds(entities_info_lists["kinds_list"], property_kinds)

    graph.create_entities(
        entities_info_lists["kinds_list"],
        entities_info_lists["ids_list"],
        property_kinds = property_kinds,
        property_values = property_values
    )
    return entities_info_lists


def prepare_triplets(entities_in_index, triplets, user_id):
    """Prepares the triplets to be in the format '[{"subject": user_id, "relationship": value, "object": entity_id}]'
    to be used in check_triplets_in_kg. Where value is got from triplets and entity_id is got from entities_in_index.
    """
    prepared_triplets = []
    new_entities_in_index = {}
    for (entity_substr, _), entity_id in entities_in_index.items():
        new_entities_in_index[entity_substr] = entity_id
    logger.info(f"entities_in_index -- {new_entities_in_index}")
    for triplet in triplets:
        logger.info(f"triplet -- {triplet}")
        prepared_triplets.append({
            "subject": user_id,
            "relationship": triplet["relation"],
            "object": new_entities_in_index.get(triplet["object"]),
        })
    return prepared_triplets


def check_triplets_in_kg(graph, triplets):
    """Checks if the prop_ex relationship kinds, between user and some entities, are the same as the ones in kg."""
    triplets_in_kg, triplets_not_in_kg = [], {
        "ids_a": [], "relationship_kinds": [], "ids_b": []
    }
    for triplet in triplets:
        if triplet["object"] is None: # when the object isn't in index
            add_to_kg = True
        else:
            for entity_id in triplet["object"]:
                relationship_kinds = graph.search_for_relationships(id_a=triplet["subject"], id_b=entity_id)
                if triplet["relationship"] in relationship_kinds:
                    triplets_in_kg.append(triplet)
                    add_to_kg = False
                    break
            else:
                add_to_kg = True
            
        if add_to_kg:
            triplets_not_in_kg["ids_a"].append(triplet["subject"])
            triplets_not_in_kg["relationship_kinds"].append(triplet["relationship"])
            triplets_not_in_kg["ids_b"].append(triplet["object"])
    return triplets_in_kg, triplets_not_in_kg


def prepare_triplets_to_add_to_kg(triplets_not_in_kg, prop_ex_rel_triplets, entities_in_kg_not_in_index, new_entities):
    # triplets_not_in_kg -- {'ids_a': ['User/b75d2700259bdcd44sdsdf85e7f530ed', 'User/b75d2700259bdcd44sdsdf85e7f530ed'], 'relationship_kinds': ['have_pet', 'like_goto'], 'ids_b': [None, None]}
    # prop_ex_rel_triplets -- [{'subject': 'user', 'relation': 'have_pet', 'object': 'dog'}, {'subject': 'user', 'relation': 'like_goto', 'object': 'park'}]
    # entities_in_kg -- [{'@id': 'animal/19f7c81c-04a5-492d-85cc-fcf955aec044', '@type': 'animal', 'substr': 'dog'}, {'@id': 'place/cca82750-2569-4c96-a1db-7e0cd7fb4d49', '@type': 'place', 'substr': 'park'}]
    # new_entities -- ['terminusdb:///data/animal/19f7c81c-04a5-492d-85cc-fcf955aec044', 'terminusdb:///data/place/cca82750-2569-4c96-a1db-7e0cd7fb4d49']
    # new_entities -- {"ids_list": [], "substr_list": [], "kinds_list": []}
    triplets_to_kg, triplets_to_index = triplets_not_in_kg, []
    user_id = triplets_not_in_kg["ids_a"][0]
    for idx, relationship_kind in enumerate(triplets_not_in_kg["relationship_kinds"]):
        id_b = [str(uuid4()) for triplet in prop_ex_rel_triplets if triplet["relation"]==relationship_kind][0] #TODO this 0 index could reduce solutions, fix that
        triplets_to_kg["ids_b"][idx] = id_b
    for entity in entities_in_kg_not_in_index:
        relationship_kind = [triplet["relation"] for triplet in prop_ex_rel_triplets if triplet["object"]==entity["substr"]][0] #TODO this 0 index could reduce solutions, fix that
        triplets_to_kg["ids_a"].append(user_id)
        triplets_to_kg["relationship_kinds"].append(relationship_kind)
        triplets_to_kg["ids_b"].append(entity["@id"])
    if new_entities:
        for idx, entity_substr in enumerate(new_entities["substr_list"]):
            relationship_kind = [triplet["relation"] for triplet in prop_ex_rel_triplets if triplet["object"]==entity_substr][0] #TODO this 0 index could reduce solutions, fix that
            triplets_to_kg["ids_a"].append(user_id)
            triplets_to_kg["relationship_kinds"].append(relationship_kind)
            triplets_to_kg["ids_b"].append(new_entities["ids_list"][idx])

    # triplets_to_kg -- {'ids_a': ['User/b75d2700259bdcd44sdsdf85e7f530ed', 'User/b75d2700259bdcd44sdsdf85e7f530ed'], 'relationship_kinds': ['have_pet', 'like_goto'], 'ids_b': [None, None]}
    # triplets_to_index -- {"substr_list": [], "kinds_list": [], "ids_list": []}
    return triplets_to_kg, triplets_to_index


def add_triplets_to_dbs(graph, user_id, triplets_to_kg, triplets_to_index):
    kinds_b = [id_b.split("/")[0] for id_b in triplets_to_kg["ids_b"]]
    graph.ontology.create_relationship_kinds(
        ["User"]*len(triplets_to_kg["ids_a"]),
        triplets_to_kg["relationship_kinds"],
        kinds_b
    )
    graph.create_relationships(
        triplets_to_kg["ids_a"],
        triplets_to_kg["relationship_kinds"],
        triplets_to_kg["ids_b"],
    )
    add_entities_to_index(graph, user_id, entities_info_lists=triplets_to_index)



def get_result(request, graph):
    uttrs = request.json.get("utterances", [])
    utt = uttrs[0]

    user_id = "/".join(["User", str(utt.get("user", {}).get("id", ""))])
    last_utt = utt["text"]
    logger.info(f"last_utt --  {last_utt}")
    annotations = utt.get("annotations", {})
    custom_el_annotations = annotations.get("custom_entity_linking", [])
    logger.info(f"custom_el_annotations --  {custom_el_annotations}")
    prop_ex_annotations = annotations.get("property_extraction", [])
    logger.info(f"prop_ex_annotations --  {prop_ex_annotations}")

    prop_ex_rel_triplets, prop_triplets = check_property_vs_relationship(prop_ex_annotations)
    # check and add properties
    logger.info(f"rel_triplets, prop_triplets --  {prop_ex_rel_triplets, prop_triplets}")

    entities_in_index, entities_not_in_index = check_entities_in_index(custom_el_annotations, prop_ex_rel_triplets)
    logger.info(f"entities_in_index, entities_not_in_index --  {entities_in_index, entities_not_in_index}")

    if entities_not_in_index:
        entities_in_kg, entities_not_in_kg_info = check_entities_in_kg(graph, entities_not_in_index)
        logger.info(f"entities_in_kg, entities_not_in_kg_info -- {entities_in_kg, entities_not_in_kg_info}")

        if entities_not_in_kg_info:
            new_entities = create_entities(graph, entities_not_in_kg_info)
            logger.info(f"new_entities -- {new_entities}")
        else:
            new_entities = {}
    else:
        entities_in_kg =[]
        new_entities = {}

    # if entities_in_index:
    triplets_of_entities_in_index = prepare_triplets(entities_in_index, prop_ex_rel_triplets, user_id)
    triplets_already_in_kg, triplets_not_in_kg = check_triplets_in_kg(graph, triplets_of_entities_in_index)
    logger.info(f"triplets_already_in_kg -- {triplets_already_in_kg}\ntriplets_not_in_kg -- {triplets_not_in_kg}")
    if triplets_not_in_kg:
        triplets_to_kg, triplets_to_index = prepare_triplets_to_add_to_kg(triplets_not_in_kg, prop_ex_rel_triplets, entities_in_kg, new_entities)
        logger.info(f"triplets_to_kg -- {triplets_to_kg}\n triplets_to_index -- {triplets_to_index}")
        triplets_added_to_kg = add_triplets_to_dbs(graph, user_id, triplets_to_kg, triplets_to_index)
    else:
        triplets_added_to_kg = []

    return [{'triplets_added_to_graph': triplets_added_to_kg, "triplets_already_in_graph": triplets_already_in_kg}]

@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request, graph)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
