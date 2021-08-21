# %%
import json
import logging
import os
import random
import re

import sentry_sdk
from spacy import load

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils

# from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.utils import get_sentiment

# , get_intents
from common.bot_persona import YOUR_FAVORITE_COMPILED_PATTERN

import dialogflows.scopes as scopes
from dialogflows.flows import shared

# from dialogflows.flows.starter_states import State as StarterState
from dialogflows.flows.bot_persona_states import State as BS


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


spacy_nlp = load("en_core_web_sm")


with open("common/topic_favorites.json", "r") as f:
    FAV_STORIES_TOPICS = json.load(f)

CATEGORIES_OBJECTS = {
    "movie": ["actors"],
    "show": ["actors", "episodes"],
    "sport": ["athletes", "teams"],
    "team": ["athletes"],
    "music": ["singers", "songs", "albums"],
    "song": ["singers", "albums"],
    "singer": ["songs", "albums"],
    # "albums": ["songs", "singers"],
    # "athletes": ["teams"],
}

CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9


# %%

##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extension.DFEasyFilling(BS.USR_START)

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
    # user_lets_chat_about = (
    #     "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
    #     or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
    #     or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    # )
    flag = any(
        [
            any(["favorite" in utt, "favourite" in utt, "do you do on weekdays" in utt]),
            re.search(YOUR_FAVORITE_COMPILED_PATTERN, utt),
        ]
    )
    # and user_lets_chat_about
    logger.info(f"fav_or_lets_chat_request {flag}")
    return flag


def my_fav_story_response(vars):
    try:
        utt = state_utils.get_last_human_utterance(vars)["text"].lower()

        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = shared_memory.get("used_topics", [])
        name = ""
        story = ""
        question = ""
        response = ""
        for topic in FAV_STORIES_TOPICS:
            if topic in utt:
                name = FAV_STORIES_TOPICS.get(topic, "").get("name", "")
                story = FAV_STORIES_TOPICS.get(topic, "").get("story", "")
                question = FAV_STORIES_TOPICS.get(topic, "").get("question", "")
                if name and (topic not in used_topics):
                    if topic == "weekdays":
                        response = f"{story} {question}"
                    else:
                        response = f"My favorite {topic} is {name}. {story} {question}"
                    if topic == "book":
                        state_utils.set_confidence(vars, confidence=CONF_LOW)
                        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    elif topic == "music" and "what kind of music do you like" in utt:
                        state_utils.set_confidence(vars, confidence=CONF_HIGH)
                        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                    elif topic == "music":
                        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    elif (topic == "game") and ("to play with" in utt):
                        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                        return error_response(vars)
                    else:
                        state_utils.set_confidence(vars, confidence=CONF_HIGH)
                        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                    state_utils.save_to_shared_memory(vars, used_topics=used_topics + [topic])
                    return response
                else:
                    state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                    return error_response(vars)
        if not name and any(
            [("my" not in utt) and ("favorite" in utt), re.search(YOUR_FAVORITE_COMPILED_PATTERN, utt)]
        ):
            response = "Oh, I don't have one. What about you?"
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        else:
            response = "I've never heard about it. Could you please tell me more about it?"
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
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
        "negative" not in get_sentiment(annot_utt, probs=False)
    ):
        flag = True
    logger.info(f"check_fav_request {flag}")
    return flag


def why_fav_request(ngrams, vars):
    flag = False
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    if "why" in utt:
        flag = True
    logger.info(f"why_fav_request {flag}")
    return flag


def explain_fav_response(vars):
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    curr_topic = ""
    curr_item = ""
    _object = ""
    wp_top = []
    shared_memory = state_utils.get_shared_memory(vars)
    used_topics = list(set(shared_memory.get("used_topics", [])))
    if used_topics:
        curr_topic = used_topics[-1]
        curr_item = FAV_STORIES_TOPICS.get(curr_topic, "").get("name", "")
        if curr_topic in CATEGORIES_OBJECTS:
            _object = random.choice(CATEGORIES_OBJECTS[curr_topic])
    try:
        if utt == "why?":
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        elif ("why" in utt) and ("?" in utt):
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        else:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        if curr_topic in ["movie", "show"]:
            fake_utterance = f"I like to learn more about {curr_item} {_object} {curr_topic}"
            wp_top = shared.get_object_top_wiki_parser(curr_item, _object, curr_topic, fake_utterance)
        elif curr_topic == "sport":
            wp_top = shared.get_genre_top_wiki_parser(_object, curr_item)
        elif curr_topic == "team":
            fake_utterance = f"I like to learn more about {curr_item}"
            wp_top = shared.get_team_players_top_wiki_parser(curr_item, fake_utterance)
        elif curr_topic in ["music", "song", "singer"]:
            fake_utterance = f"I like to learn more about {curr_item} {_object} {curr_topic}"
            wp_top = shared.get_object_top_wiki_parser(curr_item, _object, curr_topic, fake_utterance)
        else:
            wp_top = []
        if wp_top:
            res = " ".join(wp_top)
            return f"I like its {_object}. {res} are my favorites. What do you think about them?"
        else:
            return "Hmm, I am just a fan of it!"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def do_you_like_topic_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = list(
            set(
                shared_memory.get("used_topics", [])
                + ["thing", "day", "book genre", "singer", "actor", "song", "color", "team", "all time favorite movie"]
            )
        )
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
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
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
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        return "What are your top three favorite things in the world?"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def smth_request(ngrams, vars):
    flag = condition_utils.no_requests(vars)
    logger.info(f"smth_request {flag}")
    return flag


