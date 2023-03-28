import logging
import re
from typing import Callable, Any
import sentry_sdk
from os import getenv
import functools
import json
from deeppavlov_kg import TerminusdbKnowledgeGraph
from scenario.config import TERMINUSDB_SERVER_URL, TERMINUSDB_SERVER_PASSWORD, TERMINUSDB_SERVER_DB, TERMINUSDB_SERVER_TEAM


from df_engine.core import Context, Actor
import df_engine.conditions as cnd

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx

from common.travel_italy import ITALY_PATTERN, italy_travel_skill_was_proposed
from common.food import FOOD_WORDS, FAVORITE_FOOD_WORDS

from common.universal_templates import (
    NOT_LIKE_PATTERN,
    if_chat_about_particular_topic,
    is_switch_topic,
    tell_me_more,
)
from common.utils import (
    get_intents,
    get_sentiment,
    is_question,
    is_opinion_request,
    is_opinion_expression,
)  # present in integration

# import scenario.response as loc_rsp
# import scenario.universal as universal
# from scenario.universal import GENRE_PATTERN, get_slot

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


USE_CACHE = True

# ....

SIDE_INTENTS = {
    "exit",
    "don't understand",
    "what_can_you_do",
    "what_is_your_job",
    "what_is_your_name",
    "what_time",
    "where_are_you_from",
    "who_made_you",
}

graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
)


def check_flag(prop: str) -> Callable:
    def check_flag_handler(ctx: Context, actor: Actor) -> bool:
        return ctx.misc.get("flags", {}).get(prop, False)

    return check_flag_handler

def start_condition(ctx: Context, actor: Actor) -> bool:
    # with open("new.json", "w") as ctx_file:               # to get contents of ctx.misc["agent"]
    #     json.dump(ctx.misc["agent"], ctx_file, indent=2)
    
    return if_chat_about_particular_topic(
        int_ctx.get_last_human_utterance(ctx, actor),
        int_ctx.get_last_bot_utterance(ctx, actor),
        compiled_pattern=ITALY_PATTERN,
    )

def is_side_or_stop(ctx: Context, actor: Actor) -> bool:
    """
    Check for side intents (including exit)
    """
    intents = set(get_intents(int_ctx.get_last_human_utterance(ctx, actor), which="intent_catcher", probs=False))
    side_intent_present = len(intents.intersection(SIDE_INTENTS)) > 0
    logger.debug("Side intent detected, exiting")
    return side_intent_present

def is_proposed_skill(ctx: Context, actor: Actor) -> bool:
    return italy_travel_skill_was_proposed(int_ctx.get_last_bot_utterance(ctx, actor))

def travel_italy_skill_switch(ctx: Context, actor: Actor) -> bool:
    user_uttr = int_ctx.get_last_human_utterance(ctx, actor)

    return re.findall(ITALY_PATTERN, user_uttr["text"])

def sentiment_detected(name: str = "positive", threshold: float = 0.6) -> Callable:
    def sentiment_detected_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            return False
        sentiment_probs = get_sentiment(int_ctx.get_last_human_utterance(ctx, actor), probs=True)
        return sentiment_probs.get(name, 0) >= threshold

    return sentiment_detected_handler

exit_skill = cnd.any(
    [
        is_side_or_stop,
        # int_cnd.is_switch_topic,
        # is_switch_topic,
        cnd.all([is_proposed_skill, int_cnd.is_no_vars]),
    ]
)

asked_about_italian_cuisine = cnd.regexp(re.compile(FOOD_WORDS, re.IGNORECASE))

uttr_about_favorite_food = cnd.regexp(re.compile(FAVORITE_FOOD_WORDS, re.IGNORECASE))

def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def get_current_user_id(ctx: Context, actor: Actor) -> bool:
    if "agent" in ctx.misc:
        user_id = ctx.misc["agent"]["dialog"]["human_utterances"][-1]["user"]["id"]

        return user_id
    
    return None
    

def has_entity_in_graph(property):
    def has_entity_in_graph_handler(ctx: Context, actor: Actor) -> Context:
        user_id = get_current_user_id(ctx, actor)
        if user_id:
            current_user_id = "User/" + user_id
            logger.info(f"current user id -- {current_user_id}")
            user_existing_properties = graph.get_properties_of_entity(entity_id=current_user_id)
            logger.info(f"user_existing_properties -- {user_existing_properties}")
            logger.info(f"property to search for -- {property}")
            if property in user_existing_properties:
                return True
        
        return False
    
    return has_entity_in_graph_handler
    
    