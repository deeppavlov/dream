# %%
import logging
import os
import re

import common.speech_functions.generic_responses_templates as current_templates
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
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(agree_patterns_re, sf_type))
    # fallback to yes/no intents
    flag = flag or common_utils.is_yes(human_utterance)

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
    # fallback to yes/no intents
    flag = flag or common_utils.is_no(human_utterance)

    return flag


patterns_express_opinion = [
    "Initiate.Give.Opinion",
]
express_opinion_patterns_re = re.compile("(" + "|".join(patterns_express_opinion) + ")", re.IGNORECASE)


def is_speech_function_express_opinion(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(express_opinion_patterns_re, sf_type))
    # fallback to MIDAS & CoBot
    flag = flag or common_utils.is_opinion_expression(human_utterance)
    # # fallback to CoBot intents
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
    # # fallback to CoBot & MIDAS intents
    flag = flag or common_utils.is_opinion_request(human_utterance)
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
        all_templates=current_templates.GENERIC_REACTION_TO_USER_SPEECH_FUNCTION[proposed_sf],
    )

    used_resp = last_responses + [resp]
    state_utils.save_to_shared_memory(vars, last_responses=used_resp[-2:])
    return resp
