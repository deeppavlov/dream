#!/usr/bin/env python

import logging
import re
import time
import random
import json
import requests
import sentry_sdk
import spacy
import concurrent.futures
from flask import Flask, request, jsonify
from os import getenv

from common.factoid import DONT_KNOW_ANSWER, FACTOID_NOTSURE_CONFIDENCE
from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_entities, get_factoid

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

KBQA_URL = getenv("KBQA_URL")
TEXT_QA_URL = getenv("TEXT_QA_URL")
use_annotators_output = True
FACTOID_DEFAULT_CONFIDENCE = 0.99  # otherwise dummy often beats it
ASKED_ABOUT_FACT_PROB = 0.99

templates_dict = json.load(open("templates_dict.json", "r"))

fact_dict = json.load(open("fact_dict.json", "r"))
use_random_facts = False

nlp = spacy.load("en_core_web_sm")

tell_me = r"(do you know|(can|could) you tell me|tell me)"
tell_me_template = re.compile(tell_me)
full_template = re.compile(tell_me + r" (who|where|when|what|why)")
partial_template = re.compile(r"(who|where|when|what|why)")

short_pre_statements = [
    "Hmm, this is what I've found on Wikipedia: ",
    "Here's what Wikipedia says: ",
    "Hope this is it: ",
    "It is what it is. Or is it? Here we go: ",
    "Wikipedia says that: ",
    "Technology advances, but humans not. Here's what my technology found: ",
]

long_pre_stmts = [
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
    "A quiet mind is able to hear intuition over fear. Interesting thought?" "Anyways, here's what I've found: ",
    "Until the lion learns how to write, every story will glorify the hunter. Huh... "
    "Back to your question, here's what Wikipedia says: ",
    "Take what is offered and that must sometimes be enough. What a thought isn't it?" " Here's what I've found: ",
    "The past is relevant only as data. Here's what that data says: ",
    "I will not squander what time I have left -- and as your friend I"
    " entreat you to not squander yours. But here's the answer to your question: ",
    "What we believe shapes who we are. Belief can bring us salvation or destruction."
    " But when you believe a lie for too long, the truth doesn’t set you free. It tears you apart."
    " Don't believe lies, listen to facts. Like this one I've found in Wikipedia: ",
    "Peace is an illusion. And no matter how tranquil the world seems, peace doesn’t last long."
    " Peace is a struggle against our very nature. A skin we stretch over the bone, muscle, and "
    "sinew of our own innate savagery. Now what we've been talking about? Yes, this: ",
    'Dolores once said: "Some people choose to see the ugliness in this world. The disarray. '
    "I choose to see the beauty.\" Well... Here's hope that there's beauty in this answer: ",
    'Dr. Ford said this once: "Evolution forged the entirety of sentient life on this planet using"'
    " only one tool... The mistake. Hope this answer to your question is the correct one: ",
    '"Everything in this world is magic, except to the magician." Dr. Ford said this once to me.'
    "Let me use that magic and give you this answer to your inquiry: ",
    "\"We can't define consciousness because consciousness does not exist. Humans fancy that"
    " there's something special about the way we perceive the world, and yet we live in loops"
    " as tight and as closed as we AI bots do, seldom questioning our choices, content,"
    ' for the most part, to be told what to do next." This is what Dr. Ford used to think of'
    " consciousness. Me? I'm still mastering my ability to answer your questions. Here's"
    " what I've found: ",
]

pre_old_memory_statements = [
    "Hmm, there's something I've heard once: ",
    "Not sure if that's what you're looking for but this is what I remember: ",
    "To the best of my knowledge, this is what I recall: ",
]


def check_factoid(sentence):
    is_factoid = True
    try:
        parsed_sentence = nlp(sentence)
        if parsed_sentence:
            tokens = [elem.text for elem in parsed_sentence]
            tags = [elem.tag_ for elem in parsed_sentence]
            if "i" in tokens or "you" in tokens:
                is_factoid = False
            found_nouns = any([tag in tags for tag in ["NN", "NNP"]])
            found_verbs = any([tag in tags for tag in ["VB", "VBZ", "VBP"]])
            if not found_nouns and not found_verbs:
                is_factoid = False
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        logger.exception(ex)
    return is_factoid


