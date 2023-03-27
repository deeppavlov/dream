import logging
import re
from typing import Callable, Any
import sentry_sdk
from os import getenv
import functools
import json
# from deeppavlov_kg import TerminusdbKnowledgeGraph
# from scenario.config import KG_DB_NAME, KG_PASSWORD, KG_SERVER
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
    return if_chat_about_particular_topic(
        int_ctx.get_last_human_utterance(ctx, actor),
        int_ctx.get_last_bot_utterance(ctx, actor),
        compiled_pattern=BAKERY_PATTERN,
    )

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