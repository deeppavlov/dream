#!/usr/bin/env python

import logging

from os import getenv
from random import choice
import sentry_sdk
import requests
import spacy
from spacy.symbols import nsubj, VERB  # , xcomp, NOUN, ADP

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from utils import get_used_attributes_by_name, get_not_used_template, get_comet_atomic, \
    remove_duplicates, custom_request, correct_verb_form


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_sm")

CONCEPTNET_SERVICE_URL = "http://comet_conceptnet:8065/comet"

ATOMIC_PAST_QUESTION_TEMPLATES = {
    "So, do you feel RELATION?": {"attribute": "xReact"},  # adjective relation
    "So, did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "You seem to be RELATION.": {"attribute": "xAttr"},  # adjective relation
    "You are so RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Did you RELATION as a result?": {"attribute": "xEffect"},  # relation `do that`
    "So, will you RELATION?": {"attribute": "xIntent"},  # relation `do that`
    "Do you want to RELATION now?": {"attribute": "xWant"}  # relation `do that`
}


ATOMIC_FUTURE_QUESTION_TEMPLATES = {
    "Do you feel RELATION?": {"attribute": "xReact"},  # adjective relation
    "Did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "Did you prepared? Did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "Are you ready for that? Did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "You seem to be RELATION.": {"attribute": "xAttr"},  # adjective relation
    "You are RELATION enough to do that.": {"attribute": "xAttr"},  # adjective relation
    "So, will you RELATION as a result?": {"attribute": "xEffect"},  # relation `do that`
    "So, will you RELATION?": {"attribute": "xIntent"},  # relation `do that`
    "Do you expect to RELATION now?": {"attribute": "xWant"}  # relation `do that`
}

ATOMIC_COMMENT_TEMPLATES = {
    "I feel RELATION for you.": {"attribute": "oReact"},  # adjective relation
    "I am RELATION for you.": {"attribute": "oReact"},  # adjective relation
    "I am RELATION to hear that.": {"attribute": "oReact"},  # adjective relation
    "I hope you RELATION.": {"attribute": "oEffect"},  # relation `do that`
    "I believe you will RELATION.": {"attribute": "oEffect"},  # relation `do that`
    "I am sure you will RELATION.": {"attribute": "oEffect"}  # relation `do that`
}

CONCEPTNET_PAST_QUESTION_TEMPLATES = {
    "Is it located in RELATION?": {"attribute": "AtLocation"},  # noun relation
    "So, did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "You seem to be RELATION.": {"attribute": "xAttr"},  # adjective relation
    "You are so RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Did you RELATION as a result?": {"attribute": "xEffect"},  # relation `do that`
    "So, will you RELATION?": {"attribute": "xIntent"},  # relation `do that`
    "Do you want to RELATION now?": {"attribute": "xWant"}  # relation `do that`
}


def get_main_verb_tense_for_user_doings(utterance):
    doc = nlp(utterance.replace("gonna ", "going to ").replace("wanna ", "want to "))
    target = False

    for token in doc:
        if token.dep == nsubj and token.text.lower() == "i":
            target = True

    if target:
        for token in doc:
            if token.tag_ == "VBD" and token.dep_ == "ROOT":
                return "past"
            elif token.tag_ == "VBZ" and token.dep_ == "ROOT":
                return "present"
            elif token.dep_ == "aux" and token.pos == VERB and token.tag_ == "VBD":
                return "past"
            elif token.dep_ == "aux" and token.pos == VERB and token.tag_ == "VBZ":
                return "present"
            elif token.dep_ == "aux" and token.pos == VERB and token.tag_ == "MD":
                return "future"
    return False


def ask_question_using_atomic(dialog):
    attr = {}
    confidence = 0.

    curr_user_uttr = dialog["human_utterances"][-1]["text"]
    if len(curr_user_uttr.split()) <= 3 or len(curr_user_uttr.split()) > 10:
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="atomic_question_template",
        value_by_default=None, activated=True)[-4:]
    tense = get_main_verb_tense_for_user_doings(curr_user_uttr)
    if tense:
        logger.info(f"Found user action of {tense} tense.")
    if tense == "past":
        comet_question_template = get_not_used_template(used_templates, ATOMIC_PAST_QUESTION_TEMPLATES)
        attr["atomic_question_template"] = comet_question_template
        relation = ATOMIC_PAST_QUESTION_TEMPLATES[comet_question_template]["attribute"]
    elif tense == "present" or tense == "future":
        comet_question_template = get_not_used_template(used_templates, ATOMIC_FUTURE_QUESTION_TEMPLATES)
        attr["atomic_question_template"] = comet_question_template
        relation = ATOMIC_FUTURE_QUESTION_TEMPLATES[comet_question_template]["attribute"]
    else:
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    logger.info(f"Choose template: {comet_question_template}")
    prediction = get_comet_atomic(curr_user_uttr, relation)
    logger.info(f"Get prediction: {prediction}")
    if prediction == "":
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}
    if relation in ["xIntent", "xNeed", "xWant", "oWant", "xEffect", "oEffect"] and prediction[:3] == "to ":
        # convert `to do something` to `do something`
        prediction = prediction[3:]

    response = comet_question_template.replace("RELATION", prediction)

    if len(response) > 0:
        response = response.replace("Did you be", "Were you")
        confidence = 0.95
        attr["can_continue"] = CAN_CONTINUE
        attr["atomic_dialog"] = "ask_question"
    return response, confidence, attr


