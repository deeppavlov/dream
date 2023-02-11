# %%
import logging
import os
import random
import re

from common.fact_random import get_fact
from enum import Enum, auto

import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import dialogflows.scopes as scopes
from common.constants import CAN_CONTINUE_PROMPT, CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO
from common.universal_templates import DONOTKNOW_LIKE, COMPILE_NOT_WANT_TO_TALK_ABOUT_IT
from common.utils import get_entities, join_words_in_or_pattern, get_comet_conceptnet_annotations
from common.food import (
    FAST_FOOD_FACTS,
    FAST_FOOD_QUESTIONS,
    FAST_FOOD_WHAT_QUESTIONS,
    FOOD_WORDS,
    CONCEPTNET_SYMBOLOF_FOOD,
    CONCEPTNET_HASPROPERTY_FOOD,
    CONCEPTNET_CAUSESDESIRE_FOOD,
)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9
CONF_LOWEST = 0.8

FOOD_WORDS_RE = re.compile(FOOD_WORDS, re.IGNORECASE)
NO_WORDS_RE = re.compile(r"(\bnot\b|n't|\bno\b) ", re.IGNORECASE)
DONOTKNOW_LIKE_RE = re.compile(join_words_in_or_pattern(DONOTKNOW_LIKE), re.IGNORECASE)


class State(Enum):
    USR_START = auto()
    #
    SYS_SAID_FAV_FOOD = auto()
    USR_HOW_OFTEN = auto()
    SYS_HOW_OFTEN = auto()
    USR_WHAT_EAT = auto()
    SYS_FOOD_CHECK = auto()
    USR_FAST_FOOD_FACT = auto()
    SYS_SMTH = auto()
    SYS_SMTH_ELSE = auto()
    USR_LINKTO = auto()
    #
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
# yes
##################################################################################################################


def yes_request(ngrams, vars):
    flag = condition_utils.is_yes_vars(vars)
    logger.info(f"yes_request {flag}")
    return flag


##################################################################################################################
# no
##################################################################################################################


def no_request(ngrams, vars):
    flag = condition_utils.is_no_vars(vars)
    logger.info(f"no_request {flag}")
    return flag


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return "Sorry"


##################################################################################################################
# let's talk about fast food
##################################################################################################################


def is_question(vars):
    annotations_sentseg = state_utils.get_last_human_utterance(vars)["annotations"].get("sentseg", {})
    flag = "?" in annotations_sentseg.get("punct_sent", "")
    return flag


def check_conceptnet(vars):
    annotations_conceptnet = get_comet_conceptnet_annotations(state_utils.get_last_human_utterance(vars))
    conceptnet = False
    food_item = None
    for elem, triplets in annotations_conceptnet.items():
        conceptnet_symbolof = any([i in triplets.get("SymbolOf", []) for i in CONCEPTNET_SYMBOLOF_FOOD])
        conceptnet_hasproperty = any([i in triplets.get("HasProperty", []) for i in CONCEPTNET_HASPROPERTY_FOOD])
        causes_desire = triplets.get("CausesDesire", [])
        conceptnet_causesdesire = any([i in causes_desire for i in CONCEPTNET_CAUSESDESIRE_FOOD]) or any(
            ["eat" in i for i in causes_desire] + ["cook" in i for i in causes_desire]
        )
        conceptnet = any([conceptnet_symbolof, conceptnet_hasproperty, conceptnet_causesdesire])
        if conceptnet:
            food_item = elem
            return conceptnet, food_item
    return conceptnet, food_item


def dont_want_talk(vars):
    utt = state_utils.get_last_human_utterance(vars)["text"]
    flag = bool(re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, utt))
    logger.info(f"dont_want_talk {flag}")
    return flag


def smth_request(ngrams, vars):
    flag = condition_utils.no_requests(vars) and (not dont_want_talk(vars))
    logger.info(f"smth_request {flag}")
    return flag


def fast_food_request(ngrams, vars):
    if all([not condition_utils.no_requests(vars), dont_want_talk(vars), is_question(vars)]):
        flag = False
    else:
        flag = True
    logger.info(f"fast_food_request {flag}")
    return flag


