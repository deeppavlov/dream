# pylint: disable=W1203

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from uuid import uuid4
from flask import Flask, jsonify, request
from deeppavlov_kg import TerminusdbKnowledgeGraph


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)

with open("rel_list.json") as file:
    rel_kinds_dict = json.load(file)

with open("abstract_rels.txt", "r") as file:
    abstract_rels = [line.strip() for line in file.readlines()]

TERMINUSDB_SERVER_URL = os.getenv("TERMINUSDB_SERVER_URL")
TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")
assert TERMINUSDB_SERVER_PASSWORD, "TerminusDB server password is not specified"
TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM")
INDEX_LOAD_PATH = Path(os.path.expanduser(os.getenv("INDEX_LOAD_PATH")))

kg_graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
    index_load_path=INDEX_LOAD_PATH,
)
logger.info("Graph Loaded!")


def check_property_vs_relationship(utterances_info: List[dict]) -> Tuple[list, list]:
    """Checks if the prop_ex triplets are relationship or property triplets.

    Args:
      utterances_info: List of dictionaries containing the utterance information.

    Returns:
      A tuple containing two lists: relationships and properties.
    """
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


def get_entity_type(attributes):
    # TODO: this doesn't work. Most likely it should get output of entity-detection not prop-ex
    """Extracts DBPedia type from property extraction annotator."""
    if not isinstance(attributes, dict):
        return "Misc"
    entity_info = attributes.get("entity_info", [])
    if not entity_info:
        return "Misc"
    exact_entity_info = entity_info[list(entity_info.keys())[0]]
    finegrained = exact_entity_info.get("finegrained_types", [])
    if finegrained:
        entity_type = finegrained[0].capitalize()
        logger.info(f"Fine-grained type: {entity_type}")
        return entity_type
    return "Misc"


def is_abstract_relationship(relationship_kind, entity_substr, text):
    """Returns true if the relationship kind is abstract according to 'abstract_rels.txt' file and if there's no
    article before the entity substring in the text, that would indicate non-abstraction. Otherwise, returns false.
    """
    if relationship_kind.lower() in abstract_rels and not any(
        [f" {word} {entity_substr}" in text for word in ["the", "my", "his", "her"]]
    ):
        return True
    else:
        return False


def check_entities_in_index(custom_el_annotations: list, prop_ex_triplets: list, text: str) -> Tuple[dict, list]:
    """Checks if the entities returned by property extraction are present in the index.

    Returns:
      A tuple containing a dictionary and a list: entities_in_index and entities_not_in_index.
    Output example:
      entities_in_index, entities_not_in_index --  {('dog', 'Animal'):
        'Animal/ed8f16ae-56fb-46dc-b542-20987056fd00'}, [('dog', 'Animal'))]
    """
    def check_abstraction_in_index(relationship, entity_info, text):
        """Returns true if kind in index is 'Abstract' and the relationship in prop_ex is abstract, or if both aren't
        abstract. Otherwise, returns false."""
        return is_abstract_relationship(
            relationship, entity_info["entity_substr"], text) == ("Abstract" in entity_info["entity_id_tags"]
        )

    entities_in_index, entities_not_in_index = {}, []
    for triplet in prop_ex_triplets:
        in_index = False
        for entity_info in custom_el_annotations:
            if triplet["object"] == entity_info["entity_substr"] and check_abstraction_in_index(
                triplet["relation"], entity_info, text
            ):
                in_index = True
                entities_in_index[(entity_info["entity_substr"], entity_info["entity_id_tags"][0])] = entity_info[
                    "entity_ids"
                ][0]
                break
        if not in_index:
            if triplet["relation"] in rel_kinds_dict:
                entity_kind = rel_kinds_dict[triplet["relation"]]
            else:
                entity_kind = get_entity_type(triplet["object"])
            entities_not_in_index.append((triplet["object"], entity_kind))
    return entities_in_index, entities_not_in_index


def check_entities_in_kg(graph, entities: list) -> Tuple[list, list]:
    """Checks if the entities, that aren't in index, are present in kg.

    As index stores and retrieves entities only related to each user (it stores them as triplets), there are
    situations where the entity exists in kg but not connected to this current user, so not found in index.

    Returns:
      A tuple containing two lists: entities_in_kg and entities_not_in_kg.
    Output example:
      entities_in_kg -- [{'@id': 'Animal/L83', '@type': 'Animal', 'substr': 'dog'}]
      entities_not_in_kg -- [('park', 'Place')]
    """
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


