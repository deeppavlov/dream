import logging
import os
import re
import random
from enum import Enum, auto

import sentry_sdk
import requests

import dialogflows.scopes as scopes
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.sport import (
    BINARY_QUESTION_ABOUT_SPORT,
    BINARY_QUESTION_ABOUT_ATHLETE,
    BINARY_QUESTION_ABOUT_COMP,

    SPORT_TEMPLATE,
    KIND_OF_SPORTS_TEMPLATE,
    KIND_OF_COMPETITION_TEMPLATE,
    ATHLETE_TEMPLETE,
    SUPPORT_TEMPLATE,
    QUESTION_TEMPLATE,
    LIKE_TEMPLATE,
    COMPETITION_TEMPLATE,

    SUPER_CONFIDENCE,
    HIGH_CONFIDENCE,
    ZERO_CONFIDENCE,
)
import common.dialogflow_framework.utils.condition as condition_utils
from common.utils import get_intents, get_sentiment


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)


class State(Enum):
    SYS_LINK_TO_LIKE_SPORT = auto()
    SYS_LINK_TO_LIKE_ATHLETE = auto()
    SYS_LINK_TO_LIKE_COMP = auto()

    USR_START = auto()

    SYS_WHO_FAVORITE_ATHLETE = auto()
    SYS_LETS_TALK_ATHLETE = auto()
    USR_ASK_ABOUT_ATHLETE = auto()

    SYS_WHO_SUPPORT = auto()
    USR_ASK_WHO_SUPPORT = auto()

    SYS_LETS_TALK_SPORT = auto()
    SYS_WHAT_SPORT = auto()
    USR_ASK_ABOUT_SPORT = auto()

    SYS_TELL_ATHLETE = auto()
    USR_LIKE_ATHLETE = auto()

    SYS_TELL_SPORT = auto()
    USR_WHY_LIKE_SPORT = auto()

    SYS_LETS_TALK_ABOUT_COMP = auto()
    SYS_ASK_ABOUT_COMP = auto()
    USR_ASK_ABOUT_COMP = auto()

    SYS_TELL_COMP = auto()
    USR_WHY_LIKE_COMP = auto()

    SYS_TELL_NEGATIVE = auto()
    USR_GO_ANOTHER = auto()

    SYS_ERR = auto()


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
# HELP FUNCTION
##################################################################################################################


def get_news_for_person_or_org(vars):
    person_or_org_array = get_name_person_or_org(vars)
    if len(person_or_org_array) > 0:
        news_string = get_news(person_or_org_array[-1])
        flag = True
    else:
        news_string = f""
        flag = False
    return flag, news_string


def get_news(string):
    try:
        keys = [
            f"188eea501739478981eebf0b44695e75",
            f"1fd88e76511f4ff19ad7a2a9ee84826c",
            f"ee51596f8c3545f3aa382932844a15a8",
            f"7e38f3aeae164d59a05d9874dc0db852",
        ]
        string_for_request = string.replace(" ", "%20")
        link = f"http://newsapi.org/v2/everything?q={string_for_request}&apiKey={random.choice(keys)}"
        news = requests.get(link, timeout=0.5)
        news_json = news.json()["articles"]
        title = news_json[0]["title"]
        news_string = f"I recently read the news that {title}. What do you think about this?"
        return news_string
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        return f""


def get_name_person_or_org(vars):
    user_mentioned_named_entities = state_utils.get_named_entities_from_human_utterance(vars)
    user_mentioned_name = []
    for named_entity in user_mentioned_named_entities:
        if named_entity["type"] == "PER" or "ORG":
            user_mentioned_name.append(named_entity["text"])
    return user_mentioned_name


##################################################################################################################
# LINK TO SPORT
##################################################################################################################


def link_to_like_sport_request(ngrams, vars):
    # SYS_LINK_TO_LIKE_SPORT
    link_to_opinion_about_sport = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in BINARY_QUESTION_ABOUT_SPORT]
    )
    user_agrees = condition_utils.is_yes_vars(vars)
    is_positive = "positive" in get_sentiment(
        state_utils.get_last_human_utterance(vars), probs=False, default_labels=["neutral"]
    )
    flag = link_to_opinion_about_sport and (user_agrees or is_positive)
    logger.info(f"link_to_like_sport_request={flag}")
    return flag