def fast_food_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_facts = shared_memory.get("fast_food_facts", [])
        unused_facts = [i for i in FAST_FOOD_FACTS if i not in used_facts]
        used_questions = shared_memory.get("fast_food_questions", [])
        unused_questions = [i for i in FAST_FOOD_QUESTIONS if i not in used_questions]
        fact = ""
        question = ""
        if unused_facts:
            fact = random.choice(unused_facts)
            state_utils.save_to_shared_memory(vars, fast_food_facts=used_facts + [fact])
        if unused_questions:
            question = random.choice(unused_questions)
            state_utils.save_to_shared_memory(vars, fast_food_questions=used_questions + [question])
        if fact and question:
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
            return f"I just found out that {fact} {question}"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def what_eat_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_questions = shared_memory.get("fast_food_what_questions", [])
        question = random.choice([i for i in FAST_FOOD_WHAT_QUESTIONS if i not in used_questions])
        user_utt = state_utils.get_last_human_utterance(vars)["text"].lower()
        bot_utt = state_utils.get_last_bot_utterance(vars)["text"].lower()
        state_utils.save_to_shared_memory(vars, fast_food_what_questions=used_questions + [question])
        if "how often" in bot_utt:
            if any([i in user_utt for i in ["times", "every"]]):
                question = "Not so often as some people do! " + question
            else:
                question = "Okay. " + question
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        return question
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def fav_food_request(ngrams, vars):
    flag = False
    user_fav_food = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    food_words_search = re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"])
    if all(
        [
            any([user_fav_food, check_conceptnet(vars), food_words_search]),
            condition_utils.no_requests(vars),
            not re.search(NO_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"]),
        ]
    ):
        flag = True
    logger.info(f"fav_food_request {flag}")
    return flag


def food_fact_response(vars):
    acknowledgements = ["I like it too.", "I'm not fond of it.", "It's awesome.", "Fantastic.", "Loving it.", "Yummy!"]
    human_utt = state_utils.get_last_human_utterance(vars)
    annotations = human_utt["annotations"]
    human_utt_text = human_utt["text"].lower()
    bot_utt_text = state_utils.get_last_bot_utterance(vars)["text"].lower()

    fact = ""
    berry_name = ""
    entity = ""
    facts = annotations.get("fact_random", [])
    if "berry" in bot_utt_text:
        berry_names = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
        if berry_names:
            berry_name = berry_names[0]

        if all(["berry" not in human_utt_text, len(human_utt_text.split()) == 1, berry_name]):
            berry_name += "berry"
            fact = get_fact(berry_name, f"fact about {berry_name}")
            entity = berry_name
        elif berry_name:
            if facts:
                fact = facts[0].get("fact", "")
                entity = facts[0].get("entity_substr", "")
    else:
        if facts:
            fact = facts[0].get("fact", "")
            entity = facts[0].get("entity_substr", "")
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        if re.search(DONOTKNOW_LIKE_RE, human_utt_text):
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
        # "I have never heard about it. Could you tell me more about that please."
        elif (not fact) and check_conceptnet(vars):
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return "I haven't tried yet. Why do you like it?"
        elif not fact:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
        elif fact and entity:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return f"{entity}. {random.choice(acknowledgements)} {fact}"
        elif fact:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return f"Okay. {fact}"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def where_are_you_from_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        return "Where are you from?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START
simplified_dialogflow.add_user_transition(State.USR_START, State.SYS_SAID_FAV_FOOD, fast_food_request)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)


##################################################################################################################

simplified_dialogflow.add_system_transition(State.SYS_SAID_FAV_FOOD, State.USR_HOW_OFTEN, fast_food_response)
simplified_dialogflow.set_error_successor(State.SYS_SAID_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_HOW_OFTEN, State.SYS_HOW_OFTEN, smth_request)
simplified_dialogflow.set_error_successor(State.USR_HOW_OFTEN, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_HOW_OFTEN, State.USR_WHAT_EAT, what_eat_response)
simplified_dialogflow.set_error_successor(State.SYS_HOW_OFTEN, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_EAT,
    {
        State.SYS_FOOD_CHECK: fav_food_request,
        State.SYS_SMTH_ELSE: smth_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_EAT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_FOOD_CHECK, State.USR_FAST_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_FOOD_CHECK, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_FAST_FOOD_FACT, State.SYS_SMTH, smth_request)
simplified_dialogflow.set_error_successor(State.USR_FAST_FOOD_FACT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_SMTH, State.USR_HOW_OFTEN, fast_food_response)
simplified_dialogflow.set_error_successor(State.SYS_SMTH, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_SMTH_ELSE, State.USR_LINKTO, where_are_you_from_response)
simplified_dialogflow.set_error_successor(State.SYS_SMTH_ELSE, State.SYS_ERR)


#################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