def create_entities(
    graph, entities_info: List[Tuple[str, str]], has_name_property=False, entity_ids: Optional[List[str]] = None
) -> Dict[str, list]:
    """Adds entities and entity kinds into kg.
    Returns:
      entities_info_lists: new created entities
    Output example:
      {
        'substr_list': ['dog', 'park'],
        'tags_list': ['Animal', 'Place'],
        'entity_ids': ['Animal/6e224463-e9a9-4e43-b548-a3c52f30de66', 'Place/aa3f15fb-b00d-4f92-be95-75b3748d6f5f']
      }
    """
    if entity_ids is None:
        entity_ids = [""] * len(entities_info)

    entities_info_lists = {"substr_list": [], "tags_list": [], "entity_ids": []}
    for entity_info, entity_id in zip(entities_info, entity_ids):
        entities_info_lists["substr_list"].append(entity_info[0])
        entities_info_lists["tags_list"].append(entity_info[1])
        if not entity_id:
            entity_id = "/".join([entity_info[1], str(uuid4())])
        entities_info_lists["entity_ids"].append(entity_id)
    logger.debug(f"entities_info_lists -- {entities_info_lists}")

    try:
        graph.ontology.create_entity_kinds(entities_info_lists["tags_list"])
    except ValueError:
        logger.info(f"All entity kinds '{entities_info_lists['tags_list']}' are already in KG")

    substr = "name" if has_name_property else "substr"
    property_kinds = [[substr]] * len(entities_info_lists["substr_list"])
    property_values = [[substr] for substr in entities_info_lists["substr_list"]]
    graph.ontology.create_property_kinds_of_entity_kinds(entities_info_lists["tags_list"], property_kinds)

    try:
        graph.create_entities(
            entities_info_lists["tags_list"],
            entities_info_lists["entity_ids"],
            property_kinds=property_kinds,
            property_values=property_values,
        )
    except Exception:
        logger.info(f"Entities {entities_info_lists['entity_ids']} already exist in kg.")
    return entities_info_lists


def prepare_triplets(entities_in_index: dict, triplets: list, user_id: str) -> List[dict]:
    """Prepares the property extraction triplets to be in the format
    '[{"subject": user_id, "relationship": value, "object": entity_id}]' to be used in check_triplets_in_kg.
    Where value is got from triplets and entity_id is got from entities_in_index.
    """
    prepared_triplets = []
    new_entities_in_index = {}
    for (entity_substr, _), entity_id in entities_in_index.items():
        new_entities_in_index[entity_substr] = entity_id
    for triplet in triplets:
        prepared_triplets.append(
            {
                "subject": user_id,
                "relationship": triplet["relation"],
                "object": new_entities_in_index.get(triplet["object"]),
            }
        )
    return prepared_triplets


def check_triplets_in_kg(graph, triplets: List[dict]) -> Tuple[list, dict]:
    """Checks if the subject and object, that've been extracted by property extraction and present in index,
    are connected by the same relationship as in kg.
    """
    triplets_in_kg, triplets_not_in_kg = [], {"ids_a": [], "relationship_kinds": [], "ids_b": []}
    for triplet in triplets:
        entity_id = triplet["object"]
        relationship_kinds = graph.search_for_relationships(id_a=triplet["subject"], id_b=entity_id)
        if triplet["relationship"] in [rel["rel"] for rel in relationship_kinds]:
            triplets_in_kg.append([triplet["subject"], triplet["relationship"], triplet["object"]])
            add_to_kg = False
        else:
            add_to_kg = True

        if add_to_kg:
            triplets_not_in_kg["ids_a"].append(triplet["subject"])
            triplets_not_in_kg["relationship_kinds"].append(triplet["relationship"])
            triplets_not_in_kg["ids_b"].append(triplet["object"])
    return triplets_in_kg, triplets_not_in_kg


