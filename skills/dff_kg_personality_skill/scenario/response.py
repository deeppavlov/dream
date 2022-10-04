import logging
import json
import re
import random
import numpy as np
import uuid

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
from deeppavlov_kg import KnowledgeGraph, mocks
from common.utils import get_named_persons, get_named_locations
from common.personal_info import _is_not_re, my_name_is_not_pattern, my_name_is_pattern

logger = logging.getLogger(__name__)

# graph = KnowledgeGraph(
#     "bolt://neo4j:neo4j@neo4j:7687",
#     ontology_kinds_hierarchy_path="deeppavlov_kg/database/ontology_kinds_hierarchy.pickle",
#     ontology_data_model_path="deeppavlov_kg/database/ontology_data_model.json",
#     db_ids_file_path="deeppavlov_kg/database/db_ids.txt"
# )

# graph.drop_database()
# if 'User' not in dict_tree['Kinds']:
# graph.ontology.create_entity_kind("User", kind_properties=["name"])
# mocks.populate(graph, drop=True)

# graph.ontology.create_relationship_kind("SPOKE_ABOUT", "User")
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


# for rel in rel_type_dict:
#     if rel_type_dict[rel] == 'relation':
#         rel_name = '_'.join(rel.split(' ')).upper()
#         graph.ontology.create_relationship_kind(rel_name, "User")
#     else:
#         graph.ontology.create_entity_kind_properties("User", [rel])


