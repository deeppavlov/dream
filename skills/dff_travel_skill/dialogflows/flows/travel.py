# %%
import logging
import os
import re
import random
from copy import deepcopy
from enum import Enum, auto

import sentry_sdk

import dialogflows.scopes as scopes
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.condition as condition_utils
import common.dialogflow_framework.utils.state as state_utils

from CoBotQA.cobotqa_service import send_cobotqa, TRAVEL_FACTS
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.news import TOPIC_NEWS_OFFER
from common.travel import OPINION_REQUESTS_ABOUT_TRAVELLING, TRAVELLING_TEMPLATE, I_HAVE_BEEN_TEMPLATE, \
    WHY_DONT_USER_LIKES_TRAVELLING_RESPONSES, USER_IMPRESSIONS_REQUEST, \
    WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS, ACKNOWLEDGE_USER_WILL_VISIT_LOC, QUESTIONS_ABOUT_LOCATION, \
    ACKNOWLEDGE_USER_DO_NOT_WANT_TO_VISIT_LOC, OFFER_FACT_RESPONSES, OPINION_REQUESTS, HAVE_YOU_BEEN_TEMPLATE, \
    ACKNOWLEDGE_USER_DISLIKE_LOC, OFFER_MORE_FACT_RESPONSES, HAVE_YOU_BEEN_IN_PHRASES, \
    QUESTIONS_ABOUT_BOT_LOCATIONS, WHY_BOT_LIKES_TO_TRAVEL, I_HAVE_BEEN_IN_AND_LIKED_MOST
from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_intents, get_sentiment, get_not_used_template, get_named_locations, \
    get_all_not_used_templates

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)

SUPER_CONFIDENCE = 1.
HIGH_CONFIDENCE = 0.99
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.


class State(Enum):
    USR_START = auto()

    SYS_HAVE_BOT_BEEN = auto()
    SYS_LOC_DETECTED = auto()
    USR_HAVE_BEEN = auto()

    SYS_USR_HAVE_BEEN = auto()

    SYS_LETS_CHAT_ABOUT_TRAVELLING = auto()
    USR_OPINION_TRAVELLING = auto()

    SYS_USR_DISLIKE_MENTIONED_BY_USER_LOC = auto()
    SYS_NOT_WANT_FACT_ABOUT_LOC = auto()
    SYS_GET_FACT_ABOUT_LOC = auto()
    USR_WHAT_LOC_NOT_CONF = auto()

    SYS_USR_LIKE_MENTIONED_BY_USER_LOC = auto()
    USR_WHAT_BEST_MENTIONED_BY_USER_LOC = auto()

    USR_DISLIKE_AND_WHAT_LOC_NOT_CONF = auto()

    SYS_NO_DIALOG_BREAKDOWN_REQUEST = auto()

    SYS_USR_HAVE_NOT_BEEN = auto()
    USR_WOULD_LIKE_VISIT_LOC = auto()

    SYS_WOULD_VISIT_LOC = auto()
    USR_WISH_WOULD_VISIT_LOC = auto()

    SYS_WOULD_NOT_VISIT_LOC = auto()
    USR_ACK_NOT_VISIT_LOC_WHAT_LOC = auto()

    SYS_USR_RESP_ABOUT_WISHES = auto()
    USR_OFFER_FACT_ABOUT_LOC = auto()

    SYS_WANT_FACT_ABOUT_LOC = auto()
    USR_SHARE_FACT_ABOUT_LOC = auto()

    SYS_LIKE_TRAVELLING = auto()
    USR_WHAT_LOC_CONF = auto()

    SYS_DISLIKE_TRAVELLING = auto()
    USR_NOT_TRAVELLING_PREF = auto()

    SYS_WHY_NOT_LIKE_TRAVELLING = auto()
    USR_ASK_ABOUT_ORIGIN = auto()

    SYS_BEST_MENTIONED_BY_USER_LOC = auto()
    SYS_MENTIONED_TRAVELLING = auto()

    SYS_LOC_NOT_DETECTED = auto()

    SYS_ERR = auto()


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
# utils
##################################################################################################################
# ....


##################################################################################################################
# general requests
##################################################################################################################

