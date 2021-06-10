# %%
import logging
import os
import re

import dialogflows.scenarios.generic_responses_templates as current_templates
import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
import common.utils as common_utils

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98


##################################################################################################################
# utils
##################################################################################################################


##################################################################################################################
# speech functions
##################################################################################################################


def get_speech_function_for_human_utterance(human_utterance):
    sfs = human_utterance["annotations"].get("speech_function_classifier", {})
    phrases = human_utterance["annotations"].get("sentseg", {}).get("segments", {})

    sfunctions = {}
    i = 0
    for phrase in phrases:
        if len(sfs) > i:
            sfunctions[phrase] = sfs[i]
        i = i + 1

    return sfunctions


def get_speech_function_predictions_for_human_utterance(human_utterance):
    predicted_sfs = human_utterance["annotations"].get("speech_function_predictor", [])
    return predicted_sfs


def filter_speech_function_predictions_for_human_utterance(predicted_sfs):
    filtered_sfs = [sf_item for sf_item in predicted_sfs if "Open" not in sf_item]
    return filtered_sfs


patterns_agree = [
    "Support.Reply.Accept",
    "Support.Reply.Agree",
    "Support.Reply.Comply",
    "Support.Reply.Acknowledge",
    "Support.Reply.Affirm",
]
agree_patterns_re = re.compile("(" + "|".join(patterns_agree) + ")", re.IGNORECASE)


def is_speech_function_agree(vars):
    # fallback to MIDAS
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(agree_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_positive_answer(vars)
    # fallback to yes/no intents
    flag = flag or common_utils.is_yes(human_utterance)

    flag = flag and not is_not_interested_speech_function(vars)
    return flag


patterns_disagree = [
    "Support.Reply.Decline",
    "Support.Reply.Disagree",
    "Support.Reply.Non-comply",
    "Support.Reply.Withold",
    "Support.Reply.Disawow",
    "Support.Reply.Conflict",
]
disagree_patterns_re = re.compile("(" + "|".join(patterns_disagree) + ")", re.IGNORECASE)


def is_speech_function_disagree(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(disagree_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_negative_answer(vars)
    # fallback to yes/no intents
    flag = flag or common_utils.is_no(human_utterance)

    flag = flag and not is_not_interested_speech_function(vars)
    return flag


patterns_express_opinion = [
    "Initiate.Give.Opinion",
]
express_opinion_patterns_re = re.compile("(" + "|".join(patterns_express_opinion) + ")", re.IGNORECASE)


def is_cobot_opinion_expressed(vars):
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    opinion_expression_detected = "Opinion_ExpressionIntent" in intents
    return bool(opinion_expression_detected)


def is_cobot_opinion_demanded(vars):
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    opinion_request_detected = "Opinion_RequestIntent" in intents
    return bool(opinion_request_detected)


def is_speech_function_express_opinion(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(express_opinion_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_opinion_expression(vars)
    # # fallback to CoBot intents
    flag = flag or is_cobot_opinion_expressed(vars)
    flag = flag or common_utils.is_no(human_utterance)
    # bug check (sometimes opinion by MIDAS can be incorrectly detected in a simple yes/no answer from user)
    flag = flag and not common_utils.is_no(human_utterance) and not common_utils.is_yes(human_utterance)
    return flag


patterns_demand_opinion = [
    "Initiate.Demand.Opinion",
]
demand_opinion_patterns_re = re.compile("(" + "|".join(patterns_demand_opinion) + ")", re.IGNORECASE)


def is_speech_function_demand_opinion(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(demand_opinion_patterns_re, sf_type))
    # # fallback to CoBot intents
    flag = flag or is_cobot_opinion_demanded(vars)
    flag = flag or common_utils.is_no(human_utterance)
    # bug check (sometimes opinion by MIDAS can be incorrectly detected in a simple yes/no answer from user)
    flag = flag and not common_utils.is_no(human_utterance) and not common_utils.is_yes(human_utterance)
    return flag


##################################################################################################################
# more specific intents
##################################################################################################################


def get_not_used_and_save_generic_response(proposed_sf, vars):
    logger.info(f"Getting not yet used generic response for proposed speech function {proposed_sf}...")
    shared_memory = state_utils.get_shared_memory(vars)
    last_responses = shared_memory.get(proposed_sf + "_last_responses", [])

    resp = common_utils.get_not_used_template(
        used_templates=last_responses,
        all_templates=current_templates.GENERIC_REACTION_TO_USER_SPEECH_FUNCTION[proposed_sf]
    )

    used_resp = last_responses + [resp]
    state_utils.save_to_shared_memory(vars, last_responses=used_resp[-2:])
    return resp


##################################################################################################################
# more specific intents
##################################################################################################################


patterns_not_interested = [
    "not interested",
    "don't care",
    "move on",
    "skip",
    "cancel",
    "avoid",
    "not into",
    "not really into",
    "no interest for me",
    "I don't bother",
    "don't really want to talk about this",
    "don't feel comfortable discussing this",
    "We’d better not to enter this subject",
    "I'd rather not go there right now",
    "have no interest in discussing that",
    "What an idiotic topic of conversation",
    "That subject really bothers me and I don't want to talk about it",
    "Can we talk about something else",
    "Must we discuss this",
    "Can we discuss this later",
]
patterns_not_interested_re = re.compile("(" + "|".join(patterns_not_interested) + ")", re.IGNORECASE)


def is_not_interested_speech_function(vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(patterns_not_interested_re, human_text))

    return flag


##################################################################################################################
# MIDAS
##################################################################################################################


def is_midas_positive_answer(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")

    intent_detected = any([intent in midas_classes for intent in ["pos_answer"]])

    return intent_detected


def is_midas_negative_answer(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")

    intent_detected = any([intent in midas_classes for intent in ["neg_answer"]])

    return intent_detected


def is_midas_opinion_expression(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")
    intent_detected = any([intent in midas_classes for intent in ["opinion"]])

    return intent_detected