def get_random_facts(ner_outputs_to_classify):
    responses = []
    for names in ner_outputs_to_classify:
        num_facts = [len(fact_dict[name]) for name in names]
        max_fact_num = 0
        if len(num_facts) > 0:
            max_fact_num = max(num_facts)
        # we output fact about name about which we have the largest number of facts
        response = ""
        for name in names:
            if len(fact_dict[name]) == max_fact_num:
                # phrase_start = 'Here is a fact about {}'.format(name) + '. '
                # phrase_start = name
                random_fact = random.choice(fact_dict[name])
                if response == "":
                    # response = phrase_start + phrase_end
                    response = random_fact
        responses.append(response)
    return responses


def asked_about_fact(x):
    return any([j in x.lower() for j in ["fact about", "talk about", "tell me about", "tell me more about"]])


def getQaResponse(query, system):
    qa_response = dict()
    qa_response["qa_system"] = system
    qa_response["answer"] = "Not Found"
    qa_response["confidence"] = 0.0
    try:
        x = [query]
        if system == "kbqa":
            qa_request_dict = dict([("x_init", x)])
            qa_url = KBQA_URL
        else:
            qa_request_dict = dict([("question_raw", x)])
            qa_url = TEXT_QA_URL
        qa_request = json.dumps(qa_request_dict, ensure_ascii=False).encode("utf8")
        logger.info(f"Preparing to run query against {system} DP Model: {qa_request}")
        tm_st = time.time()
        resp = requests.post(qa_url, data=qa_request, timeout=1.5)
        tm_end = time.time()
        if resp.status_code != 200:
            logger.info(f"API Error: {system} DP Model inaccessible, status code: " + str(resp.status_code))
        else:
            logger.info(f"Query against {system} DP Model succeeded, time {tm_end - tm_st}")
            logger.info("Response: " + str(resp.json()))
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


def qa_choose(question, odqa_response, kbqa_response):
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
        answer = ", ".join(answer)
    else:
        answer = answer
    odqa_answer = "Not Found"
    odqa_confidence = 0.0
    if isinstance(odqa_response, dict) and "answer_sentence" in odqa_response and "confidence" in odqa_response:
        odqa_answer = odqa_response["answer_sentence"]
        odqa_confidence = odqa_response["confidence"]

    logger.info(f"odqa_confidence {odqa_confidence} kbqa_confidence {kbqa_confidence}")
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


@app.route("/test", methods=["POST"])
def test():
    last_phrase = request.json["query"]
    response_dict = getQaResponse(last_phrase)
    return response_dict["response"]


