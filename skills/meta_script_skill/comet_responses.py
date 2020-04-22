#!/usr/bin/env python

import logging
import re
from os import getenv
import sentry_sdk
import spacy
from spacy.symbols import nsubj, VERB  # , xcomp, NOUN, ADP

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from utils import get_used_attributes_by_name, get_comet_atomic, TOP_FREQUENT_WORDS, get_all_not_used_templates
from constants import idopattern, DEFAULT_ASK_ATOMIC_QUESTION_CONFIDENCE, DEFAULT_ATOMIC_CONTINUE_CONFIDENCE, \
    NUMBER_OF_HYPOTHESES_COMET_DIALOG


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_sm")

CONCEPTNET_SERVICE_URL = "http://comet_conceptnet:8065/comet"

ATOMIC_PAST_QUESTION_TEMPLATES = {
    "I guess you are RELATION now?": {"attribute": "xReact"},  # adjective relation
    "Well, did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "Oh, now I feel quite RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Sounds quite RELATION to me.": {"attribute": "xAttr"},  # adjective relation
    "Did you want to RELATION?": {"attribute": "xWant"},  # relation `do that`
    "In my case, I'd RELATION, too.": {"attribute": "oEffect"}  # relation `do that`
}

ATOMIC_FUTURE_QUESTION_TEMPLATES = {
    "Hope you will be RELATION": {"attribute": "xReact"},  # adjective relation
    "Don't forget RELATION": {"attribute": "xNeed"},  # relation `do that`
    "Sounds RELATION to me!": {"attribute": "xAttr"},  # adjective relation
    "Feels RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Guess you're gonna RELATION?": {"attribute": "xIntent"},  # relation `do that`
    "Will you RELATION after that?": {"attribute": "xWant"}  # relation `do that`
}

ATOMIC_COMMENT_TEMPLATES = {
    "Others will feel RELATION after that, won't they?": {"attribute": "oReact"},  # adjective relation
    "I suppose some people may feel RELATION, what do you think?": {"attribute": "oReact"},  # adjective relation
    "I am RELATION to hear that.": {"attribute": "oReact"},  # adjective relation
    "It seems others want to RELATION.": {"attribute": "oEffect"},  # relation `do that`
    "I suppose somebody wants to RELATION, am I right?": {"attribute": "oEffect"},  # relation `do that`
    "I am wondering if other RELATION.": {"attribute": "oEffect"}  # relation `do that`
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


def fill_comet_atomic_template(curr_user_uttr, template, relation):
    prediction = get_comet_atomic(curr_user_uttr, relation)
    logger.info(f"Get prediction: {prediction}")
    if prediction == "":
        return ""
    if relation in ["xIntent", "xNeed", "xWant", "oWant", "xEffect", "oEffect"] and prediction[:3] == "to ":
        # convert `to do something` to `do something`
        prediction = prediction[3:]

    response = template.replace("RELATION", prediction)
    return response


grammar_compiled = [[re.compile("did you not be", re.IGNORECASE), "were not you"],
                    [re.compile("did you be", re.IGNORECASE), "were you"],
                    [re.compile("(\bhis\b|\bher\b|\btheir\b)", re.IGNORECASE), "your"]]


def grammar_fixes(uttr):
    for pair in grammar_compiled:
        uttr = re.sub(pair[0], pair[1], uttr)

    return uttr


def ask_question_using_atomic(dialog):
    responses, confidences, attrs = [], [], []
    default_return = [""], [0.0], [{"can_continue": CAN_NOT_CONTINUE}]

    curr_user_uttr = dialog["human_utterances"][-1]["text"]
    idosents = re.findall(idopattern, curr_user_uttr.lower())
    logger.info(f"Found `I do` - like sentences: {idosents}")
    best_sent = ""
    best_freq_portion = 0.
    if len(idosents) > 0:
        best_freq_portion = 1.
        for sent in idosents:
            words = sent.split()
            freq_words_portion = sum([1 if word in TOP_FREQUENT_WORDS[:100] else 0 for word in words]) * 1. / len(words)
            if freq_words_portion <= best_freq_portion:
                best_freq_portion = freq_words_portion
                best_sent = sent

    logger.info(f"Best sentence to answer: {best_sent} with frequent words portion: {best_freq_portion}")
    if len(best_sent.split()) <= 4 or len(best_sent.split()) > 10:
        return default_return

    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="atomic_question_template", value_by_default=None, activated=True)[-4:]
    tense = get_main_verb_tense_for_user_doings(curr_user_uttr)
    if tense:
        logger.info(f"Found user action of {tense} tense.")

    if tense == "past":
        comet_question_templates = get_all_not_used_templates(used_templates, ATOMIC_PAST_QUESTION_TEMPLATES)
    elif tense == "present" or tense == "future":
        comet_question_templates = get_all_not_used_templates(used_templates, ATOMIC_FUTURE_QUESTION_TEMPLATES)
    else:
        return default_return

    for template in comet_question_templates[:NUMBER_OF_HYPOTHESES_COMET_DIALOG]:
        confidence, attr = 0., {}
        if tense == "past":
            attr["atomic_question_template"] = template
            relation = ATOMIC_PAST_QUESTION_TEMPLATES[template]["attribute"]
        elif tense == "present" or tense == "future":
            attr["atomic_question_template"] = template
            relation = ATOMIC_FUTURE_QUESTION_TEMPLATES[template]["attribute"]
        else:
            relation = ""
        logger.info(f"Choose template: {template}")
        response = fill_comet_atomic_template(curr_user_uttr, template, relation)
        if response == "":
            return default_return

        response = grammar_fixes(response)
        confidence = DEFAULT_ASK_ATOMIC_QUESTION_CONFIDENCE
        attr["can_continue"] = CAN_CONTINUE
        attr["atomic_dialog"] = "ask_question"
        attr["tense"] = tense
        responses.append(response)
        confidences.append(confidence)
        attrs.append(attr)

    return responses, confidences, attrs


def comment_using_atomic(dialog):
    responses, confidences, attrs = [], [], []
    default_return = [""], [0.0], [{"can_continue": CAN_NOT_CONTINUE}]

    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="atomic_comment_template",
        value_by_default=None, activated=True)[-3:]

    prev_user_uttr = dialog["human_utterances"][-2]["text"].lower()
    comet_comment_templates = get_all_not_used_templates(used_templates, ATOMIC_COMMENT_TEMPLATES)

    for template in comet_comment_templates[:NUMBER_OF_HYPOTHESES_COMET_DIALOG]:
        confidence, attr = 0., {}

        attr["atomic_comment_template"] = template
        relation = ATOMIC_COMMENT_TEMPLATES[template]["attribute"]
        logger.info(f"Choose template: {template}")
        response = fill_comet_atomic_template(prev_user_uttr, template, relation)
        if response == "":
            return default_return

        confidence = DEFAULT_ATOMIC_CONTINUE_CONFIDENCE
        attr["can_continue"] = CAN_CONTINUE
        attr["atomic_dialog"] = "comment"
        responses.append(response)
        confidences.append(confidence)
        attrs.append(attr)

    return responses, confidences, attrs


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
