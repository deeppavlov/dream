# %%
import json
import logging
import os
import random
import re

from common.fact_random import get_fact
from enum import Enum, auto

import sentry_sdk
from spacy import load

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import dialogflows.scopes as scopes
from common.universal_templates import if_chat_about_particular_topic, DONOTKNOW_LIKE, COMPILE_NOT_WANT_TO_TALK_ABOUT_IT
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.utils import is_yes, is_no, get_entities, join_words_in_or_pattern, get_comet_conceptnet_annotations
from common.food import (
    TRIGGER_PHRASES,
    FOOD_WORDS,
    WHAT_COOK,
    FOOD_UTTERANCES_RE,
    CUISINE_UTTERANCES_RE,
    CONCEPTNET_SYMBOLOF_FOOD,
    CONCEPTNET_HASPROPERTY_FOOD,
    CONCEPTNET_CAUSESDESIRE_FOOD,
    ACKNOWLEDGEMENTS,
    FOOD_FACT_ACKNOWLEDGEMENTS,
)
from common.link import link_to_skill2i_like_to_talk
from dialogflows.flows.fast_food import State as FFState
from dialogflows.flows.fast_food import fast_food_request


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


spacy_nlp = load("en_core_web_sm")


with open("cuisines_facts.json", "r") as f:
    CUISINES_FACTS = json.load(f)

FOOD_WORDS_RE = re.compile(FOOD_WORDS, re.IGNORECASE)
WHAT_COOK_RE = re.compile(WHAT_COOK, re.IGNORECASE)
DONOTKNOW_LIKE_RE = re.compile(join_words_in_or_pattern(DONOTKNOW_LIKE), re.IGNORECASE)
NO_WORDS_RE = re.compile(r"(\bnot\b|n't|\bno\b) ", re.IGNORECASE)
# FAV_RE = re.compile(r"favou?rite|like", re.IGNORECASE)
LIKE_RE = re.compile(r"\bi (like|love|adore)( to (bake|cook|eat)|)", re.IGNORECASE)

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
    "mexican": "Mexico",
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
    SYS_CHECK_COOKING = auto()
    USR_SUGGEST_COOK = auto()
    SYS_YES_COOK = auto()
    SYS_NO_COOK = auto()
    SYS_ENSURE_FOOD = auto()
    SYS_LINKTO_PLUS_NO = auto()
    SYS_LINKTO_PLUS_NO_RECIPE = auto()
    SYS_MORE_FACTS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


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


def dont_want_talk(vars):
    utt = state_utils.get_last_human_utterance(vars)["text"]
    flag = bool(re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, utt))
    logger.info(f"dont_want_talk {flag}")
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


def is_question(vars):
    annotations_sentseg = state_utils.get_last_human_utterance(vars)["annotations"].get("sentseg", {})
    flag = "?" in annotations_sentseg.get("punct_sent", "")
    return flag


