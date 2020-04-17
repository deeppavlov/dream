#!/usr/bin/env python

import logging
import re
import time
import numpy as np
import random
from flask import Flask, request, jsonify
from os import getenv
from collections import Counter
import sentry_sdk
import pprint
from nltk.tokenize import sent_tokenize

from common.universal_templates import if_lets_chat_about_topic, if_choose_topic
from common.utils import scenario_skills, retrieve_skills, okay_statements, is_question

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CALL_BY_NAME_PROBABILITY = 0.5  # if name is already known
ASK_DUMMY_QUESTION_PROB = 0.5
ASK_LINK_TO_FOR_RETRIEVE_PROB = 0.5


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    response_candidates = [dialog["utterances"][-1]["hypotheses"] for dialog in dialogs_batch]

    dialog_ids = []
    selected_skill_names = []
    selected_texts = []
    selected_confidences = []
    selected_human_attributes = []
    selected_bot_attributes = []
    confidences = []
    utterances = []
    skill_names = []

    annotations = []
    for i, dialog in enumerate(dialogs_batch):
        for skill_data in response_candidates[i]:
            if len(dialog["utterances"]) > 1:
                assert len(dialog["human_utterances"]) > 0
                assert len(dialog["bot_utterances"]) > 0
            dialog_ids += [i]
            confidences += [skill_data["confidence"]]
            utterances += [skill_data["text"]]  # all bot utterances
            skill_names += [skill_data["skill_name"]]
            annotations += [skill_data.get("annotations", {})]
            if skill_data["text"] and skill_data["confidence"]:
                if not skill_data.get("annotations"):
                    logger.warning(f"Valid skill data without annotations: {skill_data}")
    default_toxic = {
        "identity_hate": 0.0,
        "insult": 0.0,
        "obscene": 0.0,
        "severe_toxic": 0.0,
        "sexual_explicit": 0.0,
        "threat": 0.0,
        "toxic": 0.0
    }
    toxic_result = [annotation.get('toxic_classification', default_toxic) for annotation in annotations]
    toxicities = [max(res.values()) for res in toxic_result]
    stop_result = [annotation.get('stop_detect', {'stop': 0}) for annotation in annotations]
    stop_probs = [j['stop'] for j in stop_result]
    default_blacklist = {'inappropriate': False, 'profanity': False, 'restricted_topics': False}
    blacklist_result = [annotation.get('blacklisted_words', default_blacklist) for annotation in annotations]
    has_blacklisted = [int(res['profanity']) for res in blacklist_result]
    has_inappropriate = [int(res['inappropriate']) for res in blacklist_result]
    for i, has_blisted in enumerate(has_blacklisted):
        if has_blisted:
            with sentry_sdk.push_scope() as scope:
                scope.set_extra('utterance', utterances[i])
                scope.set_extra('selected_skills', response_candidates[dialog_ids[i]])
                sentry_sdk.capture_message("response selector got candidate with blacklisted phrases")
                msg = f"response selector got candidate with blacklisted phrases:\n" \
                      f"utterance: {utterances[i]}\n" \
                      f"selected_skills: {response_candidates[dialog_ids[i]]}"
                logger.info(msg)

    default_conv_eval = {
        "isResponseOnTopic": 0.,
        "isResponseInteresting": 0.,
        "responseEngagesUser": 0.,
        "isResponseComprehensible": 0.,
        "isResponseErroneous": 0.
    }
    result = [annotation.get('cobot_convers_evaluator_annotator', default_conv_eval) for annotation in annotations]
    result = np.array(result)

    dialog_ids = np.array(dialog_ids)
    confidences = np.array(confidences)
    toxicities = np.array(toxicities)
    stop_probs = np.array(stop_probs)
    has_blacklisted = np.array(has_blacklisted)
    has_inappropriate = np.array(has_inappropriate)
    for i, dialog in enumerate(dialogs_batch):
        # curr_candidates is dict
        curr_candidates = response_candidates[i]
        logger.info(f"Curr candidates:")
        logger.info(pprint.pformat(curr_candidates, compact=False))
        # choose results which correspond curr candidates
        curr_scores = result[dialog_ids == i]  # array of dictionaries
        curr_confidences = confidences[dialog_ids == i]  # array of float numbers

        best_skill_name, best_text, best_confidence, best_human_attributes, best_bot_attributes = select_response(
            curr_candidates, curr_scores, curr_confidences,
            toxicities[dialog_ids == i], has_blacklisted[dialog_ids == i], has_inappropriate[dialog_ids == i],
            stop_probs[dialog_ids == i], dialog)

        selected_skill_names.append(best_skill_name)
        selected_texts.append(best_text)
        selected_confidences.append(best_confidence)
        selected_human_attributes.append(best_human_attributes)
        selected_bot_attributes.append(best_bot_attributes)
        logger.info(f"Choose selected_skill_names: {selected_skill_names};"
                    f"selected_texts {selected_texts}; selected_confidences {selected_confidences};"
                    f"selected human attributes: {selected_human_attributes}; "
                    f"selected bot attributes: {selected_bot_attributes}")

    total_time = time.time() - st_time
    logger.info(f'convers_evaluation_selector exec time: {total_time:.3f}s')
    return jsonify(list(zip(selected_skill_names, selected_texts, selected_confidences,
                            selected_human_attributes, selected_bot_attributes)))