def choose_conf_decreasing_if_requests_in_human_uttr(vars, CONF_1, CONF_2):
    no_db = condition_utils.no_requests(vars)
    if no_db:
        return CONF_1
    else:
        return CONF_2


def get_mentioned_locations(vars):
    user_mentioned_locations = get_named_locations(vars["agent"]["dialog"]["human_utterances"][-1])

    return user_mentioned_locations


def yes_request(ngrams, vars):
    # SYS_YES_REQUEST
    flag = True
    flag = flag and condition_utils.is_yes_vars(vars)
    return flag


def no_request(ngrams, vars):
    # SYS_NO_REQUEST
    flag = True
    flag = flag and condition_utils.is_no_vars(vars)
    return flag


def no_requests_request(ngrams, vars):
    # SYS_NO_DIALOG_BREAKDOWN_AND_NO_QUESTIONS_REQUEST
    flag = condition_utils.no_special_switch_off_requests(vars)

    if flag:
        logger.info(f"No dialog breakdown or request intents in user utterances")
        return True
    logger.info(f"Dialog breakdown and request intents in user utterances")
    return False


def positive_sentiment_request(ngrams, vars):
    # SYS_POSITIVE_SENTIMENT_REQUEST
    is_positive = "positive" in get_sentiment(state_utils.get_last_human_utterance(vars),
                                              probs=False, default_labels=["neutral"])
    return is_positive


def negative_sentiment_request(ngrams, vars):
    # SYS_NEGATIVE_SENTIMENT_REQUEST
    is_negative = "negative" in get_sentiment(state_utils.get_last_human_utterance(vars),
                                              probs=False, default_labels=["neutral"])
    return is_negative


##################################################################################################################
# let's talk about travelling
##################################################################################################################

def mentioned_travelling_request(ngrams, vars):
    # SYS_MENTIONED_TRAVELLING
    if TRAVELLING_TEMPLATE.search(state_utils.get_last_human_utterance(vars)):
        logger.info(f"Mentioned travelling in user utterances")
        return True
    return False


def lets_chat_about_travelling_request(ngrams, vars):
    # SYS_LETS_CHAT_ABOUT_TRAVELLING
    # this check will also catch linkto questions about travelling
    user_lets_chat_about_travelling = if_chat_about_particular_topic(
        state_utils.get_last_human_utterance(vars),
        state_utils.get_last_bot_utterance(vars),
        compiled_pattern=TRAVELLING_TEMPLATE)

    if user_lets_chat_about_travelling:
        logger.info(f"Let's chat about travelling in user utterances")
        return True
    return False


def lets_chat_about_travelling_response(vars):
    # USR_OPINION_TRAVELLING
    logger.info(f"Bot asks user's opinion about travelling.")
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_questions = shared_memory.get("used_opinion_request_about_travelling", [])

        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        opinion_req_travelling = random.choice(OPINION_REQUESTS_ABOUT_TRAVELLING)
        state_utils.save_to_shared_memory(
            vars, used_opinion_request_about_travelling=used_questions + [opinion_req_travelling])
        return opinion_req_travelling
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# like and not like travelling scenario
##################################################################################################################

def like_about_travelling_request(ngrams, vars):
    # SYS_LIKE_TRAVELLING
    linkto_opinion_about_travelling = any([
        req.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
        for req in OPINION_REQUESTS_ABOUT_TRAVELLING])
    user_agrees = yes_request(ngrams, vars)
    user_positive = positive_sentiment_request(ngrams, vars)

    if linkto_opinion_about_travelling and (user_agrees or user_positive):
        logger.info(f"User likes travelling in user utterances")
        return True
    return False


def dislike_about_travelling_request(ngrams, vars):
    # SYS_DISLIKE_TRAVELLING
    linkto_opinion_about_travelling = any([
        req.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
        for req in OPINION_REQUESTS_ABOUT_TRAVELLING])
    user_agrees = no_request(ngrams, vars)
    user_positive = negative_sentiment_request(ngrams, vars)

    if linkto_opinion_about_travelling and (user_agrees or user_positive):
        logger.info(f"User dislike travelling in user utterances")
        return True
    return False