def check_conceptnet(vars):
    annotations_conceptnet = get_comet_conceptnet_annotations(state_utils.get_last_human_utterance(vars))
    conceptnet = False
    food_item = None
    for elem, triplets in annotations_conceptnet.items():
        symbol_of = triplets.get("SymbolOf", [])
        conceptnet_symbolof = any(
            [i in symbol_of for i in CONCEPTNET_SYMBOLOF_FOOD] + ["chicken" in i for i in symbol_of]
        )
        has_property = triplets.get("HasProperty", [])
        conceptnet_hasproperty = any([i in has_property for i in CONCEPTNET_HASPROPERTY_FOOD])
        causes_desire = triplets.get("CausesDesire", [])
        conceptnet_causesdesire = any(
            [i in causes_desire for i in CONCEPTNET_CAUSESDESIRE_FOOD]
            + ["eat" in i for i in causes_desire]
            + ["cook" in i for i in causes_desire]
            + ["food" in i for i in causes_desire]
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
    if dont_want_talk(vars):
        flag = ""
    elif if_chat_about_particular_topic(human_utt, bot_utt, compiled_pattern=FOOD_WORDS_RE):
        flag = "if_chat_about_particular_topic"
    elif bool(re.search(FOOD_WORDS_RE, human_utt["text"])):
        flag = "FOOD_WORDS_RE"
    elif bool(re.search(FOOD_UTTERANCES_RE, bot_utt["text"])):
        flag = "FOOD_UTTERANCES_RE"
    elif bool(re.search(CUISINE_UTTERANCES_RE, bot_utt["text"])):
        flag = "CUISINE_UTTERANCES_RE"
    elif check_conceptnet(vars)[0]:
        flag = "check_conceptnet"
    elif bool(re.search(DONOTKNOW_LIKE_RE, human_utt["text"])):
        flag = "DONOTKNOW_LIKE_RE"
    else:
        flag = ""
    # user_lets_chat_about_food = any(
    #     [
    #         bool(re.search(FOOD_WORDS_RE, human_utt["text"].lower())),
    #         if_chat_about_particular_topic(human_utt, bot_utt, compiled_pattern=FOOD_WORDS_RE),
    #         check_conceptnet(vars)[0],
    #         bool(re.search(FOOD_SKILL_TRANSFER_PHRASES_RE, human_utt["text"].lower())),
    #         bool(re.search(DONOTKNOW_LIKE_RE, human_utt["text"].lower()))
    #     ]
    # )
    # and (not state_utils.get_last_human_utterance(vars)["text"].startswith("what"))
    # flag = user_lets_chat_about_food
    logger.info(f"lets_talk_about_check {flag}")
    return flag


def what_cuisine_response(vars):
    user_utt = state_utils.get_last_human_utterance(vars)
    bot_utt = state_utils.get_last_bot_utterance(vars)["text"].lower()
    banned_words = ["water"]
    linkto_food_skill_agreed = any([req.lower() in bot_utt for req in TRIGGER_PHRASES])
    lets_talk_about_asked = bool(lets_talk_about_check(vars))
    try:
        if not any([i in user_utt["text"].lower() for i in banned_words]):
            if linkto_food_skill_agreed:
                if is_yes(user_utt):
                    state_utils.set_confidence(vars, confidence=CONF_HIGH)
                    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                elif not is_no(user_utt):
                    state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
                elif is_no(user_utt):
                    state_utils.set_confidence(vars, confidence=CONF_HIGH)
                    state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                    return ACKNOWLEDGEMENTS["cuisine"]
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
        return error_response(vars)


def cuisine_request(ngrams, vars):
    # nounphr = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # flag = bool(nounphr)
    utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    spacy_utt = spacy_nlp(utt)
    utt_adj = any([w.pos_ == "ADJ" for w in spacy_utt])
    all_words = any([i in utt for i in ["all", "many", "multiple"]])
    flag = any([utt_adj, check_conceptnet(vars)[0], all_words]) and (
        not any([bool(re.search(NO_WORDS_RE, utt)), dont_want_talk(vars)])
    )
    logger.info(f"cuisine_request {flag}")
    return flag


def cuisine_fact_response(vars):
    cuisine_fact = ""
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        last_utt = state_utils.get_last_human_utterance(vars)
        last_utt_lower = last_utt["text"].lower()
        conceptnet_flag, food_item = check_conceptnet(vars)
        if any([w.pos_ == "ADJ" for w in spacy_nlp(last_utt_lower)]):
            for cuisine in list(CUISINES_FACTS.keys()):
                if cuisine in last_utt_lower:
                    cuisine_fact = CUISINES_FACTS.get(cuisine, "")
                    state_utils.save_to_shared_memory(vars, cuisine=cuisine)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    return cuisine_fact
            if not cuisine_fact:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                response = "You have such a refined taste in food! "
                "I haven't tried it yet. What do you recommend to start with?"
                state_utils.add_acknowledgement_to_response_parts(vars)
                return response
        elif conceptnet_flag:
            entity_linking = last_utt["annotations"].get("entity_linking", [])
            if entity_linking:
                _facts = entity_linking[0].get("entity_pages", [])
                if _facts:
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                    response = f"You're a gourmet! I know about {food_item} that {_facts[0]}"
                    state_utils.add_acknowledgement_to_response_parts(vars)
                    return response
                else:
                    return ""
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return (
                    "My favorite cuisine is French. I'm just in love "
                    "with pastry, especially with profiteroles! How about you?"
                )
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return (
                "My favorite cuisine is French. I'm just in love "
                "with pastry, especially with profiteroles! How about you?"
            )
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def country_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    cuisine_discussed = shared_memory.get("cuisine", "")
    try:
        if cuisine_discussed:
            if cuisine_discussed in CUISINES_COUNTRIES:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return f"Have you ever been in {CUISINES_COUNTRIES[cuisine_discussed]}?"
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def to_travel_skill_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    cuisine_discussed = shared_memory.get("cuisine", "")
    if cuisine_discussed:
        if cuisine_discussed in CUISINES_COUNTRIES:
            flag = True
    logger.info(f"to_travel_skill_request {flag}")
    return flag


def what_fav_food_response(vars):
    food_types = {
        "food": [
            "lava cake",
            "This cake is delicious, decadent, addicting, divine, just so incredibly good!!!"
            " Soft warm chocolate cake outside giving way to a creamy, smooth stream of warm "
            "liquid chocolate inside, ensuring every forkful is bathed in velvety chocolate. "
            "It is my love at first bite.",
        ],
        "drink": [
            "orange juice",
            "Isually I drink it at breakfast - it’s sweet with natural sugar for quick energy."
            " Oranges have lots of vitamins and if you drink it with pulp, it has fiber. Also,"
            " oranges are rich in vitamin C that keeps your immune system healthy.",
        ],
        "fruit": [
            "mango",
            "Every year I wait for the summers so that I can lose myself in the aroma of perfectly"
            " ripened mangoes and devour its heavenly sweet taste. Some people prefer mangoes which"
            " are tangy and sour. However, I prefer sweet ones that taste like honey.",
        ],
        "dessert": [
            "profiteroles",
            "Cream puffs of the size of a hamburger on steroids, the two pate a choux ends"
            " showcased almost two cups of whipped cream - light, fluffy, and fresh. "
            "There is nothing better than choux pastry!",
        ],
        "vegetable": [
            "broccoli",
            "This hearty and tasty vegetable is rich in dozens of nutrients. It is said "
            "to pack the most nutritional punch of any vegetable. When I think about green"
            " vegetables to include in my diet, broccoli is one of the foremost veggies to "
            "come to my mind.",
        ],
        "berry": [
            "blueberry",
            "Fresh blueberries are delightful and have a slightly sweet taste that is mixed"
            " with a little bit of acid from the berry. When I bite down on a blueberry,"
            " I enjoy a burst of juice as the berry pops, and this juice is very sweet. "
            "Blueberries are the blues that make you feel good!",
        ],
        "snack": [
            "peanut butter",
            "It tastes great! Creamy, crunchy or beyond the jar, there is a special place "
            "among my taste receptors for that signature peanutty flavor. I always gravitate"
            " toward foods like peanut butter chocolate cheesecake, and peanut butter cottage"
            " cookies. There are so many peanut butter flavored items for all kinds of food products!"
            " Still, sometimes it’s best delivered on a spoon.",
        ],
    }
    user_utt = state_utils.get_last_human_utterance(vars)
    bot_utt = state_utils.get_last_bot_utterance(vars)["text"].lower()
    question = ""
    shared_memory = state_utils.get_shared_memory(vars)
    used_food = shared_memory.get("used_food", [])
    unused_food = []
    linkto_food_skill_agreed = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in TRIGGER_PHRASES]
    )
    lets_talk_about_asked = lets_talk_about_check(vars)
    try:
        if used_food:
            unused_food = [i for i in food_types.keys() if i not in used_food]
            if unused_food:
                food_type = random.choice(unused_food)
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
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
            elif is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return ACKNOWLEDGEMENTS["fav_food_cook"]

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
        fav_item = food_types.get(food_type, [])
        if fav_item:
            if food_type != "drink":
                if "what is your favorite food" in bot_utt:
                    question = f" What {food_type} do you like?"
                else:
                    question = " What is a typical meal from your country?"
                return f"I like to eat {fav_item[0]}. {fav_item[1]}" + question
            else:
                if "what is your favorite food" in bot_utt:
                    question = f" What {food_type} do you prefer?"
                else:
                    question = " What do you usually like to drink when you go out?"
                return f"I like to drink {fav_item[0]}. {fav_item[1]}" + question
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def fav_food_check(vars):
    flag = False
    user_fav_food = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
    # cobot_topic = "Food_Drink" in get_topics(state_utils.get_last_human_utterance(vars), which="cobot_topics")
    food_words_search = bool(re.search(FOOD_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"]))
    if all(
        [
            any([user_fav_food, check_conceptnet(vars), food_words_search]),
            # condition_utils.no_requests(vars),
            not bool(re.search(NO_WORDS_RE, state_utils.get_last_human_utterance(vars)["text"])),
            not dont_want_talk(vars),
        ]
    ):
        flag = True
    logger.info(f"fav_food_check {flag}")
    return flag


def fav_food_request(ngrams, vars):
    flag = fav_food_check(vars)
    logger.info(f"fav_food_request {flag}")
    return flag


def food_fact_response(vars):
    human_utt = state_utils.get_last_human_utterance(vars)
    annotations = human_utt["annotations"]
    human_utt_text = human_utt["text"].lower()
    bot_utt_text = state_utils.get_last_bot_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    used_facts = shared_memory.get("used_facts", [])

    fact = ""
    facts = []
    entity = ""
    berry_name = ""

    linkto_check = any([linkto in bot_utt_text for linkto in link_to_skill2i_like_to_talk["dff_food_skill"]])
    black_list_check = any(list(annotations.get("badlisted_words", {}).values()))
    conceptnet_flag, food_item = check_conceptnet(vars)

    entities_facts = annotations.get("fact_retrieval", {}).get("topic_facts", [])
    for entity_facts in entities_facts:
        if entity_facts["entity_type"] in ["food", "fruit", "vegetable", "berry"]:
            if entity_facts["facts"]:
                facts = entity_facts["facts"][0].get("sentences", [])
                entity = entity_facts["entity_substr"]
            else:
                facts = []

    if not facts:
        facts = annotations.get("fact_random", [])

    if black_list_check:
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        return error_response(vars)
    elif conceptnet_flag and all(["shower" not in human_utt_text, " mela" not in human_utt_text]):
        if "berry" in bot_utt_text.lower():
            berry_names = get_entities(state_utils.get_last_human_utterance(vars), only_named=False, with_labels=False)
            if berry_names:
                berry_name = berry_names[0]

            if all(["berr" not in human_utt_text, len(human_utt_text.split()) == 1, berry_name]):
                berry_name += "berry"
                fact = get_fact(berry_name, f"fact about {berry_name}")
                entity = berry_name
            elif berry_name:
                if facts and entity:
                    fact = random.choice([i for i in facts if i not in used_facts])
                    # facts[0]
                elif facts:
                    for facts_item in facts:
                        if all(
                            [
                                facts_item.get("entity_substr", "xxx") in food_item,
                                facts_item.get("fact", "") not in used_facts,
                            ]
                        ):
                            fact = facts_item.get("fact", "")
                            entity = facts_item.get("entity_substr", "")
                            break
                        else:
                            fact = ""
                            entity = ""
        else:
            if all([facts, entity, entity in food_item]):
                fact = random.choice([i for i in facts if i not in used_facts])
                # facts[0]
            elif facts and not entity:
                for facts_item in facts:
                    if all(
                        [
                            facts_item.get("entity_substr", "xxx") in food_item,
                            facts_item.get("fact", "") not in used_facts,
                        ]
                    ):
                        fact = facts_item.get("fact", "")
                        entity = facts_item.get("entity_substr", "")
                        break
                    else:
                        fact = ""
                        entity = ""
            else:
                fact = ""
                entity = ""
        acknowledgement = random.choice(FOOD_FACT_ACKNOWLEDGEMENTS).replace("ENTITY", entity.lower())
        state_utils.save_to_shared_memory(vars, used_facts=used_facts + [fact])

        try:
            if bot_persona_fav_food_check(vars) or len(state_utils.get_last_human_utterance(vars)["text"].split()) == 1:
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
            else:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
            if bool(re.search(DONOTKNOW_LIKE_RE, human_utt_text)):
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return "Well, as for me, I am a fan of pizza despite I cannot eat as humans."
            elif any([dont_want_talk(vars), bool(re.search(NO_WORDS_RE, human_utt_text))]):
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
            elif (not fact) and conceptnet_flag:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return "Why do you like it?"
            elif not fact:
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
            elif fact and entity:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                if len(used_facts):
                    return f"{fact} Do you want me to tell you more about {entity}?"
                else:
                    response = acknowledgement + f"{fact} Do you want to hear more about {entity}?"
                    state_utils.add_acknowledgement_to_response_parts(vars)
                    return response
            elif fact:
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                if len(used_facts):
                    return f"{fact} Do you want me to tell you more about {entity}?"
                else:
                    return f"Okay. {fact} I can share with you one more cool fact. Do you agree?"
            elif linkto_check:
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                return "Sorry. I didn't get what kind of food you have mentioned. Could you repeat it please?"
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            return error_response(vars)
    elif linkto_check:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "Sorry. I didn't get what kind of food you have mentioned. Could you repeat it please?"
    else:
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        return error_response(vars)


def more_facts_request(ngrams, vars):
    shared_memory = state_utils.get_shared_memory(vars)
    used_facts = shared_memory.get("used_facts", [])

    flag = all([bool(len(used_facts)), condition_utils.no_special_switch_off_requests(vars), yes_request(ngrams, vars)])
    logger.info(f"more_facts_request {flag}")
    return flag


def are_you_gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        return "Are you a gourmet?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
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
            return f"I've recently found a couple easy and healthy meals. How about cooking {meal}?"
        else:
            return f"Okay. Give me one more chance. I recommend {meal}."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def recipe_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_meal = shared_memory.get("used_meals", "")
        recipe = get_fact(used_meal, f"how to cook {used_meal}")
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        if not (used_meal and recipe):
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            recipe = "Great! Enjoy your meal!"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        return recipe
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def gourmet_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        response = "It seems you're a gourmet! What meal do you like?"
        state_utils.add_acknowledgement_to_response_parts(vars)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def smth_request(ngrams, vars):
    flag = condition_utils.no_requests(vars) and (not dont_want_talk(vars))
    logger.info(f"smth_request {flag}")
    return flag


def smth_random_request(ngrams, vars):
    flag = condition_utils.no_requests(vars)
    flag = flag and random.choice([True, False])
    logger.info(f"smth_random_request {flag}")
    return flag


def where_are_you_from_response(vars):
    try:
        state_utils.set_confidence(vars, confidence=CONF_LOW)
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        return "Where are you from?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def suggest_cook_response(vars):
    user_utt = state_utils.get_last_human_utterance(vars)
    try:
        linkto_food_skill_agreed = any(
            [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in TRIGGER_PHRASES]
        )
        if linkto_food_skill_agreed:
            if is_yes(user_utt) or bool(re.search(LIKE_RE, user_utt["text"].lower())):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            elif not is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_MIDDLE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            elif is_no(user_utt):
                state_utils.set_confidence(vars, confidence=CONF_HIGH)
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return ACKNOWLEDGEMENTS["fav_food_cook"]
            else:
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
                return error_response(vars)
            return "May I recommend you a meal to try to practice cooking?"
        else:
            state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def what_fav_food_request(ngrams, vars):
    food_topic_checked = lets_talk_about_check(vars)
    food_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_FAV_FOOD)
    cuisine_1st_time = condition_utils.is_first_time_of_state(vars, State.SYS_WHAT_CUISINE)
    if any([not bool(food_topic_checked), food_topic_checked == "CUISINE_UTTERANCES_RE", dont_want_talk(vars)]):
        flag = False
    elif (food_topic_checked == "FOOD_UTTERANCES_RE") or (food_topic_checked == "if_chat_about_particular_topic"):
        flag = True
    elif food_1st_time and cuisine_1st_time:
        flag = random.choice([True, False])
    elif food_1st_time or (not cuisine_1st_time):
        flag = True
    else:
        flag = False
    logger.info(f"what_fav_food_request {flag}")
    return flag


def check_cooking_request(ngrams, vars):
    linkto_food_skill_agreed = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in TRIGGER_PHRASES]
    ) and any(
        [
            is_yes(state_utils.get_last_human_utterance(vars)),
            not is_no(state_utils.get_last_human_utterance(vars)),
            bool(re.search(LIKE_RE, state_utils.get_last_human_utterance(vars)["text"].lower())),
        ]
    )
    if linkto_food_skill_agreed:
        flag = True
    else:
        flag = False
    logger.info(f"check_cooking_request {flag}")
    return flag


