import copy
import logging
import random

from df_engine.core import Actor, Context

from common.constants import MUST_CONTINUE
from common.dff.integration.context import (
    get_last_human_utterance,
    get_shared_memory,
    save_to_shared_memory,
    set_can_continue,
    set_confidence,
)
from common.fact_random import get_fact
from common.funfact import FUNFACT_LIST, make_question
from common.utils import get_topics

logger = logging.getLogger(__name__)

CONF_HIGH = 1.0
CONF_ZERO = 0.0


def random_funfact_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    set_confidence(ctx, actor, CONF_HIGH)
    set_can_continue(ctx, actor, MUST_CONTINUE)
    funfact_list = copy.deepcopy(FUNFACT_LIST)
    random.shuffle(funfact_list)
    shared_memory = get_shared_memory(ctx, actor)
    given_funfacts = []
    if shared_memory:
        given_funfacts = shared_memory.get("given_funfacts", [])
    for funfact, topic in funfact_list:
        if funfact not in given_funfacts:
            given_funfacts.append(funfact)
            save_to_shared_memory(ctx, actor, given_funfacts=given_funfacts)
            link_question = make_question(topic)
            response = f"{funfact} {link_question}"
            break
    if not response:
        set_confidence(ctx, actor, CONF_ZERO)
    return response


def thematic_funfact_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    set_confidence(ctx, actor, CONF_HIGH)
    set_can_continue(ctx, actor, MUST_CONTINUE)
    entity = ctx.last_request.split("about")
    if len(entity) > 1:
        entity = entity[1]
        human_utter = get_last_human_utterance(ctx, actor)
        topic = get_topics(human_utter, which="cobot_topics")[0]
        funfact = get_fact(entity, f"fact about {entity}")
        if funfact:
            link_question = make_question(topic)
            response = f"{funfact} {link_question}"
    if not response:
        set_confidence(ctx, actor, CONF_ZERO)
    return response