def not_like_travelling_response(vars):
    # USR_NOT_TRAVELLING_PREF
    logger.info(f"Bot asks why user does not like travelling.")
    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)

        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        return random.choice(WHY_DONT_USER_LIKES_TRAVELLING_RESPONSES)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def linkto_personal_info_response(vars):
    # USR_ASK_ABOUT_ORIGIN
    responses = ["Okay. Where are from?",
                 "Then let's talk about you. Where are you from?"
                 ]
    logger.info(f"Bot asks user about his/her origin/home town.")
    try:
        state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        return random.choice(responses)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# user mentions named entity of type LOC
##################################################################################################################


def user_mention_named_entity_loc_request(ngrams, vars):
    # SYS_LOC_DETECTED
    user_mentioned_locations = get_mentioned_locations(vars)
    weather_forecast = "weather_forecast_intent" in get_intents(state_utils.get_last_human_utterance(vars),
                                                                which="intent_catcher")
    prev_active_skill = state_utils.get_last_bot_utterance(vars).get("active_skill", "")
    if weather_forecast or prev_active_skill == "weather_skill":
        logger.info(f"Found mentioned named locations in user utterances BUT it's about weather. Don't respond.")
        return False

    if len(user_mentioned_locations) > 0:
        logger.info(f"Found mentioned named locations in user utterances")
        return True
    return False


def user_not_mention_named_entity_loc_request(ngrams, vars):
    # SYS_LOC_NOT_DETECTED
    asked_for_loc = any([question in state_utils.get_last_bot_utterance(vars).get("text", "")
                         for question in QUESTIONS_ABOUT_LOCATION])
    user_mentioned_locations = get_mentioned_locations(vars)
    weather_forecast = "weather_forecast_intent" in get_intents(state_utils.get_last_human_utterance(vars),
                                                                which="intent_catcher")
    prev_active_skill = state_utils.get_last_bot_utterance(vars).get("active_skill", "")
    if weather_forecast or prev_active_skill == "weather_skill":
        logger.info(f"Not found mentioned named locations in user utterances BUT it's about weather. Don't respond.")
        return False

    if asked_for_loc and len(user_mentioned_locations) == 0:
        logger.info(f"Not found mentioned named locations in user utterances")
        return True
    return False

##################################################################################################################
# user asks if bot have been in LOC
##################################################################################################################


def have_bot_been_in(vars):
    user_asks_have_you_been = re.search(HAVE_YOU_BEEN_TEMPLATE,
                                        state_utils.get_last_human_utterance(vars)["text"])
    user_mentioned_locations = get_mentioned_locations(vars)

    if user_asks_have_you_been and len(user_mentioned_locations) > 0:
        return True
    return False


def have_bot_been_in_request(ngrams, vars):
    # SYS_HAVE_BOT_BEEN
    if have_bot_been_in(vars):
        logger.info(f"User asks if bot have been in LOC in user utterances")
        return True
    return False


def have_bot_been_in_response(vars):
    # USR_HAVE_BEEN
    try:
        user_mentioned_locations = get_mentioned_locations(vars)

        if len(user_mentioned_locations):
            location = f"in {user_mentioned_locations[-1]}"
            collect_and_save_facts_about_location(location, vars)
            shared_memory = state_utils.get_shared_memory(vars)
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=user_mentioned_locations[-1])
            state_utils.save_to_shared_memory(
                vars, discussed_locations=discussed_locations + [user_mentioned_locations[-1]])
            collect_and_save_facts_about_location(user_mentioned_locations[-1], vars)
        else:
            location = "there"
        logger.info(f"Bot responses that bot has not been in LOC: {location}.")

        if have_bot_been_in(vars):
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        else:
            confidence = DEFAULT_CONFIDENCE
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return random.choice(HAVE_YOU_BEEN_IN_PHRASES).replace("LOCATION", location)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# user have been in LOC
##################################################################################################################

