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
from common.universal_templates import if_chat_about_particular_topic, DONOTKNOW_LIKE
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_SCENARIO_DONE, MUST_CONTINUE
from common.utils import is_yes, is_no, get_entities, join_words_in_or_pattern
from common.food import TRIGGER_PHRASES


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


spacy_nlp = load("en_core_web_sm")


with open("cuisines_facts.json", "r") as f:
    CUISINES_FACTS = json.load(f)
CONCEPTNET_SYMBOLOF_FOOD = [
    "food", "coffee", "sweetness", "hunger",
    "breakfast", "dinner", "pizza", "potato",
    "meal", "japanese cuisine", "sushi",
    "italian cuisine"
]
CONCEPTNET_HASPROPERTY_FOOD = [
    "delicious", "tasty", "sweet", "good with potato", "edible"
]
CONCEPTNET_CAUSESDESIRE_FOOD = [
    "eat", "eat chocolate", "eat breakfast", "eat food", "eat quickly",
    "eat hamburger", "eat potato",
    "have meal", "have breakfast", "have food", "have steak",
    "cook dinner", "cook potato", "cook meal", "cook food", "cook pasta"
]
FOOD_WORDS_RE = re.compile(
    r"(food|cook|cooking|bake|baking|cuisine|daily bread|meals|foodstuffs"
    "|edibles|drink|pepperoni|pizza|strawberries|chocolate|coffee|eat|dinner"
    "|breakfast|pasta|burger|cheese|tasty|waffles)",
    re.IGNORECASE
)
FOOD_SKILL_TRANSFER_PHRASES_RE = re.compile(
    r"(do you know .* most (favorite|favourite) food?|.*what is your (favorite|favourite) food?"
    "|.*by the way, what food do you like?|do you like .* cuisine?"
    "|.*what kind of cuisine do you like?)",
    re.IGNORECASE
)
WHAT_COOK_RE = re.compile(
    r"(what should i|what do you suggest me to) (cook|make for dinner)( tonight| today| tomorrow){0,1}",
    re.IGNORECASE,
)
DONOTKNOW_LIKE_RE = re.compile(join_words_in_or_pattern(DONOTKNOW_LIKE), re.IGNORECASE)
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
CUISINES_COUNTRIES = {
    "french": "France",
    "chinese": "China",
    "japanese": "Japan",
    "italian": "Italy",
    "greek": "Greece",
    "spanish": "Spain",
    "mediterranean": "Italy",
    "thai": "Thailand",
    "indian": "India",
    "mexican": "Mexico"
}
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
    SYS_TO_TRAVEL_SKILL = auto()
    USR_COUNTRY = auto()
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


def check_conceptnet(vars):
    annotations_conceptnet = state_utils.get_last_human_utterance(vars)["annotations"].get(
        "conceptnet", {})
    conceptnet = False
    food_item = None
    for elem, triplets in annotations_conceptnet.items():
        conceptnet_symbolof = any(
            [
                i in triplets.get("SymbolOf", []) for i in CONCEPTNET_SYMBOLOF_FOOD
            ]
        )
        conceptnet_hasproperty = any(
            [
                i in triplets.get("HasProperty", []) for i in CONCEPTNET_HASPROPERTY_FOOD
            ]
        )
        conceptnet_causesdesire = any(
            [
                i in triplets.get("CausesDesire", []) for i in CONCEPTNET_CAUSESDESIRE_FOOD
            ]
        )
        conceptnet = any([conceptnet_symbolof, conceptnet_hasproperty, conceptnet_causesdesire])
        if conceptnet:
            food_item = elem
            return conceptnet, food_item
    return conceptnet, food_item


def lets_talk_about_check(vars):
    # user_lets_chat_about = (
    #     "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
    #     or if_chat_about_particular_topic(state_utils.get_last_human_utterance(vars), prev_uttr)
    # )
    human_utt = state_utils.get_last_human_utterance(vars)
    bot_utt = state_utils.get_last_bot_utterance(vars)
    user_lets_chat_about_food = any(
        [
            re.search(FOOD_WORDS_RE, human_utt["text"].lower()),
            if_chat_about_particular_topic(human_utt, bot_utt, compiled_pattern=FOOD_WORDS_RE),
            check_conceptnet(vars)[0],
            re.search(FOOD_SKILL_TRANSFER_PHRASES_RE, human_utt["text"].lower()),
            re.search(DONOTKNOW_LIKE_RE, human_utt["text"].lower())
        ]
    )
    # and (not state_utils.get_last_human_utterance(vars)["text"].startswith("what"))
    flag = user_lets_chat_about_food
    logger.info(f"lets_talk_about_check {flag}")
    return flag


