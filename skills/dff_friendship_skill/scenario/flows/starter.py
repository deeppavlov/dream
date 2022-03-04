import logging
import random
import os
import datetime
import json
import pytz
import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
from common.constants import CAN_CONTINUE_PROMPT, MUST_CONTINUE

# from common.greeting import HI_THIS_IS_ALEXA
from common.starter import (
    INTROS,
    OUTROS,
    CATEGORIES_VERBS,
    PERSONA1_GENRES,
    GENRES_ATTITUDES,
    GENRE_ITEMS,
    WEEKDAYS_ATTITUDES,
    WHATS_YOUR_FAV_PHRASES,
    WHY_QUESTIONS,
    ACKNOWLEDGEMENTS,
    MY_FAV_ANSWERS,
    WONDER_WHY_QUESTIONS,
    OH_PHRASES,
    SO_YOU_SAY_PHRASES,
    ASSENT_YES_PHRASES,
    ASSENT_NO_PHRASES,
)
from common.music import OPINION_REQUESTS_ABOUT_MUSIC

import dialogflows.scopes as scopes

# from dialogflows.flows import shared
from dialogflows.flows.starter_states import State

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

with open("common/topic_favorites.json", "r") as f:
    FAV_STORIES_TOPICS = json.load(f)

CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9


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
# scenario
##################################################################################################################