# def starter_request(ngrams, vars):
#     flag = len(vars["agent"]["dialog"]["human_utterances"]) == 1
#     logger.info(f"starter_request {flag}")
#     return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START

# simplified_dialogflow.add_user_serial_transitions(
#     BS.USR_START,
#     {
#         (scopes.STARTER, StarterState.USR_START): starter_request,
#         BS.SYS_FAV_OR_LETS_CHAT: fav_or_lets_chat_request
#     })
simplified_dialogflow.add_user_transition(BS.USR_START, BS.SYS_FAV_OR_LETS_CHAT, fav_or_lets_chat_request)
simplified_dialogflow.set_error_successor(BS.USR_START, BS.SYS_ERR)

##################################################################################################################

simplified_dialogflow.add_system_transition(BS.SYS_FAV_OR_LETS_CHAT, BS.USR_MY_FAV_STORY, my_fav_story_response)
simplified_dialogflow.set_error_successor(BS.SYS_FAV_OR_LETS_CHAT, BS.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    BS.USR_MY_FAV_STORY,
    {BS.SYS_WHY_FAV: why_fav_request, BS.SYS_CHECK_FAV: check_fav_request},
)
simplified_dialogflow.set_error_successor(BS.USR_MY_FAV_STORY, BS.SYS_ERR)


simplified_dialogflow.add_system_transition(BS.SYS_WHY_FAV, BS.USR_EXPLAIN_FAV, explain_fav_response)
simplified_dialogflow.set_error_successor(BS.SYS_WHY_FAV, BS.SYS_ERR)


simplified_dialogflow.add_user_transition(BS.USR_EXPLAIN_FAV, BS.SYS_CHECK_FAV, smth_request)
simplified_dialogflow.set_error_successor(BS.USR_EXPLAIN_FAV, BS.SYS_ERR)


simplified_dialogflow.add_system_transition(BS.SYS_CHECK_FAV, BS.USR_DO_YOU_LIKE_TOPIC, do_you_like_topic_response)
simplified_dialogflow.set_error_successor(BS.SYS_CHECK_FAV, BS.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    BS.USR_DO_YOU_LIKE_TOPIC,
    {
        BS.SYS_LIKE_TOPIC: yes_request,
        BS.SYS_NOT_LIKE_TOPIC: no_request,
    },
)
simplified_dialogflow.set_error_successor(BS.USR_DO_YOU_LIKE_TOPIC, BS.SYS_ERR)


simplified_dialogflow.add_system_transition(BS.SYS_LIKE_TOPIC, BS.USR_WHATS_YOUR_FAV, whats_your_fav_response)
simplified_dialogflow.set_error_successor(BS.SYS_LIKE_TOPIC, BS.SYS_ERR)


simplified_dialogflow.add_user_transition(BS.USR_WHATS_YOUR_FAV, BS.SYS_FAV_OR_LETS_CHAT, check_fav_request)
simplified_dialogflow.set_error_successor(BS.USR_WHATS_YOUR_FAV, BS.SYS_ERR)


simplified_dialogflow.add_system_transition(BS.SYS_NOT_LIKE_TOPIC, BS.USR_TOP_FAVS, top_favs_response)
simplified_dialogflow.set_error_successor(BS.SYS_NOT_LIKE_TOPIC, BS.SYS_ERR)


simplified_dialogflow.add_user_transition(BS.USR_TOP_FAVS, BS.SYS_FAV_OR_LETS_CHAT, check_fav_request)
simplified_dialogflow.set_error_successor(BS.USR_TOP_FAVS, BS.SYS_ERR)

#################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    BS.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
