# %%
from common.scenarios.games import was_game_mentioned
import random
import os
import logging
from enum import Enum, auto
import re

import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.utils as common_utils
import common.universal_templates as common_universal_templates
import common.scenarios.weekend as common_weekend
import dialogflows.scopes as scopes
from dialogflows.flows.shared import link_to_by_enity_request
from dialogflows.flows.shared import link_to_by_enity_response
from dialogflows.flows.shared import error_response

# import dialog_flows.components.greeting as flows_greeting

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


class State(Enum):
    USR_START = auto()
    SYS_WEEKEND = auto()
    USR_WEEKEND = auto()

    USR_TOO_CLEAN = auto()

    USR_CLEANED_UP = auto()
    SYS_CLEANED_UP = auto()

    SYS_LINK_TO_BY_ENITY = auto()
    USR_LINK_TO_BY_ENITY = auto()
    #
    SYS_SLEPT_IN = auto()
    USR_SLEPT_IN = auto()

    SYS_FEEL_GREAT = auto()
    USR_FEEL_GREAT = auto()

    SYS_NEED_MORE_TIME = auto()
    USR_NEED_MORE_TIME = auto()

    USR_WHATS_NEXT = auto()

    SYS_WATCHED_FILM_TV = auto()
    USR_WATCHED_FILM_TV = auto()

    SYS_READ_BOOK = auto()
    USR_READ_BOOK = auto()

    SYS_PLAYED_COMPUTER_GAME = auto()
    USR_PLAYED_COMPUTER_GAME = auto()

    SYS_PLAYED_ALL_WEEKEND = auto()
    USR_PLAYED_ALL_WEEKEND = auto()

    SYS_PLAY_REGULARLY = auto()
    USR_PLAY_REGULARLY = auto()

    SYS_PLAYED_ONCE = auto()
    USR_PLAYED_ONCE = auto()

    SYS_ERR = auto()
    USR_ERR = auto()


DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98


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


##################################################################################################################
# std weekend
##################################################################################################################

patterns_bot = ["chat about", "talk about", "on your mind"]
re_patterns_bot = re.compile("(" + "|".join(patterns_bot) + ")", re.IGNORECASE)

patterns_human = ["no idea", "don't know", "nothing", "anything", "your favorite topic"]
re_patterns_human = re.compile("(" + "|".join(patterns_human) + ")", re.IGNORECASE)


def std_weekend_request(ngrams, vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    prev_was_about_topic = common_universal_templates.if_utterance_requests_topic(
        state_utils.get_last_bot_utterance(vars)
    )
    anything = re.search(re_patterns_human, human_text)

    flag = bool(prev_was_about_topic and anything)

    logger.info(f"weekend_request={flag}")
    return flag


def std_weekend_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.WEEKEND_QUESTIONS)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# cleaned up
##################################################################################################################


patterns_human = ["clean", "tide", "reorganize", "tidi", "laundry"]
cleaned_up_patterns_re = re.compile("(" + "|".join(patterns_human) + ")", re.IGNORECASE)


def sys_cleaned_up_request(ngrams, vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(cleaned_up_patterns_re, human_text))
    logger.info(f"sys_cleaned_up_request={flag}")
    return flag


def sys_cleaned_up_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.CLEANED_UP_STATEMENTS)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# slept in
##################################################################################################################


def sys_slept_in_request(ngrams, vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = "slept" in human_text
    logger.info(f"sys_slept_in_request={flag}")
    return flag


def sys_slept_in_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.SLEPT_IN_QUESTIONS)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# feel great
##################################################################################################################


def sys_feel_great_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)

    flag = common_utils.is_no(human_utterance)
    logger.info(f"sys_feel_great_request={flag}")
    return flag


def sys_feel_great_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.WHAT_PLANS_FOR_TODAY)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# need more time
##################################################################################################################


def sys_need_more_time_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)

    flag = common_utils.is_no(human_utterance)
    logger.info(f"sys_need_more_time_request={flag}")
    return flag


def sys_need_more_time_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.WISH_MORE_TIME)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# watched_film
##################################################################################################################

patterns_human_1 = ["movie", "tv", "netflix", "hulu", "disney", "hbo", "cbs", "paramount"]

watched_film_patterns_1_re = re.compile("(" + "|".join(patterns_human_1) + ")", re.IGNORECASE)

patterns_human_2 = ["watched", "seen", "saw", "enjoyed", "binged"]

watched_film_patterns_2_re = re.compile("(" + "|".join(patterns_human_2) + ")", re.IGNORECASE)


def sys_watched_film_request(ngrams, vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(watched_film_patterns_1_re, human_text) and re.search(watched_film_patterns_2_re, human_text))
    logger.info(f"sys_watched_film_request={flag}")
    return flag


