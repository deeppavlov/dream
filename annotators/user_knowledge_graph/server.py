import logging
import uuid
import os

import inflect
from flask import Flask, jsonify, request
from pathlib import Path
from deeppavlov_kg import TerminusdbKnowledgeGraph

from common.utils import get_named_persons
from common.personal_info import my_name_is_pattern

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

inflect = inflect.engine()

USE_ABSTRACT_KINDS = True

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

# graph.ontology.drop_database(drop_index=True)

def add_name_property(graph, user_id, names):
    """Adds User Name property."""
    graph.ontology.create_property_kind_of_entity_kind(
        entity_kind="User",
        property_kind="Name",
        property_type=str
    )
    graph.create_or_update_property_of_entity(
        entity_id=user_id,
        property_kind="Name",
        new_property_value=names[0],
    )
    logger.info(
        f"Updated property 'Name' for user '{user_id}' to {names[0]}!"
    )


def add_relationships2kg(
        utt, graph, relationships_to_add2kg, user_id, entities_with_types, ex_triplets, all_entities
    ):
    """Creates an entity and a relation between it and the User from property extraction service."""
    text = utt.get("text", "")

    entity_kinds=[]
    new_entity_ids = []
    entity_info = {}
    entity_names = []
    all_entities_in_kg = {(entity["@type"], entity.get("Name")):entity["@id"] for entity in all_entities}
    for (entity_kind, entity_name, rel_name) in relationships_to_add2kg:
        if USE_ABSTRACT_KINDS and \
                rel_name.lower() in {"favorite_animal", "like_animal", "favorite_book", "like_read", "favorite_movie",
                                    "favorite_food", "like_food", "favorite_drink", "like_drink", "favorite_sport",
                                    "like_sports"} \
                and not any([f" {word} {entity_name}" in text for word in ["the", "my", "his", "her"]]):    
            entity_kind = f"Abstract{entity_kind.capitalize()}"
            inflect_entity_name = inflect.singular_noun(entity_name)
            if inflect_entity_name:
                entity_name = inflect_entity_name
            logger.info(f"correcting type and name, entity_kind: {entity_kind}, entity_name: {entity_name}")

        if (entity_name, entity_kind) in entities_with_types:
            new_entity_id = entities_with_types[(entity_name, entity_kind)]
            logger.info(f"Entity exists: '{new_entity_id}'")
        else:
            # Entity might be in KG, but still not in entities_with_types in case if the entity
            # isn't connected to this exact user. So, to avoid creating entities more than
            # once -once for each user-, here's a checking if this entity exists in KG at all.
            # If so, assign the entity id to `new_entity_id` to create a new relationship with this
            # existing entity -or not, if the same relationship, that's in utterance, exists in KG-
            if (entity_kind, entity_name) in all_entities_in_kg:
                new_entity_id = all_entities_in_kg[(entity_kind, entity_name)]
                logger.info(f"Entity exists: '{new_entity_id}'")
            else:
                new_entity_id = str(uuid.uuid4())
                new_entity_id = entity_kind + '/' + new_entity_id
                new_entity_ids.append(new_entity_id)
                entity_names.append(entity_name)
                entity_kinds.append(entity_kind)

        if (user_id, rel_name, new_entity_id) in ex_triplets:
            logger.info(f"triplet exists: {(rel_name, new_entity_id)}")
        else:
            if not entity_info:
                entity_info = {
                    "entity_kinds": [],
                    "rel_names": [],
                    "entity_ids": [],
                    "entity_names": [],
                }
            entity_info["entity_kinds"].append(entity_kind)
            entity_info["rel_names"].append(rel_name)
            entity_info["entity_ids"].append(new_entity_id)
            entity_info["entity_names"].append(entity_name)

    if entity_kinds:
        entity_kinds_to_create = list(set(entity_kinds))
        try:
            logger.debug(f"Creating entity kinds: {entity_kinds_to_create}")
            graph.ontology.create_entity_kinds(entity_kinds=entity_kinds_to_create, parents=None)
        except ValueError:
            logger.info(f"All kinds '{entity_kinds_to_create}' are already in DB")

        logger.debug("Adding `Name` property to entity kinds")
        graph.ontology.create_property_kinds_of_entity_kinds(
            entity_kinds=entity_kinds, property_kinds=[["Name"]]*len(entity_kinds), property_types=[[str]]*len(entity_kinds)
        )

        logger.debug(f"Creating entities: {new_entity_ids} with names: {entity_names}")
        graph.create_entities(entity_kinds, new_entity_ids, [["Name"]]*len(entity_kinds), [[name] for name in entity_names])

    if entity_info and entity_info["rel_names"]:
        logger.debug(
            f"Creating relationship kinds: {entity_info['rel_names']} --> "
            f"{entity_info['entity_ids']}"
        )
        graph.ontology.create_relationship_kinds(
            ["User"]*len(entity_info["rel_names"]),
            entity_info["rel_names"],
            entity_info["entity_kinds"],
        )

        logger.debug("Creating relationships")
        graph.create_relationships(
            [user_id]*len(entity_info["rel_names"]),
            entity_info["rel_names"],
            entity_info["entity_ids"]
        )

        # add to index
        substr_list = entity_info["entity_names"]
        ids_list = entity_info["entity_ids"]
        tags_list = entity_info["entity_kinds"]

        logger.debug(f"Adding to index user_id '{user_id}' - entity_info: "
                     f"'entity_substr': {substr_list}, 'entity_ids': {ids_list},"
                     f" 'tags': {tags_list}")
        graph.index.set_active_user_id(str(user_id.split("/")[-1]))
        graph.index.add_entities(substr_list, ids_list, tags_list)
    return entity_info