def comment_using_atomic(dialog):
    attr = {}
    confidence = 0.

    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="atomic_comment_template",
        value_by_default=None, activated=True)[-3:]

    if len(dialog["human_utterances"]) >= 2:
        prev_user_uttr = dialog["human_utterances"][-2]["text"]
    tense = get_main_verb_tense_for_user_doings(prev_user_uttr)

    if tense:
        logger.info(f"Found user action of {tense} tense.")
    if tense == "past":
        comet_comment_template = get_not_used_template(used_templates, ATOMIC_PAST_QUESTION_TEMPLATES)
        attr["atomic_comment_template"] = comet_comment_template
        relation = ATOMIC_PAST_QUESTION_TEMPLATES[comet_comment_template]["attribute"]
    elif tense == "present" or tense == "future":
        comet_comment_template = get_not_used_template(used_templates, ATOMIC_FUTURE_QUESTION_TEMPLATES)
        attr["atomic_comment_template"] = comet_comment_template
        relation = ATOMIC_FUTURE_QUESTION_TEMPLATES[comet_comment_template]["attribute"]
    else:
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    logger.info(f"Choose template: {comet_comment_template}")
    prediction = get_comet_atomic(prev_user_uttr, relation)
    logger.info(f"Get prediction: {prediction}")
    if prediction == "":
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}
    if relation in ["xIntent", "xNeed", "xWant", "oWant", "xEffect", "oEffect"] and prediction[:3] == "to ":
        # convert `to do something` to `do something`
        prediction = prediction[3:]

    response = comet_comment_template.replace("RELATION", prediction)

    if len(response) > 0:
        confidence = 0.98
        attr["can_continue"] = CAN_CONTINUE
        attr["atomic_dialog"] = "comment"
    return response, confidence, attr


def get_comet_conceptnet(topic, relation):
    """
    Get COMeT ConceptNet prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form of nounphrase
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    logger.info(f"Comet ConceptNet request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None:
        return ""

    # send request to COMeT ConceptNet service on `topic & relation`
    try:
        comet_result = custom_request(CONCEPTNET_SERVICE_URL, {"input": f"{topic}.",
                                                               "category": relation}, 1.5)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("COMeT ConceptNet result Timeout")
        sentry_sdk.capture_exception(e)
        comet_result = requests.Response()
        comet_result.status_code = 504

    if comet_result.status_code != 200:
        msg = "COMeT ConceptNet: result status code is not 200: {}. result text: {}; result status: {}".format(
            comet_result, comet_result.text, comet_result.status_code)
        logger.warning(msg)
        relation_phrases = []
    else:
        relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    relation_phrases = [el for el in relation_phrases if el != "none"]

    banned = [topic, f"be {topic}", f"be a {topic}"]
    relation_phrases = remove_duplicates(banned + relation_phrases)[len(banned):]

    relation_phrases = correct_verb_form(relation, relation_phrases)

    if len(relation_phrases) > 0:
        return choice(relation_phrases)
    else:
        return ""


# def ask_question_using_conceptnet(dialog):
#     attr = {}
#     confidence = 0.
#
#     curr_user_uttr = dialog["human_utterances"][-1]["text"]
#     if len(curr_user_uttr.split()) <= 3 or len(curr_user_uttr.split()) > 10:
#         return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}
#
#     used_templates = get_used_attributes_by_name(
#         dialog["utterances"], attribute_name="conceptnet_question_template",
#         value_by_default=None, activated=True)[-4:]
#     tense = get_main_verb_tense_for_user_doings(curr_user_uttr)
#     if tense:
#         logger.info(f"Found user action of {tense} tense.")
#     if tense == "past":
#         comet_question_template = get_not_used_template(used_templates, CONCEPTNET_PAST_QUESTION_TEMPLATES)
#         attr["conceptnet_question_template"] = comet_question_template
#         relation = CONCEPTNET_PAST_QUESTION_TEMPLATES[comet_question_template]["attribute"]
#     elif tense == "present" or tense == "future":
#         comet_question_template = get_not_used_template(used_templates, CONCEPTNET_FUTURE_QUESTION_TEMPLATES)
#         attr["conceptnet_question_template"] = comet_question_template
#         relation = CONCEPTNET_FUTURE_QUESTION_TEMPLATES[comet_question_template]["attribute"]
#     else:
#         return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}
#
#     logger.info(f"Choose template: {comet_question_template}")
#     prediction = get_comet_conceptnet(curr_user_uttr, relation)
#     logger.info(f"Get prediction: {prediction}")
#     if prediction == "":
#         return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}
#     if relation in ["xIntent", "xNeed", "xWant", "oWant", "xEffect", "oEffect"] and prediction[:3] == "to ":
#         # convert `to do something` to `do something`
#         prediction = prediction[3:]
#
#     response = comet_question_template.replace("RELATION", prediction)
#
#     if len(response) > 0:
#         confidence = 0.98
#         attr["can_continue"] = CAN_CONTINUE
#         attr["conceptnet_dialog"] = "ask_question"
#     return response, confidence, attr
