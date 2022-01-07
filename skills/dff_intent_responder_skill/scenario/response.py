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

def exit_respond(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    apology_bye_phrases = [
        "Sorry, have a great day!",
        "Sorry to bother you, see you next time!",
        "My bad. Have a great time!",
        "Didn't mean to be rude. Talk to you next time.",
        "Sorry for interrupting you. Talk to you soon.",
        "Terribly sorry. Have a great day!",
        "Thought you wanted to chat. My bad. See you soon!",
        "Oh, sorry. Have a great day!",
    ]

    response = ""
    set_confidence(ctx, actor, CONF_HIGH)
    set_can_continue(ctx, actor, MUST_CONTINUE)
    response = random.choice(apology_bye_phrases)
    '''
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
    '''
    return response
