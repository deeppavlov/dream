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
LANGUAGE = getenv("LANGUAGE", "EN")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

ASK_DUMMY_QUESTION_PROB = 0.5
ASK_LINK_TO_FOR_RETRIEVE_PROB = 0.5
CONFIDENCE_STRENGTH = float(getenv("CONFIDENCE_STRENGTH"))
CONV_EVAL_STRENGTH = float(getenv("CONV_EVAL_STRENGTH"))
QUESTION_TO_QUESTION_DOWNSCORE_COEF = float(getenv("QUESTION_TO_QUESTION_DOWNSCORE_COEF"))
how_are_you_spec = "Do you want to know what I can do?"  # this is always at the end of answers to `how are you`
what_i_can_do_spec = "socialbot running inside"
misheard_with_spec1 = "I misheard you"
misheard_with_spec2 = "like to chat about"

LET_ME_ASK_YOU_PHRASES = {
    "EN": [
        "Let me ask you something.",
        "I would like to ask you a question.",
        "Hey, I have a quesiton to you.",
        "May I ask you one interesting thing.",
    ],
    "RU": [
        "Я бы хотела кое-что спросить.",
        "О, у меня как раз есть вопрос для обсуждения.",
        "Я хочу спросить тебя кое-о-чем интересном.",
        "У меня есть кое-что интересное для обсуждения.",
    ],
}


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
    prev_skill_names,
):

    if not_sure_factoid and "factoid_qa" in best_skill_name:
        best_candidate["text"] = "I am not sure in my answer but I can try. " + best_candidate["text"]
    if best_candidate["text"].strip() in okay_statements:
        if dummy_question != "" and random.random() < ASK_DUMMY_QUESTION_PROB:
            logger.info(f"adding {dummy_question} to response.")
            best_candidate["text"] += f"{np.random.choice(LET_ME_ASK_YOU_PHRASES[LANGUAGE])} {dummy_question}"
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
    elif LANGUAGE == "RU" and best_skill_name == "dff_generative_skill":
        if prev_skill_names[-3:] == 3 * ["dff_generative_skill"] and random.random() < ASK_DUMMY_QUESTION_PROB:
            logger.info(f"adding russian {dummy_question} to dff-generative-skill response.")
            best_candidate["text"] += f"{np.random.choice(LET_ME_ASK_YOU_PHRASES[LANGUAGE])} {dummy_question}"

    return best_candidate


def lower_duplicates_score(candidates, bot_utt_counter, scores, confidences):
    for i, cand in enumerate(candidates):
        # no penalties for repeat intent
        if cand["skill_name"] == "dff_intent_responder_skill" and "#+#repeat" in cand["text"]:
            continue
        # TODO: remove the quick fix of gcs petitions, issue is https://github.com/deeppavlov/assistant/issues/80
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
            scores[i] /= coeff


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
                scores[i] *= lower_coeff


def calculate_single_evaluator_score(hypothesis_annotations, confidence):
    if "convers_evaluator_annotator" in hypothesis_annotations:
        cand_scores = hypothesis_annotations["convers_evaluator_annotator"]
        score_conv_eval = sum(
            [
                cand_scores["isResponseOnTopic"],
                cand_scores["isResponseInteresting"],
                cand_scores["responseEngagesUser"],
                cand_scores["isResponseComprehensible"],
            ]
        )
        score_conv_eval -= cand_scores["isResponseErroneous"]
        score = CONV_EVAL_STRENGTH * score_conv_eval + CONFIDENCE_STRENGTH * confidence
        return score
    elif "dialogrpt" in hypothesis_annotations:
        score_conv_eval = hypothesis_annotations["dialogrpt"]
        score = CONV_EVAL_STRENGTH * score_conv_eval + CONFIDENCE_STRENGTH * confidence
        return score
    elif "sentence_ranker" in hypothesis_annotations:
        score_conv_eval = hypothesis_annotations["sentence_ranker"]
        score = CONV_EVAL_STRENGTH * score_conv_eval + CONFIDENCE_STRENGTH * confidence
        return score
    elif "hypothesis_scorer" in hypothesis_annotations:
        return hypothesis_annotations["hypothesis_scorer"]
    else:
        return 0.0


def downscore_toxic_badlisted_responses(scores, confidences, is_toxics):
    # exclude toxic messages and messages with badlisted phrases
    ids = np.arange(len(confidences))[is_toxics]
    logger.info(f"Bot excluded utterances: {ids}. is_toxics: {is_toxics}")
    scores[ids] = 0.0
    confidences[ids] = 0.0

    return len(ids), scores, confidences


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


def downscore_if_question_to_question(scores, is_questions):
    ids = np.arange(len(scores))[is_questions]
    scores[ids] *= QUESTION_TO_QUESTION_DOWNSCORE_COEF

    return scores