def _user_have_been_in_request(vars):
    bot_asks_have_you_been_and_user_agrees = re.search(
        HAVE_YOU_BEEN_TEMPLATE,
        state_utils.get_last_bot_utterance(vars).get("text", "")) and condition_utils.is_yes_vars(vars)
    user_says_been_in = re.search(
        I_HAVE_BEEN_TEMPLATE, state_utils.get_last_human_utterance(vars).get("text", ""))

    user_mentioned_locations = get_mentioned_locations(vars)
    bot_asked_about_location = any([req.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
                                    for req in QUESTIONS_ABOUT_LOCATION])

    if bot_asks_have_you_been_and_user_agrees or user_says_been_in or (
            bot_asked_about_location and len(user_mentioned_locations) > 0):
        return True
    return False


def user_have_been_in_request(ngrams, vars):
    # SYS_USR_HAVE_BEEN
    if _user_have_been_in_request(vars):
        logger.info(f"User says he/she was in LOC in user utterances")
        return True
    return False


def user_have_been_in_response(vars):
    # USR_WHAT_BEST_MENTIONED_BY_USER_LOC
    try:
        user_mentioned_locations = get_mentioned_locations(vars)
        if len(user_mentioned_locations) > 0:
            location = user_mentioned_locations[-1]
            collect_and_save_facts_about_location(location, vars)
        else:
            location = "there"
        shared_memory = state_utils.get_shared_memory(vars)
        logger.info(f"Bot acknowledges that user liked LOC and asks about best about LOC: {location}.")

        if condition_utils.is_yes_vars(vars):
            confidence = SUPER_CONFIDENCE
        else:
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])

        used_user_impressions_requests = shared_memory.get("used_user_impressions_requests", [])
        user_impressions_request = get_not_used_template(used_user_impressions_requests, USER_IMPRESSIONS_REQUEST)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_user_impressions_requests + [user_impressions_request])

        used_what_do_i_love = shared_memory.get("used_what_do_i_love", [])
        what_do_i_love = get_not_used_template(used_what_do_i_love, I_HAVE_BEEN_IN_AND_LIKED_MOST)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_what_do_i_love + [what_do_i_love])

        response = user_impressions_request.replace("WHAT_DO_I_LOVE", what_do_i_love)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def user_no_or_disliked_request(ngrams, vars):
    # SYS_USR_DISLIKE_MENTIONED_BY_USER_LOC
    # on this request we will answer with new question about other locations
    flag = no_request(ngrams, vars) or negative_sentiment_request(ngrams, vars)
    if flag:
        logger.info(f"User disagrees or have negative sentiment in user utterances")
        return True
    return False


def user_disliked_mentioned_by_user_loc_response(vars):
    # USR_DISLIKE_AND_WHAT_LOC_NOT_CONF
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_questions_about_location = shared_memory.get("used_questions_about_location", [])
        logger.info(f"Bot acknowledges user dislike loc and asks a question about some other LOC.")

        if condition_utils.is_no_vars(vars):
            confidence = SUPER_CONFIDENCE
        else:
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_questions_about_location + [question_about_location])
        return f"{random.choice(ACKNOWLEDGE_USER_DISLIKE_LOC)} {question_about_location}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# user have NOT been in LOC
##################################################################################################################

I_HAVE_NOT_BEEN_TEMPLATE = re.compile(r"(i|we|me) (have|did|was|had|were) (not|never) (been (in|on|there)|visit)",
                                      re.IGNORECASE)


def user_have_not_been_in_request(ngrams, vars):
    # SYS_USR_HAVE_NOT_BEEN
    bot_asks_have_you_been_and_user_disagrees = re.search(
        HAVE_YOU_BEEN_TEMPLATE,
        state_utils.get_last_bot_utterance(vars).get("text", "")) and condition_utils.is_no_vars(vars)
    user_says_not_been_in = re.search(
        I_HAVE_NOT_BEEN_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])

    if bot_asks_have_you_been_and_user_disagrees or user_says_not_been_in:
        logger.info(f"User says he/she has not been in LOC in user utterances")
        return True
    return False


def user_have_not_been_in_response(vars):
    # USR_WOULD_LIKE_VISIT_LOC
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        location = shared_memory.get("discussed_location", "")
        collect_and_save_facts_about_location(location, vars)
        logger.info(f"Bot asks if user wants to visit non-visited LOC: {location}.")

        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])
        return random.choice(WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


# if user answers he/she would like to visit location
def user_would_like_to_visit_response(vars):
    # USR_WISH_WOULD_VISIT_LOC
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        location = shared_memory.get("discussed_location", "")
        collect_and_save_facts_about_location(location, vars)
        logger.info(f"Bot acknowledges that user would liked to visit LOC: {location}. Wish he/she will do.")

        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])
        return random.choice(ACKNOWLEDGE_USER_WILL_VISIT_LOC)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


