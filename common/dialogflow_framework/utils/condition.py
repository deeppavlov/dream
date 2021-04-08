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


def is_lets_chat_about_topic_human_initiative(vars):
    flag = universal_templates.if_chat_about_particular_topic(
        state_utils.get_last_human_utterance(vars), state_utils.get_last_bot_utterance(vars))
    logging.debug(f"is_lets_chat_about_topic_human_initiative = {flag}")
    return flag


def is_lets_chat_about_topic(vars):
    flag = is_lets_chat_about_topic_human_initiative(vars)

    last_human_uttr = state_utils.get_last_human_utterance(vars)
    last_bot_uttr_text = state_utils.get_last_bot_utterance(vars)["text"]
    is_bot_initiative = bool(re.search(universal_templates.COMPILE_WHAT_TO_TALK_ABOUT, last_bot_uttr_text))
    flag = flag or (is_bot_initiative and not common_utils.is_no(last_human_uttr))
    logging.debug(f"is_lets_chat_about_topic = {flag}")
    return flag


def is_begin_of_dialog(vars, begin_dialog_n=10):
    flag = state_utils.get_human_utter_index(vars) < begin_dialog_n
    logging.debug(f"is_begin_of_dialog = {flag}")
    return flag


def is_interrupted(vars):
    flag = (state_utils.get_human_utter_index(vars) - state_utils.get_previous_human_utter_index(vars)) != 1
    logging.debug(f"is_interrupted = {flag}")
    return flag


def is_long_interrupted(vars, how_long=3):
    flag = (state_utils.get_human_utter_index(vars) - state_utils.get_previous_human_utter_index(vars)) > how_long
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


def is_no_human_abandon(vars):
    """Is dialog breakdown in human utterance or no. Uses MIDAS hold/abandon classes.
    """
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")
    if "abandon" not in midas_classes:
        return True
    return False


def no_requests(vars):
    """Function to determine if user didn't asked to switch topic, user didn't ask to talk about something particular,
    user didn't requested some special intents (like what_is_your_name, what_are_you_talking_about),
    user didn't asked or requested something,
    """
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    intents_by_catcher = common_utils.get_intents(
        state_utils.get_last_human_utterance(vars), probs=False, which="intent_catcher"
    )
    is_high_priority_intent = any([intent not in common_utils.service_intents for intent in intents_by_catcher])

    request_intents = [
        "opinion_request",
        "topic_switching",
        "lets_chat_about",
        "what_are_you_talking_about",
        "Information_RequestIntent",
        "Topic_SwitchIntent",
        "Opinion_RequestIntent",
    ]
    is_not_request_intent = all([intent not in request_intents for intent in intents])
    is_no_question = "?" not in state_utils.get_last_human_utterance(vars)["text"]

    if not is_high_priority_intent and is_not_request_intent and is_no_question:
        return True
    return False


def is_yes_vars(vars):
    flag = True
    flag = flag and common_utils.is_yes(state_utils.get_last_human_utterance(vars))
    return flag


def is_no_vars(vars):
    flag = True
    flag = flag and common_utils.is_no(state_utils.get_last_human_utterance(vars))
    return flag
