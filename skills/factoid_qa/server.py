#!/usr/bin/env python

import logging
import re
import time
import random
import json
import requests
import sentry_sdk
import concurrent.futures
from deeppavlov import build_model
from deeppavlov.core.data.utils import simple_download
from flask import Flask, request, jsonify
from os import getenv

from common.factoid import DONT_KNOW_ANSWER, FACTOID_NOTSURE_CONFIDENCE
from common.universal_templates import if_lets_chat_about_topic

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

KBQA_URL = getenv('KBQA_URL')
ODQA_URL = getenv('ODQA_URL')
use_annotators_output = True
FACTOID_DEFAULT_CONFIDENCE = 0.99  # otherwise dummy often beats it
ASKED_ABOUT_FACT_PROB = 0.99
FACTOID_CLASS_THRESHOLD = 0.5
factoid_classifier = build_model(config="./yahoo_convers_vs_info_light.json", download=False)

templates_dict_url = "http://files.deeppavlov.ai/kbqa/templates_dict.json"
simple_download(templates_dict_url, "templates_dict.json")
templates_dict = json.load(open('templates_dict.json', 'r'))

fact_dict = json.load(open("fact_dict.json", 'r'))
use_random_facts = False
decrease_coef = 0.8

tell_me = r"(do you know|(can|could) you tell me|tell me)"
tell_me_template = re.compile(tell_me)
full_template = re.compile(tell_me + r" (who|where|when|what|why)")
partial_template = re.compile(r"(who|where|when|what|why)")

short_pre_statements = ["Hmm, this is what I've found on Wikipedia: ",
                        "Here's what Wikipedia says: ",
                        "Hope this is it: ",
                        "It is what it is. Or is it? Here we go: ",
                        "Wikipedia says that: ",
                        "Technology advances, but humans not. Here's what my technology found: "]

long_pre_stmts = ["It is the impractical things in this tumultuous hellscape"
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
                  " what I've found: "]

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


def getQaResponse(query, system):
    qa_response = dict()
    qa_response["qa_system"] = system
    qa_response["answer"] = "Not Found"
    qa_response["confidence"] = 0.0
    try:
        x = [query]
        if system == "kbqa":
            qa_request_dict = dict([('x_init', x)])
            qa_url = KBQA_URL
        else:
            qa_request_dict = dict([('question_raw', x)])
            qa_url = ODQA_URL
        qa_request = json.dumps(qa_request_dict, ensure_ascii=False).encode('utf8')
        logger.info(f'Preparing to run query against {system} DP Model: ' + str(qa_request))
        tm_st = time.time()
        resp = requests.post(qa_url, data=qa_request, timeout=1.5)
        tm_end = time.time()
        if resp.status_code != 200:
            logger.info(f'API Error: {system} DP Model inaccessible, status code: ' + str(resp.status_code))
        else:
            logger.info(f'Query against {system} DP Model succeeded, time {tm_end - tm_st}')
            logger.info('Response: ' + str(resp.json()))
            if system == "kbqa":
                qa_response["answer"] = resp.json()[0][0][0]
                qa_response["confidence"] = resp.json()[0][0][1]
            else:
                qa_response["answer"] = resp.json()[0][0]
                qa_response["answer_sentence"] = resp.json()[0][3]
                qa_response["confidence"] = resp.json()[0][1]
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        logger.exception(ex)

    return qa_response


def odqa_kbqa_choose(question, odqa_response, kbqa_response):
    answer = ""
    confidence = 0.0
    question_type = ""
    for template, template_type in templates_dict.items():
        if re.findall(template, question, re.IGNORECASE):
            question_type = template_type
            break
    kbqa_answer = "Not Found"
    kbqa_confidence = 0.0
    if isinstance(kbqa_response, dict) and "answer" in kbqa_response and "confidence" in kbqa_response:
        kbqa_answer = kbqa_response["answer"]
        kbqa_confidence = kbqa_response["confidence"]
    if isinstance(answer, list):
        answer = ', '.join(answer)
    else:
        answer = answer
    odqa_answer = "Not Found"
    odqa_confidence = 0.0
    if isinstance(odqa_response, dict) and "answer_sentence" in odqa_response and "confidence" in odqa_response:
        odqa_answer = odqa_response["answer_sentence"]
        odqa_confidence = odqa_response["confidence"]

    logger.info(f'odqa_confidence {odqa_confidence} kbqa_confidence {kbqa_confidence}')
    if question_type == "odqa" and odqa_confidence > 0.9998:
        return odqa_answer, odqa_confidence
    elif question_type == "kbqa" and kbqa_confidence > 0.95:
        return kbqa_answer, kbqa_confidence
    elif odqa_answer and odqa_confidence > kbqa_confidence:
        return odqa_answer, odqa_confidence
    elif kbqa_answer != "Not Found" and kbqa_confidence > odqa_confidence:
        return kbqa_answer, kbqa_confidence
    else:
        return odqa_answer, odqa_confidence

    return answer, confidence