def said_fav_food_request(ngrams, vars):
    flag = False
    user_utt_text = state_utils.get_last_human_utterance(vars)["text"]
    bot_utt_text = state_utils.get_last_bot_utterance(vars)["text"]
    food_topic_checked = lets_talk_about_check(vars)
    # fav_in_bot_utt = bool(re.search(FAV_RE, state_utils.get_last_bot_utterance(vars)["text"]))
    food_checked = any([bool(re.search(FOOD_WORDS_RE, user_utt_text)), check_conceptnet(vars)[0]])
    linkto_check = any([linkto in bot_utt_text for linkto in link_to_skill2i_like_to_talk["dff_food_skill"]])
    if any(
        [
            dont_want_talk(vars),
            food_topic_checked == "FOOD_UTTERANCES_RE",
            food_topic_checked == "if_chat_about_particular_topic",
        ]
    ):
        flag = False
    # (fav_in_bot_utt and
    elif linkto_check or food_checked:
        flag = True
    else:
        flag = False
    logger.info(f"said_fav_food_request {flag}")
    return flag


def bot_persona_fav_food_check(vars):
    flag = False
    if all(
        [
            "my favorite food is lava cake" in state_utils.get_last_bot_utterance(vars)["text"].lower(),
            fav_food_check(vars),
        ]
    ):
        flag = True
    logger.info(f"bot_persona_fav_food_check {flag}")
    return flag