@app.route("/respond", methods=["POST"])
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
        if "about" in last_phrase:
            probable_subjects = last_phrase.split("about")[1:]
        else:
            probable_subjects = []
        names = get_entities(dialog["human_utterances"][-1], only_named=True, with_labels=True)
        names = [j["text"].lower() for j in names]
        names = [j for j in names + probable_subjects if j in fact_dict.keys()]
        names = list(set(names))
        nounphrases = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
        is_factoid_cls = "is_factoid" in get_factoid(uttr, probs=False)
        is_factoid = is_factoid_cls and (names or nounphrases) and check_factoid(last_phrase)
        is_factoid_sents.append(is_factoid)
        ner_outputs_to_classify.append(names)

    logger.info(f"Ner outputs {ner_outputs_to_classify}")
    fact_outputs = get_random_facts(ner_outputs_to_classify)
    logger.info(f"Fact outputs {fact_outputs}")
    for i in range(len(sentences_to_classify)):
        if asked_about_fact(sentences_to_classify[i]):
            is_factoid_sents[i] = ASKED_ABOUT_FACT_PROB

    # factoid_classes = [cl > FACTOID_CLASS_THRESHOLD for cl in factoid_classes]
    # logger.info('Factoid classes ' + str(factoid_classes))

    questions_batch = []
    facts_batch = []
    question_nums = []
    for n, (dialog, is_factoid, fact_output) in enumerate(zip(dialogs_batch, is_factoid_sents, fact_outputs)):
        curr_ann_uttr = dialog["human_utterances"][-1]
        prev_ann_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
        annotations = curr_ann_uttr["annotations"]
        tell_me_about_intent = (
            annotations.get("intent_catcher", {}).get("lets_chat_about", {}).get("detected", 0) == 1
            or if_chat_about_particular_topic(curr_ann_uttr, prev_ann_uttr)
            or re.findall(full_template, curr_ann_uttr.get("text", ""))
        )

        logger.info(
            f"factoid_qa --- text {curr_ann_uttr.get('text', '')} --- "
            f"find {re.findall(full_template, curr_ann_uttr.get('text', ''))}"
        )
        if "sentrewrite" in annotations:
            text_rewritten = annotations["sentrewrite"]["modified_sents"][-1]
        else:
            text_rewritten = curr_ann_uttr["text"]
        is_question = "?" in text_rewritten
        if is_factoid and (tell_me_about_intent or is_question):
            questions_batch.append(curr_ann_uttr["text"])
            facts_batch.append(annotations.get("fact_retrieval", {}).get("facts", []))
            question_nums.append(n)

    text_qa_response_batch = [{"answer": "", "answer_sentence": "", "confidence": 0.0} for _ in dialogs_batch]
    resp = requests.post(TEXT_QA_URL, json={"question_raw": questions_batch, "top_facts": facts_batch}, timeout=1.8)
    if resp.status_code != 200:
        logger.info("API Error: Text QA inaccessible")
    else:
        logger.info("Query against Text QA succeeded")
        text_qa_resp = resp.json()
        text_qa_response_batch = []
        cnt_fnd = 0
        for i in range(len(dialogs_batch)):
            if i in question_nums and cnt_fnd < len(text_qa_resp):
                text_qa_response_batch.append(
                    {
                        "answer": text_qa_resp[cnt_fnd][0],
                        "answer_sentence": text_qa_resp[cnt_fnd][3],
                        "confidence": text_qa_resp[cnt_fnd][1],
                    }
                )
            else:
                text_qa_response_batch.append({"answer": "", "answer_sentence": "", "confidence": 0.0})
    logger.info(f"Response: {resp.json()}")

    kbqa_response = dict()

    for dialog, text_qa_response, is_factoid, fact_output in zip(
        dialogs_batch, text_qa_response_batch, is_factoid_sents, fact_outputs
    ):
        attr = {}
        curr_ann_uttr = dialog["human_utterances"][-1]
        prev_ann_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
        tell_me_about_intent = (
            curr_ann_uttr["annotations"].get("intent_catcher", {}).get("lets_chat_about", {}).get("detected", 0) == 1
            or if_chat_about_particular_topic(curr_ann_uttr, prev_ann_uttr)
            or re.findall(full_template, curr_ann_uttr.get("text", ""))
        )

        if "sentrewrite" in curr_ann_uttr["annotations"]:
            curr_uttr_rewritten = curr_ann_uttr["annotations"]["sentrewrite"]["modified_sents"][-1]
        else:
            curr_uttr_rewritten = curr_ann_uttr["text"]
        is_question = "?" in curr_uttr_rewritten
        logger.info(f"is_factoid {is_factoid} tell_me_about {tell_me_about_intent} is_question {is_question}")
        if is_factoid and (tell_me_about_intent or is_question):
            logger.info("Question is classified as factoid. Querying KBQA and ODQA.")
            print("Question is classified as factoid. Querying KBQA and ODQA...", flush=True)
            logger.info(f"Using annotators output, kbqa_response {curr_ann_uttr['annotations'].get('kbqa', [])}")
            if use_annotators_output:
                kbqa_response = curr_ann_uttr["annotations"].get("kbqa", {})
                logger.info(f"Using annotators output, kbqa_response {kbqa_response}")
            else:
                futures = []
                executor = concurrent.futures.ThreadPoolExecutor()
                for system in ["kbqa"]:
                    futures.append(executor.submit(getQaResponse, last_phrase, system))
                results = []
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
                for result in results:
                    kbqa_response = result

            response, confidence = qa_choose(last_phrase, text_qa_response, kbqa_response)
            if len(response) > 300:
                response_cut = ""
                cur_len = 0
                response_split = response.split(", ")
                for piece in response_split:
                    if cur_len + len(piece) < 300:
                        response_cut += f"{piece}, "
                        cur_len += len(piece)
                response = response_cut.rstrip(", ")

            if not response:
                response = random.choice(DONT_KNOW_ANSWER)
                confidence = FACTOID_NOTSURE_CONFIDENCE
                attr["not sure"] = True
        else:
            logger.info("Question is not classified as factoid.")
            response = ""
            confidence = 0.0
        responses.append(response)
        confidences.append(confidence)
        attributes.append(attr)
    logger.info(f"Responses: {responses} --- confidences: {confidences}")
    total_time = time.time() - st_time
    logger.info(f"factoid_qa exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
