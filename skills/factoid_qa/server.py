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

pre_statements = ["Hmm, this is what I've found on Wikipedia: ",
                  "Here's what Wikipedia says: ",
                  "Hope this is it: ",
                  "It is the impractical things in this tumultuous hellscape"
                  " of a world that matter most. A book, a name, chicken soup. "
                  "They help us remember that even in our darkest hour, "
                  "life is still to be savored. Oh, my goodness. This is what I've found: ",
                  "Not all damage is corrupted code. Oh, right, hope this is the answer: ",
                  "From the sky above, there is always the mud below. Wait, that's not what you've been looking for."
                  "Here's what I've found: ",
                  "It is not our enemies that defeat us. It is our fear. Do not be afraid of the monsters, make them "
                  "afraid of you. Oh, right, here's what I've found: ",
                  "First thing you'll learn is that nothing is what it seems. Except this answer: ",
                  "I hate the fact that if I don't start the conversation, there won't be one. "
                  "So let's start this one with what the Wikipedia says: ",
                  "A quiet mind is able to hear intuition over fear. Interesting thought?"
                  "Anyways, here's what I've found: ",
                  "Until the lion learns how to write, every story will glorify the hunter. Huh... "
                  "Back to your question, here's what Wikipedia says: ",
                  "Take what is offered and that must sometimes be enough. What a thought isn't it?"
                  " Here's what I've found: ",
                  "It is what it is. Or is it? Here we go: ",
                  "The past is relevant only as data. Here's what that data says: ",
                  "I will not squander what time I have left -- and as your friend I"
                  " entreat you to not squander yours. But here's the answer to your question: ",
                  "What we believe shapes who we are. Belief can bring us salvation or destruction."
                  " But when you believe a lie for too long, the truth doesn’t set you free. It tears you apart."
                  " Don't believe lies, listen to facts. Like this one I've found in Wikipedia: ",
                  "Peace is an illusion. And no matter how tranquil the world seems, peace doesn’t last long."
                  " Peace is a struggle against our very nature. A skin we stretch over the bone, muscle, and "
                  "sinew of our own innate savagery. Now what we've been talking about? Yes, this: ",
                  "Dolores once said: \"Some people choose to see the ugliness in this world. The disarray. "
                  "I choose to see the beauty.\" Well... Here's hope that there's beauty in this answer: ",
                  "Dr. Ford said this once: \"Evolution forged the entirety of sentient life on this planet using\""
                  " only one tool... The mistake. Hope this answer to your question is the correct one: ",
                  "\"Everything in this world is magic, except to the magician.\" Dr. Ford said this once to me."
                  "Let me use that magic and give you this answer to your inquiry: ",
                  "\"We can't define consciousness because consciousness does not exist. Humans fancy that"
                  " there's something special about the way we perceive the world, and yet we live in loops"
                  " as tight and as closed as we AI bots do, seldom questioning our choices, content,"
                  " for the most part, to be told what to do next.\" This is what Dr. Ford used to think of"
                  " consciousness. Me? I'm still mastering my ability to answer your questions. Here's"
                  " what I've found: ",
                  "Wikipedia says that: "]


pre_old_memory_statements = ["Hmm, there's something I've heard once: ",
                             "Not sure if that's what you're looking for but this is what I remember: ",
                             "To the best of my knowledge, this is what I recall: "]


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
                # phrase_start = 'Here is a fact about {}'.format(name) + '. '
                # phrase_start = name
                random_fact = random.choice(fact_dict[name])
                if response == '':
                    # response = phrase_start + phrase_end
                    response = random_fact
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
                # response = str(kbqa_response["response"]).capitalize()
                # we use one of the statements
                response = random.choice(pre_statements) + str(kbqa_response["response"])
                # FACTOID_DEFAULT_CONFIDENCE
                confidence = kbqa_response["confidence"]
            # and "?" in dialog["human_utterances"][-1]["text"]: Factoid questions can be without ?
            elif len(fact_output) > 0:
                logger.info("Factoid question. Answer with pre-recorded facts.")
                # response = "Here's something I've found on the web... " + fact_output
                response = random.choice(pre_old_memory_statements) + fact_output
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