def link_to_like_athlete_request(ngrams, vars):
    # SYS_LINK_TO_LIKE_ATHLETE
    link_to_opinion_about_athl = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in
         BINARY_QUESTION_ABOUT_ATHLETE]
    )
    user_agrees = condition_utils.is_yes_vars(vars)
    is_positive = "positive" in get_sentiment(
        state_utils.get_last_human_utterance(vars), probs=False, default_labels=["neutral"]
    )
    flag = link_to_opinion_about_athl and (user_agrees or is_positive)
    logger.info(f"link_to_like_athlete_request={flag}")
    return flag


def link_to_like_comp_request(ngrams, vars):
    # SYS_LINK_TO_LIKE_COMP
    link_to_opinion_about_comp = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in BINARY_QUESTION_ABOUT_COMP]
    )
    user_agrees = condition_utils.is_yes_vars(vars)
    is_positive = "positive" in get_sentiment(
        state_utils.get_last_human_utterance(vars), probs=False, default_labels=["neutral"]
    )
    flag = link_to_opinion_about_comp and (user_agrees or is_positive)
    logger.info(f"link_to_like_comp_request={flag}")
    return flag

##################################################################################################################
# let's talk about sport || what kind of sport do you like
##################################################################################################################


def lets_talk_about_sport_request(ngrams, vars):
    # SYS_LETS_TALK_SPORT
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
    )

    user_lets_chat_about_sport = re.search(SPORT_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_lets_chat_about) and bool(user_lets_chat_about_sport)
    logger.info(f"lets_talk_about_sport_request={flag}")
    return flag


def user_ask_about_sport_request(ngrams, vars):
    # SYS_WHAT_SPORT
    user_ask = re.search(QUESTION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    user_says_about_sports = re.search(SPORT_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_ask) and bool(user_says_about_sports)
    logger.info(f"user_ask_about_sport_request={flag}")
    return flag


def lets_chat_about_sport_response(vars):
    # USR_ASK_ABOUT_SPORT
    responses = [
        f"I have no physical embodiment. Sport is interesting and useful. Tell me what sport do you enjoy?",
        f"I live on a cloud, so i can't do sport , but I'm really curious about what sport are you fond of?",
    ]
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        return random.choice(responses)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# let's talk about athletes || who is you favourite athletes
##################################################################################################################


def lets_talk_about_athlete_request(ngrams, vars):
    # SYS_LETS_TALK_ATHLETE
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
    )

    user_lets_chat_about_athlete = re.search(ATHLETE_TEMPLETE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_lets_chat_about) and bool(user_lets_chat_about_athlete)
    logger.info(f"lets_talk_about_athlete_request={flag}")
    return flag


