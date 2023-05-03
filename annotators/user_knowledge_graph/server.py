import json
import logging
import uuid
import os
import openai
import re

import inflect
import requests
from flask import Flask, jsonify, request
from pathlib import Path
from deeppavlov_kg import TerminusdbKnowledgeGraph

from common.utils import get_named_persons
from common.personal_info import my_name_is_pattern

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

inflect = inflect.engine()

CUSTOM_EL_ADD = os.getenv("CUSTOM_EL_ADD")
logger.info(f"URL of custom EL: {CUSTOM_EL_ADD}")
USE_ABSTRACT_KINDS = True
INDEX_LOAD_PATH=Path(os.path.expanduser(os.getenv("INDEX_LOAD_PATH")))
OPENAI_API_KEY=os.getenv("INDEX_LOAD_PATH")

# read all relations & properties to add them into ontology
rel_type_dict = {}
with open("rel_list.txt", "r") as fl:
    lines = fl.readlines()
    for line in lines:
        rel, rel_type = line.strip().split()
        if rel_type == "r":
            rel_type = "relation"
        else:
            rel_type = "property"
        rel_type_dict[rel.replace("_", " ")] = rel_type

rel_kinds_dict = {
    "favorite_animal": "animal",
    "have_pet": "animal",
    "like_animal": "animal",
    "favorite_book": "book",
    "like_read": "book",
    "favorite_movie": "film",
    "favorite_food": "food",
    "like_food": "food",
    "favorite_drink": "food",
    "like_drink": "food",
    "favorite_sport": "type_of_sport",
    "like_sports": "type_of_sport"
}

DB = "test_italy_skill1"
TEAM = "yashkens|c77b"
openai.api_key = OPENAI_API_KEY

graph = TerminusdbKnowledgeGraph(
    team=TEAM,
    db_name=DB,
    server="https://7063.deeppavlov.ai/",
    password="G5KMuz9dF1K2mD5cPz726oazSJJtkFLw",
    index_load_path=INDEX_LOAD_PATH
)

logger.info('Graph Loaded!')

# graph.ontology.drop_database(drop_index=True)

def add_name_property(graph, user_id, names):
    """Adds User Name property."""
    graph.create_or_update_property_of_entity(
        id_=user_id,
        property_kind="Name",
        property_value=names[0],
    )
    logger.info(f"I already have you in the graph! Updating your property name to {names[0]}!")


def add_any_relationship(utt, graph, entity_kind, entity_name, rel_type, user_id, entities_with_types, ex_triplets,
                         existing_ids):
    """Creates an entity and a relation between it and the User from property extraction service."""
    entity_kind = entity_kind.replace('_', '').title()
    graph.ontology.create_property_kind_of_entity_kind(entity_kind, "Name")

    logger.info(f"add_any_relationship, rel_type: {rel_type} --- entity_name: {entity_name} --- "
                f"inflected: {inflect.singular_noun(entity_name)}")
    text = utt.get("text", "")

    if USE_ABSTRACT_KINDS and \
            rel_type.lower() in {"favorite_animal", "like_animal", "favorite_book", "like_read", "favorite_movie",
                                 "favorite_food", "like_food", "favorite_drink", "like_drink", "favorite_sport",
                                 "like_sports"} \
            and not any([f" {word} {entity_name}" in text for word in ["the", "my", "his", "her"]]):    
        entity_kind = f"Abstract{entity_kind.capitalize()}"
        inflect_entity_name = inflect.singular_noun(entity_name)
        if inflect_entity_name:
            entity_name = inflect_entity_name
        logger.info(f"correcting type and name, entity_kind: {entity_kind}, entity_name: {entity_name}")

    try:
        logger.debug(f"Creating entity kind: {entity_kind}")
        graph.ontology.create_entity_kind(entity_kind=entity_kind, parent=None)
        logger.info(f"Created entity kind: {entity_kind}")
    except ValueError:
        logger.info(f"Kind '{entity_kind}' is already in DB")

    entity_kind_properties = graph.ontology.get_entity_kind(entity_kind)
    if "Name" not in entity_kind_properties:
        logger.debug(f"Creating property kind 'Name' for kind '{entity_kind}'")
        graph.ontology.create_property_kind_of_entity_kind(
            entity_kind=entity_kind, property_kind="Name", property_type=str
        )
        logger.info(f"Created property kind 'Name' for kind '{entity_kind}'")
    else:
        logger.info(f"Kind '{entity_kind}' already has Name as a property") # try run it and observe debuging messages
    if (entity_name, entity_kind) in entities_with_types:
        new_entity_id = entities_with_types[(entity_name, entity_kind)]
        logger.info(f"Entity exists: '{new_entity_id}'")
    else:
        new_entity_id = str(uuid.uuid4())
        new_entity_id = entity_kind + '/' + new_entity_id
        logger.debug(f"Adding entity with kind: {entity_kind} -- new_entity_id:'{new_entity_id}'")
        graph.create_entity(entity_kind, new_entity_id, ["Name"], [entity_name])
        logger.info(f"Added entity '{new_entity_id}' with Kind '{entity_kind}' and property Name '{entity_name}'!")

    logger.info(f"define rel_name, entity_kind {entity_kind} --- entity_kind {entity_kind}")
    rel_name = rel_type

    if (user_id, rel_name, new_entity_id) in ex_triplets:
        logger.info(f"triplet exists: {(rel_name, new_entity_id)}")
    else:
        logger.info(f"connecting {entity_name} with User by rel_type: {rel_type}, rel_name: {rel_name} relationship, "
                    f"entity_kind {entity_kind} new_entity_id {new_entity_id}")
        graph.ontology.create_relationship_kind("User", rel_name, entity_kind)
        graph.create_relationship(user_id, rel_name, new_entity_id)
        logger.info(f"{entity_name} is connected with User by {rel_type} relationship.")