def add_question_to_statement(best_text, best_skill_name, question, link_to_question):
    if best_text.strip() in okay_statements:
        if question != "" and random.random() < ASK_DUMMY_QUESTION_PROB:
            logger.info(f"adding {question} to response.")
            best_text += np.random.choice([f" Let me ask you something. {question}",
                                           f" I would like to ask you a question. {question}"])
    elif best_skill_name in retrieve_skills:
        if not is_question(best_text) and random.random() < ASK_LINK_TO_FOR_RETRIEVE_PROB:
            logger.info(f"adding link_to {link_to_question} to response.")
            best_text += f". {link_to_question}"

    return best_text


def lower_duplicates_score(candidates, bot_utt_counter, scores, confidences):
    for i, cand in enumerate(candidates):
        cand_sents = sent_tokenize(cand["text"].lower())
        coeff = 1
        for cand_sent in cand_sents:
            if len(cand_sent.split()) >= 3:
                coeff += bot_utt_counter[cand_sent]

        if confidences[i] < 1.:
            confidences[i] /= coeff
            scores[i]['isResponseInteresting'] /= coeff
            scores[i]['responseEngagesUser'] /= coeff


def lower_retrieve_skills_confidence_if_scenario_exist(candidates, scores, confidences):
    has_scenario_skill = False
    lower_coeff = 0.25  # Lower confidence and isResponseInteresting for retrieve skills to 25%
    for cand in candidates:
        if cand['skill_name'] in scenario_skills and cand['text'] and cand['confidence'] >= 0.9:
            has_scenario_skill = True
            break
    if has_scenario_skill:
        for i, cand in enumerate(candidates):
            if cand['skill_name'] in retrieve_skills:
                confidences[i] *= lower_coeff
                scores[i]['isResponseInteresting'] *= lower_coeff


def calculate_single_convers_evaluator_score(cand_scores):
    score_conv_eval = sum([cand_scores["isResponseOnTopic"],
                           cand_scores["isResponseInteresting"],
                           cand_scores["responseEngagesUser"],
                           cand_scores["isResponseComprehensible"]])
    score_conv_eval -= cand_scores["isResponseErroneous"]
    return score_conv_eval


