#!/usr/bin/env python
import logging
import pprint
import random

import re
import time
from collections import Counter
from os import getenv

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from nltk.tokenize import sent_tokenize

from common.greeting import greeting_spec, HI_THIS_IS_DREAM
from common.universal_templates import if_chat_about_particular_topic, if_choose_topic, DUMMY_DONTKNOW_RESPONSES
from common.utils import (
    get_intent_name,
    low_priority_intents,
    substitute_nonwords,
    is_toxic_or_badlisted_utterance,
)
from tag_based_selection import tag_based_response_selection
from utils import (
    add_question_to_statement,
    lower_duplicates_score,
    lower_retrieve_skills_confidence_if_scenario_exist,
    calculate_single_evaluator_score,
    downscore_toxic_badlisted_responses,
    how_are_you_spec,
    what_i_can_do_spec,
    misheard_with_spec1,
    misheard_with_spec2,
)


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CALL_BY_NAME_PROBABILITY = float(getenv("CALL_BY_NAME_PROBABILITY", 0.5))  # if name is already known
TAG_BASED_SELECTION = getenv("TAG_BASED_SELECTION", False)
MOST_DUMMY_RESPONSES = [
    "I really do not know what to answer.",
    "Sorry, probably, I didn't get what you mean.",
    "I didn't get it. Sorry",
]
LANGUAGE = getenv("LANGUAGE", "EN")


@app.route("/respond", methods=["POST"])
def respond():
    print("Convers_Evaluation_Based_Response_Selector: Beginning", flush=True)

    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    all_prev_active_skills_batch = request.json.get("all_prev_active_skills", [[]] * len(dialogs_batch))

    selected_skill_names = []
    selected_texts = []
    selected_confidences = []
    selected_human_attributes = []
    selected_bot_attributes = []

    for i, (dialog, all_prev_active_skills) in enumerate(zip(dialogs_batch, all_prev_active_skills_batch)):
        curr_confidences = []
        curr_scores = []
        curr_is_toxics = []

        try:
            curr_candidates = dialog["human_utterances"][-1]["hypotheses"]
            logger.info("Curr candidates:")
            logger.info(pprint.pformat(curr_candidates, compact=False))

            for skill_data in curr_candidates:
                if len(dialog["utterances"]) > 1:
                    assert len(dialog["human_utterances"]) > 0
                    assert len(dialog["bot_utterances"]) > 0

                curr_confidences += [skill_data["confidence"]]
                if skill_data["text"] and skill_data["confidence"]:
                    if not skill_data.get("annotations"):
                        logger.warning(f"Valid skill data without annotations: {skill_data}")

                is_toxic_utterance = is_toxic_or_badlisted_utterance(skill_data)
                curr_is_toxics.append(is_toxic_utterance)

                if is_toxic_utterance:
                    with sentry_sdk.push_scope() as scope:
                        scope.set_extra("utterance", skill_data["text"])
                        scope.set_extra("selected_skills", skill_data)
                        sentry_sdk.capture_message("response selector got candidate with badlisted phrases")
                        msg = (
                            "response selector got candidate with badlisted phrases:\n"
                            f"utterance: {skill_data['text']}\n"
                            f"skill name: {skill_data['skill_name']}"
                        )
                        logger.info(msg)

                curr_scores += [
                    calculate_single_evaluator_score(skill_data.get("annotations"), skill_data["confidence"])
                ]

            curr_is_toxics = np.array(curr_is_toxics)
            curr_scores = np.array(curr_scores)
            curr_confidences = np.array(curr_confidences)
            # now we collected all current candidates and their annotations. select response among them
            best_skill_name, best_text, best_confidence, best_human_attributes, best_bot_attributes = select_response(
                curr_candidates,
                curr_scores,
                curr_confidences,
                curr_is_toxics,
                dialog,
                all_prev_active_skills,
            )
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            if dialog["human_utterances"][-1].get("hypotheses", []):
                logger.info("Response Selector Error: randomly choosing final response among hypotheses.")
                best_cand = random.choice(dialog["human_utterances"][-1]["hypotheses"])
            else:
                logger.info("Response Selector Error: randomly choosing response among dummy responses.")
                best_cand = {
                    "text": random.choice(DUMMY_DONTKNOW_RESPONSES[LANGUAGE]),
                    "confidence": 0.1,
                    "human_attributes": {},
                    "bot_attributes": {},
                    "skill_name": "dummy_skill",
                    "active_skill": "dummy_skill",
                }
            best_skill_name = best_cand["skill_name"]
            best_text = best_cand["text"]
            best_confidence = best_cand["confidence"]
            best_human_attributes = best_cand.get("human_attributes", {})
            best_bot_attributes = best_cand.get("bot_attributes", {})

        selected_skill_names.append(best_skill_name)
        selected_texts.append(best_text)
        selected_confidences.append(best_confidence)
        selected_human_attributes.append(best_human_attributes)
        selected_bot_attributes.append(best_bot_attributes)

    logger.info(
        f"Choose selected_skill_names: {selected_skill_names};"
        f"selected_texts {selected_texts}; selected_confidences {selected_confidences};"
        f"selected human attributes: {selected_human_attributes}; "
        f"selected bot attributes: {selected_bot_attributes}"
    )

    total_time = time.time() - st_time
    logger.info(f"convers_evaluation_selector exec time: {total_time:.3f}s")
    return jsonify(
        list(
            zip(
                selected_skill_names,
                selected_texts,
                selected_confidences,
                selected_human_attributes,
                selected_bot_attributes,
            )
        )
    )