@app.route("/test", methods=['POST'])
def test():
    last_phrase = request.json["query"]
    response_dict = getQaResponse(last_phrase)
    return response_dict["response"]


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    # to clarify, there's just one (1) dialog returned, not multiple
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
        last_phrase = dialog["human_utterances"][-1]["text"]
        if 'about' in last_phrase:
            probable_subjects = last_phrase.split('about')[1:]
        else:
            probable_subjects = []
        names = dialog["human_utterances"][-1]["annotations"]["ner"]
        names = [j[0]['text'].lower() for j in names if len(j) > 0]
        names = [j for j in names + probable_subjects if j in fact_dict.keys()]
        names = list(set(names))
        nounphrases = dialog['human_utterances'][-1]['annotations'].get('cobot_nounphrases', [])
        is_factoid_class = uttr["annotations"].get("factoid_classification", {}).get("factoid", 0)
        is_factoid = is_factoid_class and (names or nounphrases)
        is_factoid_sents.append(is_factoid)
        ner_outputs_to_classify.append(names)

    logger.info('Ner outputs ' + str(ner_outputs_to_classify))
    fact_outputs = get_random_facts(ner_outputs_to_classify)
    logger.info('Fact outputs ' + str(fact_outputs))
    for i in range(len(sentences_to_classify)):
        if asked_about_fact(sentences_to_classify[i]):
            is_factoid_sents[i] = ASKED_ABOUT_FACT_PROB

    # factoid_classes = [cl > FACTOID_CLASS_THRESHOLD for cl in factoid_classes]
    # logger.info('Factoid classes ' + str(factoid_classes))

    kbqa_response = dict()
    odqa_response = dict()

    for dialog, is_factoid, fact_output in zip(dialogs_batch,
                                               is_factoid_sents,
                                               fact_outputs):
        attr = {}
        curr_ann_uttr = dialog["human_utterances"][-1]
        tell_me_about_intent = curr_ann_uttr["annotations"].get("intent_catcher", {}).get("lets_chat_about", {}).get(
            "detected", 0) == 1 or if_lets_chat_about_topic(curr_ann_uttr["text"])
        is_question = "?" in curr_ann_uttr['annotations']['sentrewrite']['modified_sents'][-1]
        if is_factoid and (tell_me_about_intent or is_question):
            logger.info("Question is classified as factoid. Querying KBQA and ODQA.")
            print("Question is classified as factoid. Querying KBQA and ODQA...", flush=True)
            logger.info(
                f"Using annotators output, kbqa_response {curr_ann_uttr['annotations'].get('kbqa', [])} "
                f"odqa_response {curr_ann_uttr['annotations'].get('odqa', [])}")
            if use_annotators_output:
                kbqa_response = curr_ann_uttr["annotations"].get("kbqa", {})
                odqa_response = curr_ann_uttr["annotations"].get("odqa", {})
                logger.info(f"Using annotators output, kbqa_response {kbqa_response} odqa_response {odqa_response}")
            else:
                futures = []
                executor = concurrent.futures.ThreadPoolExecutor()
                for system in ["odqa", "kbqa"]:
                    futures.append(executor.submit(getQaResponse, last_phrase, system))
                results = []
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
                for result in results:
                    if result["qa_system"] == "kbqa":
                        kbqa_response = result
                    else:
                        odqa_response = result

            response, confidence = odqa_kbqa_choose(last_phrase, odqa_response, kbqa_response)
            if not response:
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
    logger.info("Responses " + str(responses))
    total_time = time.time() - st_time
    logger.info(f'factoid_qa exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
