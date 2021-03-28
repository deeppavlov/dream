# %%
import json
import logging
import os
import random
import re

# from CoBotQA.cobotqa_service import send_cobotqa
from enum import Enum, auto

import sentry_sdk

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import dialogflows.scopes as scopes
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.utils import get_intents, is_yes, is_no


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


MUST_CONTINUE_CONFIDENCE = 0.98
CANNOT_CONTINUE_CONFIDENCE = 0.0

with open("music_data.json", "r") as f:
    MUSIC_DATA = json.load(f)

music_words_re = re.compile(
    r"(music)|(musics)|(song)|(rap)|(rock)|(melody)|(symphony)|(pop)|\
    (jazz)|(funk)|(blues)|(hip hop)|(folk)|(trance)|(reggae)|(artist)|(heavy metal)",
    re.IGNORECASE,
)
like_re = re.compile("what ((songs)|(music)|(song)|(artist)) do you ((like)|(listen))")
i_like_re = re.compile(r"I ((like)|(love)|(adore)|(listen to)|(prefer))", re.IGNORECASE)
what_listen_re = re.compile("what ((((should)|(can)|(may)) I listen)|(you suggest listening))")
# what_music = re.compile(r"(what should i|what do you suggest me to) (cook|make for dinner)"
#                        "( tonight| today| tomorrow){0,1}", re.IGNORECASE)


class State(Enum):
    USR_START = auto()
    #
    SYS_LETS_TALK_ABOUT = auto()
    USR_WHAT_MUSIC_LIKE = auto()
    SYS_OPINION = auto()
    USR_GUESS = auto()
    USR_WHAT_LIKE_ABOUT = auto()
    SYS_NOT_GUESSED = auto()
    SYS_GUESSED = auto()
    USR_NOT_GUESSED = auto()
    #
    SYS_LIKE = auto()
    USR_OPINION = auto()
    SYS_ASK_LIKE = auto()
    SYS_LIKE_ARTIST = auto()
    SYS_DONT_LIKE_ARTIST = auto()
    USR_WHY_NOT_LIKE = auto()
    SYS_ASK_LATEST = auto()
    SYS_NOT_HEARD = auto()
    SYS_HEARD = auto()
    USR_OK = auto()
    USR_ASK_LATEST = auto()
    USR_LISTEN_LATER = auto()
    #
    SYS_WHAT_LISTEN = auto()
    USR_SUGGEST = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
    SYS_END = auto()
    USR_END = auto()


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
    flag = True
    flag = flag and is_yes(state_utils.get_last_human_utterance(vars))
    logger.info(f"yes_request {flag}")
    return flag


##################################################################################################################
# no
##################################################################################################################


def no_request(ngrams, vars):
    flag = True
    flag = flag and is_no(state_utils.get_last_human_utterance(vars))
    logger.info(f"no_request {flag}")
    return flag


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
    return "Sorry"


##################################################################################################################
# let's talk about music
##################################################################################################################


def lets_talk_about_request(ngrams, vars):
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
        or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    )
    user_lets_chat_about_music = bool(music_words_re.search(state_utils.get_last_human_utterance(vars)["text"].lower()))
    flag = bool(user_lets_chat_about) and user_lets_chat_about_music
    logger.info(f"lets_talk_about_request {flag}")
    return flag


def what_like_request(ngrams, vars):
    flag = bool(like_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"what_like_request {flag}")
    return flag


def what_music_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Sure. Which music do you like?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def let_me_guess_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        genre = random.choice(list(MUSIC_DATA))
        artist = random.choice(list(MUSIC_DATA[genre]))
        return f'Ok. Let me guess your favorite artist. Is it "{artist}"?'
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def i_like_request(ngrams, vars):
    flag = bool(i_like_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"i_like_request {flag}")
    return flag