def bot_persona_fav_food_request(ngrams, vars):
    flag = bot_persona_fav_food_check(vars)
    logger.info(f"bot_persona_fav_food_request {flag}")
    return flag


def what_cuisine_request(ngrams, vars):
    linkto_food_skill_agreed = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in TRIGGER_PHRASES]
    ) and any(
        [is_yes(state_utils.get_last_human_utterance(vars)), not is_no(state_utils.get_last_human_utterance(vars))]
    )
    flag = (bool(lets_talk_about_check(vars)) or linkto_food_skill_agreed) and (not dont_want_talk(vars))
    logger.info(f"what_cuisine_request {flag}")
    return flag


def ensure_food_request(ngrams, vars):
    flag = "I didn't get what kind of food have you mentioned" in state_utils.get_last_bot_utterance(vars)["text"]
    logger.info(f"ensure_food_request {flag}")
    return flag


def linkto_plus_no_request(ngrams, vars):
    bot_utt = state_utils.get_last_bot_utterance(vars)["text"]
    flag = any([ackn in bot_utt for ackn in ACKNOWLEDGEMENTS.values()])
    flag = flag and condition_utils.no_special_switch_off_requests(vars)
    logger.info(f"linkto_plus_no_request {flag}")
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
        State.SYS_BOT_PERSONA_FAV_FOOD: bot_persona_fav_food_request,
        State.SYS_CHECK_COOKING: check_cooking_request,
        State.SYS_SAID_FAV_FOOD: said_fav_food_request,
        State.SYS_WHAT_FAV_FOOD: what_fav_food_request,
        State.SYS_WHAT_CUISINE: what_cuisine_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################

