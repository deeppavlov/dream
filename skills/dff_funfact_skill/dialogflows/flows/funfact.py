# %%
import os
import logging
import random
from enum import Enum, auto
import copy

import sentry_sdk

from common.funfact import funfact_requested, story_requested, FUNFACT_LIST, make_question
from common.constants import MUST_CONTINUE
from common.utils import get_topics
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils

from common.fact_random import get_facts

import dialogflows.scopes as scopes

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


class State(Enum):
    USR_START = auto()
    SYS_OFFERS_FACT = auto()
    SYS_ERR = auto()
    USR_ERR = auto()


# %%

##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extension.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################
# utils
##################################################################################################################
# ....

##################################################################################################################
# std greeting
##################################################################################################################
CONF_HIGH = 1.0


def funfact_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    bot_utterance = state_utils.get_last_bot_utterance(vars)
    flag = funfact_requested(human_utterance, bot_utterance)
    logging.info(f"funfact_request {flag}")
    return flag


def funfact_response(vars, shuffle=True):
    logger.info("exec funfact_response")
    state_utils.set_confidence(vars, confidence=CONF_HIGH)
    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
    shared_memory = state_utils.get_shared_memory(vars)
    given_funfacts = shared_memory.get("given_funfacts", [])
    funfact_list = copy.deepcopy(FUNFACT_LIST)
    if shuffle:
        random.shuffle(funfact_list)
    answer = ""
    human_utterance = state_utils.get_last_human_utterance(vars)
    funfacts_to_iterate = funfact_list
    entity = ""
    if story_requested(human_utterance):
        answer = (
            "Unfortunately, rules of the competition forbid me to tell you a story, " "but I can tell you a fun fact."
        )
    elif "fact about" in human_utterance["text"]:  # entity requested
        entity = human_utterance["text"].split("fact about")[1]
        topic = get_topics(human_utterance, which="cobot_topics")[0]
        funfact = get_facts(f"fact about {entity}")
        funfacts_to_iterate = [(funfact, topic)] + funfacts_to_iterate
    for funfact, topic in funfacts_to_iterate:
        if given_funfacts:
            link_question = make_question()
        else:
            link_question = make_question(topic)
        if funfact not in given_funfacts:
            state_utils.save_to_shared_memory(vars, given_funfacts=given_funfacts + [funfact])
        answer = f"{answer} {funfact} {link_question}"
        return answer
    state_utils.set_confidence(vars, confidence=0)
    answer = ""
    return answer


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    logger.info("exec error_response")
    state_utils.set_confidence(vars, 0)
    return ""


##################################################################################################################
#  START
# ######### transition State.USR_START -> State.SYS_HI if hi_request==True (request returns only bool values) ####
simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {State.SYS_OFFERS_FACT: funfact_request},
)
simplified_dialogflow.add_system_transition(State.SYS_OFFERS_FACT, State.USR_START, funfact_response)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

##################################################################################################################
#  Compile and get dialogflow
##################################################################################################################
# do not foget this line
dialogflow = simplified_dialogflow.get_dialogflow()
