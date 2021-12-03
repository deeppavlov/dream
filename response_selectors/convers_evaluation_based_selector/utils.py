from copy import deepcopy
import logging
import random
from os import getenv

import numpy as np
import sentry_sdk
from nltk.tokenize import sent_tokenize

from common.duplicates import NOT_LOWER_DUPLICATES_SENTS
from common.link import skills_phrases_map
from common.utils import (
    scenario_skills,
    retrieve_skills,
    okay_statements,
    is_question,
    substitute_nonwords,
    get_sentiment,
    get_toxic,
    is_no,
)

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

ASK_DUMMY_QUESTION_PROB = 0.5
ASK_LINK_TO_FOR_RETRIEVE_PROB = 0.5
CONFIDENCE_STRENGTH = 2
CONV_EVAL_STRENGTH = 0.4
how_are_you_spec = "Do you want to know what I can do?"  # this is always at the end of answers to `how are you`
what_i_can_do_spec = "socialbot running inside"
psycho_help_spec = "you can call the National Suicide Prevention Lifeline"
misheard_with_spec1 = "I misheard you"
misheard_with_spec2 = "like to chat about"
alexa_abilities_spec = "If you want to use the requested feature say"

LET_ME_ASK_YOU_PHRASES = [
    "Let me ask you something.",
    "I would like to ask you a question.",
    "Hey, I have a quesiton to you.",
    "May I ask you one interesting thing.",
]


def join_used_links_in_attributes(main_attrs, add_attrs):
    result = deepcopy(main_attrs)
    result["used_links"] = result.get("used_links", {})

    for skill_name in add_attrs.get("used_links", {}).keys():
        result["used_links"][skill_name] = result["used_links"].get(skill_name, []) + add_attrs["used_links"].get(
            skill_name, []
        )
    return result


def add_question_to_statement(
    best_candidate,
    best_skill_name,
    dummy_question,
    dummy_question_human_attr,
    link_to_question,
    link_to_human_attrs,
    not_sure_factoid,
):

    if not_sure_factoid and "factoid_qa" in best_skill_name:
        best_candidate["text"] = "I am not sure in my answer but I can try. " + best_candidate["text"]
    if best_candidate["text"].strip() in okay_statements:
        if dummy_question != "" and random.random() < ASK_DUMMY_QUESTION_PROB:
            logger.info(f"adding {dummy_question} to response.")
            best_candidate["text"] += f"{np.random.choice(LET_ME_ASK_YOU_PHRASES)} {dummy_question}"
            # if this is not a link-to question, bot attributes will be still empty
            best_candidate["human_attributes"] = join_used_links_in_attributes(
                best_candidate.get("human_attributes", {}), dummy_question_human_attr
            )
    elif best_skill_name in retrieve_skills:
        if not is_question(best_candidate["text"]) and random.random() < ASK_LINK_TO_FOR_RETRIEVE_PROB:
            logger.info(f"adding link_to {link_to_question} to response.")
            best_candidate["text"] += f". {link_to_question}"
            best_candidate["human_attributes"] = join_used_links_in_attributes(
                best_candidate.get("human_attributes", {}), link_to_human_attrs
            )

    return best_candidate


def lower_duplicates_score(candidates, bot_utt_counter, scores, confidences):
    for i, cand in enumerate(candidates):
        # no penalties for repeat intent
        if cand["skill_name"] == "intent_responder" and "#+#repeat" in cand["text"]:
            continue
        # TODO: remove the quick fix of gcs petitions, issue is https://github.com/deepmipt/assistant/issues/80
        if cand["skill_name"] in ["game_cooperative_skill", "news_api_skill", "dff_movie_skill"]:
            continue

        cand_sents = sent_tokenize(cand["text"].lower())
        coeff = 1
        n_duplicates = 0
        for cand_sent in cand_sents:
            if len(cand_sent.split()) >= 3 and cand_sent not in NOT_LOWER_DUPLICATES_SENTS:
                cand_sent = substitute_nonwords(cand_sent)
                coeff += bot_utt_counter[cand_sent]
                n_duplicates += 1

        # apply penalties to non-script skills and in case if response consists only from duplicates
        if confidences[i] < 1.0 or n_duplicates == len(cand_sents):
            confidences[i] /= coeff
            scores[i]["isResponseInteresting"] /= coeff
            scores[i]["responseEngagesUser"] /= coeff


def lower_retrieve_skills_confidence_if_scenario_exist(candidates, scores, confidences):
    has_scenario_skill = False
    lower_coeff = 0.25  # Lower confidence and isResponseInteresting for retrieve skills to 25%
    for cand in candidates:
        if cand["skill_name"] in scenario_skills and cand["text"] and cand["confidence"] >= 0.9:
            has_scenario_skill = True
            break
    if has_scenario_skill:
        for i, cand in enumerate(candidates):
            if cand["skill_name"] in retrieve_skills:
                confidences[i] *= lower_coeff
                scores[i]["isResponseInteresting"] *= lower_coeff


def calculate_single_convers_evaluator_score(cand_scores):
    score_conv_eval = sum(
        [
            cand_scores["isResponseOnTopic"],
            cand_scores["isResponseInteresting"],
            cand_scores["responseEngagesUser"],
            cand_scores["isResponseComprehensible"],
        ]
    )
    score_conv_eval -= cand_scores["isResponseErroneous"]
    return score_conv_eval


def downscore_toxic_badlisted_responses(scores, confidences, is_toxics):
    # exclude toxic messages and messages with badlisted phrases
    ids = np.arange(len(confidences))[is_toxics]
    logger.info(f"Bot excluded utterances: {ids}. is_toxics: {is_toxics}")
    scores[ids] = {
        "isResponseOnTopic": 0.0,
        "isResponseInteresting": 0.0,
        "responseEngagesUser": 0.0,
        "isResponseComprehensible": 0.0,
        "isResponseErroneous": 1.0,
    }
    confidences[ids] = 0.0

    return sum(ids), scores, confidences


def get_updated_disliked_skills(dialog, can_not_be_disliked_skills=None):
    can_not_be_disliked_skills = [] if can_not_be_disliked_skills is None else can_not_be_disliked_skills
    disliked_skills = dialog["human"]["attributes"].get("disliked_skills", [])
    prev_bot_uttr = dialog["bot_utterances"][-1]["text"].lower() if len(dialog["bot_utterances"]) > 0 else ""

    linked_to_skill = ""
    for skill_name, link_phrases in skills_phrases_map.items():
        for phrase in link_phrases:
            if phrase.lower() in prev_bot_uttr:
                linked_to_skill = skill_name
                break

    if linked_to_skill:
        negative_prob = get_sentiment(dialog["human_utterances"][-1], probs=True).get("negative", 0.0)
        toxicity = get_toxic(dialog["human_utterances"][-1], probs=False)
        _is_no = is_no(dialog["human_utterances"][-1])
        if negative_prob > 0.8 or toxicity or _is_no:
            if linked_to_skill not in can_not_be_disliked_skills:
                disliked_skills.append(linked_to_skill)

    return disliked_skills
