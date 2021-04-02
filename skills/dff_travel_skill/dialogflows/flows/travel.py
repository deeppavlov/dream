# %%
import logging
import os
import re
import random
from enum import Enum, auto

import sentry_sdk

import dialogflows.scopes as scopes
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.condition as condition_utils
import common.dialogflow_framework.utils.state as state_utils

from CoBotQA.cobotqa_service import send_cobotqa
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_SCENARIO_DONE, MUST_CONTINUE
from common.travel import OPINION_REQUESTS_ABOUT_TRAVELLING, TRAVELLING_TEMPLATE, I_HAVE_BEEN_TEMPLATE, \
    WHY_DONT_USER_LIKES_TRAVELLING_RESPONSES, OPINION_REQUEST_ABOUT_MENTIONED_BY_USER_LOC, USER_IMPRESSIONS_REQUEST, \
    WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS, ACKNOWLEDGE_USER_WILL_VISIT_LOC, QUESTIONS_ABOUT_LOCATION, \
    ACKNOWLEDGE_USER_DO_NOT_WANT_TO_VISIT_LOC, OFFER_FACT_RESPONSES, OPINION_REQUESTS, HAVE_YOU_BEEN_TEMPLATE, \
    ACKNOWLEDGE_USER_DISLIKE_LOC
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.utils import get_intents, get_sentiment, get_not_used_template

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
    USR_OPINION_MENTIONED_BY_USER_LOC = auto()

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
    user_mentioned_named_entities = state_utils.get_named_entities_from_human_utterance(vars)
    user_mentioned_locations = []
    for named_entity in user_mentioned_named_entities:
        if named_entity["type"] == "LOC":
            user_mentioned_locations.append(named_entity["text"])
    # if len(user_mentioned_locations) == 0:
    #     nounphrases = state_utils.get_nounphrases_from_human_utterance(vars)
    #     travel_topic = any([
    #         spec_topic in get_topics(state_utils.get_last_human_utterance(vars), probs=False, which="all")
    #         for spec_topic in ["Travel_Geo", "Politics"]])
    #
    #     if len(nounphrases) == 1 and travel_topic:
    #         user_mentioned_locations.append(nounphrases[0])

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
    flag = condition_utils.no_requests(vars)

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

def lets_chat_about_travelling_request(ngrams, vars):
    # SYS_LETS_CHAT_ABOUT_TRAVELLING
    # this check will also catch linkto questions about travelling
    user_lets_chat_about = "lets_chat_about" in get_intents(
        state_utils.get_last_human_utterance(vars), which="intent_catcher") or if_lets_chat_about_topic(
        state_utils.get_last_human_utterance(vars)["text"]) or re.search(
        COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])

    user_lets_chat_about_travelling = re.search(TRAVELLING_TEMPLATE,
                                                state_utils.get_last_human_utterance(vars)["text"])

    if user_lets_chat_about and user_lets_chat_about_travelling:
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
    linkto_opinion_about_travelling = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                                           for req in OPINION_REQUESTS_ABOUT_TRAVELLING])
    user_agrees = yes_request(ngrams, vars)
    user_positive = positive_sentiment_request(ngrams, vars)

    if linkto_opinion_about_travelling and (user_agrees or user_positive):
        logger.info(f"User likes travelling in user utterances")
        return True
    return False


def dislike_about_travelling_request(ngrams, vars):
    # SYS_DISLIKE_TRAVELLING
    linkto_opinion_about_travelling = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
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

        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
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

    if len(user_mentioned_locations) > 0:
        logger.info(f"Found mentioned named locations in user utterances")
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
    user_mentioned_locations = get_mentioned_locations(vars)

    if len(user_mentioned_locations):
        location = f"in {user_mentioned_locations[-1]}"
    else:
        location = "there"
    responses = [f"I've been {location} just virtually because physically I live in the cloud. Have you been there?",
                 f"I've been {location} via pictures and videos. Have you been there?",
                 ]
    logger.info(f"Bot responses that bot has not been in LOC: {location}.")
    try:
        if have_bot_been_in(vars):
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        else:
            confidence = DEFAULT_CONFIDENCE
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        if len(user_mentioned_locations) > 0:
            state_utils.save_to_shared_memory(vars, discussed_location=user_mentioned_locations[-1])
        return random.choice(responses)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# user have been in LOC
##################################################################################################################

def user_have_been_in_request(ngrams, vars):
    # SYS_USR_HAVE_BEEN
    bot_asks_have_you_been_and_user_agrees = re.search(
        HAVE_YOU_BEEN_TEMPLATE, state_utils.get_last_bot_utterance(vars)["text"]) and condition_utils.is_yes_vars(vars)
    user_says_been_in = re.search(
        I_HAVE_BEEN_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    bot_asked_about_location = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                                    for req in QUESTIONS_ABOUT_LOCATION])

    if bot_asks_have_you_been_and_user_agrees or user_says_been_in or bot_asked_about_location:
        logger.info(f"User says he/she was in LOC in user utterances")
        return True
    return False


