#!/usr/bin/env python

import logging
import re
from os import getenv
import sentry_sdk
import spacy
from spacy.symbols import nsubj, VERB, PROPN, NOUN
from random import choice, shuffle

from common.constants import CAN_NOT_CONTINUE
from common.universal_templates import join_words_in_or_pattern
from common.utils import is_opinion_request, get_skill_outputs_from_dialog, get_entities, get_toxic
from common.greeting import dont_tell_you_answer
from utils import (
    get_used_attributes_by_name,
    get_comet_atomic,
    TOP_100_FREQUENT_WORDS,
    get_all_not_used_templates,
    get_comet_conceptnet,
    get_nltk_sentiment,
    get_not_used_template,
)
from constants import (
    idopattern,
    DEFAULT_ASK_ATOMIC_QUESTION_CONFIDENCE,
    DEFAULT_ATOMIC_CONTINUE_CONFIDENCE,
    ATOMIC_PAST_QUESTION_TEMPLATES,
    ATOMIC_FUTURE_QUESTION_TEMPLATES,
    ATOMIC_COMMENT_TEMPLATES,
    CONCEPTNET_OPINION_TEMPLATES,
    OPINION_EXPRESSION_TEMPLATES,
    REQUESTED_CONCEPTNET_OPINION_CONFIDENCE,
    NOT_REQUESTED_CONCEPTNET_OPINION_CONFIDENCE,
    NUMBER_OF_HYPOTHESES_COMET_DIALOG,
    possessive_pronouns,
    BANNED_NOUNS_FOR_OPINION_EXPRESSION,
    BANNED_PROPERTIES,
    NUMBER_OF_HYPOTHESES_OPINION_COMET_DIALOG,
    BANNED_WORDS_IN_NOUNS_FOR_OPINION_EXPRESSION,
)

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")


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
            elif token.tag_ == "VBP" and token.dep_ == "ROOT":
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


grammar_compiled = [
    [re.compile("did you not be", re.IGNORECASE), "were not you"],
    [re.compile("did you be", re.IGNORECASE), "were you"],
    [re.compile(r"(\bhis\b|\bher\b|\btheir\b)", re.IGNORECASE), "your"],
    [re.compile(r"\bdo n't\b", re.IGNORECASE), "don't"],
    [re.compile("'d don't", re.IGNORECASE), "'b not"],
]


def grammar_fixes(uttr):
    for pair in grammar_compiled:
        uttr = re.sub(pair[0], pair[1], uttr)

    return uttr


