import logging
import json
import re
import random

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
from deeppavlov_kg import KnowledgeGraph, mocks
from common.utils import get_named_persons, get_named_locations
from common.personal_info import _is_not_re, my_name_is_not_pattern

logger = logging.getLogger(__name__)

graph = KnowledgeGraph(
    "bolt://neo4j:neo4j@neo4j:7687",
    ontology_kinds_hierarchy_path="deeppavlov_kg/database/ontology_kinds_hierarchy.pickle",
    ontology_data_model_path="deeppavlov_kg/database/ontology_data_model.json",
    db_ids_file_path="deeppavlov_kg/database/db_ids.txt"
)

# graph.drop_database()
# tree = graph.ontology._load_ontology_kinds_hierarchy()
# dict_tree = tree.to_dict()
# logger.warning(f'Kinds: {dict_tree}')
# if 'User' not in dict_tree['Kinds']:
# graph.ontology.create_entity_kind("User", kind_properties=["name"])
# mocks.populate(graph, drop=True)


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


def find_name(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        user_id = utt.get("user", {}).get("id", "")
        logger.info(f'User id: {user_id}')

        entity_detection = utt.get("annotations", {}).get("entity_detection", [])
        logger.info(f'Entity detection answer: {entity_detection}')
        entities = entity_detection.get('labelled_entities', [])
        types = []
        texts = []
        for entity in entities:
            name = entity.get('text', 'no entity name')
            types.append(entity.get('label', 'no entity label'))
            texts.append(name)
        logger.info(f'Entity types: {types}')
        logger.info(f'Entity names: {texts}')
        if texts:
            names = get_named_persons(utt)
            logger.info(f'Names from entities: {names}')
            if names:
                existing_ids = [
                    user[0].get("Id") for user in graph.search_for_entities("User")
                ]
                logger.info(f"Existing Ids: {existing_ids}")

                if user_id not in existing_ids:
                    # user_id is new -- adding entity + property
                    graph.create_entity("User", str(user_id), ['name'], [names[0]])

                    check_graph_entities(graph)

                    return f"I guess your name is {names[0]}! I added it as your property!"
                else:
                    # user_id is already in the graph -- updating property
                    graph.create_or_update_property_of_entity(
                        id_=user_id,
                        property_kind="name",
                        property_value=names[0],
                    )

                    check_graph_entities(graph)

                    return f"I already have you in the graph! Updating your property name to {names[0]}!"

        check_graph_entities(graph)
    return "No entities in the utterance!"