def sys_watched_film_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.MOVIE_NAME_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# read_book
##################################################################################################################


patterns_human_1 = ["book", "story", "article", "magazine"]

read_book_patterns_1_re = re.compile("(" + "|".join(patterns_human_1) + ")", re.IGNORECASE)

patterns_human_2 = ["read", "enjoy", "looked through", "wade", "flicked"]

read_book_patterns_1_re = re.compile("(" + "|".join(patterns_human_2) + ")", re.IGNORECASE)


def sys_read_book_request(ngrams, vars):

    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(read_book_patterns_1_re, human_text) and re.search(read_book_patterns_1_re, human_text))
    logger.info(f"sys_read_book_request={flag}")
    return flag


def sys_read_book_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.BOOK_NAME_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# played_computer_game
##################################################################################################################


patterns_human_1 = ["game", "computergame", "videogame", "xbox", "x box", "playstation", "play station", "nintendo"]

played_computer_game_patterns_1_re = re.compile("(" + "|".join(patterns_human_1) + ")", re.IGNORECASE)

patterns_human_2 = ["play", "enjoy"]

played_computer_game_patterns_2_re = re.compile("(" + "|".join(patterns_human_2) + ")", re.IGNORECASE)


def sys_played_computer_game_request(ngrams, vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(
        re.search(played_computer_game_patterns_1_re, human_text)
        and re.search(played_computer_game_patterns_2_re, human_text)
    )
    logger.info(f"sys_played_computer_game_request={flag}")
    return flag


def sys_played_computer_game_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.COMPUTER_GAME_NAME_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# play each weekend
##################################################################################################################


def sys_play_on_weekends_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)

    flag = bool(was_game_mentioned(human_utterance))
    logger.info(f"sys_play_on_weekends_request={flag}")
    return flag


def sys_play_on_weekends_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.GAME_EMOTIONS_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# play regularly
##################################################################################################################


def sys_play_regularly_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)

    flag = common_utils.is_yes(human_utterance)
    logger.info(f"sys_play_regularly_request={flag}")
    return flag


def sys_play_regularly_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.REGULAR_PLAYER_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# played once
##################################################################################################################


def sys_play_once_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)

    flag = common_utils.is_no(human_utterance)
    logger.info(f"sys_play_once_request={flag}")
    return flag


def sys_play_once_response(vars):
    try:
        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # obtaining random response from weekend questions
        body = random.choice(common_weekend.OCCASIONAL_PLAYER_QUESTION)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body])
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

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {State.SYS_WEEKEND: std_weekend_request},
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_WEEKEND

simplified_dialogflow.add_system_transition(State.SYS_WEEKEND, State.USR_WEEKEND, std_weekend_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WEEKEND,
    {
        State.SYS_CLEANED_UP: sys_cleaned_up_request,
        State.SYS_SLEPT_IN: sys_slept_in_request,
        State.SYS_READ_BOOK: sys_read_book_request,
        State.SYS_WATCHED_FILM_TV: sys_watched_film_request,
        State.SYS_PLAYED_COMPUTER_GAME: sys_played_computer_game_request,
    },
)


simplified_dialogflow.set_error_successor(State.USR_WEEKEND, State.SYS_ERR)


##################################################################################################################
# LEVEL1: SYS_CLEANED_UP
simplified_dialogflow.add_system_transition(
    State.SYS_CLEANED_UP,
    State.USR_CLEANED_UP,
    sys_cleaned_up_response,
)
simplified_dialogflow.set_error_successor(State.SYS_CLEANED_UP, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_CLEANED_UP,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_CLEANED_UP, State.SYS_ERR)


##################################################################################################################
# LEVEL1: SYS_SLEPT_IN
simplified_dialogflow.add_system_transition(
    State.SYS_SLEPT_IN,
    State.USR_SLEPT_IN,
    sys_slept_in_response,
)
simplified_dialogflow.set_error_successor(State.SYS_SLEPT_IN, State.SYS_ERR)


# adding another conditional transition
simplified_dialogflow.add_user_transition(
    State.USR_SLEPT_IN,
    State.SYS_FEEL_GREAT,
    sys_feel_great_request,
)


simplified_dialogflow.add_user_transition(
    State.USR_SLEPT_IN,
    State.SYS_NEED_MORE_TIME,
    sys_need_more_time_request,
)
simplified_dialogflow.set_error_successor(State.USR_SLEPT_IN, State.SYS_ERR)