def what_like_about_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        return f"What do you like about it?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def i_give_up_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Ok. I give up. Who is it?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def i_like_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        genre = random.choice(list(MUSIC_DATA))
        artist = random.choice(list(MUSIC_DATA[genre]))
        return f"Well, I like {artist}, but I don't listen to them very often. Do you like {artist}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def heard_latest_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Have you been listening to it lately?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def why_dont_like_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        return "Ok. Why is that?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def listen_later_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        return "Well, I really like it. You can check it out later, after our talk."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def suggest_song_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        genre = random.choice(list(MUSIC_DATA))
        artist = random.choice(list(MUSIC_DATA[genre]))
        song = random.choice(MUSIC_DATA[genre][artist])
        return f'Well, i like "{artist}" and {genre} in general. Have you heard the song "{song}"'
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def cool_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        return "Cool, you seem to be really into it."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def end_request(ngrams, vars):
    flag = True
    logger.info(f"end_request {flag}")
    return flag


def end_response(vars):
    try:
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return ""
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


# def music_request(ngrams, vars):
#    logger.info("music_request True")
#    return True


# def music_fact_response(vars):
#     music_fact = ""
#     try:
#         for c in list(MUSIC_DATA.keys()):
#             if c in state_utils.get_last_human_utterance(vars)["text"].lower():
#                 music_fact = MUSIC_FACTS.get(c, "")
#         if not music_fact:
#             cuisine_fact = "Haven't tried it yet. What do you recommend to start with?"
#         return music_fact
#         state_utils.set_confidence(vars)
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)


# def what_fav_music_response(vars):
#     music_genres = ["rock", "pop", "hip hop", "jazz"]
#     try:
#         genre = random.choice(music_genres)
#
#         state_utils.set_confidence(vars)
#         state_utils.set_can_continue(vars)
#         return f"What is your favorite {genre} artist?"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)
#
#
# def fav_music_request(ngrams, vars):
#     logger.info("FAV_MUSIC_REQUEST IN")
#     user_fav_music = []
#     annotations = state_utils.get_last_human_utterance(vars)["annotations"]
#     nounphr = annotations.get("cobot_nounphrases", [])
#     for ne in nounphr:
#         user_fav_music.append(ne)
#     if user_fav_music:
#         return True
#     return False


# def music_fact_response(vars):
#     annotations = state_utils.get_last_human_utterance(vars)["annotations"]
#     # nounphr = annotations.get("cobot_nounphrases", [])
#     # fact = ""
#     # if nounphr:
#     #     fact = send_cobotqa(f"fact about {nounphr[0]}")
#     #     if "here" in fact.lower():
#     fact = annotations.get("odqa", {}).get("answer_sentence", "")
#     try:
#         state_utils.set_confidence(vars)
#         if not fact:
#             return "Never heard about it. Do you suggest listening to it?"
#         return f"I like it too. Did you know that {fact}"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)


##################################################################################################################
# what to listen
##################################################################################################################


def what_listen_request(ngrams, vars):
    flag = bool(what_listen_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"what_listen_request {flag}")
    return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_LETS_TALK_ABOUT: lets_talk_about_request,
        State.SYS_WHAT_LISTEN: what_listen_request,
        State.SYS_LIKE: what_like_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_LETS_TALK_ABOUT

simplified_dialogflow.add_system_transition(State.SYS_LETS_TALK_ABOUT, State.USR_WHAT_MUSIC_LIKE, what_music_response)
simplified_dialogflow.set_error_successor(State.SYS_LETS_TALK_ABOUT, State.SYS_ERR)

##################################################################################################################
#  USR_WHAT_MUSIC_LIKE

simplified_dialogflow.add_user_transition(
    State.USR_WHAT_MUSIC_LIKE,
    State.SYS_OPINION,
    i_like_request,
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_MUSIC_LIKE, State.SYS_ERR)

##################################################################################################################
#  USR_GUESS

simplified_dialogflow.add_user_serial_transitions(
    State.USR_GUESS, {State.SYS_NOT_GUESSED: no_request, State.SYS_GUESSED: yes_request}
)
simplified_dialogflow.set_error_successor(State.USR_GUESS, State.SYS_ERR)

##################################################################################################################
#  SYS_OPINION

simplified_dialogflow.add_system_transition(
    State.SYS_OPINION,
    State.USR_WHAT_LIKE_ABOUT,
    what_like_about_response,
)
simplified_dialogflow.set_error_successor(State.SYS_OPINION, State.SYS_ERR)

