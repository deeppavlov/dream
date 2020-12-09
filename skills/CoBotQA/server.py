#!/usr/bin/env python

import logging
import os
import string
from time import time
import random
import re

import numpy as np
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk
from cobotqa_service import send_cobotqa

from common.universal_templates import opinion_request_question, fact_about_replace, FACT_ABOUT_TEMPLATES


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

N_FACTS_TO_CHOSE = 3
ASK_QUESTION_PROB = 0.5

ASYNC_SIZE = int(os.environ.get('ASYNC_SIZE', 6))
COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_QA_SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError('COBOT_QA_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

with open("./google-english-no-swears.txt", "r") as f:
    UNIGRAMS = set(f.read().splitlines())

with open("./common_user_phrases.txt", "r") as f:
    COMMON_USER_PHRASES = set(f.read().splitlines())


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
    responses = []
    confidences = []

    questions = []
    dialog_ids = []
    for i, dialog in enumerate(dialogs):
        curr_uttr = dialog["human_utterances"][-1]
        curr_uttr_rewritten = curr_uttr["annotations"]["sentrewrite"]["modified_sents"][-1]
        curr_uttr_clean = remove_punct_and_articles(curr_uttr_rewritten)
        if curr_uttr_clean in COMMON_USER_PHRASES:
            # do not add any fact about ... and
            # replace human utterance by special string
            # cobotqa will respond with ''
            questions.append(f'[common_phrase_replaced: {curr_uttr_clean}]')
            dialog_ids += [i]
            continue
        # fix to question what is fact, cobotqa gives random fact on such question
        what_is_fact = 'what is fact'
        if remove_punct_and_articles(curr_uttr_rewritten)[-len(what_is_fact):] == what_is_fact:
            curr_uttr_rewritten = 'definition of fact'
        questions.append(curr_uttr_rewritten)
        dialog_ids += [i]

        facts_questions = []
        facts_dialog_ids = []
        entities = []
        attit = curr_uttr["annotations"].get("sentiment_classification", {}).get("text", [""])[0]
        for _ in range(N_FACTS_TO_CHOSE):
            for ent in curr_uttr["annotations"]["ner"]:
                if not ent:
                    continue
                ent = ent[0]
                if ent["text"].lower() not in UNIGRAMS and not (
                        ent["text"].lower() == "alexa" and curr_uttr["text"].lower()[:5] == "alexa"):
                    if attit in ["neutral", "positive"]:
                        entities.append(ent["text"].lower())
                        facts_questions.append("Fun fact about {}".format(ent["text"]))
                        facts_dialog_ids += [i]
                    else:
                        entities.append(ent["text"].lower())
                        facts_questions.append("Fact about {}".format(ent["text"]))
                        facts_dialog_ids += [i]
            if len(entities) == 0:
                for ent in curr_uttr["annotations"]["cobot_nounphrases"]:
                    if ent.lower() not in UNIGRAMS:
                        if ent in entities + ["I", 'i']:
                            pass
                        else:
                            facts_questions.append("Fact about {}".format(ent))
                            facts_dialog_ids += [i]

        if len(facts_questions) > 6:
            ids = np.random.choice(np.arange(len(facts_questions)), size=6)
            facts_questions = np.array(facts_questions)[ids].tolist()
            facts_dialog_ids = np.array(facts_dialog_ids)[ids].tolist()

        questions.extend(facts_questions)
        dialog_ids.extend(facts_dialog_ids)

    executor = ThreadPoolExecutor(max_workers=ASYNC_SIZE)
    responses_for_this_dialog = []
    curr_dialog_id = dialog_ids[0]
    for i, response in enumerate(executor.map(send_cobotqa, questions)):
        if curr_dialog_id != dialog_ids[i]:
            curr_dialog_id = dialog_ids[i]
            responses_for_this_dialog = []

        if response in responses_for_this_dialog:
            response = ""
        else:
            responses_for_this_dialog.append(response)

        logger.info("Question: {}".format(questions[i]))
        logger.info("Response: {}".format(response))

        # fix for cases when fact is about fun, but fun is not in entities
        fun_fact_q = 'Fun fact about'
        if fun_fact_q in questions[i] and ' fun' not in questions[i][len(fun_fact_q):].lower() \
                and 'Fun is defined by the Oxford English Dictionary as' in response:
            response = ''

        bad_answers = ['You can now put your wizarding world knowledge to the test with the official Harry Potter '
                       'quiz. Just say: "Play the Harry Potter Quiz."',
                       "I can provide information, music, news, weather, and more.",
                       'For the latest in politics and other news, try asking "Alexa, play my Flash Briefing."',
                       "I don't have an opinion on that.", "[GetMusicDetailsIntent:Music]",
                       "Thank you!",
                       "Thanks!",
                       "That's really nice, thanks.",
                       "That's nice of you to say.",
                       "Kazuo Ishiguro, Gretchen Mol, Benjamin Wadsworth, Johann Mühlegg, Ramkumar Ramanathan"
                       " and others.",
                       ]
        bad_subanswers = ["let's talk about", "i have lots of", "world of warcraft",
                          " wow ", " ok is", "coolness is ", "about nice",
                          "\"let's talk\" is a 2002 drama", "visit amazon.com/",
                          'alexa, play my flash briefing.', "amazon alexa",
                          "past tense", "plural form", "singular form", "present tense", "future tense", "bob cut",
                          "movie theater", "alexa app", "more news", "be here when you need me", "the weeknd",
                          "faktas", "fact about amazing", "also called movie or motion picture",
                          "known as eugen warming", "select a chat program that fits your needs",
                          "is usually defined as a humorous anecdote or remark intended to provoke laughter",
                          "joke is a display of humour in which words are used within a specific"]

        curr_nounphrases = dialogs[curr_dialog_id]["human_utterances"][-1]["annotations"].get("cobot_nounphrases", [])
        if len(response) > 0 and 'skill://amzn1' not in response:
            sentences = sent_tokenize(response.replace(".,", "."))
            full_resp = response
            response = " ".join(sentences[:2])
            if full_resp in bad_answers or any([bad_substr in full_resp.lower() for bad_substr in bad_subanswers]):
                confidence = 0.
                response = ""
            elif len(sentences[0]) < 100 and "fact about" in sentences[0]:
                # this is a fact from cobotqa itself
                # cobotqa answer `Here's a fact about Hollywood. Hollywood blablabla.`
                subjects = re.findall(r"fact about (.+)\.", sentences[0].lower())
                response = fact_about_replace() + " " + " ".join(sentences[1:2])

                if len(subjects) > 0 and random.random() < ASK_QUESTION_PROB:
                    # randomly append question about found NP
                    response += " " + opinion_request_question()

                if len(subjects) > 0 and len(get_common_words(subjects[0], questions[i])) > 0:
                    # in case if subject in response is same as in user question
                    confidence = 0.7
                else:
                    confidence = 0.3
            elif "fact about" in questions[i].lower():
                response = " ".join(sentences[:1])
                # check this is requested `fact about NP/NE`
                subjects = re.findall(r"fact about (.+)", questions[i].lower())

                if len(subjects) > 0 and random.random() < ASK_QUESTION_PROB:
                    # randomly append question about requested fact
                    response += " " + opinion_request_question()

                if len(subjects) > 0 and len(get_common_words(subjects[0], response)) > 0:
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
            elif len(full_resp.split()) > 10 and any([noun.lower() in full_resp.lower() for noun in curr_nounphrases]):
                confidence = 0.7
            else:
                confidence = 0.95
        else:
            confidence = 0.00
            response = ""

        bot_uttr = dialogs[curr_dialog_id]["bot_utterances"]
        bot_uttr = bot_uttr[-1] if len(bot_uttr) > 0 else {}
        if confidence == 0.7 and bot_uttr.get("active_skill", "") == "greeting_skill" and \
                "?" not in dialogs[curr_dialog_id]["human_utterances"][-1]["text"]:
            confidence = 0.9

        confidences += [confidence]
        responses += [response]

    dialog_ids = np.array(dialog_ids)
    responses = np.array(responses)
    confidences = np.array(confidences)
    final_responses = []
    final_confidences = []

    for i, dialog in enumerate(dialogs):
        resp_cands = list(responses[dialog_ids == i])
        conf_cands = list(confidences[dialog_ids == i])

        annotations = dialog["human_utterances"][-1]["annotations"]
        intents = annotations.get("cobot_dialogact_intents", {}).get("text", [])
        opinion_request_detected = annotations["intent_catcher"].get(
            "opinion_request", {}).get("detected") == 1
        reply = dialog['human_utterances'][-1]['text'].replace("\'", " \'").lower()

        sensitive_topics = {"Politics", "Celebrities", "Religion", "Sex_Profanity", "Sports", "News", "Psychology"}
        # `General_ChatIntent` sensitive in case when `?` in reply
        sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"}
        cobot_topics = set(dialog['human_utterances'][-1]['annotations']['cobot_topics']['text'])
        sensitive_topics_detected = any([t in sensitive_topics for t in cobot_topics])
        sensitive_dialogacts_detected = any([(t in sensitive_dialogacts and "?" in reply) for t in intents])
        blist_topics_detected = dialog['human_utterances'][-1]['annotations']['blacklisted_words']['restricted_topics']

        for j in range(len(resp_cands)):
            if j != 0:
                # facts
                if (("Opinion_RequestIntent" in intents) or opinion_request_detected or blist_topics_detected or (
                        sensitive_topics_detected and sensitive_dialogacts_detected)) and len(resp_cands[j]) > 0:
                    if any([templ in resp_cands[j] for templ in FACT_ABOUT_TEMPLATES]):
                        resp_cands[j] = f"I don't have an opinion on that but... {resp_cands[j]}"
                    else:
                        resp_cands[j] = f"I don't have an opinion on that but I've heard that {resp_cands[j]}"

        final_responses.append(resp_cands)
        final_confidences.append(conf_cands)

    total_time = time() - st_time
    logger.info(f'cobotqa exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
