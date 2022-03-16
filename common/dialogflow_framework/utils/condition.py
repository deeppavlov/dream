import logging
import re

from nltk.stem import WordNetLemmatizer

import common.utils as common_utils
import common.universal_templates as universal_templates
import common.dialogflow_framework.utils.state as state_utils
from common.acknowledgements import GENERAL_ACKNOWLEDGEMENTS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

wnl = WordNetLemmatizer()


#  vars is described in README.md


def was_clarification_request(vars):
    flag = vars["agent"]["clarification_request_flag"]
    logging.debug(f"was_clarification_request = {flag}")
    return flag


def is_opinion_request(vars):
    flag = common_utils.is_opinion_request(vars["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_opinion_request = {flag}")
    return flag


def is_opinion_expression(vars):
    flag = common_utils.is_opinion_expression(vars["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_opinion_expression = {flag}")
    return flag


def is_previous_turn_dff_suspended(vars):
    flag = vars["agent"].get("previous_turn_dff_suspended", False)
    logging.debug(f"is_previous_turn_dff_suspended = {flag}")
    return flag


def is_current_turn_dff_suspended(vars):
    flag = vars["agent"].get("current_turn_dff_suspended", False)
    logging.debug(f"is_current_turn_dff_suspended = {flag}")
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
        state_utils.get_last_human_utterance(vars), state_utils.get_last_bot_utterance(vars)
    )
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
    flag = (
        state_utils.get_human_utter_index(vars) - state_utils.get_previous_human_utter_index(vars)
    ) != 1 and not was_clarification_request(vars)
    logging.debug(f"is_interrupted = {flag}")
    return flag


def is_long_interrupted(vars, how_long=3):
    flag = (
        state_utils.get_human_utter_index(vars) - state_utils.get_previous_human_utter_index(vars)
    ) > how_long and not was_clarification_request(vars)
    logging.debug(f"is_long_interrupted = {flag}")
    return flag


def is_new_human_entity(vars):
    new_entities = state_utils.get_new_human_labeled_noun_phrase(vars)
    flag = bool(new_entities)
    logging.debug(f"is_new_human_entity = {flag}")
    return flag


def get_last_state(vars):
    last_state = ""
    history = list(vars["agent"]["history"].items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        last_state = history_sorted[-1][1]
    return last_state


def get_n_last_state(vars, n):
    last_state = ""
    history = list(vars["agent"]["history"].items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        if len(history_sorted) >= n:
            last_state = history_sorted[-n][1]
    return last_state


def is_last_state(vars, state):
    flag = False
    history = list(vars["agent"]["history"].items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        last_state = history_sorted[-1][1]
        if last_state == state:
            flag = True
    return flag


def is_first_time_of_state(vars, state):
    flag = state not in list(vars["agent"]["history"].values())
    logging.debug(f"is_first_time_of_state {state} = {flag}")
    return flag


def if_was_prev_active(vars):
    flag = False
    skill_uttr_indices = set(vars["agent"]["history"].keys())
    human_uttr_index = str(vars["agent"]["human_utter_index"] - 1)
    if human_uttr_index in skill_uttr_indices:
        flag = True
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
    """Is dialog breakdown in human utterance or no. Uses MIDAS hold/abandon classes."""
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")
    if "abandon" not in midas_classes:
        return True
    return False


def no_special_switch_off_requests(vars):
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    """
    intents_by_catcher = common_utils.get_intents(
        state_utils.get_last_human_utterance(vars), probs=False, which="intent_catcher"
    )
    is_high_priority_intent = any([intent not in common_utils.service_intents for intent in intents_by_catcher])
    is_switch = is_switch_topic(vars)
    is_lets_chat = is_lets_chat_about_topic_human_initiative(vars)

    if not (is_high_priority_intent or is_switch or is_lets_chat):
        return True
    return False


def no_requests(vars):
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    - user didn't requested any special intents
    - user didn't ask questions
    """
    contain_no_special_requests = no_special_switch_off_requests(vars)

    request_intents = [
        "opinion_request",
        "topic_switching",
        "lets_chat_about",
        "what_are_you_talking_about",
        "Information_RequestIntent",
        "Topic_SwitchIntent",
        "Opinion_RequestIntent",
    ]
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    is_not_request_intent = all([intent not in request_intents for intent in intents])
    is_no_question = "?" not in state_utils.get_last_human_utterance(vars)["text"]

    if contain_no_special_requests and is_not_request_intent and is_no_question:
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


def is_do_not_know_vars(vars):
    flag = True
    flag = flag and common_utils.is_donot_know(state_utils.get_last_human_utterance(vars))
    return flag


def is_passive_user(vars, history_len=2):
    """Check history_len last human utterances on the number of tokens.
    If number of tokens in ALL history_len uterances is <= 3 tokens, then consider user passive - return True.
    """
    user_utterances = vars["agent"]["dialog"]["human_utterances"][-history_len:]
    user_utterances = [utt["text"] for utt in user_utterances]

    uttrs_lens = [len(uttr.split()) <= 5 for uttr in user_utterances]
    if all(uttrs_lens):
        return True
    return False


def get_not_used_and_save_sentiment_acknowledgement(vars, lang="EN"):
    sentiment = state_utils.get_human_sentiment(vars)
    if is_yes_vars(vars) or is_no_vars(vars):
        sentiment = "neutral"

    shared_memory = state_utils.get_shared_memory(vars)
    last_acknowledgements = shared_memory.get("last_acknowledgements", [])

    ack = common_utils.get_not_used_template(
        used_templates=last_acknowledgements, all_templates=GENERAL_ACKNOWLEDGEMENTS[lang][sentiment]
    )

    used_acks = last_acknowledgements + [ack]
    state_utils.save_to_shared_memory(vars, last_acknowledgements=used_acks[-2:])
    return ack