def prepare_triplets_to_add_to_dbs(
    triplets_not_in_kg: Dict[str, list],
    prop_ex_rel_triplets: list,
    entities_in_kg_not_in_index: list,
    new_entities: dict,
    abstract_triplets: List[tuple],
    user_id: str,
):
    """Prepares each of these triplets to be added to dbs:
    [triplets not in kg but in index,
    triplets between user and entities, that're in kg but not in index,
    triplets between user and new created entities,
    new triplets, that have abstract relationships]

    Output example:
      triplets_to_kg -- {
        'ids_a': ['User/b75d2700259bdc44sdsdf85e7f530ed'],
        'relationship_kinds': ['HAVE_PET'],
        'ids_b': ['Animal/6e224463-e9a9-4e43-b548-a3c52f30de66']
      }
      triplets_to_index -- {
        'substr_list': ['dog'], 'tags_list': ['Animal'], 'entity_ids': ['Animal/6e224463-e9a9-4e43-b548-a3c52f30de66']
      }
    """
    triplets_to_kg, triplets_to_index = triplets_not_in_kg, {"substr_list": [], "tags_list": [], "entity_ids": []}

    for entity in entities_in_kg_not_in_index:
        relationship_kind = [
            triplet["relation"] for triplet in prop_ex_rel_triplets if triplet["object"] == entity["substr"]
        ][
            0
        ]  # TODO this 0 index could reduce solutions, fix that
        triplets_to_kg["ids_a"].append(user_id)
        triplets_to_kg["relationship_kinds"].append(relationship_kind)
        triplets_to_kg["ids_b"].append(entity["@id"])

        triplets_to_index["substr_list"].append(entity["substr"])
        triplets_to_index["tags_list"].append(entity["@type"])
        triplets_to_index["entity_ids"].append(entity["@id"])
    if new_entities:
        for idx, entity_substr in enumerate(new_entities["substr_list"]):
            relationship_kind = [
                triplet["relation"] for triplet in prop_ex_rel_triplets if triplet["object"] == entity_substr
            ][
                0
            ]  # TODO this 0 index could reduce solutions, fix that
            triplets_to_kg["ids_a"].append(user_id)
            triplets_to_kg["relationship_kinds"].append(relationship_kind)
            triplets_to_kg["ids_b"].append(new_entities["entity_ids"][idx])

        triplets_to_index["substr_list"] += new_entities["substr_list"]
        triplets_to_index["tags_list"] += new_entities["tags_list"]
        triplets_to_index["entity_ids"] += new_entities["entity_ids"]

    for id_a, rel, id_b in abstract_triplets:
        triplets_to_kg["ids_a"].append(id_a)
        triplets_to_kg["relationship_kinds"].append(rel)
        triplets_to_kg["ids_b"].append(id_b)

        triplets_to_index["substr_list"].append(id_b.split("/")[-1])
        triplets_to_index["tags_list"].append("Abstract")
        triplets_to_index["entity_ids"].append(id_b)

    return triplets_to_kg, triplets_to_index


def add_entities_to_index(graph, user_id: str, entities_info_lists: dict):
    user_id = user_id.split("/")[-1]
    substr_list = entities_info_lists["substr_list"]
    entity_ids = entities_info_lists["entity_ids"]
    tags_list = entities_info_lists["tags_list"]
    logger.debug(
        f"Adding to index user_id '{user_id}' - entity_info: "
        f"'entity_substr': {substr_list}, 'entity_ids': {entity_ids},"
        f" 'tags': {tags_list}"
    )
    graph.index.set_active_user_id(user_id)
    graph.index.add_entities(substr_list, entity_ids, tags_list)


def add_triplets_to_dbs(graph, user_id: str, triplets_to_kg: dict, triplets_to_index: dict) -> List[tuple]:
    """Adds triplets to each of kg and index."""
    kinds_b = [id_b.split("/")[0] for id_b in triplets_to_kg["ids_b"]]

    if len(triplets_to_kg["ids_a"]):
        graph.ontology.create_relationship_kinds(
            ["User"] * len(triplets_to_kg["ids_a"]), triplets_to_kg["relationship_kinds"], kinds_b
        )
        logger.debug(
            f"""to be added to kg\n
            ids_a -- {triplets_to_kg["ids_a"]}\n
            relationship_kinds -- {triplets_to_kg["relationship_kinds"]}\n
            ids_b -- {triplets_to_kg["ids_b"]}\n
        """
        )

        graph.create_relationships(
            triplets_to_kg["ids_a"],
            triplets_to_kg["relationship_kinds"],
            triplets_to_kg["ids_b"],
        )
    if triplets_to_index["substr_list"]:
        add_entities_to_index(graph, user_id, entities_info_lists=triplets_to_index)

    output = zip(
        [user_id] * len(triplets_to_index["entity_ids"]),
        triplets_to_kg["relationship_kinds"],
        triplets_to_index["entity_ids"],
    )
    return list(output)