def add_any_property(graph, user_id, property_type, property_value):
    """Adds a property from property extraction service."""
    if property_type == "<blank>":
        property_type = "other"
    property_type = '_'.join(property_type.split(' '))
    graph.ontology.create_property_kind_of_entity_kind("User", property_type)
    graph.create_or_update_property_of_entity(
        entity_id=user_id,
        property_kind=property_type,
        new_property_value=property_value,
    )
    logger.info(f"I added a property {property_type} with value {property_value}!")


def get_entity_type(attributes):
    """Extracts DBPedia type from property extraction annotator."""
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


def add_relations_or_properties(utt, user_id, entities_with_types, ex_triplets, existing_ids):
    """Chooses what to add: property, relationship or nothing."""
    no_rel_message = "No relations were found!"
    attributes = utt.get("annotations", {}).get("property_extraction", {})
    logger.info(f'Attributes: {attributes}')

    if isinstance(attributes, dict):
        attributes = [attributes]
    for attribute in attributes:
        if attribute and attribute['triplet']:
            triplet = attribute['triplet']
            if triplet['subject'] != 'user':
                logger.info(no_rel_message)
                return {}
            if 'relation' in triplet:
                entity_kind = get_entity_type(attribute)
                entity_name = triplet['object']
                relation = '_'.join(triplet['relation'].split(' '))
                if relation in rel_kinds_dict:
                    entity_kind = rel_kinds_dict[relation]
                add_any_relationship(utt, graph, entity_kind, entity_name, relation.upper(), user_id,
                                     entities_with_types, ex_triplets, existing_ids)
                return triplet
            else:
                add_any_property(graph, user_id, triplet['property'], triplet['object'])
                return triplet
    logger.info(no_rel_message)
    return {}


def name_scenario(utt, user_id):
    """Checks if there is a Name given and adds it as a property."""
    names = get_named_persons(utt)
    if not names:
        logger.info('No names were found.')
        return {}
    logger.info(f'I found a name: {names[0]}')
    existing_ids = [entity["@id"] for entity in graph.get_all_entities() if entity["@type"]=="User"]
    if user_id not in existing_ids:
        # let's hope user is telling us their name if they're new here
        # actually that's an unreal situation -- delete this part
        add_name_property(graph, user_id, names)
        result = {'subject': 'user', 'property': 'Name', 'object': names[0]}
    elif my_name_is_pattern.search(utt.get("text", "")):
        # if they're not new, search for pattern
        logger.info('I am in my name is patter if')
        add_name_property(graph, user_id, names)
        result = {'subject': 'user', 'property': 'Name', 'object': names[0]}
    else:
        logger.info("You are telling me someone's name, but I guess it's not yours!")
        result = {}
    return result