##################################################################################################################
# SYS_END, USR_END

simplified_dialogflow.add_user_transition(
    State.USR_WHAT_LIKE_ABOUT,
    State.SYS_END,
    end_request,
)
simplified_dialogflow.set_error_successor(State.SYS_END, State.SYS_ERR)

simplified_dialogflow.add_system_transition(
    State.SYS_END,
    State.USR_END,
    end_response,
)
simplified_dialogflow.set_error_successor(State.USR_END, State.SYS_ERR)

##################################################################################################################
#  SYS_NOT_GUESSED

simplified_dialogflow.add_system_transition(
    State.SYS_NOT_GUESSED,
    State.USR_NOT_GUESSED,
    i_give_up_response,
)
simplified_dialogflow.set_error_successor(State.SYS_NOT_GUESSED, State.SYS_ERR)

##################################################################################################################
#  SYS_GUESSED

simplified_dialogflow.add_system_transition(
    State.SYS_GUESSED,
    State.USR_WHAT_LIKE_ABOUT,
    what_like_about_response,
)
simplified_dialogflow.set_error_successor(State.SYS_NOT_GUESSED, State.SYS_ERR)

##################################################################################################################
#  USR_NOT_GUESSED

simplified_dialogflow.add_user_transition(
    State.USR_NOT_GUESSED,
    State.USR_WHAT_LIKE_ABOUT,
    what_like_about_response,
)
simplified_dialogflow.set_error_successor(State.USR_NOT_GUESSED, State.SYS_ERR)

##################################################################################################################
#  SYS_LIKE

simplified_dialogflow.add_system_transition(
    State.SYS_LIKE,
    State.USR_OPINION,
    i_like_response,
)
simplified_dialogflow.set_error_successor(State.SYS_LIKE, State.SYS_ERR)

##################################################################################################################
#  USR_OPINION

simplified_dialogflow.add_user_serial_transitions(
    State.USR_OPINION, {State.SYS_LIKE_ARTIST: yes_request, State.SYS_DONT_LIKE_ARTIST: no_request}
)
simplified_dialogflow.set_error_successor(State.USR_OPINION, State.SYS_ERR)

##################################################################################################################
#  SYS_LIKE

simplified_dialogflow.add_system_transition(
    State.SYS_LIKE_ARTIST,
    State.USR_ASK_LATEST,
    heard_latest_response,
)
simplified_dialogflow.set_error_successor(State.SYS_LIKE_ARTIST, State.SYS_ERR)

##################################################################################################################
#  SYS_DONT_LIKE_ARTIST

simplified_dialogflow.add_system_transition(
    State.SYS_DONT_LIKE_ARTIST,
    State.USR_WHY_NOT_LIKE,
    why_dont_like_response,
)
simplified_dialogflow.set_error_successor(State.SYS_DONT_LIKE_ARTIST, State.SYS_ERR)

##################################################################################################################
#  USR_ASK_LATEST

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_LATEST, {State.SYS_NOT_HEARD: no_request, State.SYS_HEARD: yes_request}
)
simplified_dialogflow.set_error_successor(State.USR_ASK_LATEST, State.SYS_ERR)

##################################################################################################################
#  SYS_NOT_HEARD

simplified_dialogflow.add_system_transition(State.SYS_NOT_HEARD, State.USR_LISTEN_LATER, listen_later_response)
simplified_dialogflow.set_error_successor(State.SYS_NOT_HEARD, State.SYS_ERR)

##################################################################################################################
#  SYS_HEARD

simplified_dialogflow.add_system_transition(State.SYS_HEARD, State.USR_OK, cool_response)
simplified_dialogflow.set_error_successor(State.SYS_HEARD, State.SYS_ERR)

##################################################################################################################
#  SYS_WHAT_LISTEN

simplified_dialogflow.add_system_transition(State.SYS_WHAT_LISTEN, State.USR_SUGGEST, suggest_song_response)

simplified_dialogflow.set_error_successor(State.SYS_WHAT_LISTEN, State.SYS_ERR)

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