def rule_score_based_selection(dialog, candidates, scores, confidences, is_toxics, bot_utterances):
    curr_single_scores = []

    bot_utt_counter = Counter(bot_utterances)
    lower_duplicates_score(candidates, bot_utt_counter, scores, confidences)
    lower_retrieve_skills_confidence_if_scenario_exist(candidates, scores, confidences)

    # prev_active_skill = dialog["bot_utterances"][-1]['active_skill'] if len(dialog["bot_utterances"]) > 0 else ''
    skill_names = [c["skill_name"] for c in candidates]

    very_big_score = 100
    very_low_score = -100
    dummy_question = ""
    dummy_question_human_attr = {}
    link_to_question = ""
    link_to_human_attrs = {}
    not_sure_factoid = False
    if "factoid_qa" in skill_names:
        factoid_index = skill_names.index("factoid_qa")
        logging.debug("factoid")
        logging.debug(str(candidates[factoid_index]))
        if "not sure" in candidates[factoid_index] and candidates[factoid_index]["not sure"]:
            not_sure_factoid = True
    for i in range(len(scores)):
        curr_score = None
        is_misheard = misheard_with_spec1 in candidates[i]["text"] or misheard_with_spec2 in candidates[i]["text"]
        intent_name = get_intent_name(candidates[i]["text"])
        is_intent_candidate = (skill_names[i] in ["dff_intent_responder_skill", "dff_program_y_skill"]) and intent_name
        is_intent_candidate = is_intent_candidate and intent_name not in low_priority_intents
        # print("is intent candidate? " + str(is_intent_candidate), flush=True)

        if len(dialog["human_utterances"]) == 1 and greeting_spec[LANGUAGE] not in candidates[i]["text"]:
            logger.info("Dialog Beginning detected.")
            if (
                if_chat_about_particular_topic(dialog["utterances"][0])
                and "about it" not in dialog["utterances"][0]["text"].lower()
            ):
                logger.info("User wants to talk about particular topic")
                # if user says `let's chat about blablabla`
                if skill_names[i] == "factoid_qa":
                    logger.info("Particular topic. Facts + Greeting to very big score.")
                    # I don't have an opinion on that but I know some facts.
                    resp = candidates[i]["text"].replace("I don't have an opinion on that but I know some facts.", "")
                    candidates[i]["text"] = f"{HI_THIS_IS_DREAM[LANGUAGE]} {resp}"
                    curr_score = very_big_score
                elif skill_names[i] == "meta_script_skill" and len(candidates[i]["text"]) > 0 and confidences[i] > 0.98:
                    logger.info("Particular topic. meta_script_skill + Greeting to very big score.")
                    # I don't have an opinion on that but I know some facts.
                    resp = candidates[i]["text"]
                    candidates[i]["text"] = f"{HI_THIS_IS_DREAM[LANGUAGE]} {resp}"
                    curr_score = very_big_score
                elif skill_names[i] == "small_talk_skill":
                    logger.info("Particular topic. Small-talk + Greeting NOT to very big score.")
                    # for now do not give small talk a very big score here
                    candidates[i]["text"] = f"{HI_THIS_IS_DREAM[LANGUAGE]} {candidates[i]['text']}"
                    # curr_score = very_big_score
            elif if_choose_topic(dialog["utterances"][0]) and "about it" not in dialog["utterances"][0]["text"].lower():
                logger.info("User wants bot to choose the topic")
                # if user says `let's chat about something`
                if skill_names[i] == "small_talk_skill":
                    logger.info("No topic. Small-talk + Greeting to very big score.")
                    candidates[i]["text"] = f"{HI_THIS_IS_DREAM[LANGUAGE]} {candidates[i]['text']}"
                    curr_score = very_big_score
                elif skill_names[i] == "meta_script_skill" and len(candidates[i]["text"]) > 0:
                    logger.info("No topic. Meta-script + Greeting to very big score.")
                    candidates[i]["text"] = f"{HI_THIS_IS_DREAM[LANGUAGE]} {candidates[i]['text']}"
                    curr_score = very_big_score
            else:
                logger.info("User just wants to talk.")
                # if user says something else
                if skill_names[i] == "program_y" and greeting_spec[LANGUAGE] in candidates[i]["text"]:
                    logger.info("Just chat. Program-y to very big score.")
                    curr_score = very_big_score
        elif (
            skill_names[i] == "dff_friendship_skill"
            and (how_are_you_spec in candidates[i]["text"] or what_i_can_do_spec in candidates[i]["text"])
            and len(dialog["utterances"]) < 16
        ):
            curr_score = very_big_score
        elif skill_names[i] == "dff_friendship_skill" and greeting_spec[LANGUAGE] in candidates[i]["text"]:
            if len(dialog["utterances"]) < 2:
                curr_score = very_big_score
            else:
                confidences[i] = 0.2  # Low confidence for greeting in the middle of dialogue
        # we don't have 'cobotqa' anymore; instead we have factoid_qa
        elif skill_names[i] in ["factoid_qa"] and "Here's something I found on the web." in candidates[i]["text"]:
            confidences[i] = 0.6
        elif (
            skill_names[i] == "factoid_qa"
            and dialog["human_utterances"][-1]["annotations"]
            .get("intent_catcher", {})
            .get("weather_forecast_intent", {})
            .get("detected", 0)
            == 1
        ):
            confidences[i] = 0.8
        elif skill_names[i] == "misheard_asr" and is_misheard:
            curr_score = very_big_score
        elif is_intent_candidate:
            curr_score = very_big_score
        elif skill_names[i] in ["dummy_skill", "convert_reddit", "alice", "eliza", "tdidf_retrieval", "program_y"]:
            if "question" in candidates[i].get("type", "") or "?" in candidates[i]["text"]:
                penalty_start_utt = 1
                if skill_names[i] == "program_y":
                    penalty_start_utt = 4

                n_questions = 0
                if len(bot_utterances) >= penalty_start_utt and "?" in bot_utterances[-1]:
                    confidences[i] /= 1.5
                    n_questions += 1
                if len(bot_utterances) >= penalty_start_utt + 1 and "?" in bot_utterances[-2]:
                    confidences[i] /= 1.1
                    n_questions += 1
                if n_questions == 2:
                    # two subsequent questions (1 / (1.5 * 1.1 * 1.2) = ~0.5)
                    confidences[i] /= 1.2
            # this is only about `dummy_skill`
            if "link_to_for_response_selector" in candidates[i].get("type", ""):
                link_to_question = candidates[i]["text"]
                link_to_human_attrs = candidates[i].get("human_attributes", {})
        if skill_names[i] == "dummy_skill" and "question" in candidates[i].get("type", ""):
            dummy_question = candidates[i]["text"]
            dummy_question_human_attr = candidates[i].get("human_attributes", {})

        if curr_score is None:
            score = scores[i]
            confidence = confidences[i]
            skill_name = skill_names[i]
            logger.info(
                f"Skill {skill_name} has final score: {score}. Confidence: {confidence}. " f"Toxicity: {is_toxics[i]}"
            )
            curr_single_scores.append(score)
        else:
            score = scores[i]
            skill_name = skill_names[i]
            logger.info(f"Skill {skill_name} has final score: {score}. " f"Toxicity: {is_toxics[i]}")
            curr_single_scores.append(score)

    highest_conf_exist = True if any(confidences >= 1.0) else False
    if highest_conf_exist:
        logger.info("Found skill with the highest confidence.")
    for j in range(len(candidates)):
        if highest_conf_exist and confidences[j] < 1.0 and curr_single_scores[j] < very_big_score:
            # need to drop this candidates
            logger.info(f"Dropping {skill_names[j]} which does not have a highest confidence or `very big score`.")
            curr_single_scores[j] = very_low_score

    best_id = np.argmax(curr_single_scores)
    best_candidate = candidates[best_id]
    best_skill_name = skill_names[int(best_id)]
    prev_skill_names = [uttr["skill_name"] for uttr in dialog["bot_utterances"][-5:]]

    best_candidate = add_question_to_statement(
        best_candidate,
        best_skill_name,
        dummy_question,
        dummy_question_human_attr,
        link_to_question,
        link_to_human_attrs,
        not_sure_factoid,
        prev_skill_names,
    )

    return best_candidate, best_id, curr_single_scores