##################################################################################################################
#  SYS_NEED_MORE_TIME
simplified_dialogflow.add_system_transition(
    State.SYS_NEED_MORE_TIME,
    State.USR_NEED_MORE_TIME,
    sys_need_more_time_response,
)
simplified_dialogflow.set_error_successor(State.SYS_NEED_MORE_TIME, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_NEED_MORE_TIME,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_NEED_MORE_TIME, State.SYS_ERR)


##################################################################################################################
#  SYS_FEEL_GREAT
simplified_dialogflow.add_system_transition(
    State.SYS_FEEL_GREAT,
    State.USR_FEEL_GREAT,
    sys_feel_great_response,
)
simplified_dialogflow.set_error_successor(State.SYS_FEEL_GREAT, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_FEEL_GREAT,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_FEEL_GREAT, State.SYS_ERR)


##################################################################################################################
# LEVEL1: SYS_WATCHED_FILM_TV
simplified_dialogflow.add_system_transition(
    State.SYS_WATCHED_FILM_TV,
    State.USR_WATCHED_FILM_TV,
    sys_watched_film_response,
)
simplified_dialogflow.set_error_successor(State.SYS_WATCHED_FILM_TV, State.SYS_ERR)


# adding another conditional transition
simplified_dialogflow.add_user_transition(
    State.USR_WATCHED_FILM_TV,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_WATCHED_FILM_TV, State.SYS_ERR)


##################################################################################################################
# LEVEL1: SYS_READ_BOOK
simplified_dialogflow.add_system_transition(
    State.SYS_READ_BOOK,
    State.USR_READ_BOOK,
    sys_read_book_response,
)
simplified_dialogflow.set_error_successor(State.SYS_READ_BOOK, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_READ_BOOK,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_READ_BOOK, State.SYS_ERR)


##################################################################################################################
# LEVEL1: SYS_PLAYED_COMPUTER_GAME
simplified_dialogflow.add_system_transition(
    State.SYS_PLAYED_COMPUTER_GAME, State.USR_PLAYED_COMPUTER_GAME, sys_played_computer_game_response
)
simplified_dialogflow.set_error_successor(State.SYS_PLAYED_COMPUTER_GAME, State.SYS_ERR)


# adding another conditional transition
simplified_dialogflow.add_user_transition(
    State.USR_PLAYED_COMPUTER_GAME, State.SYS_PLAYED_ALL_WEEKEND, sys_play_on_weekends_request
)
simplified_dialogflow.set_error_successor(State.USR_PLAYED_COMPUTER_GAME, State.SYS_ERR)


##################################################################################################################
#  SYS_PLAYED_ALL_WEEKEND
simplified_dialogflow.add_system_transition(
    State.SYS_PLAYED_ALL_WEEKEND, State.USR_PLAYED_ALL_WEEKEND, sys_play_on_weekends_response
)
simplified_dialogflow.set_error_successor(State.SYS_PLAYED_ALL_WEEKEND, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_PLAYED_ALL_WEEKEND,
    {State.SYS_PLAY_REGULARLY: sys_play_regularly_request, State.SYS_PLAYED_ONCE: sys_play_once_request},
)

simplified_dialogflow.set_error_successor(State.USR_PLAYED_ALL_WEEKEND, State.SYS_ERR)


##################################################################################################################
#  SYS_PLAY_REGULARLY
simplified_dialogflow.add_system_transition(
    State.SYS_PLAY_REGULARLY, State.USR_PLAY_REGULARLY, sys_play_regularly_response
)
simplified_dialogflow.set_error_successor(State.SYS_PLAY_REGULARLY, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_PLAY_REGULARLY,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_PLAY_REGULARLY, State.SYS_ERR)


##################################################################################################################
#  SYS_PLAYED_ONCE
simplified_dialogflow.add_system_transition(State.SYS_PLAYED_ONCE, State.USR_PLAYED_ONCE, sys_play_once_response)
simplified_dialogflow.set_error_successor(State.SYS_PLAYED_ONCE, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_PLAYED_ONCE,
    State.SYS_LINK_TO_BY_ENITY,
    # using
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_PLAYED_ONCE, State.SYS_ERR)


##################################################################################################################
#  SYS_LINK_TO_BY_ENITY

simplified_dialogflow.add_system_transition(
    State.SYS_LINK_TO_BY_ENITY,
    State.USR_LINK_TO_BY_ENITY,
    link_to_by_enity_response,
)

simplified_dialogflow.add_user_transition(
    State.USR_LINK_TO_BY_ENITY,
    State.SYS_WEEKEND,
    std_weekend_request,
)
simplified_dialogflow.set_error_successor(State.USR_LINK_TO_BY_ENITY, State.SYS_ERR)


##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)


dialogflow = simplified_dialogflow.get_dialogflow()
