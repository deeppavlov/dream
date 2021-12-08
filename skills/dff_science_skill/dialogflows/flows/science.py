# %%
import logging
import os
import random
import re

from enum import Enum, auto

import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import dialogflows.scopes as scopes
import dialogflows.flows.utils as local_utils
from common.science import science_topics, NICE_CHAT_ACKS

from common.science import SCIENCE_COMPILED_PATTERN, OPINION_REQUESTS_ABOUT_SCIENCE, OFFER_TALK_ABOUT_SCIENCE
from common.link import link_to_skill2i_like_to_talk
from common.constants import CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from common.universal_templates import (
    if_chat_about_particular_topic,
    NOT_LIKE_PATTERN,
    if_not_want_to_chat_about_particular_topic,
)


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
SERVICE_NAME = os.getenv("SERVICE_NAME")

logger = logging.getLogger(__name__)


LINKTO_PHRASES = (
    link_to_skill2i_like_to_talk.get("dff_science_skill", [])
    + OPINION_REQUESTS_ABOUT_SCIENCE
    + OFFER_TALK_ABOUT_SCIENCE
)
LINKTO_PHRASES = [phrase.lower() for phrase in LINKTO_PHRASES]

CONF_100 = 1.0
CONF_98 = 0.98
CONF_95 = 0.95
CONF_90 = 0.9
CONF_85 = 0.85
CONF_75 = 0.75
CONF_65 = 0.65
CONF_0 = 0.0


class State(Enum):
    USR_START = auto()
    #
    SYS_NO_SCIENCE = auto()
    USR_NO_SCIENCE = auto()
    #
    SYS_REQUEST_SCIENCE_TOPIC = auto()
    USR_REQUEST_SCIENCE_TOPIC = auto()
    #
    SYS_CAN_YOU_IMAGINE = auto()
    USR_CAN_YOU_IMAGINE = auto()
    #
    SYS_I_THINK_IT_CAN_CHANGE = auto()
    USR_I_THINK_IT_CAN_CHANGE = auto()
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


def true_request(ngrams, vars):
    return True


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
    return ""


def linkto_yes(vars):
    prev_uttr = state_utils.get_last_bot_utterance(vars)
    bot_text = prev_uttr.get("text", "").lower()
    flag = any([phrase in bot_text for phrase in LINKTO_PHRASES]) and condition_utils.is_yes_vars(vars)
    logger.info(f"linkto_yes {flag}")
    return flag


def if_chat_about_science_topic_pattern(vars, compiled_pattern=SCIENCE_COMPILED_PATTERN):
    uttr = state_utils.get_last_human_utterance(vars)
    prev_uttr = state_utils.get_last_bot_utterance(vars)
    prev_uttr = {} if prev_uttr is None else prev_uttr
    flag = if_chat_about_particular_topic(uttr, prev_uttr, compiled_pattern=compiled_pattern)
    return bool(flag)


def is_mentioned_science_pattern(vars, compiled_pattern=SCIENCE_COMPILED_PATTERN):
    uttr = state_utils.get_last_human_utterance(vars)
    prev_uttr = state_utils.get_last_bot_utterance(vars)
    prev_uttr = {} if prev_uttr is None else prev_uttr
    is_not_wanted = if_not_want_to_chat_about_particular_topic(uttr, prev_uttr)
    flag = bool(re.search(compiled_pattern, uttr.get("text", "").lower())) and not is_not_wanted
    return flag


def science_request(ngrams, vars):
    flag = any(
        [
            if_chat_about_science_topic_pattern(vars),
            is_mentioned_science_pattern(vars),
            linkto_yes(vars),
        ]
    )
    logger.info(f"science_request {flag}")
    return flag


def lets_talk_about_request(ngrams, vars):
    is_lets_chat = condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    is_key_phrase = science_request(ngrams, vars)
    flag = all(
        [
            is_lets_chat,
            is_key_phrase,
        ]
    )
    logger.info(f"lets_talk_about_request {flag}")
    return flag


def not_lets_talk_about_request(ngrams, vars):
    flag = not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    logger.info(f"not_lets_talk_about_request {flag}")
    return flag


def lets_talk_about_current_subtopic_request(ngrams, vars):
    last_human_utterance = state_utils.get_last_human_utterance(vars)

    # get key_phrases_re
    shared_memory = state_utils.get_shared_memory(vars)
    current_topic = shared_memory["current_topic"]
    key_phrases_re = local_utils.science_topics[current_topic]["key_phrases_re"]
    flag = any(
        [
            yes_request(ngrams, vars),
            key_phrases_re.search(last_human_utterance["text"]),
        ]
    )
    logger.info(f"lets_talk_about_current_subtopic_request {flag}")
    return flag


