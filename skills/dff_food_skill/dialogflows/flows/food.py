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
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.utils import is_yes, is_no, get_entities, join_words_in_or_pattern
from common.food import TRIGGER_PHRASES, FOOD_WORDS, WHAT_COOK, FOOD_UTTERANCES_RE, CUISINE_UTTERANCES_RE


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
FOOD_WORDS_RE = re.compile(FOOD_WORDS, re.IGNORECASE)
WHAT_COOK_RE = re.compile(WHAT_COOK, re.IGNORECASE)
DONOTKNOW_LIKE_RE = re.compile(join_words_in_or_pattern(DONOTKNOW_LIKE), re.IGNORECASE)
NO_WORDS_RE = re.compile(r"(\bnot\b|n't|\bno\b) ", re.IGNORECASE)
FAV_RE = re.compile(r"favou?rite|like", re.IGNORECASE)
LIKE_RE = re.compile(r"i (like|love|adore)", re.IGNORECASE)

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
    SYS_BOT_PERSONA_FAV_FOOD = auto()
    SYS_SAID_FAV_FOOD = auto()
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
        causes_desire = triplets.get("CausesDesire", [])
        conceptnet_causesdesire = any(
            [
                i in causes_desire for i in CONCEPTNET_CAUSESDESIRE_FOOD
            ]
        ) or any(
            [
                'eat' in i for i in causes_desire
            ] + [
                'cook' in i for i in causes_desire
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
    # if "weather" in human_utt["text"].lower():
    #     flag = ""
    #     logger.info(f"lets_talk_about_check {flag}, weather detected")
    #     return flag
    if if_chat_about_particular_topic(human_utt, bot_utt, compiled_pattern=FOOD_WORDS_RE):
        flag = "if_chat_about_particular_topic"
    elif re.search(FOOD_WORDS_RE, human_utt["text"]):
        flag = "FOOD_WORDS_RE"
    elif re.search(FOOD_UTTERANCES_RE, bot_utt["text"]):
        flag = "FOOD_UTTERANCES_RE"
    elif re.search(CUISINE_UTTERANCES_RE, bot_utt["text"]):
        flag = "CUISINE_UTTERANCES_RE"
    elif check_conceptnet(vars)[0]:
        flag = "check_conceptnet"
    elif re.search(DONOTKNOW_LIKE_RE, human_utt["text"]):
        flag = "DONOTKNOW_LIKE_RE"
    else:
        flag = ""
    # user_lets_chat_about_food = any(
    #     [
    #         re.search(FOOD_WORDS_RE, human_utt["text"].lower()),
    #         if_chat_about_particular_topic(human_utt, bot_utt, compiled_pattern=FOOD_WORDS_RE),
    #         check_conceptnet(vars)[0],
    #         re.search(FOOD_SKILL_TRANSFER_PHRASES_RE, human_utt["text"].lower()),
    #         re.search(DONOTKNOW_LIKE_RE, human_utt["text"].lower())
    #     ]
    # )
    # and (not state_utils.get_last_human_utterance(vars)["text"].startswith("what"))
    # flag = user_lets_chat_about_food
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
    lets_talk_about_asked = bool(lets_talk_about_check(vars))
    try:
        if linkto_food_skill_agreed:
            if is_yes(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            elif not is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        elif lets_talk_about_asked:
            state_utils.set_confidence(vars, confidence=CONF_HIGH)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "I'm a fan of Mediterranean cuisine dishes. What cuisine do you prefer?"
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
    flag = any([utt_adj, check_conceptnet(vars)[0], all_words]) and (not re.search(NO_WORDS_RE, utt))
    logger.info(f"cuisine_request {flag}")
    return flag


def cuisine_fact_response(vars):
    cuisine_fact = ""
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        last_utt = state_utils.get_last_human_utterance(vars)
        last_utt_lower = last_utt["text"].lower()
        conceptnet_flag, food_item = check_conceptnet(vars)
        if any([w.pos_ == 'ADJ' for w in spacy_nlp(last_utt_lower)]):
            for cuisine in list(CUISINES_FACTS.keys()):
                if cuisine in last_utt_lower:
                    cuisine_fact = CUISINES_FACTS.get(cuisine, "")
                    state_utils.save_to_shared_memory(vars, cuisine=cuisine)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    return cuisine_fact
            if not cuisine_fact:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return "Haven't tried it yet. What do you recommend to start with?"
        elif conceptnet_flag:
            entity_linking = last_utt["annotations"].get("entity_linking", [])
            if entity_linking:
                _facts = entity_linking[0].get("entity_pages", [])
                if _facts:
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    return f"Jummy! I know about {food_item} that {_facts[0]}"
                else:
                    return ""
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return "My favorite cuisine is French. I'm just in love " \
                       "with pastry, especially with profiteroles! How about you?"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return "My favorite cuisine is French. I'm just in love " \
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
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return f"Have you been in {CUISINES_COUNTRIES[cuisine_discussed]}?"
        else:
            state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return "Where are you from?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def what_fav_food_response(vars):
    food_types = {
        "food": "lava cake",
        "drink": "orange juice",
        "fruit": "mango",
        "dessert": "profiteroles",
        "vegetable": "broccoli",
        "berry": "blueberry"
    }
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
            unused_food = [i for i in food_types.keys() if i not in used_food]
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
                elif food_type == "snack":
                    state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                elif unused_food:
                    state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                else:
                    state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

            elif not is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_LOW)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        elif bool(lets_talk_about_asked):
            if (food_type == "food") or (lets_talk_about_asked == "if_chat_about_particular_topic"):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            elif food_type == "snack":
                state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            elif unused_food:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            else:
                state_utils.set_confidence(vars, confidence=CONF_LOWEST)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        else:
            state_utils.set_confidence(vars, confidence=CONF_LOW)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        state_utils.save_to_shared_memory(vars, used_food=used_food + [food_type])
        fav_item = food_types.get(food_type, "peanut butter")
        if food_type != "drink":
            return f"I like to eat {fav_item}. What is your favorite {food_type}?"
        else:
            return f"I like to drink {fav_item}. What is your favorite {food_type}?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def fav_food_request(ngrams, vars):
    flag = False
    user_fav_food = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # cobot_topic = "Food_Drink" in get_topics(state_utils.get_last_human_utterance(vars), which="cobot_topics")
    food_words_search = re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"])
    if all(
        [
            any([user_fav_food, check_conceptnet(vars), food_words_search]),
            condition_utils.no_requests(vars),
            not re.search(NO_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"])
        ]
    ):
        flag = True
    logger.info(f"fav_food_request {flag}")
    return flag


def food_fact_response(vars):
    acknowledgements = [
        "I like it too.", "I'm not fond of it.", "It's awesome.",
        "Fantastic.", "Loving it.", "Yummy!"
    ]
    human_utt = state_utils.get_last_human_utterance(vars)
    annotations = human_utt["annotations"]
    human_utt_text = human_utt["text"].lower()
    bot_utt_text = state_utils.get_last_bot_utterance(vars)["text"].lower()

    fact = ""
    berry_name = ""
    intro = "Did you know that "
    if "berry" in bot_utt_text:
        intro = ""
        berry_names = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
        if berry_names:
            berry_name = berry_names[0]

        if all(["berry" not in human_utt_text, len(human_utt_text.split()) == 1, berry_name]):
            berry_name += "berry"
            fact = send_cobotqa(f"fact about {berry_name}")
        elif berry_name:
            fact = send_cobotqa(f"fact about {berry_name}")
    else:
        facts = annotations.get("fact_retrieval", [])
        if facts:
            fact = facts[0]
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        if re.search(DONOTKNOW_LIKE_RE, human_utt_text):
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            state_utils.set_confidence(vars, confidence=0.)
            return error_response(vars)
        # "I have never heard about it. Could you tell me more about that please."
        elif (not fact) and check_conceptnet(vars):
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            endings = ["Do you recommend", "Why do you like it"]
            return f"I haven't heard about it. {random.choice(endings)}?"
        elif not fact:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            state_utils.set_confidence(vars, confidence=0.)
            return error_response(vars)
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return f"{random.choice(acknowledgements)} {intro}{fact}"
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
        if not (used_meal and recipe):
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            recipe = "Great! Enjoy your meal!"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        return recipe
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
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
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        return "Where are you from?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def what_fav_food_request(ngrams, vars):
    food_topic_checked = lets_talk_about_check(vars)
    linkto_food_skill_agreed = any(
        [
            req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
            for req in TRIGGER_PHRASES
        ]
    ) and any(
        [
            is_yes(state_utils.get_last_human_utterance(vars)),
            not is_no(state_utils.get_last_human_utterance(vars)),
            re.search(LIKE_RE, state_utils.get_last_human_utterance(vars)["text"].lower())
        ]
    )
    food_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_FAV_FOOD)
    cuisine_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_CUISINE)

    if any(
        [
            not (bool(food_topic_checked) or linkto_food_skill_agreed),
            food_topic_checked == "CUISINE_UTTERANCES_RE"
        ]
    ):
        flag = False
    elif food_topic_checked == "FOOD_UTTERANCES_RE":
        flag = True
    elif (food_1st_time and cuisine_1st_time):
        flag = random.choice([True, False])
    elif (food_1st_time or (not cuisine_1st_time)):
        flag = True
    else:
        flag = False
    logger.info(f"what_fav_food_request {flag}")
    return flag


def said_fav_food_request(ngrams, vars):
    flag = False
    fav_in_bot_utt = re.search(FAV_RE, state_utils.get_last_bot_utterance(vars)["text"])
    food_checked = any(
        [
            re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"]),
            check_conceptnet(vars)[0]
        ]
    )
    if (fav_in_bot_utt and food_checked):
        flag = True
    logger.info(f"said_fav_food_request {flag}")
    return flag


def bot_persona_fav_food_request(ngrams, vars):
    flag = False
    if all(
        [
            "my favorite food is lava cake" in state_utils.get_last_bot_utterance(vars)["text"].lower(),
            fav_food_request(ngrams, vars)
        ]
    ):
        flag = True
    logger.info(f"bot_persona_fav_food_request {flag}")
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
    flag = bool(lets_talk_about_check(vars)) or linkto_food_skill_agreed
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
        State.SYS_SAID_FAV_FOOD: said_fav_food_request,
        State.SYS_WHAT_COOK: what_cook_request,
        State.SYS_BOT_PERSONA_FAV_FOOD: bot_persona_fav_food_request,
        State.SYS_WHAT_FAV_FOOD: what_fav_food_request,
        State.SYS_WHAT_CUISINE: what_cuisine_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################

simplified_dialogflow.add_system_transition(State.SYS_SAID_FAV_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_SAID_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_WHAT_FAV_FOOD, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_BOT_PERSONA_FAV_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_BOT_PERSONA_FAV_FOOD, State.SYS_ERR)


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