def get_result(request):
    """Collects all relation & property information from one utterance and adds to graph."""
    uttrs = request.json.get("utterances", [])
    utt = uttrs[0]
    annotations = uttrs[0].get("annotations", {})
    custom_el_annotations = annotations.get("custom_entity_linking", [])
    entities_with_types = {}
    found_kg_ids = []
    for entity_info in custom_el_annotations:
        if entity_info.get("entity_id_tags", []):
            entities_with_types[(entity_info["entity_substr"], entity_info["entity_id_tags"][0])] = \
                entity_info["entity_ids"][0]
            found_kg_ids.append(entity_info["entity_ids"][0])
    logger.info(f"Entities_with_types: {entities_with_types}")
    logger.info(f"Text: {uttrs[0]['text']}")

    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if not last_utt:
        return "Empty utterance"

    user_id = str(utt.get("user", {}).get("id", ""))
    user_id = "User/" + user_id
    all_entities = graph.get_all_entities()
    existing_ids = [entity["@id"] for entity in all_entities]
    logger.info(f"Existing ids: {existing_ids}")

    triplets = []
    for entity, entity_id in entities_with_types.items():
        rels = graph.search_for_relationships(id_a=user_id, id_b=entity_id)
        for rel in rels:
            triplets.append(["User", entity[0], rel['rel'].split('_')[0].lower()]) #TODO: you can do better than this naive split
        logger.info(f"rels from custom_el in KG --||-- {rels}")

    logger.info(f"Found triplets in KG -- {triplets}")
    if triplets:
        prompt = ("Generate facts about user out of the following triplets. Don't remove objects!"
                  "Separate the generated facts with '-'.")

        # convert the triplets into a prompt
        for triplet in triplets:
            prompt = "\n".join([
                prompt,
                ", ".join(triplet)
            ])

        # define the parameters for the GPT-3 model
        model_engine = "text-davinci-002"
        max_tokens = 1024

        # generate text from the prompt using the GPT-3 API
        response = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.5,
        )

        # extract the generated text from the API response
        generated_triplets = response.choices[0].text

        # remove any extraneous whitespace from the generated text
        generated_triplets = re.sub(r"\s+", " ", generated_triplets).strip()


    else:
        generated_triplets = ""
    logger.info(f"Generated_triplets by gpt-3 -- {generated_triplets}")

    kg_parser_annotations = []
    ex_triplets = []
    if user_id in existing_ids:
        entity_rel_info = graph.search_for_relationships(id_a=user_id)
        for dic in entity_rel_info:
            rel = dic["rel"]
            obj = dic["id_b"]
            ex_triplets.append((user_id, rel, obj))
            if obj in found_kg_ids:
                kg_parser_annotations.append([user_id, rel, obj])
        logger.info(f"User with id {user_id} already exists!")
    else:
        if len(graph.ontology.get_entity_kind("User")) == 1:
            graph.ontology.create_entity_kind("User")
        graph.create_entity("User", user_id, [], [])
        logger.info(f"Created User with id: {user_id}")

    entity_detection = utt.get("annotations", {}).get("entity_detection", {})
    entities = entity_detection.get("labelled_entities", [])
    entities = [entity.get("text", "no entity name") for entity in entities]
    added = []
    name_result = {}
    if entities:
        name_result = name_scenario(utt, user_id)
    property_result = add_relations_or_properties(utt, user_id, entities_with_types, ex_triplets, existing_ids)
    if name_result:
        added.append(name_result)
    if property_result:
        added.append(property_result)

    all_entities_new = graph.get_all_entities()
    all_entities_new = [entity for entity in all_entities_new
                        if (entity["@id"] not in existing_ids and not entity["@id"].startswith("User/"))]

    substr_list, ids_list, tags_list = [], [], []
    for entity in all_entities_new:
        if "Name" in entity:
            substr_list.append(entity["Name"])
            ids_list.append(entity["@id"])
            tags_list.append(entity["@type"])
    if name_result:
        substr_list.append(name_result["object"])
        ids_list.append(user_id)
        tags_list.append("Name")
    if substr_list:
        user_id = utt.get("user", {}).get("id", "")
        logger.debug(f"""Adding to index user_id '{user_id}' "entity_info": "entity_substr": {substr_list},
                                                           "entity_ids": {ids_list}, "tags": {tags_list}""")
        graph.index.set_active_user_id(str(user_id))
        graph.index.add_entities(substr_list, ids_list, tags_list)
    logger.info(f"kg_parser_annotations: {kg_parser_annotations}")

    return [{'added_to_graph': added, "triplets": kg_parser_annotations, "NL_triplets": generated_triplets}]


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8127)
