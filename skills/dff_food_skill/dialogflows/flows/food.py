# %%
import json
import logging
import os
import random
import re

from CoBotQA.cobotqa_service import send_cobotqa
from enum import Enum, auto

import sentry_sdk
from spacy import load

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import dialogflows.scopes as scopes
# from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_SCENARIO_DONE, MUST_CONTINUE
from common.utils import is_yes, get_topics, get_entities
from common.food import TRIGGER_PHRASES


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


spacy_nlp = load("en_core_web_sm")


with open("cuisines_facts.json", "r") as f:
    CUISINES_FACTS = json.load(f)
FOOD_WORDS_RE = re.compile(
    r"(food|cooking|cuisine|daily bread|meals|foodstuffs|edibles|drinks|pepperoni)",
    re.IGNORECASE
)
WHAT_COOK_RE = re.compile(
    r"(what should i|what do you suggest me to) (cook|make for dinner)( tonight| today| tomorrow){0,1}",
    re.IGNORECASE,
)
MEALS = [
    "lazagna",
    "mac and cheese",
    "instant pot beef chili",
    "tomato basil soup",
    "spaghetti with tomato sauce",
    "chicken noodle soup",
    "rice with chicken and salad",
    "potatoes with cheese and beans",
    "fries with beef and tomatoes",
    "quinoa with turkey and broccoli",
]
CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9
CONF_LOWEST = 0.8


class State(Enum):
    USR_START = auto()
    #
    SYS_WHAT_COOK = auto()
    SYS_WHAT_FAV_FOOD = auto()
    SYS_WHAT_CUISINE = auto()
    USR_WHAT_FAV_FOOD = auto()
    SYS_FAV_FOOD = auto()
    USR_WHAT_CUISINE = auto()
    SYS_CUISINE = auto()
    USR_CUISINE_FACT = auto()
    USR_HOW_ABOUT_MEAL1 = auto()
    SYS_YES_RECIPE = auto()
    SYS_NO_RECIPE1 = auto()
    SYS_NO_RECIPE2 = auto()
    USR_RECIPE = auto()
    USR_HOW_ABOUT_MEAL2 = auto()
    USR_GOURMET = auto()
    USR_FOOD_FACT = auto()
    SYS_YES_FOOD_FACT = auto()
    SYS_NO_FOOD_FACT = auto()
    SYS_SOMETHING = auto()
    USR_WHERE_R_U_FROM = auto()
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
# let's talk about food
##################################################################################################################


def lets_talk_about_request(ngrams, vars):
    # user_lets_chat_about = (
    #     "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
    #     or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
    #     or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    # )
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    cobot_topic = "Food_Drink" in get_topics(state_utils.get_last_human_utterance(vars), which="cobot_topics")
    conceptnet = "food" in annotations.get("conceptnet", {}).get("SymbolOf", [])

    user_lets_chat_about_food = any([
        re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"].lower()),
        cobot_topic,
        conceptnet
    ]) and (not state_utils.get_last_human_utterance(vars)["text"].startswith("what"))
    flag = user_lets_chat_about_food
    logger.info(f"lets_talk_about_request {flag}")
    return flag


def what_cuisine_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "Okay. What cuisine do you prefer?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def cuisine_request(ngrams, vars):
    # nounphr = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # flag = bool(nounphr)
    utt = spacy_nlp(state_utils.get_last_human_utterance(vars)["text"].lower())
    flag = any([w.pos_ == 'ADJ' for w in utt])
    logger.info(f"cuisine_request {flag}")
    return flag


def cuisine_fact_response(vars):
    cuisine_fact = ""
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        last_utt_lower = state_utils.get_last_human_utterance(vars)["text"].lower()
        for cuisine in list(CUISINES_FACTS.keys()):
            if cuisine in last_utt_lower:
                cuisine_fact = CUISINES_FACTS.get(cuisine, "")
        if not cuisine_fact:
            cuisine_fact = "Haven't tried it yet. What do you recommend to start with?"
        return cuisine_fact
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def what_fav_food_response(vars):
    food_types = ["food", "drink", "fruit", "dessert", "vegetable", "berry"]
    shared_memory = state_utils.get_shared_memory(vars)
    used_food = shared_memory.get("used_food", [])

    try:
        if used_food:
            unused_food = [i for i in food_types if i not in used_food]
            if unused_food:
                food_type = random.choice(unused_food)
                state_utils.set_confidence(vars, confidence=CONF_LOW)
            else:
                food_type = "snack"
                state_utils.set_confidence(vars, confidence=CONF_LOWEST)
        else:
            food_type = "food"
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        state_utils.save_to_shared_memory(vars, used_food=used_food + [food_type])
        return f"What is your favorite {food_type}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def fav_food_request(ngrams, vars):
    flag = False
    user_fav_food = []
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphr = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    cobot_topic = "Food_Drink" in get_topics(state_utils.get_last_human_utterance(vars), which="cobot_topics")
    conceptnet = any([
        "food" in annotations.get("conceptnet", {}).get("SymbolOf", []),
        "delicious" in annotations.get("conceptnet", {}).get("HasProperty", []),
        "tasty" in annotations.get("conceptnet", {}).get("HasProperty", [])
    ])
    for ne in nounphr:
        user_fav_food.append(ne)
    if user_fav_food and any([cobot_topic, conceptnet]):
        flag = True
    logger.info(f"fav_food_request {flag}")
    return flag


