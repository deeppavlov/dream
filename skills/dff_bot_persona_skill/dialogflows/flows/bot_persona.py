# %%
import json
import logging
import os
import random
import re

from enum import Enum, auto

import sentry_sdk
from spacy import load

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import dialogflows.scopes as scopes
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_SCENARIO_DONE, MUST_CONTINUE
from common.utils import get_intents, get_sentiment


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


spacy_nlp = load("en_core_web_sm")


with open("topic_favorites.json", "r") as f:
    FAV_STORIES_TOPICS = json.load(f)
your_favorite_request_re = re.compile("(you|your|yours|you have a).*(favorite|favourite|like)", re.IGNORECASE)

CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9


class State(Enum):
    USR_START = auto()
    #
    SYS_FAV_OR_LETS_CHAT = auto()
    USR_MY_FAV_STORY = auto()
    SYS_CHECK_FAV = auto()
    USR_DO_YOU_LIKE_TOPIC = auto()
    SYS_LIKE_TOPIC = auto()
    SYS_NOT_LIKE_TOPIC = auto()
    USR_WHATS_YOUR_FAV = auto()
    USR_TOP_FAVS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


# %%

##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extention.DFEasyFilling(State.USR_START)

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
# let's talk about
##################################################################################################################


def fav_or_lets_chat_request(ngrams, vars):
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
        or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    )
    flag = any(
        [
            any(["favorite" in utt, "favourite" in utt]),
            re.search(your_favorite_request_re, utt),
            user_lets_chat_about
        ]
    )
    logger.info(f"fav_or_lets_chat_request {flag}")
    return flag


def my_fav_story_response(vars):
    try:
        utt = state_utils.get_last_human_utterance(vars)["text"].lower()

        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = shared_memory.get("used_topics", [])
        name = ""
        story = ""
        response = ""
        for topic in FAV_STORIES_TOPICS:
            if topic in utt:
                name = FAV_STORIES_TOPICS.get(topic, "").get("name", "")
                story = FAV_STORIES_TOPICS.get(topic, "").get("story", "")
                if name:
                    response = f"My favorite {topic} is {name}. {story}  What about you?"
                    state_utils.set_confidence(vars, confidence=CONF_HIGH)
                    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                    state_utils.save_to_shared_memory(vars, used_topics=used_topics + [topic])
                    return response
        if not name and any(
            [
                ("my" not in utt) and ("favorite" in utt),
                re.search(your_favorite_request_re, utt)
            ]
        ):
            response = "Oh, I don't have one. What about you?"
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def check_fav_request(ngrams, vars):
    flag = False
    annot_utt = state_utils.get_last_human_utterance(vars)
    utt = annot_utt["text"].lower()
    if any(["favorite" in utt, "like" in utt, "love" in utt, "prefer" in utt]) and (
        'negative' not in get_sentiment(annot_utt, probs=False)
    ):
        flag = True
    logger.info(f"check_fav_request {flag}")
    return flag


def do_you_like_topic_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = list(set(
            shared_memory.get("used_topics", []) + [
                "thing", "day", "book genre", "singer", "actor", "song", "color",
                "team", "all time favorite movie"
            ]
        ))
        unused_topic = random.choice([t for t in FAV_STORIES_TOPICS if t not in used_topics])

        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        state_utils.save_to_shared_memory(vars, used_topics=used_topics + [unused_topic])
        if unused_topic not in "series":
            unused_topic += "s"
        return f"Do you like {unused_topic}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def whats_your_fav_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = shared_memory.get("used_topics", [])
        curr_topic = ""
        if used_topics:
            curr_topic = used_topics[-1]
        if curr_topic:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
            return f"What is your favorite {curr_topic}?"
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def top_favs_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        return f"What are your top three favorites?"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START

simplified_dialogflow.add_user_transition(State.USR_START, State.SYS_FAV_OR_LETS_CHAT, fav_or_lets_chat_request)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################

simplified_dialogflow.add_system_transition(State.SYS_FAV_OR_LETS_CHAT, State.USR_MY_FAV_STORY, my_fav_story_response)
simplified_dialogflow.set_error_successor(State.SYS_FAV_OR_LETS_CHAT, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_MY_FAV_STORY, State.SYS_CHECK_FAV, check_fav_request)
simplified_dialogflow.set_error_successor(State.USR_MY_FAV_STORY, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CHECK_FAV, State.USR_DO_YOU_LIKE_TOPIC,
                                            do_you_like_topic_response)
simplified_dialogflow.set_error_successor(State.SYS_CHECK_FAV, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_DO_YOU_LIKE_TOPIC,
    {
        State.SYS_LIKE_TOPIC: yes_request,
        State.SYS_NOT_LIKE_TOPIC: no_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_DO_YOU_LIKE_TOPIC, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_LIKE_TOPIC, State.USR_WHATS_YOUR_FAV, whats_your_fav_response)
simplified_dialogflow.set_error_successor(State.SYS_LIKE_TOPIC, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_WHATS_YOUR_FAV, State.SYS_FAV_OR_LETS_CHAT, check_fav_request)
simplified_dialogflow.set_error_successor(State.USR_WHATS_YOUR_FAV, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_NOT_LIKE_TOPIC, State.USR_TOP_FAVS, top_favs_response)
simplified_dialogflow.set_error_successor(State.SYS_NOT_LIKE_TOPIC, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_TOP_FAVS, State.SYS_FAV_OR_LETS_CHAT, check_fav_request)
simplified_dialogflow.set_error_successor(State.USR_TOP_FAVS, State.SYS_ERR)

#################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