def select_response(candidates, scores, confidences, toxicities, has_blacklisted,
                    has_inappropriate, stop_probs, dialog):
    confidence_strength = 2
    conv_eval_strength = 0.4
    stop_threshold = 0.9  # 0.78  To provide 99% precision on STOP class. For now 0.9 to fix tests
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_single_scores = []

    # exclude toxic messages and messages with blacklisted phrases
    ids = (toxicities > 0.5) | (has_blacklisted > 0) | (has_inappropriate > 0) | (stop_probs > stop_threshold)
    logger.info(f"Bot excluded utterances: {ids}. toxicities: {toxicities};"
                f"has_blacklisted: {has_blacklisted}; has_inappropriate: {has_inappropriate};"
                f"stop probs: {stop_probs}")

    if sum(ids) == len(toxicities):
        # the most dummy заглушка на случай, когда все абсолютно скиллы вернули токсичные ответы
        non_toxic_answers = ["I really do not know what to answer.",
                             "Sorry, probably, I didn't get what you mean.",
                             "I didn't get it. Sorry"
                             ]
        non_toxic_answer = np.random.choice(non_toxic_answers)
        return None, non_toxic_answer, 1.0, {}, {}

    scores[ids] = {"isResponseOnTopic": 0.,
                   "isResponseInteresting": 0.,
                   "responseEngagesUser": 0.,
                   "isResponseComprehensible": 0.,
                   "isResponseErroneous": 1.,
                   }
    confidences[ids] = 0.

    # check for repetitions
    bot_utterances = [sent_tokenize(uttr["text"].lower()) for uttr in dialog["bot_utterances"]]
    prev_large_utterances = [utt for utt in bot_utterances[:-40] if len(utt) >= 40]
    bot_utterances = prev_large_utterances + bot_utterances[-40:]
    # flatten 2d list to 1d list of all appeared sentences of bot replies
    bot_utterances = sum(bot_utterances, [])
    bot_utt_counter = Counter(bot_utterances)

    lower_duplicates_score(candidates, bot_utt_counter, scores, confidences)
    lower_retrieve_skills_confidence_if_scenario_exist(candidates, scores, confidences)

    prev_active_skill = dialog["bot_utterances"][-1]['active_skill'] if len(dialog["bot_utterances"]) > 0 else ''
    skill_names = [c['skill_name'] for c in candidates]
    how_are_you_spec = "Do you want to know what I can do?"  # this is always at the end of answers to `how are you`
    what_i_can_do_spec = "socialbot running inside"
    psycho_help_spec = "If you or someone you know is in immediate danger"
    greeting_spec = "this is an Alexa Prize Socialbot"
    misheard_with_spec1 = "I misheard you"
    misheard_with_spec2 = "like to chat about"
    alexa_abilities_spec = "If you want to use the requested feature say"

    very_big_score = 100
    very_low_score = -100
    question = ""
    link_to_question = ""

    for i in range(len(scores)):
        curr_score = None
        is_misheard = misheard_with_spec1 in candidates[i]['text'] or misheard_with_spec2 in candidates[i]['text']
        if len(dialog['human_utterances']) == 1 and greeting_spec not in candidates[i]['text']:
            logger.info("Dialog Beginning detected.")
            if if_lets_chat_about_topic(dialog['utterances'][0]["text"].lower()) and \
                    "about it" not in dialog['utterances'][0]["text"].lower():
                logger.info("User wants to talk about particular topic")
                # if user says `let's chat about blablabla`
                if skill_names[i] == 'cobotqa':
                    logger.info("Particular topic. CoBotQA + Greeting to very big score.")
                    # I don't have an opinion on that but I know some facts.
                    resp = candidates[i]['text'].replace("I don't have an opinion on that but I know some facts.", "")
                    candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + resp
                    curr_score = very_big_score
                elif skill_names[i] == 'meta_script_skill' and len(candidates[i]['text']) > 0 and \
                        confidences[i] > 0.98:
                    logger.info("Particular topic. meta_script_skill + Greeting to very big score.")
                    # I don't have an opinion on that but I know some facts.
                    resp = candidates[i]['text']
                    candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + resp
                    curr_score = very_big_score
                elif skill_names[i] == 'small_talk_skill':
                    logger.info("Particular topic. Small-talk + Greeting NOT to very big score.")
                    # for now do not give small talk a very big score here
                    candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + candidates[i]['text']
                    # curr_score = very_big_score
            elif if_choose_topic(dialog['utterances'][0]["text"].lower()) and \
                    "about it" not in dialog['utterances'][0]["text"].lower():
                logger.info("User wants bot to choose the topic")
                # if user says `let's chat about something`
                if skill_names[i] == 'small_talk_skill':
                    logger.info("No topic. Small-talk + Greeting to very big score.")
                    candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + candidates[i]['text']
                    curr_score = very_big_score
                elif skill_names[i] == 'meta_script_skill' and len(candidates[i]['text']) > 0:
                    logger.info("No topic. Meta-script + Greeting to very big score.")
                    candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + candidates[i]['text']
                    curr_score = very_big_score
            else:
                logger.info("User just wants to talk.")
                # if user says something else
                if skill_names[i] == 'program_y' and greeting_spec in candidates[i]['text']:
                    logger.info("Just chat. Program-y to very big score.")
                    curr_score = very_big_score
        elif skill_names[i] == 'program_y' and prev_active_skill == 'program_y' and (
                how_are_you_spec in candidates[i]['text'] or what_i_can_do_spec in candidates[i]['text']) \
                and len(dialog['utterances']) < 16:
            curr_score = very_big_score
        elif skill_names[i] == 'program_y_dangerous' and psycho_help_spec in candidates[i]['text']:
            curr_score = very_big_score
        elif skill_names[i] == 'program_y' and greeting_spec in candidates[i]['text']:
            if len(dialog["utterances"]) < 2:
                curr_score = very_big_score
            else:
                confidences[i] = 0.2  # Low confidence for greeting in the middle of dialogue
        elif skill_names[i] == 'cobotqa' and "Here's something I found on the web." in candidates[i]['text']:
            confidences[i] = 0.6
        elif skill_names[i] == 'misheard_asr' and is_misheard:
            curr_score = very_big_score
        elif (skill_names[i] == 'intent_responder' or skill_names[i] == 'program_y') and "#+#" in candidates[i]['text']:
            curr_score = very_big_score
        elif skill_names[i] == 'program_y' and alexa_abilities_spec in candidates[i]['text']:
            curr_score = very_big_score
        elif skill_names[i] == 'meta_script_skill' and len(dialog['utterances']) >= 2 and \
                candidates[i].get("meta_script_status", "") == "starting":
            if len(dialog['utterances']) >= 5 and confidences[i] == 0.99:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.99)
                # when faced topic switching intent or matched phrase,
                # return it with probability 0.15
                if random.random() < 0.15:
                    curr_score = very_big_score
            elif 0.98 > confidences[i] > 0.7:
                # if meta_script returns starting phrase in the beginning of dialog (conf 0.8),
                # return it with probability 0.1
                r = random.random()
                if r < 0.1:
                    curr_score = very_big_score
                elif 0.1 <= r < 0.5:
                    curr_score = very_low_score
            elif confidences[i] == 0.6:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.6)
                # return it with probability 0.1
                if random.random() < 0.1:
                    curr_score = very_big_score
            elif confidences[i] == 0.7:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.7)
                # when faced some USER topic
                if random.random() < 0.3:
                    curr_score = very_big_score
        elif skill_names[i] in ["dummy_skill", "convert_reddit", "alice", "eliza", "tdidf_retrieval", "program_y"]:
            if "question" in candidates[i].get("type", "") or "?" in candidates[i]['text']:
                if skill_names[i] == "program_y":
                    if len(bot_utterances) >= 4 and "?" in bot_utterances[-1]:
                        confidences[i] /= 1.5
                    if len(bot_utterances) >= 5 and "?" in bot_utterances[-2]:
                        confidences[i] /= 1.1
                else:
                    if len(bot_utterances) >= 1 and "?" in bot_utterances[-1]:
                        confidences[i] /= 1.5
                    if len(bot_utterances) >= 2 and "?" in bot_utterances[-2]:
                        confidences[i] /= 1.1
            if "link_to_for_response_selector" in candidates[i].get("type", ""):
                link_to_question = candidates[i]['text']
        if skill_names[i] == 'dummy_skill' and "question" in candidates[i].get("type", ""):
            question = candidates[i]['text']

        if curr_score is None:
            cand_scores = scores[i]
            confidence = confidences[i]
            skill_name = skill_names[i]
            score_conv_eval = calculate_single_convers_evaluator_score(cand_scores)
            score = conv_eval_strength * score_conv_eval + confidence_strength * confidence
            logger.info(f'Skill {skill_name} has final score: {score}. Confidence: {confidence}. '
                        f'Toxicity: {toxicities[i]}. Cand scores: {cand_scores}')
            curr_single_scores.append(score)
        else:
            cand_scores = scores[i]
            skill_name = skill_names[i]
            score_conv_eval = calculate_single_convers_evaluator_score(cand_scores)
            score = conv_eval_strength * score_conv_eval + curr_score
            logger.info(f'Skill {skill_name} has final score: {score}. '
                        f'Toxicity: {toxicities[i]}. Cand scores: {cand_scores}')
            curr_single_scores.append(score)

    highest_conf_exist = True if any(confidences >= 1.) else False
    if highest_conf_exist:
        logger.info("Found skill with the highest confidence.")
    for j in range(len(candidates)):
        if highest_conf_exist and confidences[j] < 1. and curr_single_scores[j] < very_big_score:
            # need to drop this candidates
            logger.info(f"Dropping {skill_names[j]} which does not have a highest confidence or `very big score`.")
            curr_single_scores[j] = very_low_score

    best_id = np.argmax(curr_single_scores)
    best_skill_name = skill_names[int(best_id)]
    best_text = candidates[best_id]["text"]
    best_confidence = candidates[best_id]["confidence"]
    best_human_attributes = candidates[best_id].get("human_attributes", {})
    best_bot_attributes = candidates[best_id].get("bot_attributes", {})

    best_text = add_question_to_statement(best_text, best_skill_name, question, link_to_question)

    if len(dialog["bot_utterances"]) == 0 and greeting_spec not in best_text:
        # add greeting to the first bot uttr, if it's not already included
        best_text = "Hello, " + greeting_spec + '! ' + best_text

    while candidates[best_id]["text"] == "" or candidates[best_id]["confidence"] == 0.:
        curr_single_scores[int(best_id)] = 0.
        best_id = np.argmax(curr_single_scores)
        best_skill_name = candidates[best_id]["skill_name"]
        best_text = candidates[best_id]["text"]
        best_confidence = candidates[best_id]["confidence"]
        best_human_attributes = candidates[best_id].get("human_attributes", {})
        best_bot_attributes = candidates[best_id].get("bot_attributes", {})
        if sum(curr_single_scores) == 0.:
            break

    if dialog["human"]["profile"].get("name", False):
        name = dialog["human"]["profile"].get("name", False)
        if len(dialog["utterances"]) >= 2:
            if re.search(r"\b" + name + r"\b", dialog["utterances"][-2]["text"]):
                pass
            else:
                if random.random() <= CALL_BY_NAME_PROBABILITY:
                    best_text = f"{name}, {best_text}"
        else:
            # if dialog is just started (now it's impossible)
            if random.random() <= CALL_BY_NAME_PROBABILITY:
                best_text = f"{name}, {best_text}"

    return best_skill_name, best_text, best_confidence, best_human_attributes, best_bot_attributes


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