def ask_question_using_atomic(dialog):
    responses, confidences, attrs = [], [], []
    default_return = [""], [0.0], [{"can_continue": CAN_NOT_CONTINUE}]
    if get_toxic(dialog["human_utterances"][-1], probs=False):
        return default_return

    idosents = re.findall(idopattern, dialog["human_utterances"][-1]["text"].lower())
    logger.info(f"Found `I do` - like sentences: {idosents}")
    best_sent = ""
    best_freq_portion = 0.0
    # if len(idosents) == 0:
    #     if not dont_tell_you_answer(dialog["human_utterances"][-1]) and len(dialog["bot_utterances"]) > 0 and \
    #             dialog["bot_utterances"][-1]["active_skill"] in ["dff_friendship_skill"]:
    #         logger.info("Greeting skill asked personal questions and answer was not like `nothing`.")
    #         idosents = dialog["human_utterances"][-1]["annotations"].get("sentseg", {}).get("segments", [""])
    #         if len(idosents) == 1 and len(idosents[0].split()) == 1 and idosents[0] not in TOP_1k_FREQUENT_WORDS:
    #             idosents = [f"I like {idosents[0]}"]

    if len(idosents) > 0:
        # all i do sents are without punctuation
        best_freq_portion = 0.75
        for sent in idosents:
            words = sent.split()
            freq_words_portion = (
                sum([1 if word in TOP_100_FREQUENT_WORDS or word in ["did", "know", "knew"] else 0 for word in words])
                * 1.0
                / len(words)
            )
            if freq_words_portion <= best_freq_portion:
                best_freq_portion = freq_words_portion
                best_sent = sent

    logger.info(f"Best sentence to answer: {best_sent} with frequent words portion: {best_freq_portion}")
    if len(best_sent.split()) <= 2 or len(best_sent.split()) > 15:
        return default_return

    used_templates = get_used_attributes_by_name(
        dialog["utterances"],
        attribute_name="atomic_question_template",
        value_by_default=None,
        activated=True,
        skill_name="comet_dialog_skill",
    )[-4:]
    tense = get_main_verb_tense_for_user_doings(best_sent)
    if tense:
        logger.info(f"Found user action of {tense} tense.")

    if tense == "past":
        comet_question_templates = get_all_not_used_templates(used_templates, ATOMIC_PAST_QUESTION_TEMPLATES)
    elif tense == "present" or tense == "future":
        comet_question_templates = get_all_not_used_templates(used_templates, ATOMIC_FUTURE_QUESTION_TEMPLATES)
    else:
        return default_return

    for template in comet_question_templates[:NUMBER_OF_HYPOTHESES_COMET_DIALOG]:
        confidence, attr = 0.0, {}
        if tense == "past":
            attr["atomic_question_template"] = template
            relation = ATOMIC_PAST_QUESTION_TEMPLATES[template]["attribute"]
        elif tense == "present" or tense == "future":
            attr["atomic_question_template"] = template
            relation = ATOMIC_FUTURE_QUESTION_TEMPLATES[template]["attribute"]
        else:
            relation = ""

        logger.info(f"Choose template: {template}")
        response = fill_comet_atomic_template(best_sent, template, relation)
        if response == "":
            continue

        response = grammar_fixes(response)
        confidence = DEFAULT_ASK_ATOMIC_QUESTION_CONFIDENCE
        attr["can_continue"] = CAN_NOT_CONTINUE
        attr["atomic_dialog"] = "ask_question"
        attr["tense"] = tense
        attr["atomic_best_sent"] = best_sent
        responses.append(response)
        confidences.append(confidence)
        attrs.append(attr)

    return responses, confidences, attrs


def comment_using_atomic(dialog):
    responses, confidences, attrs = [], [], []
    if get_toxic(dialog["human_utterances"][-1], probs=False):
        return [""], [0.0], [{}]

    used_templates = get_used_attributes_by_name(
        dialog["utterances"],
        attribute_name="atomic_comment_template",
        value_by_default=None,
        activated=True,
        skill_name="comet_dialog_skill",
    )[-3:]

    prev_comet_outputs = get_skill_outputs_from_dialog(
        dialog["utterances"][-3:], skill_name="comet_dialog_skill", activated=True
    )
    prev_best_sent = prev_comet_outputs[-1].get("atomic_best_sent", "") if len(prev_comet_outputs) > 0 else ""
    comet_comment_templates = get_all_not_used_templates(used_templates, ATOMIC_COMMENT_TEMPLATES)

    for template in comet_comment_templates[:NUMBER_OF_HYPOTHESES_COMET_DIALOG]:
        confidence, attr = 0.0, {}

        attr["atomic_comment_template"] = template
        relation = ATOMIC_COMMENT_TEMPLATES[template]["attribute"]
        logger.info(f"Choose template: {template}")
        response = fill_comet_atomic_template(prev_best_sent, template, relation)
        if response == "":
            continue

        confidence = DEFAULT_ATOMIC_CONTINUE_CONFIDENCE
        attr["can_continue"] = CAN_NOT_CONTINUE
        attr["atomic_dialog"] = "comment"
        attr["atomic_best_sent"] = prev_best_sent

        if get_nltk_sentiment(response) == "negative":
            response = ""
            confidence = 0.0
            attr = {}

        responses.append(response)
        confidences.append(confidence)
        attrs.append(attr)

    return responses, confidences, attrs


BANNED_WORDS_IN_NOUNS_FOR_OPINION_EXPRESSION_COMPILED = join_words_in_or_pattern(
    BANNED_WORDS_IN_NOUNS_FOR_OPINION_EXPRESSION
)


def del_list_inplace(_list, id_to_del):
    for i in sorted(id_to_del, reverse=True):
        del _list[i]


def remove_intersections_of_entities(entity, subjects):
    ids_to_remove = list(set([i for i, subj in enumerate(subjects) if entity in subj or subj in entity]))
    del_list_inplace(subjects, ids_to_remove)
    return subjects


