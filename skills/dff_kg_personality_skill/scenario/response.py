import logging
import json
import re
import random

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
# import common.dff.integration.processing as int_prs
from common.wiki_skill import extract_entity
from deeppavlov_kg import KnowledgeGraph

logger = logging.getLogger(__name__)


def find_entities(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    extracted_entity = extract_entity(ctx, "any_entity")
    logger.info(f'Entities: {extracted_entity}')
    return "Empty response for now"