def what_cuisine_response(vars):
    user_utt = state_utils.get_last_human_utterance(vars)
    bot_utt = state_utils.get_last_bot_utterance(vars)["text"].lower()
    linkto_food_skill_agreed = any(
        [
            req.lower() in bot_utt for req in TRIGGER_PHRASES
        ]
    )
    lets_talk_about_asked = lets_talk_about_check(vars)
    try:
        if linkto_food_skill_agreed:
            if is_yes(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            elif not is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        elif lets_talk_about_asked:
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "What cuisine do you prefer?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def cuisine_request(ngrams, vars):
    # nounphr = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # flag = bool(nounphr)
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    spacy_utt = spacy_nlp(utt)
    utt_adj = any([w.pos_ == 'ADJ' for w in spacy_utt])
    all_words = any([i in utt for i in ["all", "many", "multiple"]])
    flag = any([utt_adj, check_conceptnet(vars)[0], all_words])
    logger.info(f"cuisine_request {flag}")
    return flag


def cuisine_fact_response(vars):
    cuisine_fact = ""
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        last_utt = state_utils.get_last_human_utterance(vars)
        last_utt_lower = last_utt["text"].lower()
        conceptnet_flag, food_item = check_conceptnet(vars)
        if any([w.pos_ == 'ADJ' for w in spacy_nlp(last_utt_lower)]):
            for cuisine in list(CUISINES_FACTS.keys()):
                if cuisine in last_utt_lower:
                    cuisine_fact = CUISINES_FACTS.get(cuisine, "")
                    state_utils.save_to_shared_memory(vars, cuisine=cuisine)
                    return cuisine_fact
            if not cuisine_fact:
                return "Haven't tried it yet. What do you recommend to start with?"
        elif conceptnet_flag:
            entity_linking = last_utt["annotations"].get("entity_linking", [])
            if entity_linking:
                _facts = entity_linking[0].get("entity_pages", [])
                if _facts:
                    return f"Jummy! I know about {food_item} that {_facts[0]}"
            else:
                return "My favorite cuisine is French. I'm just in love"
            "with pastry, especially with profiteroles! How about you?"
        else:
            return "My favorite cuisine is French. I'm just in love"
        "with pastry, especially with profiteroles! How about you?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def country_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    cuisine_discussed = shared_memory.get("cuisine", "")
    try:
        if cuisine_discussed:
            if cuisine_discussed in CUISINES_COUNTRIES:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
                return f"Have you been in {CUISINES_COUNTRIES[cuisine_discussed]}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def what_fav_food_response(vars):
    food_types = ["food", "drink", "fruit", "dessert", "vegetable", "berry"]
    user_utt = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    used_food = shared_memory.get("used_food", [])
    unused_food = []
    linkto_food_skill_agreed = any(
        [
            req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
            for req in TRIGGER_PHRASES
        ]
    )
    lets_talk_about_asked = lets_talk_about_check(vars)
    try:
        if used_food:
            unused_food = [i for i in food_types if i not in used_food]
            if unused_food:
                food_type = random.choice(unused_food)
            else:
                food_type = "snack"
        else:
            food_type = "food"

        if linkto_food_skill_agreed:
            if is_yes(user_utt):
                if food_type == "food":
                    state_utils.set_confidence(vars, confidence=CONF_HIGH)
                    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                if food_type == "snack":
                    state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
                if unused_food:
                    state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

            elif not is_no(user_utt):
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                state_utils.set_confidence(vars, confidence=CONF_LOW)

        elif lets_talk_about_asked:
            if food_type == "food":
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            if food_type == "snack":
                state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
            if unused_food:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        else:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        state_utils.save_to_shared_memory(vars, used_food=used_food + [food_type])
        return f"What is your favorite {food_type}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def fav_food_request(ngrams, vars):
    flag = False
    user_fav_food = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # cobot_topic = "Food_Drink" in get_topics(state_utils.get_last_human_utterance(vars), which="cobot_topics")
    food_words_search = re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"].lower())
    if any([user_fav_food, check_conceptnet(vars), food_words_search]):
        flag = True
    logger.info(f"fav_food_request {flag}")
    return flag


def food_fact_response(vars):
    cool_words = ["cool", "tasty", "delicious"]
    opinions = ["like", "love", "adore"]
    human_utt = state_utils.get_last_human_utterance(vars)
    annotations = human_utt["annotations"]
    human_utt_text = human_utt["text"].lower()
    bot_utt_text = state_utils.get_last_bot_utterance(vars)["text"].lower()
    fact = ""
    intro = "Did you know that "
    if "berry" in bot_utt_text:
        intro = ""
        if ("berry" not in human_utt_text) and (len(human_utt_text.split()) == 1):
            berry_name = human_utt_text + "berry"
            fact = send_cobotqa(f"fact about {berry_name}")
        else:
            fact = send_cobotqa(f"fact about {human_utt_text}")
    else:
        facts = annotations.get("fact_retrieval", [])
        if facts:
            fact = facts[0]
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        if not fact:
            endings = ["Do you recommend", "Why do you like it"]
            return f"Sounds {random.choice(cool_words)}. I haven't heard about it. {random.choice(endings)}?"
        return f"I {random.choice(opinions)} it too. {intro}{fact}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def are_you_gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
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
        shared_memory = state_utils.get_shared_memory(vars)
        used_meal = shared_memory.get("used_meals", "")
        recipe = send_cobotqa(f"how to cook {used_meal}")
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
        if not (used_meal and recipe):
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
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
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
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
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
    ) and any(
        [
            is_yes(state_utils.get_last_human_utterance(vars)),
            not is_no(state_utils.get_last_human_utterance(vars))
        ]
    )
    food_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_FAV_FOOD)
    cuisine_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_CUISINE)

    if not (lets_talk_about_check(vars) or linkto_food_skill_agreed):
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
    ) and any(
        [
            is_yes(state_utils.get_last_human_utterance(vars)),
            not is_no(state_utils.get_last_human_utterance(vars))
        ]
    )
    flag = lets_talk_about_check(vars) or linkto_food_skill_agreed
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


simplified_dialogflow.add_user_transition(State.USR_CUISINE_FACT, State.SYS_TO_TRAVEL_SKILL, smth_request)
simplified_dialogflow.set_error_successor(State.USR_CUISINE_FACT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_TO_TRAVEL_SKILL, State.USR_COUNTRY, country_response)
simplified_dialogflow.set_error_successor(State.SYS_TO_TRAVEL_SKILL, State.SYS_ERR)


simplified_dialogflow.add_user_transition(State.USR_COUNTRY, State.SYS_SOMETHING, smth_request)
simplified_dialogflow.set_error_successor(State.USR_COUNTRY, State.SYS_ERR)

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
