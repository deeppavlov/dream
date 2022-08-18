import logging
import uuid

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
# import common.dff.integration.processing as int_prs
from common.wiki_skill import extract_entity
from deeppavlov_kg import KnowledgeGraph

logger = logging.getLogger(__name__)

graph = KnowledgeGraph(
    "bolt://neo4j:neo4j@neo4j:7687",
    ontology_kinds_hierarchy_path="deeppavlov_kg/database/ontology_kinds_hierarchy.pickle",
    ontology_data_model_path="deeppavlov_kg/database/ontology_data_model.json",
    db_ids_file_path="deeppavlov_kg/database/db_ids.txt"
)

graph.drop_database()
graph.ontology.create_entity_kind("User",  kind_properties=["name"])


def add_new_entities(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        entity_detection = utt.get("annotations", {}).get("entity_detection", [])
        logger.info(f'Entity detection answer: {entity_detection}')
        entities = entity_detection.get('labelled_entities', [])

        logger.info('ALL CURRENT ENTITIES IN GRAPH:')
        gr_ents = graph.search_for_entities()
        for e in gr_ents:
            logger.info(f'{graph.get_current_state(e[0].get("Id")).get("name")}')

        # for entity in entities:
        #     entity_type = entity.get('label', 'no entity label')
        #     entity_name = entity.get('text', 'no entity name')
        #     logger.info(f'Entity type: {entity_type}')
        #     logger.info(f'Entity name: {entity_name}')
        #     graph.ontology.create_entity_kind(
        #         entity_type,
        #         kind_properties=set(),
        #     )
        #     graph.create_entity(entity_type, str(uuid.uuid4()), {'name': entity_name})

        graph.create_entity("User", str(uuid.uuid4()), ['name'], ["Pavel"])
        logger.info('ALL ENTITIES IN GRAPH AFTER UPDATE:')
        gr_ents = graph.search_for_entities()
        for e in gr_ents:
            logger.info(f'{graph.get_current_state(e[0].get("Id")).get("name")}')
    return "Empty response for now"


def find_name(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        entity_detection = utt.get("annotations", {}).get("entity_detection", [])
        logger.info(f'Entity detection answer: {entity_detection}')
        entities = entity_detection.get('labelled_entities', [])
        types = []
        texts = []
        for entity in entities:
            types.append(entity.get('label', 'no entity label'))
            texts.append(entity.get('text', 'no entity name'))
        logger.info(f'Entity types: {types}')
        logger.info(f'Entity names: {texts}')
    return "I can't understand names yet!"


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler
