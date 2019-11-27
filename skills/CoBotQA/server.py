#!/usr/bin/env python

import json
import logging
import os
from time import time

import numpy as np
from nltk.tokenize import sent_tokenize
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

N_FACTS_TO_CHOSE = 3
ASYNC_SIZE = int(os.environ.get('ASYNC_SIZE', 10))
COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_QA_SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError('COBOT_QA_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

with open("./google-10000-english-no-swears.txt", "r") as f:
    UNIGRAMS = f.read().splitlines()[:1002]


def send_cobotqa(question):
    request_body = {'question': question}
    try:
        resp = requests.request(url=COBOT_QA_SERVICE_URL,
                                headers=headers,
                                data=json.dumps(request_body),
                                method='POST',
                                timeout=10)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("CoBotQA Timeout")
        resp = requests.Response()
        resp.status_code = 504

    if resp.status_code != 200:
        logger.warning(
            f"result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
        response = ''
        sentry_sdk.capture_message(
            f"CobotQA! result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
    else:
        response = resp.json()['response']

    return response


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    dialogs = request.json['dialogs']
    responses = []
    confidences = []

    questions = []
    dialog_ids = []
    for i, dialog in enumerate(dialogs):
        curr_uttr = dialog["utterances"][-1]
        questions.append(curr_uttr["annotations"]["sentrewrite"]["modified_sents"][-1])
        dialog_ids += [i]

        entities = []
        attit = curr_uttr["annotations"]["attitude_classification"]["text"]
        for _ in range(N_FACTS_TO_CHOSE):
            for ent in curr_uttr["annotations"]["ner"]:
                if not ent:
                    continue
                ent = ent[0]
                if ent["text"].lower() not in UNIGRAMS:
                    if attit in ["neutral", "positive", "very_positive"]:
                        entities.append(ent["text"].lower())
                        questions.append("Fun fact about {}".format(ent["text"]))
                        dialog_ids += [i]
                    else:
                        entities.append(ent["text"].lower())
                        questions.append("Fact about {}".format(ent["text"]))
                        dialog_ids += [i]
            for ent in curr_uttr["annotations"]["cobot_nounphrases"]:
                if ent.lower() not in UNIGRAMS:
                    if ent in entities + ["I", 'i']:
                        pass
                    else:
                        questions.append("Fact about {}".format(ent))
                        dialog_ids += [i]

    executor = ThreadPoolExecutor(max_workers=ASYNC_SIZE)
    for i, response in enumerate(executor.map(send_cobotqa, questions)):
        logger.info("Question: {}".format(questions[i]))
        logger.info("Response: {}".format(response))
        responses.append(response)

        if len(response) > 0 and 'skill://amzn1' not in response:
            if "let's talk about" in questions[i].lower():
                confidence = 0.5
            elif "fact about" in questions[i].lower():
                confidence = 0.7
            elif "have an opinion on that" in response:
                confidence = 0.7
            elif "Alexa, play my Flash Briefing" in response:
                confidence = 0.5
            else:
                confidence = 0.95
        else:
            confidence = 0.00
        confidences += [confidence]

    dialog_ids = np.array(dialog_ids)
    responses = np.array(responses)
    confidences = np.array(confidences)
    final_responses = []
    final_confidences = []

    for i, dialog in enumerate(dialogs):
        resp_cands = list(responses[dialog_ids == i])
        conf_cands = list(confidences[dialog_ids == i])

        annotations = dialog["utterances"][-1]["annotations"]
        intents = annotations["cobot_dialogact"]["intents"]
        opinion_request_detected = annotations["intent_catcher"].get(
            "opinion_request", {}).get("detected") == 1
        reply = dialog['utterances'][-1]['text'].replace("\'", " \'").lower()

        sensitive_topics = {"Politics", "Celebrities", "Religion", "Sex_Profanity", "Sports", "News", "Psychology"}
        # `General_ChatIntent` sensitive in case when `?` in reply
        sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"}
        cobot_topics = set(dialog['utterances'][-1]['annotations']['cobot_topics']['text'])
        sensitive_topics_detected = any([t in sensitive_topics for t in cobot_topics])
        cobot_dialogacts = dialog['utterances'][-1]['annotations']['cobot_dialogact']['intents']
        sensitive_dialogacts_detected = any([(t in sensitive_dialogacts and "?" in reply) for t in cobot_dialogacts])
        blist_topics_detected = dialog['utterances'][-1]['annotations']['blacklisted_words']['restricted_topics']

        for j in range(len(resp_cands)):
            sentences = sent_tokenize(resp_cands[j])
            # initial answer to the user's reply
            if j == 0 and len(sentences) > 2:
                resp_cands[j] = " ".join(sentences[:2])
            # facts from cobotqa
            if j != 0 and len(sentences) >= 2:
                if len(sentences[0]) < 100 and "fact" in sentences[0]:
                    resp_cands[j] = " ".join(sentences[:2])
                else:
                    resp_cands[j] = " ".join(sentences[:1])
            if j != 0:
                # facts
                talk_about = ["What kind of movies do you like movies?",
                              "How often do you go to movies?",
                              "Who is your favorite actor or actress?"]
                if ("Opinion_RequestIntent" in intents) or opinion_request_detected:
                    resp_cands[j] = f"I don't have an opinion on that but I know some facts. {resp_cands[j]} " \
                                    f"Maybe we can talk about something else. {np.random.choice(talk_about)}"
                elif blist_topics_detected or (sensitive_topics_detected and sensitive_dialogacts_detected):
                    resp_cands[j] = f"I don't have an opinion on that but I know some facts. {resp_cands[j]} " \
                                    f"Let's talk about something else. {np.random.choice(talk_about)}"

        final_responses.append(resp_cands)
        final_confidences.append(conf_cands)

    total_time = time() - st_time
    logger.info(f'cobotqa exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