# if user answers he/she would NOT like to visit location
def user_would_not_like_to_visit_response(vars):
    # USR_ACK_NOT_VISIT_LOC_WHAT_LOC
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        location = shared_memory.get("discussed_location", "")
        used_questions_about_location = shared_memory.get("used_questions_about_location", [])
        logger.info(f"Bot acknowledges that user would not like to visit LOC: {location}, asks question about LOC.")

        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        if len(location) > 0:
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_questions_about_location + [question_about_location])
        return f"{random.choice(ACKNOWLEDGE_USER_DO_NOT_WANT_TO_VISIT_LOC)} {question_about_location}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# ask question about travelling
##################################################################################################################

def like_travelling_acknowledgement(vars):
    response = ""
    was_asked = any([phrase in state_utils.get_last_bot_utterance(vars).get("text", "")
                     for phrase in OPINION_REQUESTS_ABOUT_TRAVELLING])
    user_agrees = condition_utils.is_yes_vars(vars)
    user_positive = "positive" in get_sentiment(state_utils.get_last_human_utterance(vars),
                                                probs=False, default_labels=["neutral"])
    if was_asked and (user_agrees or user_positive):
        response = random.choice(WHY_BOT_LIKES_TO_TRAVEL)
    return response


def confident_ask_question_about_travelling_response(vars):
    # USR_WHAT_LOC_CONF
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_questions_about_location = shared_memory.get("used_questions_about_location", [])
        logger.info(f"Bot confidently asks a question about some LOC.")

        # socialbot's opinion about travelling, if we previously asked user, and user likes travelling
        bot_likes_travel = like_travelling_acknowledgement(vars)
        confidence = SUPER_CONFIDENCE
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_questions_about_location + [question_about_location])
        return f"{bot_likes_travel} {question_about_location}".strip()
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def not_confident_ask_question_about_travelling_response(vars):
    # USR_WHAT_LOC_NOT_CONF
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_questions_about_location = shared_memory.get("used_questions_about_location", [])
        logger.info(f"Bot not confidently asks a question about some LOC.")

        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_questions_about_location + [question_about_location])
        return question_about_location
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# offering fact about loc
##################################################################################################################