def upper_case_input(triplets: List[dict]) -> List[dict]:
    """Upper-cases the relationship kind in each triplet in the prop_ex annotations"""
    return [
        {
            "subject": triplet["subject"], "relation": triplet["relation"].upper(), "object": triplet["object"]
        } for triplet in triplets
    ]


def check_abstract_triplets(
    graph,entities: List[tuple], prop_ex_rel_triplets: List[dict], text: str, user_id: str
) -> Tuple[list, list]:
    abstract_triplets = []
    non_abstract_triplets = []
    kinds_to_add = []
    parents = []
    for entity in entities:
        entity_substr = entity[0]
        entity_kind = entity[1]
        relationship_kind = [
            triplet["relation"] for triplet in prop_ex_rel_triplets if triplet["object"] == entity_substr
        ][0]
        if is_abstract_relationship(relationship_kind, entity_substr, text):
            substr2kind = entity_substr.capitalize()
            kinds_to_add.append(substr2kind)
            parents.append(entity_kind)
            abstract_entity_id = "/".join(["Abstract", substr2kind])
            abstract_triplets.append((user_id, relationship_kind, abstract_entity_id))
        else:
            non_abstract_triplets.append(entity)

    logger.debug(f"abstract_kinds_to_add -- {kinds_to_add}")

    if kinds_to_add:
        try:
            graph.ontology.create_entity_kinds(kinds_to_add, parents)
        except ValueError:
            logger.info(f"All entity kinds '{kinds_to_add}' are already in KG")
        except Exception: #TODO: replace with Terminusdb DatabaseError
            graph.ontology.create_entity_kinds(parents)
            try:
                graph.ontology.create_entity_kinds(kinds_to_add, parents)
            except ValueError:
                logger.info(f"All entity kinds '{kinds_to_add}' are already in KG")
    return abstract_triplets, non_abstract_triplets


def check_and_add_properties(graph, prop_triplets: List[dict], user_id: str) -> Tuple[list, list]:
    """Checks if the property triplets exist in kg and adds them if not.
    """
    properties_to_add_to_kg, properties_already_in_kg = [], []
    try:
        user_properties = graph.get_properties_of_entity(user_id)
    except:
        user_properties = [] # new user
    for triplet in prop_triplets:
        if triplet["property"] in user_properties and triplet["object"] == user_properties[triplet["property"]]:
            properties_already_in_kg.append(triplet)
        else:
            if triplet["property"] == "misc attribute":
                triplet.update({"property_family": set})
            else:
                triplet.update({"property_family": Optional})
            properties_to_add_to_kg.append(triplet)

    if properties_to_add_to_kg:
        property_kinds = [triplet["property"] for triplet in properties_to_add_to_kg]
        properties_families = [triplet["property_family"] for triplet in properties_to_add_to_kg]
        objects = [triplet["object"] for triplet in properties_to_add_to_kg]
        logger.info(f"property_kinds -- {property_kinds}\nproperties_families -- {properties_families}\nproperties_to_add_to_kg -- {properties_to_add_to_kg}")
        graph.ontology.create_property_kinds_of_entity_kind(
            "User",
            property_kinds,
            properties_type_families=properties_families,
        )
        graph.create_or_update_properties_of_entity(user_id, property_kinds, objects)
        for prop in properties_to_add_to_kg:
            del prop["property_family"]
    return properties_to_add_to_kg, properties_already_in_kg


