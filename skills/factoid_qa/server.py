#!/usr/bin/env python

import logging
import re
import time
import random
import json
import sys
import requests
import sentry_sdk
from deeppavlov import build_model
from flask import Flask, request, jsonify
from os import getenv

from common.factoid import DONT_KNOW_ANSWER, FACTOID_NOTSURE_CONFIDENCE

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

FACTOID_DEFAULT_CONFIDENCE = 0.99  # otherwise dummy often beats it
ASKED_ABOUT_FACT_PROB = 0.99
FACTOID_CLASS_THRESHOLD = 0.5
factoid_classifier = build_model(config="./yahoo_convers_vs_info_light.json", download=False)
fact_dict = json.load(open('fact_dict.json', 'r'))

tell_me = r"(do you know|(can|could) you tell me|tell me)"
tell_me_template = re.compile(tell_me)
full_template = re.compile(tell_me + r" (who|where|when|what|why)")
partial_template = re.compile(r"(who|where|when|what|why)")


def get_random_facts(ner_outputs_to_classify):
    responses = []
    for names in ner_outputs_to_classify:
        num_facts = [len(fact_dict[name]) for name in names]
        max_fact_num = 0
        if len(num_facts) > 0:
            max_fact_num = max(num_facts)
        # we output fact about name about which we have the largest number of facts
        response = ''
        for name in names:
            if len(fact_dict[name]) == max_fact_num:
                phrase_start = 'Here is a fact about {}'.format(name) + '. '
                phrase_end = random.choice(fact_dict[name])
                if response == '':
                    response = phrase_start + phrase_end
        responses.append(response)
    return responses


def asked_about_fact(x):
    return any([j in x.lower() for j in ['fact about', 'talk about',
                                         'tell me about', 'tell me more about']])


def getKbqaResponse(query):
    kbqa_response = dict()
    kbqa_response["response"] = "Not Found"
    kbqa_response["confidence"] = 0.0
    # adding experimental KBQA support
    try:
        x = [query]
        kbqa_request_dict = dict([('x', x)])
        kbqa_request = json.dumps(kbqa_request_dict, ensure_ascii=False).encode('utf8')
        # kbqa_request = "{ \"x\": [" + last_phrase + "] }"
        logging.info('Preparing to run query against KBQA DP Model: ' + str(kbqa_request))
        # kbqa_request = kbqa_request.encode(encoding='utf-8')
        resp = requests.post('http://kbqa:8072/model', data=kbqa_request)
        if resp.status_code != 200:
            logging.info('API Error: KBQA DP Model inaccessible, status code: ' + str(resp.status_code))
        else:
            logging.info('Query against KBQA DP Model succeeded')
            logging.info('Response: ' + str(resp.json()))
            kbqa_response["response"] = resp.json()[0][0][0]
            kbqa_response["confidence"] = resp.json()[0][0][1]
    except Exception as ex:
        logging.info('Failed to run query against KBQA DP Model' + sys.exc_info()[0])
        logging.info('Exception: ' + str(ex))

    return kbqa_response


@app.route("/test", methods=['POST'])
def test():
    last_phrase = request.json["query"]
    return getKbqaResponse(last_phrase)


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    attributes = []
    sentences_to_classify = []
    ner_outputs_to_classify = []
    is_factoid_sents = []

    for dialog in dialogs_batch:
        uttr = dialog["human_utterances"][-1]
        # probabilities of being factoid question
        is_factoid_sents.append(uttr["annotations"].get("factoid_classification", {}).get("factoid", 0))
        last_phrase = dialog["human_utterances"][-1]["text"]
        if 'about' in last_phrase:
            probable_subjects = last_phrase.split('about')[1:]
        else:
            probable_subjects = []
        names = dialog["human_utterances"][-1]["annotations"]["ner"]
        names = [j[0]['text'].lower() for j in names if len(j) > 0]
        names = [j for j in names + probable_subjects if j in fact_dict.keys()]
        names = list(set(names))
        ner_outputs_to_classify.append(names)

    logging.info('Ner outputs ' + str(ner_outputs_to_classify))
    fact_outputs = get_random_facts(ner_outputs_to_classify)
    logging.info('Fact outputs ' + str(fact_outputs))
    for i in range(len(sentences_to_classify)):
        if asked_about_fact(sentences_to_classify[i]):
            is_factoid_sents[i] = ASKED_ABOUT_FACT_PROB

    # factoid_classes = [cl > FACTOID_CLASS_THRESHOLD for cl in factoid_classes]
    # logging.info('Factoid classes ' + str(factoid_classes))

    kbqa_response = dict()
    kbqa_response = getKbqaResponse(query=last_phrase)

    for dialog, is_factoid, fact_output in zip(dialogs_batch,
                                               is_factoid_sents,
                                               fact_outputs):
        attr = {}
        if is_factoid:
            logger.info("Question is classified as factoid.")
            if "Not Found" not in kbqa_response["response"]:
                logger.info("Factoid question. Answer with KBQA response.")
                # capitalizing
                response = str(kbqa_response["response"]).capitalize()
                # FACTOID_DEFAULT_CONFIDENCE
                confidence = kbqa_response["confidence"]
            # and "?" in dialog["human_utterances"][-1]["text"]: Factoid questions can be without ?
            elif len(fact_output) > 0:
                logger.info("Factoid question. Answer with pre-recorded facts.")
                response = "Here's something I've found on the web... " + fact_output
                confidence = FACTOID_DEFAULT_CONFIDENCE
            else:
                response = random.choice(DONT_KNOW_ANSWER)
                confidence = FACTOID_NOTSURE_CONFIDENCE
                attr['not sure'] = True
        else:
            logger.info("Question is not classified as factoid.")
            response = ""
            confidence = 0.

        responses.append(response)
        confidences.append(confidence)
        attributes.append(attr)
    logging.info("Responses " + str(responses))
    total_time = time.time() - st_time
    logger.info(f'factoid_qa exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