def collect_and_save_facts_about_location(location, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    facts_about_location = shared_memory.get("facts_about_discussed_location", {})

    if facts_about_location.get("location", "") == location and facts_about_location.get(
            "facts", []) and location != "there":
        facts_about_location = facts_about_location.get("facts", [])
    elif location.lower() in TRAVEL_FACTS:
        facts_about_location = deepcopy(TRAVEL_FACTS[location.lower()])
    else:
        facts_about_location = state_utils.get_fact_for_particular_entity_from_human_utterance(vars, location)
        facts_about_location = [fact for fact in facts_about_location if "is a city" not in fact.lower()]

    if len(location) > 0 and len(facts_about_location) == 0 and location != "there":
        facts_about_location = [send_cobotqa(f"fact about {location}")]
        facts_about_location = [fact for fact in facts_about_location if "is a city" not in fact.lower()]

    used_facts = shared_memory.get("used_facts", [])
    facts_about_location = get_all_not_used_templates(used_facts, facts_about_location)
    facts_about_location = [fact for fact in facts_about_location if len(fact)]

    if len(facts_about_location):
        state_utils.save_to_shared_memory(
            vars, facts_about_discussed_location={"location": location, "facts": facts_about_location})
    return facts_about_location


def is_fact_about_loc_available_request(ngrams, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    facts_about_location = collect_and_save_facts_about_location(location, vars)
    if len(location) and len(facts_about_location) > 0:
        logger.info(f"Bot has available facts about LOC: {location}.")
        return True
    return False


def offer_fact_about_loc_response(vars):
    # USR_OFFER_FACT_ABOUT_LOC
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        location = shared_memory.get("discussed_location", "")
        logger.info(f"Bot offers fact about LOC: {location}.")
        facts_about_location = collect_and_save_facts_about_location(location, vars)

        if len(location) and len(facts_about_location) > 0 and location != "there":
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
            state_utils.set_confidence(vars, confidence)
            if confidence == SUPER_CONFIDENCE:
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])
            prev_prev_bot_uttr = vars["agent"]["dialog"]["bot_utterances"][-2]["text"] if len(
                vars["agent"]["dialog"]["bot_utterances"]) >= 2 else ""
            if shared_memory.get("used_facts", []) and any([t in prev_prev_bot_uttr for t in OFFER_FACT_RESPONSES]):
                # previously were fact. So offer "more" facts
                return random.choice(OFFER_MORE_FACT_RESPONSES).replace("LOCATION", location)
            else:
                return random.choice(OFFER_FACT_RESPONSES).replace("LOCATION", location)
        else:
            if location and location != "there":
                # we are doing that only to check that we have such news, continuation is up to news-api-skill
                news_about_loc = state_utils.get_news_about_particular_entity_from_human_utterance(vars, location)
                if news_about_loc:
                    confidence = choose_conf_decreasing_if_requests_in_human_uttr(
                        vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
                    state_utils.set_confidence(vars, confidence)
                    if confidence == SUPER_CONFIDENCE:
                        state_utils.set_can_continue(vars, MUST_CONTINUE)
                    else:
                        state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
                    return f"{random.choice(TOPIC_NEWS_OFFER)} {location}?"

            another_location_question = not_confident_ask_question_about_travelling_response(vars)
            return f"Okay. Cool. Let's move on. {another_location_question}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def share_fact_about_loc_response(vars):
    # USR_SHARE_FACT_ABOUT_LOC

    try:
        shared_memory = state_utils.get_shared_memory(vars)
        location = shared_memory.get("discussed_location", "")
        facts_about_location = collect_and_save_facts_about_location(location, vars)
        used_opinion_requests = shared_memory.get("used_opinion_requests", [])
        logger.info(f"Bot shares fact about LOC: {location}.")

        if len(location) and len(facts_about_location) > 0 and location != "there":
            opinion_req = random.choice(OPINION_REQUESTS)
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
            state_utils.set_confidence(vars, confidence)
            if confidence == SUPER_CONFIDENCE:
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [location])
            state_utils.save_to_shared_memory(vars, used_opinion_requests=used_opinion_requests + [opinion_req])

            used_facts = shared_memory.get("used_facts", [])
            fact_about_location = get_not_used_template(used_facts, facts_about_location)
            state_utils.save_to_shared_memory(vars, used_facts=used_facts + [fact_about_location])
            if fact_about_location[-1] != ".":
                fact_about_location += "."
            return f"{fact_about_location} {opinion_req}"
        else:
            another_location_question = not_confident_ask_question_about_travelling_response(vars)
            return f"Okay. Cool. Let's move on. {another_location_question}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def requested_but_not_found_loc_response(vars):
    # USR_WHAT_LOC_NOT_CONF
    logger.info(f"Bot acknowledges that bot had asked question but user didn't give LOC. "
                f"Bot not confidently asks a question about some LOC.")
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        discussed_locations = list(set(shared_memory.get("discussed_locations", [])))
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_PROMPT)
        city_to_discuss = get_not_used_template(discussed_locations,
                                                [city.lower() for city in QUESTIONS_ABOUT_BOT_LOCATIONS.keys()])
        state_utils.save_to_shared_memory(vars, discussed_location=city_to_discuss)
        state_utils.save_to_shared_memory(vars, discussed_locations=discussed_locations + [city_to_discuss])
        return QUESTIONS_ABOUT_BOT_LOCATIONS[city_to_discuss.capitalize()]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, ZERO_CONFIDENCE)
    return "Sorry"


##################################################################################################################
#  START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_HAVE_BOT_BEEN: have_bot_been_in_request,
        State.SYS_USR_HAVE_NOT_BEEN: user_have_not_been_in_request,
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request,
        State.SYS_LIKE_TRAVELLING: like_about_travelling_request,
        State.SYS_LETS_CHAT_ABOUT_TRAVELLING: lets_chat_about_travelling_request,
        State.SYS_DISLIKE_TRAVELLING: dislike_about_travelling_request,
        State.SYS_MENTIONED_TRAVELLING: mentioned_travelling_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_HAVE_BOT_BEEN