def add_properties2kg(graph, user_id, properties_to_add2kg):
    """Adds properties of user in the KG"""
    property_types, property_values = [], []
    for type, value in properties_to_add2kg:
        if type == "<blank>":
            type = "other"
        type = '_'.join(type.split(' '))
        property_types.append(type)
        property_values.append(value)

    graph.ontology.create_property_kinds_of_entity_kind("User", property_types)
    graph.create_or_update_properties_of_entity(
        entity_id=user_id,
        property_kinds=property_types,
        new_property_values=property_values,
    )
    logger.info(f"Added the following (property, value) pairs: {properties_to_add2kg}")


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


def add_relations_or_properties(utt, user_id, entities_with_types, ex_triplets, all_entities):
    """Chooses what to add: property, relationship or nothing."""
    no_rel_message = "No relations were found!"
    attributes = utt.get("annotations", {}).get("property_extraction", {})
    logger.info(f'Attributes: {attributes}')

    if isinstance(attributes, dict):
        attributes = [attributes]
    relationships_to_add2kg = []
    properties_to_add2kg = []
    triplets = {}
    for attribute in attributes:
        if attribute and attribute['triplets']:
            triplets = attribute['triplets']
            for triplet in triplets:
                entity_name = triplet['object'].lower()
                if triplet['subject'] != 'user':
                    logger.info(no_rel_message)
                if 'relation' in triplet:
                    entity_kind = get_entity_type(attribute)
                    relation = '_'.join(triplet['relation'].split(' '))
                    if relation in rel_kinds_dict:
                        entity_kind = rel_kinds_dict[relation]
                    relationships_to_add2kg.append((entity_kind, entity_name, relation.upper()))
                else:
                    properties_to_add2kg.append((triplet['property'], entity_name))
                                        
    if properties_to_add2kg:
        add_properties2kg(graph, user_id, properties_to_add2kg)

    triplet_info = {}
    if relationships_to_add2kg:
        triplet_info = add_relationships2kg(
            utt,
            graph,
            relationships_to_add2kg,
            user_id,
            entities_with_types,
            ex_triplets,
            all_entities,
        )
    else:
        logger.info(no_rel_message)

    return triplet_info


def check_name_scenario(utt, user_id):
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

    logger.info(f"Text: {uttrs[0]['text']}")
    logger.info(f"Property Extraction: {annotations.get('property_extraction', [])}")

    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if not last_utt:
        return "Empty utterance"

    user_id = str(utt.get("user", {}).get("id", ""))
    user_id = "User/" + user_id
    all_entities = graph.get_all_entities()
    existing_ids = [entity["@id"] for entity in all_entities]

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
        try:
            graph.ontology.create_entity_kind("User")
        except ValueError:
            logger.info("Kind User is already in DB")
        graph.create_entity("User", user_id, [], [])
        logger.info(f"Created User with id: {user_id}")

    entity_detection = utt.get("annotations", {}).get("entity_detection", {})
    entities = entity_detection.get("labelled_entities", [])
    entities = [entity.get("text", "no entity name") for entity in entities]
    added = []
    name_result = {}
    if entities:
        name_result = check_name_scenario(utt, user_id)
    property_result = add_relations_or_properties(
        utt, user_id, entities_with_types, ex_triplets, all_entities
    )
    if name_result:
        added.append(name_result)
    if property_result:
        added.append(property_result)

    substr_list, ids_list, tags_list = [], [], []
    if name_result:
        substr_list.append(name_result["object"])
        ids_list.append(user_id)
        tags_list.append("Name")
    if substr_list:
        user_id = utt.get("user", {}).get("id", "")
        logger.debug(f"Adding to index user_id '{user_id}' - entity_info: "
                     f"'entity_substr': {substr_list}, 'entity_ids': {ids_list},"
                     f" 'tags': {tags_list}")
        graph.index.set_active_user_id(str(user_id))
        graph.index.add_entities(substr_list, ids_list, tags_list)
    logger.info(f"added_to_graph -- {added}, triplets_already_in_graph -- {kg_parser_annotations}")
    return [{'added_to_graph': added, "triplets_already_in_graph": kg_parser_annotations}]


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
