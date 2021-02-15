import logging
import pathlib


from nltk.stem import WordNetLemmatizer

import common.utils as common_utils
import common.universal_templates as universal_templates

import dialog_flows.utils as dialog_flows_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

wnl = WordNetLemmatizer()


banned_nouns_file = pathlib.Path("/src/programy_storage/sets/banned_noun.txt")
BANNED_NOUNS = [noun.strip() for noun in banned_nouns_file.open().readlines() if "#" not in noun]

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
    text = dialog_flows_utils.get_last_user_utterance(vars)["text"]
    flag = common_utils.is_question(text)
    logging.debug(f"is_question = {flag}")
    return flag


def is_lets_chat_about_topic(vars):
    text = dialog_flows_utils.get_last_user_utterance(vars)["text"]
    flag = universal_templates.if_lets_chat_about_topic(text.lower())
    logging.debug(f"is_lets_chat_about_topic = {flag}")
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
    new_entities = dialog_flows_utils.get_new_human_entities(vars)
    flag = bool(new_entities)
    logging.debug(f"is_new_human_entity = {flag}")
    return flag


def is_entities(vars):
    entities = dialog_flows_utils.get_entities(vars)
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