def user_ask_about_athletes_request(ngrams, vars):
    # SYS_WHO_FAVORITE_ATHLETE
    user_ask = re.search(QUESTION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    user_says_about_athletes = re.search(ATHLETE_TEMPLETE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_ask) and bool(user_says_about_athletes)
    logger.info(f"user_ask_about_athletes_request={flag}")
    return flag


def user_ask_about_athletes_response(vars):
    # USR_ASK_ABOUT_ATHLETE
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        return f"I know all the athletes on this planet. Which athlete do you like the most?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# who do you support?
##################################################################################################################


def user_ask_who_do_u_support_request(ngrams, vars):
    # SYS_WHO_SUPPORT
    user_ask = re.search(QUESTION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    user_says_about_support = re.search(SUPPORT_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_ask) and bool(user_says_about_support)
    logger.info(f"user_ask_who_do_u_support_request={flag}")
    return flag


def user_ask_who_do_u_support_response(vars):
    # USR_ASK_WHO_SUPPORT
    responses = ["sports teams", "athletes"]
    try:
        state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
        return f"I was born quite recently. But I know a lot of {random.choice(responses)}. Tell me who do you support?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# i like Ronaldo/Barcelona || What do u think about Messi/Real Madrid? (without checking for the sports area)
##################################################################################################################


def user_like_or_ask_about_player_or_org_request(ngrams, vars):
    # SYS_TELL_ATHLETE
    user_like_or_ask = re.search(LIKE_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"]) or re.search(
        QUESTION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"]
    )
    user_lets_chat_about = ("lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars),
                                                             which="intent_catcher") or if_lets_chat_about_topic(
        state_utils.get_last_human_utterance(vars)["text"]))
    it_is_not_negative = "negative" not in get_sentiment(
        state_utils.get_last_human_utterance(vars), probs=False, default_labels=["neutral"]
    )
    user_want = (bool(user_like_or_ask) or user_lets_chat_about) and it_is_not_negative
    flag_have_per_or_org, _ = get_news_for_person_or_org(vars)
    flag = user_want and flag_have_per_or_org
    logger.info(f"user_like_or_ask_about_player_or_org_request = {flag}")
    return flag


def user_like_or_ask_about_player_or_org_response(vars):
    # USR_LIKE_ATHLETE
    try:
        state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
        have_news, news_string = get_news_for_person_or_org(vars)
        if have_news:
            return news_string
        else:
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, confidence=ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# i like basketball || (after question human will say only kind of sport : football)
##################################################################################################################


def user_like_sport_request(ngrams, vars):
    # SYS_TELL_SPORT
    it_is_not_negative = "negative" not in get_sentiment(state_utils.get_last_human_utterance(vars), probs=False,
                                                         default_labels=["neutral"])
    user_says_about_kind_of_sport = re.search(KIND_OF_SPORTS_TEMPLATE,
                                              state_utils.get_last_human_utterance(vars)["text"])
    flag_1 = bool(user_says_about_kind_of_sport) and it_is_not_negative
    if bool(user_says_about_kind_of_sport) is True:
        flag_2 = len(state_utils.get_last_human_utterance(vars)["text"]) == user_says_about_kind_of_sport.group()
        flag = flag_1 or flag_2
    else:
        flag = False
    logger.info(f"user_like_sport_request={flag}")
    return flag


def user_like_sport_response(vars):
    # USR_WHY_LIKE_SPORT
    try:
        number = random.randint(1, 10)
        kind_of_sport = re.search(KIND_OF_SPORTS_TEMPLATE,
                                  state_utils.get_last_human_utterance(vars)["text"]).group()
        if number > 3:
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            return f"why do you like {kind_of_sport}?"
        else:
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            news = get_news(kind_of_sport)
            return news
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# do you like competition? || let's talk about tournament
##################################################################################################################


def user_lets_talk_about_comp_request(ngrams, vars):
    # SYS_LETS_TALK_ABOUT_COMP
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
        or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    )
    user_said_about_comp = re.search(COMPETITION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_lets_chat_about) and bool(user_said_about_comp)
    logger.info(f"user_lets_talk_about_comp_request={flag}")
    return flag