def get_result(request, graph):
    uttrs = request.json.get("utterances", [])
    utt = uttrs[0]

    user_id = "/".join(["User", str(utt.get("user", {}).get("id", ""))])
    user_external_id = str(utt.get("user", {}).get("user_external_id", ""))
    last_utt = utt["text"]
    logger.info(f"last_utt --  {last_utt}")
    annotations = utt.get("annotations", {})
    custom_el_annotations = annotations.get("custom_entity_linking", [])
    logger.info(f"custom_el_annotations --  {custom_el_annotations}")
    prop_ex_annotations = annotations.get("property_extraction", [])
    logger.debug(f"prop_ex_annotations before upper-casing --  {prop_ex_annotations}")
    for annotation in prop_ex_annotations:
        for triplet in annotation["triplets"]:
            if triplet["object"] == "<blank>":
                logging.error("ValueError: the property extraction output has '<blank>' object")
                return [{"added_to_graph": [], "triplets_already_in_graph": []}]

    create_entities(graph, [(user_external_id, "User")], has_name_property=True, entity_ids=[user_id])

    prop_ex_rel_triplets, prop_triplets = check_property_vs_relationship(prop_ex_annotations)
    prop_ex_rel_triplets = upper_case_input(prop_ex_rel_triplets)
    logger.info(f"rel_triplets, prop_triplets --  {prop_ex_rel_triplets, prop_triplets}")

    if prop_triplets:
        properties_added_to_kg, properties_already_in_kg = check_and_add_properties(graph, prop_triplets, user_id)
    else:
        properties_added_to_kg, properties_already_in_kg = [], []

    entities_in_index, entities_not_in_index = check_entities_in_index(custom_el_annotations, prop_ex_rel_triplets, last_utt)
    logger.info(f"entities_in_index, entities_not_in_index --  {entities_in_index, entities_not_in_index}")

    if entities_not_in_index:
        abstract_triplets, non_abstract_triplets =  check_abstract_triplets(graph, entities_not_in_index, prop_ex_rel_triplets, last_utt, user_id)
        logger.info(f"abstract_triplets -- {abstract_triplets}")
        logger.info(f"non_abstract_triplets -- {non_abstract_triplets}")

        entities_in_kg_not_in_index, entities_not_in_kg = check_entities_in_kg(graph, non_abstract_triplets)
        logger.debug(f"entities_not_in_kg -- {entities_not_in_kg}")

        if entities_not_in_kg:
            new_entities = create_entities(graph, entities_not_in_kg)
        else:
            new_entities = {}
    else:
        abstract_triplets = []
        entities_in_kg_not_in_index = []
        new_entities = {}
    logger.info(f"new_entities -- {new_entities}")
    logger.info(f"entities_in_kg_not_in_index -- {entities_in_kg_not_in_index}")

    if entities_in_index:
        triplets_of_entities_in_index = prepare_triplets(entities_in_index, prop_ex_rel_triplets, user_id)
        logger.info(f"triplets_of_entities_in_index -- {triplets_of_entities_in_index}")
        triplets_already_in_kg, triplets_not_in_kg = check_triplets_in_kg(graph, triplets_of_entities_in_index)
    else:
        triplets_already_in_kg = []
        triplets_not_in_kg = {
            "ids_a": [],
            "relationship_kinds": [],
            "ids_b": [],
        }
    logger.info(f"triplets_already_in_kg -- {triplets_already_in_kg}\ntriplets_not_in_kg -- {triplets_not_in_kg}")

    if triplets_not_in_kg["ids_b"] or new_entities or entities_in_kg_not_in_index or abstract_triplets:
        triplets_to_kg, triplets_to_index = prepare_triplets_to_add_to_dbs(
            triplets_not_in_kg, prop_ex_rel_triplets, entities_in_kg_not_in_index, new_entities, abstract_triplets, user_id
        )
        logger.debug(f"triplets_to_kg -- {triplets_to_kg}\n triplets_to_index -- {triplets_to_index}")
        triplets_added_to_kg = add_triplets_to_dbs(graph, user_id, triplets_to_kg, triplets_to_index)
    else:
        triplets_added_to_kg = []

    triplets_added_to_kg += properties_added_to_kg
    triplets_already_in_kg += properties_already_in_kg

    logger.info(f"added_to_graph -- {triplets_added_to_kg}, triplets_already_in_graph -- {triplets_already_in_kg}")
    return [{"added_to_graph": triplets_added_to_kg, "triplets_already_in_graph": triplets_already_in_kg}]


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request, kg_graph)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
