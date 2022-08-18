import logging
import numpy as np

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
# import common.dff.integration.processing as int_prs
from common.wiki_skill import extract_entity
from deeppavlov_kg import KnowledgeGraph

logger = logging.getLogger(__name__)

graph = KnowledgeGraph(
    "bolt://neo4j:neo4j@localhost:7687",
    ontology_kinds_hierarchy_path="deeppavlov_kg/database/ontology_kinds_hierarchy.pickle",
    ontology_data_model_path="deeppavlov_kg/database/ontology_data_model.json",
    db_ids_file_path="deeppavlov_kg/database/db_ids.txt"
)


def find_entities(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        entity_linking = utt.get("annotations", {}).get("entity_linking", [])
        logger.info(f'Entity linking answer: {entity_linking}')
        entity_detection = utt.get("annotations", {}).get("entity_detection", [])
        logger.info(f'Entity detection answer: {entity_detection}')
        wiki_parser = utt.get("annotations", {}).get("wiki_parser", [])
        logger.info(f'Wiki parser  answer: {wiki_parser.get("entities_info", {})}')
        # for entity in entity_answer:
        #     logger.info(f'Entities: {entity}')
        #     max_ind = np.argmax(entity['confidences'])
        #     best_entity = entity['entity_pages_titles'][max_ind]
        #     logger.info(f'Best entity: {best_entity}')
    return "Empty response for now"


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler
