#!/usr/bin/env python

import logging
import string
from time import time
import random
import re

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.universal_templates import opinion_request_question, fact_about_replace, FACT_ABOUT_TEMPLATES
from common.utils import get_topics, get_intents, get_entities, is_special_factoid_question, COBOTQA_EXTRA_WORDS
from common.factoid import FACT_REGEXP, WHAT_REGEXP


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

N_FACTS_TO_CHOSE = 1
ASK_QUESTION_PROB = 0.5


def remove_punct_and_articles(s, lowecase=True):
    articles = ['a', 'an', 'the']
    if lowecase:
        s = s.lower()
    no_punct = ''.join([c for c in s if c not in string.punctuation])
    no_articles = ' '.join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
    return no_articles


lemmatizer = WordNetLemmatizer()


def get_common_words(a: str, b: str, lemmatize: bool = True) -> set:
    """Returns set of common words (lemmatized) in strings a and b
    Args:
        a (str): string a
        b (str): string b
        lemmatize (bool, optional): Lemmatize each word. Defaults to True.
    Returns:
        set: common words in strings a and b
    """
    tokens_a = set(word_tokenize(remove_punct_and_articles(a).lower()))
    tokens_b = set(word_tokenize(remove_punct_and_articles(b).lower()))
    if lemmatize:
        tokens_a = {lemmatizer.lemmatize(t) for t in tokens_a}
        tokens_b = {lemmatizer.lemmatize(t) for t in tokens_b}
    return tokens_a & tokens_b


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    dialogs = request.json['dialogs']
    final_responses = []
    final_confidences = []

    for i, dialog in enumerate(dialogs):
        curr_uttr = dialog["human_utterances"][-1]
        curr_nounphrases = get_entities(curr_uttr, only_named=False, with_labels=False)
        cobotqa_annotations = curr_uttr.get("annotations", {}).get("cobotqa_annotator", {})
        direct_response = cobotqa_annotations.get("response", "")
        facts = cobotqa_annotations.get("facts", [])
        # each fact is a dict: `{"entity": "politics", "fact": "Politics is a ..."}`
        all_intents = set(get_intents(curr_uttr, which="cobot_dialogact_intents"))
        opinion_request_detected = "opinion_request" in get_intents(curr_uttr, which="intent_catcher", probs=False)
        sensitive_topics = {"Politics", "Religion", "Sex_Profanity", "Inappropriate_Content"}
        # `General_ChatIntent` sensitive in case when `?` in reply
        sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"}
        all_topics = set(get_topics(curr_uttr, which='all'))
        sensitive_topics_detected = sensitive_topics & all_topics
        sensitive_dialogacts_detected = "?" in curr_uttr['text'] and (sensitive_dialogacts & all_intents)
        blist_topics_detected = curr_uttr.get('annotations', {}).get('blacklisted_words', {}).get(
            "restricted_topics", False)
        opinion_request_detected = ("Opinion_RequestIntent" in all_intents) or opinion_request_detected
        sensitive_case_request = sensitive_topics_detected and sensitive_dialogacts_detected
        sensitive_case_request = sensitive_case_request or opinion_request_detected or blist_topics_detected

        hypotheses_subjects = []
        hypotheses = []
        if direct_response:
            hypotheses.append(direct_response)
            hypotheses_subjects.append(None)
        for fact in facts:
            hypotheses.append(fact["fact"])
            hypotheses_subjects.append(fact["entity"])

        curr_responses = []
        curr_confidences = []
        for response, subject in zip(hypotheses, hypotheses_subjects):
            if len(response) > 0:
                sentences = sent_tokenize(response.replace(".,", "."))
                full_resp = response
                response = " ".join(sentences[:2])
                if len(sentences[0]) < 100 and "fact about" in sentences[0]:
                    # this is a fact from cobotqa itself
                    # cobotqa answer `Here's a fact about Hollywood. Hollywood blablabla.`
                    subjects = re.findall(r"fact about (.+)\.", sentences[0].lower())
                    response = fact_about_replace() + " " + " ".join(sentences[1:2])

                    if len(subjects) > 0 and random.random() < ASK_QUESTION_PROB:
                        # randomly append question about found NP
                        response += " " + opinion_request_question()

                    if len(subjects) > 0 and subject and len(get_common_words(subjects[0], subject)) > 0:
                        # in case if subject in response is same as in user question
                        confidence = 0.7
                    else:
                        confidence = 0.3
                elif subject is not None and len(subject) > 0:
                    response = " ".join(sentences[:1])

                    if random.random() < ASK_QUESTION_PROB:
                        # randomly append question about requested fact
                        response += " " + opinion_request_question()

                    if len(get_common_words(subject, response)) > 0:
                        # in case if requested subject is in response
                        confidence = 0.7
                    else:
                        confidence = 0.3
                elif any(substr in full_resp for substr in
                         ["Here's something I found", "Here's what I found", "According to ",
                          "This might answer your question"]):
                    confidence = 0.7
                elif "is usually defined as" in full_resp:
                    confidence = 0.3
                elif len(full_resp.split()) > 10 and any([noun.lower() in full_resp.lower()
                                                          for noun in curr_nounphrases]):
                    confidence = 0.7
                else:
                    confidence = 0.95

                bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
                act_skill = bot_uttr.get("active_skill", "")
                if confidence == 0.7 and act_skill in ["greeting_skill", "dff_friendship_skill"] and \
                        "?" not in curr_uttr["text"]:
                    confidence = 0.9

                if sensitive_case_request and subject is not None:
                    if any([templ in response for templ in FACT_ABOUT_TEMPLATES]):
                        response = f"I don't have an opinion on that but... {response}"
                    else:
                        response = f"I don't have an opinion on that but I've heard that {response}"
                if (
                    any([FACT_REGEXP.search(curr_uttr["text"]), WHAT_REGEXP.search(curr_uttr["text"])])
                    and confidence >= 0.7
                ):
                    # Factual question - must increase confidence
                    confidence = 1
            else:
                confidence = 0.00
                response = ""

            if is_special_factoid_question(curr_uttr) and confidence > 0 and subject is None:
                # for special factoid questions, original cobotqa response is found, assign conf to 1.0
                _common = get_common_words(response.lower(), curr_uttr["text"].lower())
                if _common and any([len(word) > 3 for word in _common]):
                    confidence = 1.0

            response = COBOTQA_EXTRA_WORDS.sub("", response).strip()
            curr_responses.append(response)
            curr_confidences.append(confidence)
        final_responses.append(curr_responses)
        final_confidences.append(curr_confidences)

    total_time = time() - st_time
    logger.info(f'cobotqa exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
