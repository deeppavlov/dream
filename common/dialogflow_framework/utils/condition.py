import logging
import re


from nltk.stem import WordNetLemmatizer

import common.utils as common_utils
import common.universal_templates as universal_templates
import common.dialogflow_framework.utils.state as state_utils


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

wnl = WordNetLemmatizer()


#  vars is described in README.md


def is_opinion_request(vars):
    flag = common_utils.is_opinion_request(vars["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_opinion_request = {flag}")
    return flag


def is_switch_topic(vars):
    flag = universal_templates.is_switch_topic(vars["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_switch_topic = {flag}")
    return flag


def is_question(vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    flag = common_utils.is_question(text)
    logging.debug(f"is_question = {flag}")
    return flag


def is_lets_chat_about_topic(vars):
    last_human_uttr = state_utils.get_last_human_utterance(vars)
    last_human_uttr_text = last_human_uttr["text"]
    last_bot_uttr_text = state_utils.get_last_bot_utterance(vars)["text"]
    intents = common_utils.get_intents(last_human_uttr, which="intent_responder")

    flag = "lets_chat_about" in intents
    flag = flag or universal_templates.if_lets_chat_about_topic(last_human_uttr_text)
    flag = flag or re.search(common_utils.COMPILE_WHAT_TO_TALK_ABOUT, last_bot_uttr_text)
    return flag


def is_begin_of_dialog(vars, begin_dialog_n=10):
    flag = vars["agent"]["human_utter_index"] < begin_dialog_n
    logging.debug(f"is_begin_of_dialog = {flag}")
    return flag


def is_interrupted(vars):
    flag = (vars["agent"]["human_utter_index"] - vars["agent"]["last_human_utter_index"]) != 1
    logging.debug(f"is_interrupted = {flag}")
    return flag


def is_long_interrupted(vars, how_long=3):
    flag = (vars["agent"]["human_utter_index"] - vars["agent"]["last_human_utter_index"]) > how_long
    logging.debug(f"is_long_interrupted = {flag}")
    return flag


def is_new_human_entity(vars):
    new_entities = state_utils.get_new_human_labeled_noun_phrase(vars)
    flag = bool(new_entities)
    logging.debug(f"is_new_human_entity = {flag}")
    return flag


def is_entities(vars):
    entities = state_utils.get_labeled_noun_phrase(vars)
    flag = bool(entities)
    logging.debug(f"is_entities = {flag}")
    return flag


def is_first_time_of_state(vars, state):
    flag = state not in list(vars["agent"]["history"].values())
    logging.debug(f"is_first_time_of_state {state} = {flag}")
    return flag


def is_plural(word):
    lemma = wnl.lemmatize(word, "n")
    plural = True if word is not lemma else False
    return plural


def is_first_our_response(vars):
    flag = len(list(vars["agent"]["history"].values())) == 0
    logging.debug(f"is_first_our_response = {flag}")
    return flag