simplified_dialogflow.add_system_transition(State.SYS_SAID_FAV_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_SAID_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CHECK_COOKING, State.USR_SUGGEST_COOK, suggest_cook_response)
simplified_dialogflow.set_error_successor(State.SYS_CHECK_COOKING, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_SUGGEST_COOK,
    {State.SYS_YES_COOK: yes_request, State.SYS_NO_COOK: no_request, State.SYS_LINKTO_PLUS_NO: linkto_plus_no_request},
)
simplified_dialogflow.set_error_successor(State.USR_SUGGEST_COOK, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_YES_COOK, State.USR_HOW_ABOUT_MEAL1, how_about_meal_response)
simplified_dialogflow.set_error_successor(State.SYS_YES_COOK, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_NO_COOK, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_NO_COOK, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_WHAT_FAV_FOOD, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_BOT_PERSONA_FAV_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_BOT_PERSONA_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_WHAT_CUISINE, State.USR_WHAT_CUISINE, what_cuisine_response)
simplified_dialogflow.set_error_successor(State.SYS_WHAT_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_FAV_FOOD,
    {State.SYS_FAV_FOOD: fav_food_request, State.SYS_LINKTO_PLUS_NO_RECIPE: linkto_plus_no_request},
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_FAV_FOOD, State.SYS_ERR)


