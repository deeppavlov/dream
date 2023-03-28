import logging
import re
from typing import Callable, Any
import sentry_sdk
from os import getenv
import functools
import json
from deeppavlov_kg import TerminusdbKnowledgeGraph
from scenario.config import KG_DB_NAME, KG_TEAM_NAME, KG_PASSWORD, KG_SERVER
from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx

from common.food import BAKERY_PATTERN

from flask import request

from common.universal_templates import (
    NOT_LIKE_PATTERN,
    if_chat_about_particular_topic,
    is_switch_topic,
    tell_me_more,
)
logger = logging.getLogger(__name__)
# ....


def start_condition(ctx: Context, actor: Actor) -> bool:
    # with open("pr_ex.json", "w") as ctx_file:               # to get contents of ctx.misc["agent"]
    #     json.dump(ctx.misc["agent"], ctx_file, indent=2)
    return if_chat_about_particular_topic(
        int_ctx.get_last_human_utterance(ctx, actor),
        int_ctx.get_last_bot_utterance(ctx, actor),
        compiled_pattern=BAKERY_PATTERN,
    )

def get_current_dessert_name(ctx: Context, actor: Actor) -> bool:
    if "agent" in ctx.misc:
        dessert_name = ctx.misc["agent"]["dialog"]["human_utterances"][-1]["annotations"]["entity_detection"]["entities"][-1]

        return dessert_name
    
    return None

# def extract_entity(ctx, entity_type):
#     user_uttr: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
#     annotations = user_uttr.get("annotations", {})
#     logger.info(f"annotations {annotations}")
#     if entity_type.startswith("tags"):
#         tag = entity_type.split("tags:")[1]
#         nounphrases = annotations.get("entity_detection", {}).get("labelled_entities", [])
#         for nounphr in nounphrases:
#             nounphr_text = nounphr.get("text", "")
#             nounphr_label = nounphr.get("label", "")
#             if nounphr_label == tag:
#                 found_entity = nounphr_text
#                 return found_entity
    # elif entity_type.startswith("wiki"):
    #     wp_type = entity_type.split("wiki:")[1]
    #     found_entity, *_ = find_entity_by_types(annotations, [wp_type])
    #     if found_entity:
    #         return found_entity
    # elif entity_type == "any_entity":
    #     entities = annotations.get("entity_detection", {}).get("entities", [])
    #     if entities:
    #         return entities[0]
    # else:
    #     res = re.findall(entity_type, user_uttr.get("text", ""))
    #     if res:
    #         return res[0]
    # return ""


# def has_entities(*args):
#     def has_entities_func(ctx: Context, actor: Actor) -> Context:
#         for f_type in args:
#             extracted_entity = extract_entity(ctx, f_type)
#             if extracted_entity:
#                 return True
#         return False
#     return has_entities_func

def has_entity_in_graph():
    def has_entity_in_graph_handler(ctx: Context, actor: Actor) -> Context:
        dessert_id = get_current_dessert_name(ctx, actor)
        if dessert_id:
            dessert_id = dessert_id.replace(" ", "_")
            current_dessert_id = dessert_id.capitalize()

            graph = TerminusdbKnowledgeGraph(
                team=KG_TEAM_NAME, db_name=KG_DB_NAME, server=KG_SERVER, 
                password=KG_PASSWORD
            )
            if graph.ontology.get_entity_kind(current_dessert_id):
                return True
        
        return False
    
    return has_entity_in_graph_handler

def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler

def do_something():
    uttrs = request.json.get("utterances", [])
    utt = uttrs[0]
    annotations = uttrs[0].get("annotations", {})
    custom_el_annotations = annotations.get("custom_entity_linking", [])
    logger.info(f"utt --- {utt}")
    logger.info(f"custom_el_annotations --- {custom_el_annotations}")

# do_something()