def select_response(candidates, scores, confidences, is_toxics, dialog, all_prev_active_skills=None):
    # TOXICITY & BADLISTS checks
    n_toxic_candidates, scores, confidences = downscore_toxic_badlisted_responses(scores, confidences, is_toxics)
    if n_toxic_candidates == len(candidates):
        # the most dummy заглушка на случай, когда все абсолютно скиллы вернули токсичные ответы
        return None, np.random.choice(DUMMY_DONTKNOW_RESPONSES[LANGUAGE]), 1.0, {}, {}

    # REPEAT checks
    bot_utterances = [sent_tokenize(uttr["text"].lower()) for uttr in dialog["bot_utterances"]]
    prev_large_utterances = [[sent] for utt in bot_utterances[:-15] for sent in utt if len(sent) >= 40]
    bot_utterances = prev_large_utterances + bot_utterances[-15:]
    # flatten 2d list to 1d list of all appeared sentences of bot replies
    bot_utterances = sum(bot_utterances, [])
    bot_utterances = [substitute_nonwords(utt) for utt in bot_utterances]

    if TAG_BASED_SELECTION:
        logger.info("Tag based selection")
        best_candidate, best_id, curr_single_scores = tag_based_response_selection(
            dialog, candidates, scores, confidences, bot_utterances, all_prev_active_skills
        )
    else:
        logger.info("Confidence & ConvEvaluationAnnotator Scores based selection")
        best_candidate, best_id, curr_single_scores = rule_score_based_selection(
            dialog, candidates, scores, confidences, is_toxics, bot_utterances
        )

    logger.info(f"Best candidate: {best_candidate}")
    best_text = best_candidate["text"]
    best_skill_name = best_candidate["skill_name"]
    best_confidence = best_candidate["confidence"]
    best_human_attributes = best_candidate.get("human_attributes", {})
    best_bot_attributes = best_candidate.get("bot_attributes", {})

    if len(dialog["bot_utterances"]) == 0 and greeting_spec[LANGUAGE] not in best_text:
        # add greeting to the first bot uttr, if it's not already included
        best_text = f"{HI_THIS_IS_DREAM[LANGUAGE]} {best_text}"

    while candidates[best_id]["text"] == "" or candidates[best_id]["confidence"] == 0.0:
        curr_single_scores[int(best_id)] = 0.0
        best_id = np.argmax(curr_single_scores)
        best_skill_name = candidates[best_id]["skill_name"]
        best_text = candidates[best_id]["text"]
        best_confidence = candidates[best_id]["confidence"]
        best_human_attributes = candidates[best_id].get("human_attributes", {})
        best_bot_attributes = candidates[best_id].get("bot_attributes", {})
        if sum(curr_single_scores) == 0.0:
            break

    if dialog["human"]["profile"].get("name", False) and best_skill_name != "personal_info_skill":
        name = dialog["human"]["profile"].get("name", False)
        if len(dialog["bot_utterances"]) >= 1:
            if re.search(r"\b" + name + r"\b", dialog["bot_utterances"][-1]["text"]):
                pass
            else:
                if random.random() <= CALL_BY_NAME_PROBABILITY:
                    best_text = f"{name}, {best_text}"
        else:
            # if dialog is just started (now it's impossible)
            if random.random() <= CALL_BY_NAME_PROBABILITY:
                best_text = f"{name}, {best_text}"

    if dialog["human_utterances"][-1]["text"] == "/get_dialog_id":
        best_text = "Your dialog's id: " + str(dialog["dialog_id"])

    return best_skill_name, best_text, best_confidence, best_human_attributes, best_bot_attributes


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