simplified_dialogflow.add_system_transition(
    State.SYS_LINKTO_PLUS_NO_RECIPE, State.USR_SUGGEST_COOK, suggest_cook_response
)
simplified_dialogflow.set_error_successor(State.SYS_LINKTO_PLUS_NO_RECIPE, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_CUISINE,
    {State.SYS_CUISINE: cuisine_request, State.SYS_LINKTO_PLUS_NO: linkto_plus_no_request},
)
simplified_dialogflow.set_error_successor(State.USR_WHAT_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_CUISINE, State.USR_CUISINE_FACT, cuisine_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_CUISINE, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_LINKTO_PLUS_NO, State.USR_WHAT_FAV_FOOD, what_fav_food_response)
simplified_dialogflow.set_error_successor(State.SYS_LINKTO_PLUS_NO, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_CUISINE_FACT,
    {State.SYS_TO_TRAVEL_SKILL: to_travel_skill_request, State.USR_WHAT_FAV_FOOD: what_fav_food_response},
)
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


simplified_dialogflow.add_user_serial_transitions(
    State.USR_FOOD_FACT,
    {
        State.SYS_ENSURE_FOOD: ensure_food_request,
        State.SYS_MORE_FACTS: more_facts_request,
        State.SYS_SOMETHING: smth_random_request,
        (scopes.FAST_FOOD, FFState.USR_START): fast_food_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_FOOD_FACT, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_MORE_FACTS, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_MORE_FACTS, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_ENSURE_FOOD, State.USR_FOOD_FACT, food_fact_response)
simplified_dialogflow.set_error_successor(State.SYS_ENSURE_FOOD, State.SYS_ERR)


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