def genre_request(ngrams, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = greeting_type == "starter_genre"
    logger.info(f"genre_request {flag}")
    return flag


def weekday_request(ngrams, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = greeting_type == "starter_weekday"
    logger.info(f"weekday_request {flag}")
    return flag


def genre_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_categories = shared_memory.get("used_categories", [])
        # _object = ""
        category = random.choice(list(PERSONA1_GENRES))
        category_verb = CATEGORIES_VERBS.get(category, "")
        genre = random.choice(PERSONA1_GENRES.get(category, [""]))
        attitude = random.choice(GENRES_ATTITUDES.get(genre, [""]))
        item = random.choice(GENRE_ITEMS.get(genre, [""]))

        # if category in CATEGORIES_OBJECTS:
        #     _object = random.choice(CATEGORIES_OBJECTS[category])
        # item = FAV_STORIES_TOPICS.get(category, "").get("name", "")
        # if item:
        #     category_verb = CATEGORIES_VERBS.get(category, "")
        #     genre = shared.get_genre_top_wiki_parser(_object, item)[0]
        #     attitude = random.choice(GENRES_ATTITUDES.get(genre, [""]))
        #     state_utils.save_to_shared_memory(vars, used_categories=used_categories + [category])
        if all([category_verb, genre, attitude, item]):
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            state_utils.save_to_shared_memory(
                vars, used_categories=used_categories + [{"category": category, "genre": genre, "item": item}]
            )
            return (
                f"{random.choice(INTROS)} "
                + f"{category_verb} {item}. {attitude} {random.choice(OUTROS)} {genre} {category}?"
            )
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def positive_request(ngrams, vars):
    no_requests = condition_utils.no_requests(vars)
    sentiment = state_utils.get_human_sentiment(vars)
    flag = all([no_requests, sentiment == "positive", genre_request(ngrams, vars)])
    logger.info(f"positive_request {flag}")
    return flag


def negative_request(ngrams, vars):
    no_requests = condition_utils.no_requests(vars)
    sentiment = state_utils.get_human_sentiment(vars)
    flag = all([no_requests, sentiment == "negative", genre_request(ngrams, vars)])
    logger.info(f"negative_request {flag}")
    return flag


def neutral_request(ngrams, vars):
    no_requests = condition_utils.no_requests(vars)
    sentiment = state_utils.get_human_sentiment(vars)
    flag = all([no_requests, sentiment == "neutral", genre_request(ngrams, vars)])
    logger.info(f"neutral_request {flag}")
    return flag


def friday_request(ngrams, vars):
    flag = all([condition_utils.no_requests(vars), weekday_request(ngrams, vars)])
    logger.info(f"smth_request {flag}")
    return flag


def what_fav_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = shared_memory.get("used_categories", [])
        curr_topic = ""
        curr_genre = ""
        if used_topics:
            curr_topic = used_topics[-1].get("category", "")
            curr_genre = used_topics[-1].get("genre", "")
        if curr_topic:
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
            if curr_topic == "music":
                return random.choice(OPINION_REQUESTS_ABOUT_MUSIC)
            return f"{random.choice(WHATS_YOUR_FAV_PHRASES)} {curr_genre} {curr_topic}?"
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def why_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        return f"{random.choice(WHY_QUESTIONS)}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def my_fav_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_topics = shared_memory.get("used_categories", [])
        item = ""
        if used_topics:
            category = used_topics[-1].get("category", "")
            item = FAV_STORIES_TOPICS.get(category, "").get("name", "")
            if category not in ["series", "music"]:
                category += "s"
            if item:
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                return (
                    f"{random.choice(ACKNOWLEDGEMENTS)}"
                    + random.choice(MY_FAV_ANSWERS(category, item))
                    + f"{random.choice(WONDER_WHY_QUESTIONS)}"
                )
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def reason_request(ngrams, vars):
    flag = condition_utils.no_requests(vars)
    logger.info(f"reason_request {flag}")
    return flag


def repeat_response(vars):
    try:
        utt = state_utils.get_last_human_utterance(vars)["text"].lower()
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        return f"{random.choice(OH_PHRASES)} " + random.choice(SO_YOU_SAY_PHRASES(utt))
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def assent_yes_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        return random.choice(ASSENT_YES_PHRASES)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def assent_no_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        return random.choice(ASSENT_NO_PHRASES)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def my_fav_story_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_categories = shared_memory.get("used_categories", [])
        story = ""
        if used_categories:
            category = used_categories[-1].get("category", "")
            story = FAV_STORIES_TOPICS.get(category, "").get("story", "")
            if story:
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                return story
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def weekday_response(vars):
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = ""
    attitude = ""
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_categories = shared_memory.get("used_categories", [])
        category = "day"
        state_utils.save_to_shared_memory(vars, used_categories=used_categories + [category])
        weekday = weekdays[int(datetime.datetime.now(pytz.timezone("US/Mountain")).weekday()) - 1]
        attitude = WEEKDAYS_ATTITUDES.get(weekday, "")
        if weekday and attitude:
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            return f"Oh, Gosh, it's {weekday}! {attitude} What's your favorite day of the week?"
        else:
            state_utils.set_confidence(vars, 0)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def friday_response(vars):
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    friday_check = "friday" in utt
    weekday = ""
    try:
        if friday_check:
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            return "It's my favorite too!"
        else:
            for day in WEEKDAYS_ATTITUDES:
                if day in utt:
                    weekday = day
                    break
            if weekday:
                attitude = WEEKDAYS_ATTITUDES.get(weekday, "")
                if attitude:
                    state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
                    return f"Ah, interesting. I {attitude}. Why do you like it?"
            else:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
                return "Okay. But why?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def my_fav_day_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        return "Aha. Speaking of me, my favorite day is Friday. " "As the song says, Nothing matters like the weekend."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def smth_request(ngrams, vars):
    flag = condition_utils.no_requests(vars)
    logger.info(f"smth_request {flag}")
    return flag


def starter_request(ngrams, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = condition_utils.no_requests(vars) and (greeting_type in ["starter_genre", "starter_weekday"])
    logger.info(f"starter_request {flag}")
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
        # State.SYS_GENRE: genre_request,
        State.SYS_CHECK_POSITIVE: positive_request,
        State.SYS_CHECK_NEGATIVE: negative_request,
        State.SYS_CHECK_NEUTRAL: neutral_request,
        # State.SYS_WEEKDAY: weekday_request,
        State.SYS_FRIDAY: friday_request,
    },
)

##################################################################################################################
#  GENRE

# simplified_dialogflow.add_system_transition(State.SYS_GENRE, State.USR_GENRE, genre_response)
# simplified_dialogflow.set_error_successor(State.SYS_GENRE, State.SYS_ERR)


# simplified_dialogflow.add_user_serial_transitions(
#     State.USR_GENRE,
#     {
#         State.SYS_CHECK_POSITIVE: positive_request,
#         State.SYS_CHECK_NEGATIVE: negative_request,
#         State.SYS_CHECK_NEUTRAL: neutral_request
#     })
# simplified_dialogflow.set_error_successor(State.USR_GENRE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CHECK_POSITIVE, State.USR_WHAT_FAV, what_fav_response)
simplified_dialogflow.set_error_successor(State.SYS_CHECK_POSITIVE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CHECK_NEGATIVE, State.USR_WHY, why_response)
simplified_dialogflow.set_error_successor(State.SYS_CHECK_NEGATIVE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CHECK_NEUTRAL, State.USR_MY_FAV, my_fav_response)
simplified_dialogflow.set_error_successor(State.SYS_CHECK_NEUTRAL, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_WHY, State.SYS_GET_REASON, reason_request)
simplified_dialogflow.set_error_successor(State.USR_WHY, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_GET_REASON, State.USR_REPEAT, repeat_response)
simplified_dialogflow.set_error_successor(State.SYS_GET_REASON, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_REPEAT,
    {
        State.SYS_AGREED: yes_request,
        State.SYS_DISAGREED: no_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_REPEAT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_AGREED, State.USR_ASSENT_YES, assent_yes_response)
simplified_dialogflow.set_error_successor(State.SYS_AGREED, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_DISAGREED, State.USR_ASSENT_NO, assent_no_response)
simplified_dialogflow.set_error_successor(State.SYS_DISAGREED, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_MY_FAV,
    {
        State.SYS_YES: yes_request,
        State.SYS_NO: no_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_MY_FAV, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_YES, State.USR_MY_FAV_STORY, my_fav_story_response)
simplified_dialogflow.set_error_successor(State.SYS_YES, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_NO, State.USR_WHY, why_response)
simplified_dialogflow.set_error_successor(State.SYS_NO, State.SYS_ERR)


#################################################################################################################
#  WEEKDAY

# simplified_dialogflow.add_system_transition(State.SYS_WEEKDAY, State.USR_WEEKDAY, weekday_response)
# simplified_dialogflow.set_error_successor(State.SYS_WEEKDAY, State.SYS_ERR)


# simplified_dialogflow.add_user_transition(State.USR_WEEKDAY, State.SYS_FRIDAY, friday_request)
# simplified_dialogflow.set_error_successor(State.USR_WEEKDAY, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_FRIDAY, State.USR_FRIDAY, friday_response)
simplified_dialogflow.set_error_successor(State.SYS_FRIDAY, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_FRIDAY, State.SYS_SMTH, smth_request)
simplified_dialogflow.set_error_successor(State.USR_FRIDAY, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_SMTH, State.USR_MY_FAV_DAY, my_fav_day_response)
simplified_dialogflow.set_error_successor(State.SYS_SMTH, State.SYS_ERR)


#################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