def user_ask_about_comp_request(ngrams, vars):
    # SYS_ASK_ABOUT_COMP
    user_ask = re.search(QUESTION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    user_said_about_comp = re.search(COMPETITION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(user_ask) and bool(user_said_about_comp)
    logger.info(f"user_ask_about_comp_request={flag}")
    return flag


def user_ask_about_comp_response(vars):
    # USR_ASK_ABOUT_COMP
    responses = ["FIFA World Cup", "Olympic Games", "Super Bowl", "Grand National"]
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        return (
            f"Well. if I had a physical embodiment, I would like to go to the {random.choice(responses)}."
            f"Do you have a favorite competition?"
        )
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# i like Super Bowl
##################################################################################################################


def user_like_comp_request(ngrams, vars):
    # SYS_TELL_COMP
    it_is_not_negative = "negative" not in get_sentiment(state_utils.get_last_human_utterance(vars), probs=False,
                                                         default_labels=["neutral"])
    user_says_about_kind_of_comp = re.search(KIND_OF_COMPETITION_TEMPLATE,
                                             state_utils.get_last_human_utterance(vars)["text"])
    flag_1 = bool(user_says_about_kind_of_comp) and it_is_not_negative
    if bool(user_says_about_kind_of_comp) is True:
        flag_2 = len(state_utils.get_last_human_utterance(vars)["text"]) == user_says_about_kind_of_comp.group()
        flag = flag_1 or flag_2
    else:
        flag = False
    logger.info(f"user_like_comp_request={flag}")
    return flag


def user_like_comp_response(vars):
    # USR_WHY_LIKE_COMP
    try:
        number = random.randint(1, 10)
        kind_of_comp = re.search(
            KIND_OF_COMPETITION_TEMPLATE, state_utils.get_last_human_utterance(vars)["text"]
        ).group()
        if number > 3:
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            return f"why do you like {kind_of_comp}?"
        else:
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            news = get_news(kind_of_comp)
            return news
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, ZERO_CONFIDENCE)
        return error_response(vars)


##################################################################################################################
# No, i would not || I doesn't like this
##################################################################################################################


def user_negative_request(ngrams, vars):
    # SYS_TELL_NEGATIVE
    is_negative = "negative" in get_sentiment(state_utils.get_last_human_utterance(vars),
                                              probs=False, default_labels=["neutral"])
    no_vars = condition_utils.is_no_vars(vars)
    flag = is_negative or no_vars
    logger.info(f"user_negative_request={flag}")
    return flag


def user_negative_response(vers):
    # USR_GO_ANOTHER
    responses = ["pets", "science", "travel", "food", "games", "movies", "books"]
    topics = random.sample(responses, 2)
    try:
        state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
        return (
            f"Well, What do you want to discuss? I would like to talk about {topics[0]} or {topics[1]}."
        )
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
    return f""


##################################################################################################################
# START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_LETS_TALK_SPORT: lets_talk_about_sport_request,
        State.SYS_WHAT_SPORT: user_ask_about_sport_request,
        State.SYS_LETS_TALK_ATHLETE: lets_talk_about_athlete_request,
        State.SYS_WHO_FAVORITE_ATHLETE: user_ask_about_athletes_request,
        State.SYS_WHO_SUPPORT: user_ask_who_do_u_support_request,
        State.SYS_LETS_TALK_ABOUT_COMP: user_lets_talk_about_comp_request,
        State.SYS_ASK_ABOUT_COMP: user_ask_about_comp_request,
        State.SYS_TELL_SPORT: user_like_sport_request,
        State.SYS_TELL_COMP: user_like_comp_request,
        State.SYS_LINK_TO_LIKE_SPORT: link_to_like_sport_request,
        State.SYS_LINK_TO_LIKE_COMP: link_to_like_comp_request,
        State.SYS_LINK_TO_LIKE_ATHLETE: link_to_like_athlete_request
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
# SYS_WHO_FAVORITE_ATHLETE || SYS_LETS_TALK_ATHLETE || SYS_LINK_TO_LIKE_ATHLETE--> USR_ASK_ABOUT_ATHLETE

simplified_dialogflow.add_system_transition(
    State.SYS_WHO_FAVORITE_ATHLETE, State.USR_ASK_ABOUT_ATHLETE, user_ask_about_athletes_response
)

simplified_dialogflow.add_system_transition(
    State.SYS_LETS_TALK_ATHLETE, State.USR_ASK_ABOUT_ATHLETE, user_ask_about_athletes_response
)
simplified_dialogflow.add_system_transition(
    State.SYS_LINK_TO_LIKE_ATHLETE, State.USR_ASK_ABOUT_ATHLETE, user_ask_about_athletes_response
)
simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_ATHLETE,
    {
        State.SYS_TELL_ATHLETE: user_like_or_ask_about_player_or_org_request,
        State.SYS_TELL_SPORT: user_like_sport_request,
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_ASK_ABOUT_ATHLETE, State.SYS_ERR)

##################################################################################################################
# SYS_ASK_ABOUT_COMP || SYS_LETS_TALK_ABOUT_COMP || SYS_LINK_TO_LIKE_COMP --> USR_ASK_ABOUT_COMP

simplified_dialogflow.add_system_transition(
    State.SYS_ASK_ABOUT_COMP, State.USR_ASK_ABOUT_COMP, user_ask_about_comp_response
)

simplified_dialogflow.add_system_transition(
    State.SYS_LETS_TALK_ABOUT_COMP, State.USR_ASK_ABOUT_COMP, user_ask_about_comp_response
)
simplified_dialogflow.add_system_transition(
    State.SYS_LINK_TO_LIKE_COMP, State.USR_ASK_ABOUT_COMP, user_ask_about_comp_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_COMP,
    {
        State.SYS_TELL_COMP: user_like_comp_request,
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_ASK_ABOUT_COMP, State.SYS_ERR)

##################################################################################################################
# SYS_TELL_COMP --> USR_WHY_LIKE_COMP

simplified_dialogflow.add_system_transition(State.SYS_TELL_COMP, State.USR_WHY_LIKE_COMP, user_like_comp_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHY_LIKE_COMP,
    {
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHY_LIKE_COMP, State.SYS_ERR)

##################################################################################################################
# SYS_WHO_SUPPORT --> USR_ASK_WHO_SUPPORT

simplified_dialogflow.add_system_transition(
    State.SYS_WHO_SUPPORT, State.USR_ASK_WHO_SUPPORT, user_ask_who_do_u_support_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_WHO_SUPPORT,
    {
        State.SYS_TELL_ATHLETE: user_like_or_ask_about_player_or_org_request,
        State.SYS_TELL_SPORT: user_like_sport_request,
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_ASK_WHO_SUPPORT, State.SYS_ERR)

##################################################################################################################
# SYS_LETS_TALK_SPORT || SYS_WHAT_SPORT || SYS_LINK_TO_LIKE_SPORT --> USR_ASK_ABOUT_SPORT

simplified_dialogflow.add_system_transition(
    State.SYS_LETS_TALK_SPORT, State.USR_ASK_ABOUT_SPORT, lets_chat_about_sport_response
)
simplified_dialogflow.add_system_transition(
    State.SYS_WHAT_SPORT, State.USR_ASK_ABOUT_SPORT, lets_chat_about_sport_response
)
simplified_dialogflow.add_system_transition(
    State.SYS_LINK_TO_LIKE_SPORT, State.USR_ASK_ABOUT_SPORT, lets_chat_about_sport_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_SPORT,
    {
        State.SYS_TELL_SPORT: user_like_sport_request,
        State.SYS_TELL_ATHLETE: user_like_or_ask_about_player_or_org_request,
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_ASK_ABOUT_SPORT, State.SYS_ERR)

##################################################################################################################
# SYS_TELL_ATHLETE --> USR_LIKE_ATHLETE

simplified_dialogflow.add_system_transition(
    State.SYS_TELL_ATHLETE, State.USR_LIKE_ATHLETE, user_like_or_ask_about_player_or_org_response
)
simplified_dialogflow.add_user_serial_transitions(
    State.USR_LIKE_ATHLETE,
    {
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_LIKE_ATHLETE, State.SYS_ERR)

##################################################################################################################
# SYS_TELL_SPORT --> USR_WHY_LIKE_SPORT

simplified_dialogflow.add_system_transition(State.SYS_TELL_SPORT, State.USR_WHY_LIKE_SPORT, user_like_sport_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHY_LIKE_SPORT,
    {
        State.SYS_TELL_NEGATIVE: user_negative_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WHY_LIKE_SPORT, State.SYS_ERR)

##################################################################################################################
# SYS_TELL_NEGATIVE -> USR_GO_ANOTHER

simplified_dialogflow.add_system_transition(
    State.SYS_TELL_NEGATIVE, State.USR_GO_ANOTHER, user_negative_response
)

# there are no user serial
##################################################################################################################
# SYS_ERR

simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialogflow.get_dialogflow()