simplified_dialogflow.add_system_transition(State.SYS_HAVE_BOT_BEEN, State.USR_HAVE_BEEN,
                                            have_bot_been_in_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_HAVE_BEEN,
    {
        State.SYS_USR_HAVE_BEEN: yes_request,
        State.SYS_USR_HAVE_NOT_BEEN: no_request,
        State.SYS_BEST_MENTIONED_BY_USER_LOC: no_requests_request,  # offer_fact_about_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_HAVE_BEEN, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_HAVE_BEEN

# let's try not to ask opinion about location but move forward to what did he like most about this place
simplified_dialogflow.add_system_transition(State.SYS_USR_HAVE_BEEN, State.USR_WHAT_BEST_MENTIONED_BY_USER_LOC,
                                            user_have_been_in_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_BEST_MENTIONED_BY_USER_LOC,
    {
        State.SYS_BEST_MENTIONED_BY_USER_LOC: no_requests_request,  # offer_fact_about_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_BEST_MENTIONED_BY_USER_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_DISLIKE_MENTIONED_BY_USER_LOC
simplified_dialogflow.add_system_transition(State.SYS_USR_DISLIKE_MENTIONED_BY_USER_LOC,
                                            State.USR_DISLIKE_AND_WHAT_LOC_NOT_CONF,
                                            user_disliked_mentioned_by_user_loc_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_DISLIKE_AND_WHAT_LOC_NOT_CONF,
    {
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request,
        State.SYS_LOC_NOT_DETECTED: user_not_mention_named_entity_loc_request  # requested_but_not_found_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_DISLIKE_AND_WHAT_LOC_NOT_CONF, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_LOC_NOT_CONF,
    {
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request,
        State.SYS_LOC_NOT_DETECTED: user_not_mention_named_entity_loc_request  # requested_but_not_found_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_LOC_NOT_CONF, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_HAVE_NOT_BEEN
simplified_dialogflow.add_system_transition(State.SYS_USR_HAVE_NOT_BEEN, State.USR_WOULD_LIKE_VISIT_LOC,
                                            user_have_not_been_in_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WOULD_LIKE_VISIT_LOC,
    {
        State.SYS_WOULD_VISIT_LOC: yes_request,
        State.SYS_WOULD_NOT_VISIT_LOC: no_request,
        State.SYS_BEST_MENTIONED_BY_USER_LOC: no_requests_request,  # offer_fact_about_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_WOULD_LIKE_VISIT_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_WOULD_VISIT_LOC
simplified_dialogflow.add_system_transition(State.SYS_WOULD_VISIT_LOC, State.USR_WISH_WOULD_VISIT_LOC,
                                            user_would_like_to_visit_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WISH_WOULD_VISIT_LOC,
    {
        State.SYS_USR_RESP_ABOUT_WISHES: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WISH_WOULD_VISIT_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_RESP_ABOUT_WISHES
simplified_dialogflow.add_system_transition(State.SYS_USR_RESP_ABOUT_WISHES, State.USR_OFFER_FACT_ABOUT_LOC,
                                            offer_fact_about_loc_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_OFFER_FACT_ABOUT_LOC,
    {
        State.SYS_WANT_FACT_ABOUT_LOC: yes_request,
        State.SYS_NOT_WANT_FACT_ABOUT_LOC: no_request,
        State.SYS_GET_FACT_ABOUT_LOC: no_requests_request,  # not_confident_ask_question_about_travelling_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_OFFER_FACT_ABOUT_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_WOULD_NOT_VISIT_LOC
simplified_dialogflow.add_system_transition(State.SYS_WOULD_NOT_VISIT_LOC, State.USR_ACK_NOT_VISIT_LOC_WHAT_LOC,
                                            user_would_not_like_to_visit_response)
# there are no user serial transitions because we asked about other location to discuss

##################################################################################################################
#  SYS_BEST_MENTIONED_BY_USER_LOC
simplified_dialogflow.add_system_transition(State.SYS_BEST_MENTIONED_BY_USER_LOC, State.USR_OFFER_FACT_ABOUT_LOC,
                                            offer_fact_about_loc_response)
# there are no user serial transitions because we have this above

##################################################################################################################
#  SYS_WANT_FACT_ABOUT_LOC
simplified_dialogflow.add_system_transition(State.SYS_WANT_FACT_ABOUT_LOC, State.USR_SHARE_FACT_ABOUT_LOC,
                                            share_fact_about_loc_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_SHARE_FACT_ABOUT_LOC,
    {
        State.SYS_USR_RESP_ABOUT_WISHES: is_fact_about_loc_available_request,
        State.SYS_GET_FACT_ABOUT_LOC: no_requests_request,  # not_confident_ask_question_about_travelling_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_SHARE_FACT_ABOUT_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_NOT_WANT_FACT_ABOUT_LOC
simplified_dialogflow.add_system_transition(State.SYS_NOT_WANT_FACT_ABOUT_LOC, State.USR_WHAT_LOC_NOT_CONF,
                                            not_confident_ask_question_about_travelling_response)
# there are no user serial transitions because we asked about other location to discuss

##################################################################################################################
#  SYS_GET_FACT_ABOUT_LOC
simplified_dialogflow.add_system_transition(State.SYS_GET_FACT_ABOUT_LOC, State.USR_WHAT_LOC_NOT_CONF,
                                            not_confident_ask_question_about_travelling_response)
# there are no user serial transitions because we asked about other location to discuss

##################################################################################################################
#  SYS_LOC_DETECTED
simplified_dialogflow.add_system_transition(State.SYS_LOC_DETECTED, State.USR_HAVE_BEEN,
                                            have_bot_been_in_response)
# there are no serial transitions because we have USR_HAVE_BEEN in another thread

##################################################################################################################
#  SYS_MENTIONED_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_MENTIONED_TRAVELLING, State.USR_WHAT_LOC_NOT_CONF,
                                            not_confident_ask_question_about_travelling_response)
# there are no user serial transitions because we asked about other location to discuss

##################################################################################################################
#  SYS_LETS_CHAT_ABOUT_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_LETS_CHAT_ABOUT_TRAVELLING, State.USR_OPINION_TRAVELLING,
                                            lets_chat_about_travelling_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_OPINION_TRAVELLING,
    {
        State.SYS_LIKE_TRAVELLING: like_about_travelling_request,
        State.SYS_DISLIKE_TRAVELLING: dislike_about_travelling_request,
        State.SYS_GET_FACT_ABOUT_LOC: no_requests_request,  # not_confident_ask_question_about_travelling_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_OPINION_TRAVELLING, State.SYS_ERR)

##################################################################################################################
#  SYS_LIKE_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_LIKE_TRAVELLING, State.USR_WHAT_LOC_CONF,
                                            confident_ask_question_about_travelling_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_LOC_CONF,
    {
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request,
        State.SYS_LOC_NOT_DETECTED: user_not_mention_named_entity_loc_request  # requested_but_not_found_loc_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_LOC_CONF, State.SYS_ERR)

##################################################################################################################
#  SYS_DISLIKE_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_DISLIKE_TRAVELLING, State.USR_NOT_TRAVELLING_PREF,
                                            not_like_travelling_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_NOT_TRAVELLING_PREF,
    {
        State.SYS_WHY_NOT_LIKE_TRAVELLING: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_NOT_TRAVELLING_PREF, State.SYS_ERR)

##################################################################################################################
#  SYS_WHY_NOT_LIKE_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_WHY_NOT_LIKE_TRAVELLING, State.USR_ASK_ABOUT_ORIGIN,
                                            linkto_personal_info_response)
# there are no serial transitions because we have USR_ASK_ABOUT_ORIGIN in another thread

##################################################################################################################
#  SYS_LOC_NOT_DETECTED
simplified_dialogflow.add_system_transition(State.SYS_LOC_NOT_DETECTED, State.USR_HAVE_BEEN,
                                            requested_but_not_found_loc_response)
# there are no serial transitions because we have USR_WHAT_LOC_NOT_CONF in another thread

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