def user_have_been_in_response(vars):
    # USR_OPINION_MENTIONED_BY_USER_LOC
    user_mentioned_locations = get_mentioned_locations(vars)
    if len(user_mentioned_locations) > 0:
        location = user_mentioned_locations[-1]
    else:
        location = "there"
    shared_memory = state_utils.get_shared_memory(vars)
    used_opinion_requests = shared_memory.get("used_opinion_requests_mentioned_loc", [])
    logger.info(f"Bot asks if user liked visited LOC: {location}.")

    try:
        response = get_not_used_template(used_opinion_requests, OPINION_REQUEST_ABOUT_MENTIONED_BY_USER_LOC)
        if len(user_mentioned_locations) > 0:
            # if we found named location, super conf if no request in user uttrs, otherwise default conf
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        else:
            # if we did NOT find named location, default conf if no request in user uttrs, otherwise zero conf
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, DEFAULT_CONFIDENCE, ZERO_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        state_utils.save_to_shared_memory(
            vars, used_opinion_requests_mentioned_loc=used_opinion_requests + [response])
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def user_yes_or_liked_request(ngrams, vars):
    # SYS_USR_LIKE_MENTIONED_BY_USER_LOC
    flag = yes_request(ngrams, vars) or positive_sentiment_request(ngrams, vars)
    if flag:
        logger.info(f"User agrees or have positive sentiment in user utterances")
        return True
    return False


def user_liked_mentioned_by_user_loc_response(vars):
    # USR_WHAT_BEST_MENTIONED_BY_USER_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    logger.info(f"Bot acknowledges that user liked LOC and asks about best about LOC: {location}.")

    try:
        if condition_utils.is_yes_vars(vars):
            confidence = SUPER_CONFIDENCE
        else:
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            state_utils.save_to_shared_memory(vars, discussed_location=location)
        return random.choice(USER_IMPRESSIONS_REQUEST)
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
    shared_memory = state_utils.get_shared_memory(vars)
    used_questions_about_location = shared_memory.get("used_questions_about_location", [])
    logger.info(f"Bot acknowledges user dislike loc and asks a question about some other LOC.")

    try:
        if condition_utils.is_no_vars(vars):
            confidence = SUPER_CONFIDENCE
        else:
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, HIGH_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
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
        HAVE_YOU_BEEN_TEMPLATE, state_utils.get_last_bot_utterance(vars)["text"]) and condition_utils.is_no_vars(vars)
    user_says_not_been_in = re.search(
        I_HAVE_NOT_BEEN_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])

    if bot_asks_have_you_been_and_user_disagrees or user_says_not_been_in:
        logger.info(f"User says he/she has not been in LOC in user utterances")
        return True
    return False


def user_have_not_been_in_response(vars):
    # USR_WOULD_LIKE_VISIT_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    logger.info(f"Bot asks if user wants to visit non-visited LOC: {location}.")

    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            state_utils.save_to_shared_memory(vars, discussed_location=location)
        return random.choice(WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


# if user answers he/she would like to visit location
def user_would_like_to_visit_response(vars):
    # USR_WISH_WOULD_VISIT_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    logger.info(f"Bot acknowledges that user would liked to visit LOC: {location}. Wish he/she will do.")

    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        if len(location) > 0:
            state_utils.save_to_shared_memory(vars, discussed_location=location)
        return random.choice(ACKNOWLEDGE_USER_WILL_VISIT_LOC)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


# if user answers he/she would NOT like to visit location
def user_would_not_like_to_visit_response(vars):
    # USR_ACK_NOT_VISIT_LOC_WHAT_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    used_questions_about_location = shared_memory.get("used_questions_about_location", [])
    logger.info(f"Bot acknowledges that user would not like to visit LOC: {location}, asks question about other LOC.")

    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        if len(location) > 0:
            state_utils.save_to_shared_memory(vars, discussed_location=location)
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


def confident_ask_question_about_travelling_response(vars):
    # USR_WHAT_LOC_CONF
    shared_memory = state_utils.get_shared_memory(vars)
    used_questions_about_location = shared_memory.get("used_questions_about_location", [])
    logger.info(f"Bot confidently asks a question about some LOC.")

    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        if confidence == SUPER_CONFIDENCE:
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        question_about_location = get_not_used_template(used_questions_about_location, QUESTIONS_ABOUT_LOCATION)
        state_utils.save_to_shared_memory(
            vars, used_questions_about_location=used_questions_about_location + [question_about_location])
        return question_about_location
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def not_confident_ask_question_about_travelling_response(vars):
    # USR_WHAT_LOC_NOT_CONF
    shared_memory = state_utils.get_shared_memory(vars)
    used_questions_about_location = shared_memory.get("used_questions_about_location", [])
    logger.info(f"Bot not confidently asks a question about some LOC.")

    try:
        confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, DEFAULT_CONFIDENCE, ZERO_CONFIDENCE)
        state_utils.set_confidence(vars, confidence)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
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


