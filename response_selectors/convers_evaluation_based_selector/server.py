#!/usr/bin/env python

import json
import logging
import os
import re
import time
import numpy as np
from random import uniform

import requests
from flask import Flask, request, jsonify
from os import getenv
from collections import Counter
import sentry_sdk
import pprint
from nltk.tokenize import sent_tokenize

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_CONVERSATION_EVALUATION_SERVICE_URL = os.environ.get('COBOT_CONVERSATION_EVALUATION_SERVICE_URL')
TOXIC_COMMENT_CLASSIFICATION_SERVICE_URL = "http://toxic_classification:8013/toxicity_annotations"
BLACKLIST_DETECTOR_URL = "http://blacklisted_words:8018/blacklisted_words"
CALL_BY_NAME_PROBABILITY = 0.5  # if name is already known

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_CONVERSATION_EVALUATION_SERVICE_URL is None:
    raise RuntimeError('COBOT_CONVERSATION_EVALUATION_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


def custom_request(url, headers, data, timeout, method='POST'):
    return requests.request(url=url, headers=headers, data=data, method=method, timeout=timeout)


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    response_candidates_raw = [dialog["utterances"][-1]["hypotheses"] for dialog in dialogs_batch]
    response_candidates = []
    for hypots_list in response_candidates_raw:
        new_hypots = [h for h in hypots_list if h['confidence'] > 0]
        response_candidates.append(new_hypots)

    conversations = []
    dialog_ids = []
    selected_skill_names = []
    selected_texts = []
    selected_confidences = []
    selected_human_attributes = []
    selected_bot_attributes = []
    confidences = []
    utterances = []
    skill_names = []

    for i, dialog in enumerate(dialogs_batch):
        for skill_data in response_candidates[i]:
            conv = dict()

            conv["currentUtterance"] = dialog["utterances"][-1]["text"]
            conv["currentResponse"] = skill_data["text"]
            # cobot recommends to take 2 last utt for conversation evaluation service
            conv["pastUtterances"] = [uttr["text"] for uttr in dialog["human_utterances"]][-3:-1]
            conv["pastResponses"] = [uttr["text"] for uttr in dialog["bot_utterances"]][-2:]
            # collect all the conversations variants to evaluate them batch-wise
            conversations += [conv]
            dialog_ids += [i]
            confidences += [skill_data["confidence"]]
            utterances += [skill_data["text"]]  # all bot utterances
            skill_names += [skill_data["skill_name"]]

    # TODO: refactor external service calls
    # check all possible skill responses for toxicity
    conv_data = json.dumps({'conversations': conversations})
    sent_data = json.dumps({'sentences': utterances})

    try:
        toxic_result = custom_request(TOXIC_COMMENT_CLASSIFICATION_SERVICE_URL, headers, sent_data, 1)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("toxic result Timeout")
        sentry_sdk.capture_exception(e)
        toxic_result = requests.Response()
        toxic_result.status_code = 504

    try:
        blacklist_result = custom_request(BLACKLIST_DETECTOR_URL, headers, sent_data, 1)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("blacklist_result Timeout")
        sentry_sdk.capture_exception(e)
        blacklist_result = requests.Response()
        blacklist_result.status_code = 504

    try:
        # evaluate all possible skill responses
        result = custom_request(COBOT_CONVERSATION_EVALUATION_SERVICE_URL, headers, conv_data, 1)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("cobot convers eval Timeout")
        sentry_sdk.capture_exception(e)
        result = requests.Response()
        result.status_code = 504

    if toxic_result.status_code != 200:
        msg = "Toxic classifier: result status code is not 200: {}. result text: {}; result status: {}".format(
            toxic_result, toxic_result.text, toxic_result.status_code)
        logger.warning(msg)
        toxicities = [0.] * len(utterances)
    else:
        toxic_result = toxic_result.json()
        toxicities = [max(res[0].values()) for res in toxic_result]

    if blacklist_result.status_code != 200:
        msg = "blacklist detector: result status code is not 200: {}. result text: {}; result status: {}".format(
            blacklist_result, blacklist_result.text, blacklist_result.status_code)
        logger.warning(msg)
        has_blacklisted = [False] * len(utterances)
        has_inappropriate = [False] * len(utterances)
    else:
        blacklist_result = blacklist_result.json()
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

    if result.status_code != 200:
        msg = "Cobot Conversation Evaluator: result status code is \
  not 200: {}. result text: {}; result status: {}".format(result, result.text, result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        result = np.array([{"isResponseOnTopic": 0.,
                            "isResponseInteresting": 0.,
                            "responseEngagesUser": 0.,
                            "isResponseComprehensible": 0.,
                            "isResponseErroneous": 0.,
                            }
                           for _ in conversations])
    else:
        result = result.json()
        result = np.array(result["conversationEvaluationScores"])

    dialog_ids = np.array(dialog_ids)
    confidences = np.array(confidences)
    toxicities = np.array(toxicities)
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
            dialog)

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


def select_response(candidates, scores, confidences, toxicities, has_blacklisted, has_inappropriate, dialog):
    confidence_strength = 2
    conv_eval_strength = 0.4
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_single_scores = []

    # exclude toxic messages and messages with blacklisted phrases
    ids = (toxicities > 0.5) | (has_blacklisted > 0) | (has_inappropriate > 0)
    logger.info(f"Bot excluded utterances: {ids}. toxicities: {toxicities};"
                f"has_blacklisted: {has_blacklisted}; has_inappropriate: {has_inappropriate}")

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

    for i, cand in enumerate(candidates):
        cand_sents = sent_tokenize(cand["text"].lower())
        coeff = 1
        for cand_sent in cand_sents:
            coeff += bot_utt_counter[cand_sent]
        confidences[i] /= coeff
        scores[i]['isResponseInteresting'] /= coeff
        scores[i]['responseEngagesUser'] /= coeff

    skill_names = [c['skill_name'] for c in candidates]
    how_are_you_spec = "I'm fine, thanks! Do you want to know what I can do?"
    what_i_can_do_spec = "a newborn socialbot"
    psycho_help_spec = "If you or someone you know is in immediate danger"
    greeting_spec = "this is an Alexa Prize Socialbot"
    misheard_with_spec1 = "I misheard you"
    misheard_with_spec2 = "like to chat about"
    alexa_abilities_spec = "If you want to use the requested feature say"

    very_big_score = 100
    very_low_score = -100
    question = ""

    for i in range(len(scores)):
        curr_score = None
        is_misheard = misheard_with_spec1 in candidates[i]['text'] or misheard_with_spec2 in candidates[i]['text']
        if len(dialog['utterances']) < 2 and greeting_spec not in candidates[i]['text'] \
                and skill_names[i] == 'program_y':
            # greet user in first utterance
            if "Sorry, I don't have an answer for that!" in candidates[i]['text']:
                candidates[i]['text'] = "Hello, " + greeting_spec + '! '
            else:
                candidates[i]['text'] = "Hello, " + greeting_spec + '! ' + candidates[i]['text']
            curr_score = very_big_score
        elif skill_names[i] == 'program_y' and (
                candidates[i]['text'] == how_are_you_spec or what_i_can_do_spec in candidates[i]['text']) \
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
        elif skill_names[i] == 'intent_responder' and "#+#" in candidates[i]['text']:
            curr_score = very_big_score
        elif skill_names[i] == 'program_y' and alexa_abilities_spec in candidates[i]['text']:
            curr_score = very_big_score
        elif skill_names[i] == 'meta_script_skill' and len(dialog['utterances']) >= 2:
            if len(dialog['utterances']) >= 5 and confidences[i] == 0.99:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.99)
                # when faced topic switching intent or matched phrase,
                # return it with probability 0.15
                if uniform(0, 1.) < 0.15:
                    curr_score = very_big_score
            elif confidences[i] == 0.9:
                # if meta_script returns starting phrase in the beginning of dialog (conf 0.9),
                # return it with probability 0.1
                r = uniform(0, 1.)
                if r < 0.1:
                    curr_score = very_big_score
                elif 0.1 <= r < 0.5:
                    curr_score = very_low_score
            elif confidences[i] == 0.6:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.6)
                # return it with probability 0.1
                if uniform(0, 1.) < 0.1:
                    curr_score = very_big_score
            elif confidences[i] == 0.7:
                # if meta_script returns starting phrase in the middle of dialog (conf 0.7)
                # when faced some USER topic
                if uniform(0, 1.) < 0.3:
                    curr_score = very_big_score
        if skill_names[i] == 'dummy_skill' and "question" in candidates[i].get("type", ""):
            question = candidates[i]['text']

        if curr_score is None:
            cand_scores = scores[i]
            confidence = confidences[i]
            skill_name = skill_names[i]
            score_conv_eval = sum([cand_scores["isResponseOnTopic"],
                                   cand_scores["isResponseInteresting"],
                                   cand_scores["responseEngagesUser"],
                                   cand_scores["isResponseComprehensible"]])
            score_conv_eval -= cand_scores["isResponseErroneous"]
            score = conv_eval_strength * score_conv_eval + confidence_strength * confidence
            logger.info(f'Skill {skill_name} has score: {score}. Toxicity: {toxicities[i]} '
                        f'Cand scores: {cand_scores}')
            curr_single_scores.append(score)
        else:
            curr_single_scores.append(curr_score)

    highest_conf_exist = True if any(confidences >= 1.) else False
    for j in range(len(candidates)):
        if highest_conf_exist and confidences[j] < 1. and curr_single_scores[j] != very_big_score:
            # need to drop this candidates
            logger.info(f"Found highest confidence. Dropping {skill_names[j]}")
            curr_single_scores[j] = - 1.

    best_id = np.argmax(curr_single_scores)
    best_skill_name = skill_names[best_id]
    best_text = candidates[best_id]["text"]
    best_confidence = candidates[best_id]["confidence"]
    best_human_attributes = candidates[best_id].get("human_attributes", {})
    best_bot_attributes = candidates[best_id].get("bot_attributes", {})

    if best_text.strip() in ["Okay.", "That's cool!", "Interesting.", "Sounds interesting.", "Sounds interesting!",
                             "OK.", "Cool!", "Thanks!", "Okay, thanks.", "I'm glad you think so!",
                             "Sorry, I don't have an answer for that!", "Let's talk about something else.",
                             "As you wish.", "All right.", "Right.", "Anyway.", "Oh, okay.", "Oh, come on.",
                             "Really?", "Okay. I got it.", "Well, okay.", "Well, as you wish."]:
        if question != "":
            logger.info(f"adding {question} to response.")
            best_text += np.random.choice([f" Let me ask you something. {question}",
                                           f" I would like to ask you a question. {question}"])

    while candidates[best_id]["text"] == "" or candidates[best_id]["confidence"] == 0.:
        curr_single_scores[best_id] = 0.
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
                if np.random.uniform() <= CALL_BY_NAME_PROBABILITY:
                    best_text = f"{name}, {best_text}"
        else:
            # if dialog is just started (now it's impossible)
            if np.random.uniform() <= CALL_BY_NAME_PROBABILITY:
                best_text = f"{name}, {best_text}"

    return best_skill_name, best_text, best_confidence, best_human_attributes, best_bot_attributes


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