def filter_nouns_for_conceptnet(annotated_phrase):
    if get_toxic(annotated_phrase, probs=False):
        return []
    subjects = get_entities(annotated_phrase, only_named=False, with_labels=False)
    subjects = [re.sub(possessive_pronouns, "", noun) for noun in subjects]
    subjects = [re.sub(r"(\bthe\b|\ba\b|\ban\b)", "", noun) for noun in subjects]
    subjects = [noun for noun in subjects if noun not in BANNED_NOUNS_FOR_OPINION_EXPRESSION]
    subjects = [
        noun
        for noun in subjects
        if not re.search(BANNED_WORDS_IN_NOUNS_FOR_OPINION_EXPRESSION_COMPILED, annotated_phrase["text"])
    ]
    for ent in get_entities(annotated_phrase, only_named=True, with_labels=True):
        subjects = remove_intersections_of_entities(ent["text"], subjects)

    bad_subjects = []
    for subject in subjects:
        if len(subject.split()) == 1:
            doc = nlp(subject)
            if doc[0].pos not in [PROPN, NOUN]:
                bad_subjects.append(subject)
    for bad_subj in bad_subjects:
        try:
            subjects.remove(bad_subj)
        except ValueError:
            pass
    subjects = [noun for noun in subjects if len(noun) > 0]

    return subjects


def express_opinion_using_conceptnet(dialog):
    responses, confidences, attrs = [], [], []
    default_return = [""], [0.0], [{"can_continue": CAN_NOT_CONTINUE}]

    subjects = filter_nouns_for_conceptnet(dialog["human_utterances"][-1])
    nounphrase = subjects[-1] if len(subjects) > 0 else ""
    if len(nounphrase) == 0:
        return default_return

    used_templates = get_used_attributes_by_name(
        dialog["utterances"],
        attribute_name="conceptnet_opinion_template",
        value_by_default=None,
        activated=True,
        skill_name="comet_dialog_skill",
    )[-4:]
    comet_templates = get_all_not_used_templates(used_templates, CONCEPTNET_OPINION_TEMPLATES)
    shuffle(comet_templates)

    for template in comet_templates[:NUMBER_OF_HYPOTHESES_OPINION_COMET_DIALOG]:
        confidence, attr = 0.0, {}
        attr["conceptnet_opinion_template"] = template
        relation = CONCEPTNET_OPINION_TEMPLATES[template]["attribute"]
        predictions = [
            el for el in get_comet_conceptnet(nounphrase, relation, return_all=True) if el not in BANNED_PROPERTIES
        ]
        if len(predictions) == 0:
            continue
        prediction = choice(predictions)

        logger.info(f"Choose template for opinion: {template}")
        response = template.replace("RELATION", prediction)
        response = response.replace("OBJECT", nounphrase)

        # get sentiment for prediction phrase (not all response, as response is mostly neutral)
        sentiment = get_nltk_sentiment(prediction)
        logger.info(f"Prediction `{prediction}` has sentiment `{sentiment}`")
        used_templates = get_used_attributes_by_name(
            dialog["utterances"],
            attribute_name="conceptnet_opinion_expr_template",
            value_by_default=None,
            activated=True,
            skill_name="comet_dialog_skill",
        )[-2:]
        opinion_expr_template = get_not_used_template(used_templates, OPINION_EXPRESSION_TEMPLATES[sentiment])
        attr["conceptnet_opinion_expr_template"] = opinion_expr_template
        response = f"{opinion_expr_template} {response}"
        response = response.replace("OBJECT", nounphrase)

        if response == "":
            continue

        if is_opinion_request(dialog["human_utterances"][-1]):
            confidence = REQUESTED_CONCEPTNET_OPINION_CONFIDENCE
        elif not dont_tell_you_answer(dialog["human_utterances"][-1]):
            confidence = NOT_REQUESTED_CONCEPTNET_OPINION_CONFIDENCE
        else:
            response = ""
            confidence = 0.0

        attr["conceptnet_dialog"] = "express_opinion"
        attr["conceptnet_opinion_object"] = nounphrase

        responses.append(response)
        confidences.append(confidence)
        attrs.append(attr)

    return responses, confidences, attrs