def offer_fact_about_loc_response(vars):
    # USR_OFFER_FACT_ABOUT_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    logger.info(f"Bot offers fact about LOC: {location}.")

    if len(location) > 0:
        fact_about_location = send_cobotqa(f"fact about {location}")
    else:
        fact_about_location = ""

    try:
        if len(location) and len(fact_about_location) > 0:
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
            state_utils.set_confidence(vars, confidence)
            if confidence == SUPER_CONFIDENCE:
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, fact_about_discussed_location=fact_about_location)
            return random.choice(OFFER_FACT_RESPONSES).replace("LOCATION", location)
        else:
            state_utils.set_confidence(vars, ZERO_CONFIDENCE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


def share_fact_about_loc_response(vars):
    # USR_SHARE_FACT_ABOUT_LOC
    shared_memory = state_utils.get_shared_memory(vars)
    location = shared_memory.get("discussed_location", "")
    fact_about_location = shared_memory.get("fact_about_discussed_location", "")
    used_opinion_requests = shared_memory.get("used_opinion_requests", [])
    logger.info(f"Bot shares fact about LOC: {location}.")

    try:
        if len(location) and len(fact_about_location) > 0:
            opinion_req = random.choice(OPINION_REQUESTS)
            confidence = choose_conf_decreasing_if_requests_in_human_uttr(vars, SUPER_CONFIDENCE, DEFAULT_CONFIDENCE)
            state_utils.set_confidence(vars, confidence)
            if confidence == SUPER_CONFIDENCE:
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
            state_utils.save_to_shared_memory(vars, discussed_location=location)
            state_utils.save_to_shared_memory(vars, used_opinion_requests=used_opinion_requests + [opinion_req])
            return f"{fact_about_location} {opinion_req}"
        else:
            state_utils.set_confidence(vars, ZERO_CONFIDENCE)
            return error_response(vars)
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
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request,
        State.SYS_LETS_CHAT_ABOUT_TRAVELLING: lets_chat_about_travelling_request,
        State.SYS_LIKE_TRAVELLING: like_about_travelling_request,
        State.SYS_DISLIKE_TRAVELLING: dislike_about_travelling_request,
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
    },
)
simplified_dialogflow.set_error_successor(State.USR_HAVE_BEEN, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_HAVE_BEEN
simplified_dialogflow.add_system_transition(State.SYS_USR_HAVE_BEEN, State.USR_OPINION_MENTIONED_BY_USER_LOC,
                                            user_have_been_in_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_OPINION_MENTIONED_BY_USER_LOC,
    {
        State.SYS_USR_LIKE_MENTIONED_BY_USER_LOC: user_yes_or_liked_request,
        State.SYS_USR_DISLIKE_MENTIONED_BY_USER_LOC: user_no_or_disliked_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_OPINION_MENTIONED_BY_USER_LOC, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_LIKE_MENTIONED_BY_USER_LOC
simplified_dialogflow.add_system_transition(State.SYS_USR_LIKE_MENTIONED_BY_USER_LOC,
                                            State.USR_WHAT_BEST_MENTIONED_BY_USER_LOC,
                                            user_liked_mentioned_by_user_loc_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_BEST_MENTIONED_BY_USER_LOC,
    {
        State.SYS_BEST_MENTIONED_BY_USER_LOC: no_requests_request,
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
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request
    },
)
simplified_dialogflow.set_error_successor(State.USR_DISLIKE_AND_WHAT_LOC_NOT_CONF, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_LOC_NOT_CONF,
    {
        State.SYS_USR_HAVE_BEEN: user_have_been_in_request,
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request
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
        State.SYS_GET_FACT_ABOUT_LOC: no_requests_request,
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
#  SYS_LETS_CHAT_ABOUT_TRAVELLING
simplified_dialogflow.add_system_transition(State.SYS_LETS_CHAT_ABOUT_TRAVELLING, State.USR_OPINION_TRAVELLING,
                                            lets_chat_about_travelling_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_OPINION_TRAVELLING,
    {
        State.SYS_LIKE_TRAVELLING: like_about_travelling_request,
        State.SYS_DISLIKE_TRAVELLING: dislike_about_travelling_request,
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
        State.SYS_LOC_DETECTED: user_mention_named_entity_loc_request
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
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