def food_fact_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    # nounphr = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # fact = ""
    # if nounphr:
    #     fact = send_cobotqa(f"fact about {nounphr[0]}")
    #     if "here" in fact.lower():
    facts = annotations.get("fact_retrieval", [])
    fact = ""
    if facts:
        fact = facts[0]
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        if not fact:
            endings = ["Do you recommend", "Why do you like it"]
            return f"Sounds tasty. I haven't heard about it. {random.choice(endings)}?"
        return f"I like it too. Do you know that {fact}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def are_you_gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "Are you a gourmet?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# what to cook
##################################################################################################################


def what_cook_request(ngrams, vars):
    what_cook_re_search = re.search(WHAT_COOK_RE, state_utils.get_last_human_utterance(vars)["text"])
    flag = bool(what_cook_re_search)
    logger.info(f"what_cook_request {flag}")
    return flag


def how_about_meal_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    used_meals = shared_memory.get("used_meals", "")
    meal = random.choice([i for i in MEALS if i != used_meals])
    try:
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        # first attempt to suggest a meal
        state_utils.save_to_shared_memory(vars, used_meals=meal)
        if not used_meals:
            return f"How about cooking {meal}?"
        else:
            return f"Okay. Give me one more chance. I recommend {meal}."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def recipe_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        shared_memory = state_utils.get_shared_memory(vars)
        used_meal = shared_memory.get("used_meals", "")
        recipe = send_cobotqa(f"how to cook {used_meal}")
        if not(used_meal and recipe):
            recipe = "Great! Enjoy your meal!"
        return recipe
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "It seems you're a gourmet! What is your favorite meal?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def smth_request(ngrams, vars):
    flag = condition_utils.no_requests(vars)
    logger.info(f"smth_request {flag}")
    return flag


def where_are_you_from_response(vars):
    try:
        state_utils.set_confidence(vars)
        return "Where are you from?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def what_fav_food_request(ngrams, vars):
    linkto_food_skill_agreed = any(
        [
            req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
            for req in TRIGGER_PHRASES
        ]
    ) and is_yes(state_utils.get_last_human_utterance(vars))
    food_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_FAV_FOOD)
    cuisine_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_CUISINE)

    if not (lets_talk_about_request(ngrams, vars) or linkto_food_skill_agreed):
        flag = False
    elif (food_1st_time and cuisine_1st_time):
        flag = random.choice([True, False])
    elif (food_1st_time or (not cuisine_1st_time)):
        flag = True
    else:
        flag = False
    logger.info(f"what_fav_food_request {flag}")
    return flag


def what_cuisine_request(ngrams, vars):
    linkto_food_skill_agreed = any(
        [
            req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
            for req in TRIGGER_PHRASES
        ]
    ) and is_yes(state_utils.get_last_human_utterance(vars))
    flag = lets_talk_about_request(ngrams, vars) or linkto_food_skill_agreed
    logger.info(f"what_cuisine_request {flag}")
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
        State.SYS_WHAT_COOK: what_cook_request,
        State.SYS_WHAT_FAV_FOOD: what_fav_food_request,
        State.SYS_WHAT_CUISINE: what_cuisine_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################

simplified_dialogflow.add_system_transition(State.SYS_WHAT_FAV_FOOD, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_WHAT_CUISINE, State.USR_WHAT_CUISINE, what_cuisine_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_WHAT_FAV_FOOD, State.SYS_FAV_FOOD, fav_food_request)
simplified_dialogflow.set_error_successor(State.USR_WHAT_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_WHAT_CUISINE, State.SYS_CUISINE, cuisine_request)
simplified_dialogflow.set_error_successor(State.USR_WHAT_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CUISINE, State.USR_CUISINE_FACT, cuisine_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_CUISINE_FACT, State.SYS_SOMETHING, smth_request)
simplified_dialogflow.set_error_successor(State.USR_CUISINE_FACT, State.SYS_ERR)

##################################################################################################################
#  SYS_WHAT_COOK

simplified_dialogflow.add_system_transition(State.SYS_WHAT_COOK, State.USR_HOW_ABOUT_MEAL1, how_about_meal_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_COOK, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_HOW_ABOUT_MEAL1,
    {
        State.SYS_YES_RECIPE: yes_request,
        State.SYS_NO_RECIPE1: no_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HOW_ABOUT_MEAL1, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_YES_RECIPE, State.USR_RECIPE, recipe_response)
simplified_dialogflow.set_error_successor(State.SYS_YES_RECIPE, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_RECIPE, State.SYS_SOMETHING, smth_request)
simplified_dialogflow.set_error_successor(State.USR_RECIPE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_NO_RECIPE1, State.USR_HOW_ABOUT_MEAL2, how_about_meal_response)
simplified_dialogflow.set_error_successor(State.SYS_NO_RECIPE1, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_HOW_ABOUT_MEAL2,
    {
        State.SYS_YES_RECIPE: yes_request,
        State.SYS_NO_RECIPE2: no_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HOW_ABOUT_MEAL2, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_NO_RECIPE2, State.USR_GOURMET, gourmet_response)
simplified_dialogflow.set_error_successor(State.SYS_NO_RECIPE2, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_GOURMET, State.SYS_FAV_FOOD, fav_food_request)
simplified_dialogflow.set_error_successor(State.USR_GOURMET, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_FAV_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_FOOD_FACT, State.SYS_SOMETHING, smth_request)
simplified_dialogflow.set_error_successor(State.USR_FOOD_FACT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_SOMETHING, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_SOMETHING, State.SYS_ERR)

#################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