def request_science_topic_response(vars):
    try:
        # get_unused_topics
        science_topics_names = local_utils.get_unused_topics(vars)
        if not science_topics_names:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
            state_utils.set_confidence(vars, confidence=CONF_100)
            next_index = state_utils.get_unrepeatable_index_from_rand_seq(
                vars,
                "nice_chat_acks",
                len(NICE_CHAT_ACKS),
                True,
            )
            ack = f"{NICE_CHAT_ACKS[next_index]}"
            body = (
                "Okay, There are many scientific topics that could be discussed, "
                "when I learn something new I will be ready to talk to you about it."
            )
            return " ".join([ack, body])
        science_topics_names = science_topics_names if science_topics_names else list(science_topics.keys())
        current_topic = random.sample(science_topics_names, 1)[0]
        local_utils.add_unused_topics(vars, current_topic)

        # save is_requested_topic_before
        shared_memory = state_utils.get_shared_memory(vars)
        is_requested_topic_before = shared_memory.get("is_requested_topic_before")
        state_utils.save_to_shared_memory(vars, current_topic=current_topic, is_requested_topic_before=True)

        if is_requested_topic_before:
            next_index = state_utils.get_unrepeatable_index_from_rand_seq(
                vars,
                "nice_chat_acks",
                len(NICE_CHAT_ACKS),
                True,
            )
            ack = f"{NICE_CHAT_ACKS[next_index]}"
            body = f"So, maybe next? Do you wanna talk about {current_topic}?"
        else:
            ack = "I think people who are interested in science are special."
            body = f"I like to talk about a variety of scientific topics. Do you wanna talk about {current_topic}?"
        state_utils.add_acknowledgement_to_response_parts(vars)
        if linkto_yes(vars):
            state_utils.set_can_continue(vars, MUST_CONTINUE)
            state_utils.set_confidence(vars, confidence=CONF_100)
        elif if_chat_about_science_topic_pattern(vars):
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            state_utils.set_confidence(vars, confidence=CONF_95)
        elif is_mentioned_science_pattern(vars):
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            state_utils.set_confidence(vars, confidence=CONF_95)
        else:
            return error_response(vars)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def can_you_imagine_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        current_topic = shared_memory["current_topic"]
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
        body = f"Can you imagine how much {current_topic} can change the world?"

        state_utils.set_confidence(vars, confidence=CONF_100)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def i_think_it_can_change_the_world_response(vars):
    try:
        # get world_changes
        shared_memory = state_utils.get_shared_memory(vars)
        current_topic = shared_memory["current_topic"]
        world_changes = science_topics[current_topic]["world_changes"]

        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
        if world_changes:
            body = " ".join(["I think it can change the world a lot."] + world_changes)
        else:
            body = "I think this is an insignificant technology and may not greatly affect the world."

        state_utils.set_confidence(vars, confidence=CONF_100)
        state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def no_science_request(ngrams, vars):
    human_uttr_text = state_utils.get_last_human_utterance(vars).get("text", "")
    bot_uttr_text = state_utils.get_last_bot_utterance(vars).get("text", "")
    if NOT_LIKE_PATTERN.search(human_uttr_text) and (
        SCIENCE_COMPILED_PATTERN.search(human_uttr_text) or SCIENCE_COMPILED_PATTERN.search(bot_uttr_text)
    ):
        return True
    return False


def no_science_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_100)
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        state_utils.save_to_shared_memory(vars, current_status="")
        return "Okay, if I'm always ready to talk about science, the achievements of humanity inspire me. "
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
#  USR_START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_NO_SCIENCE: no_science_request,
        State.SYS_REQUEST_SCIENCE_TOPIC: science_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
# SYS_NO_SCIENCE

simplified_dialogflow.add_system_transition(
    State.SYS_NO_SCIENCE,
    State.USR_START,
    request_science_topic_response,
)
simplified_dialogflow.set_error_successor(State.SYS_NO_SCIENCE, State.SYS_ERR)

##################################################################################################################
# SYS_REQUEST_SCIENCE_TOPIC

simplified_dialogflow.add_system_transition(
    State.SYS_REQUEST_SCIENCE_TOPIC,
    State.USR_REQUEST_SCIENCE_TOPIC,
    request_science_topic_response,
)
simplified_dialogflow.set_error_successor(State.SYS_REQUEST_SCIENCE_TOPIC, State.SYS_ERR)

##################################################################################################################
# USR_REQUEST_SCIENCE_TOPIC
simplified_dialogflow.add_user_serial_transitions(
    State.USR_REQUEST_SCIENCE_TOPIC,
    {
        State.SYS_NO_SCIENCE: no_science_request,
        State.SYS_CAN_YOU_IMAGINE: lets_talk_about_current_subtopic_request,
        State.SYS_REQUEST_SCIENCE_TOPIC: lets_talk_about_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_REQUEST_SCIENCE_TOPIC, State.SYS_ERR)

##################################################################################################################
# SYS_CAN_YOU_IMAGINE
simplified_dialogflow.add_system_transition(
    State.SYS_CAN_YOU_IMAGINE,
    State.USR_CAN_YOU_IMAGINE,
    can_you_imagine_response,
)
simplified_dialogflow.set_error_successor(State.SYS_CAN_YOU_IMAGINE, State.SYS_ERR)

##################################################################################################################
##################################################################################################################
# USR_CAN_YOU_IMAGINE
simplified_dialogflow.add_user_serial_transitions(
    State.USR_CAN_YOU_IMAGINE,
    {
        State.SYS_NO_SCIENCE: no_science_request,
        State.SYS_I_THINK_IT_CAN_CHANGE: not_lets_talk_about_request,
        State.SYS_REQUEST_SCIENCE_TOPIC: lets_talk_about_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_CAN_YOU_IMAGINE, State.SYS_ERR)

##################################################################################################################
# SYS_I_THINK_IT_CAN_CHANGE
simplified_dialogflow.add_system_transition(
    State.SYS_I_THINK_IT_CAN_CHANGE,
    State.USR_START,
    i_think_it_can_change_the_world_response,
)
simplified_dialogflow.set_error_successor(State.SYS_I_THINK_IT_CAN_CHANGE, State.SYS_ERR)

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