def fallback(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.info('You are in the Fallback node.')
    return "Something went wrong! You are in the fallback node!"


def check_graph_entities(graph):
    # check the graph state
    logger.info('ALL ENTITIES IN GRAPH AFTER UPDATE:')
    gr_ents = graph.search_for_entities("User")
    logger.info(f'Num of entities in graph: {len(gr_ents)}')
    for e in gr_ents:
        logger.info(f'{graph.get_current_state(e[0].get("Id")).get("name")}')


def add_entity_from_triplet_extraction(graph, entity_kind, entity_name, rel_type, user_id):
    entity_kind = entity_kind.replace('_', '').title()
    new_entity_id = str(uuid.uuid4())
    graph.ontology.create_entity_kind(entity_kind, kind_properties=["name"])
    graph.create_entity(entity_kind, new_entity_id, ["name"], [entity_name])
    graph.create_relationship(user_id, rel_type, new_entity_id)
    logger.info(f'Added entity {entity_name} with Kind {entity_kind}! and connected it with the User {user_id}!')
    logger.info(f'{entity_name} is connected with User by {rel_type} relationship.')


def add_entity_with_abstract_relationship(graph, entity_kind, entity_name, user_id):
    entity_kind = entity_kind.replace('_', '').title()
    new_entity_id = str(uuid.uuid4())
    graph.ontology.create_entity_kind(entity_kind, kind_properties=["name"])
    graph.create_entity(entity_kind, new_entity_id, ["name"], [entity_name])
    rel = 'SPOKE_ABOUT'
    graph.create_relationship(user_id, rel, new_entity_id)
    logger.info(f'Added entity {entity_name} with Kind {entity_kind} and connected it with the User {user_id}!')


def update_name_property(graph, user_id, names):
    # user_id is already in the graph -- updating property
    graph.create_or_update_property_of_entity(
        id_=user_id,
        property_kind="name",
        property_value=names[0],
    )
    # check_graph_entities(graph)
    return f"I already have you in the graph! Updating your property name to {names[0]}!"


def add_name_property(graph, user_id, names):
    # user_id is new -- adding entity + property
    graph.create_entity("User", str(user_id), ['name'], [names[0]])
    # check_graph_entities(graph)
    return f"I guess your name is {names[0]}! I added it as your property!"


def add_any_property(graph, user_id, property_type, property_value):
    graph.create_or_update_property_of_entity(
        id_=user_id,
        property_kind=property_type,
        property_value=property_value,
    )
    return f"I added a property {property_type} with value {property_value}!"


def fix_wrong_name(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        names = get_named_persons(utt)
        user_id = utt.get("user", {}).get("id", "")
        if names:
            update_message = update_name_property(graph, user_id, names)
            return update_message
    return "I don't recognize any names in you answer, so no updates! Sorry!"


def get_entities_with_dbpedia_type(utt):
    entity_linking = utt.get("annotations", {}).get("entity_linking", [])
    logger.info(f'Entity linking answer: {entity_linking}')
    entities_to_add = {}
    for entity_link in entity_linking:
        confs = entity_link.get('confidences', [])
        dbpedia_types = entity_link.get('dbpedia_types', [])
        if dbpedia_types:
            max_ind = np.argmax(confs)
            logger.info(f'Types: {dbpedia_types[max_ind]}')
            main_kind = dbpedia_types[max_ind][0].split('/')[-1].replace("Wikipedia:", "")
            entity_name = entity_link.get("entity_substr", "")
            logger.info(f'Entity Name: {entity_name}')
            entities_to_add[entity_name] = main_kind
    logger.info(f'Entities to add: {entities_to_add}')
    return entities_to_add


def get_entity_type_from_property_extraction(attributes):
    entity_info = attributes['entity_info']
    if not entity_info:
        return 'Misc'
    exact_entity_info = entity_info[attributes['triplet']['object']]
    entity_kinds = exact_entity_info['dbpedia_types']
    if entity_kinds:
        if entity_kinds[0]:
            return entity_kinds[0][0].split('/')[-1].replace("Wikipedia:", "")
    else:
        return 'Misc'


def add_relations_and_properties(utt, user_id):
    attributes = utt.get("annotations", {}).get("property_extraction", {})
    # logger.info(f'Attributes: {attributes}')
    if attributes and attributes['triplet']:
        triplet = attributes['triplet']
        if triplet['subject'] != 'user':
            return "No relations to the User were found!"
        if 'relation' in triplet:
            entity_kind = get_entity_type_from_property_extraction(attributes)
            entity_name = triplet['object']
            relation = '_'.join(triplet['relation'].split(' ')).upper()
            add_entity_from_triplet_extraction(graph, entity_kind, entity_name, relation, user_id)
            return f"Added entity {entity_name} and connected it with you! "
        else:
            ans = add_any_property(graph, user_id, triplet['property'], triplet['object'])
            return ans
    return 'No relationships found!'


def find_name(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)

    # attributes = utt.get("annotations", {}).get("property_extraction", [])
    # logger.info(f'Attributes: {attributes}')

    entity_linking = utt.get("annotations", {}).get("entity_linking", {})
    logger.info(f'Entity linking answer: {entity_linking}')

    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        user_id = utt.get("user", {}).get("id", "")

        entity_detection = utt.get("annotations", {}).get("entity_detection", [])
        entities = entity_detection.get('labelled_entities', [])
        entities = [entity.get('text', 'no entity name') for entity in entities]
        if not entities:
            ans = add_relations_and_properties(utt, user_id)
            return ans
            # return "No entities in the utterance!"

        names = get_named_persons(utt)
        if names:
            existing_ids = [user[0].get("Id") for user in graph.search_for_entities("User")]
            if user_id not in existing_ids:
                add_name_message = add_name_property(graph, user_id, names)
                return add_name_message
            elif my_name_is_pattern.search(last_utt):
                name_update_message = update_name_property(graph, user_id, names)
                return name_update_message
            else:
                return "You are telling me someone's name, but I guess it's not yours!"
        else:
            ans = add_relations_and_properties(utt, user_id)
            return ans

            # ENTITIES WITH ABSTRACT RELATION "SPOKE ABOUT" IF FOUND ANY DBPEDIA TYPES
            # entities_to_add = get_entities_with_dbpedia_type(utt)
            # if not entities_to_add:
            #     return f"Couldn't get Kinds for entities {','.join(entities)}, " \
            #            f"so won't add anything to graph :("
            # for entity_name in entities_to_add:
            #     add_entity_with_abstract_relationship(graph, entities_to_add[entity_name], entity_name, user_id)
            # entities_joined = ', '.join(list(entities_to_add.keys()))
            # return f"Added entities {entities_joined} to the graph as related to you!"

    check_graph_entities(graph)
    return "We shouldn't be here."
