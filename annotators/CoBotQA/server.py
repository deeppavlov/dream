#!/usr/bin/env python

import logging
import os
import re
import string
from time import time

import en_core_web_sm
import inflect
import numpy as np
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk
from cobotqa_service import send_cobotqa, TRAVEL_FACTS, FOOD_FACTS, ANIMALS_FACTS

from common.travel import TOO_SIMPLE_TRAVEL_FACTS
from common.utils import get_entities, COBOTQA_EXTRA_WORDS


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

nlp = en_core_web_sm.load()
inflect_engine = inflect.engine()

N_FACTS_TO_CHOSE = 1
ASK_QUESTION_PROB = 0.5

ASYNC_SIZE = int(os.environ.get("ASYNC_SIZE", 6))
COBOT_API_KEY = os.environ.get("COBOT_API_KEY")
COBOT_QA_SERVICE_URL = os.environ.get("COBOT_QA_SERVICE_URL")

if COBOT_API_KEY is None:
    raise RuntimeError("COBOT_API_KEY environment variable is not set")
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError("COBOT_QA_SERVICE_URL environment variable is not set")

headers = {"Content-Type": "application/json;charset=utf-8", "x-api-key": f"{COBOT_API_KEY}"}

with open("./google-english-no-swears.txt", "r") as f:
    UNIGRAMS = set(f.read().splitlines())

with open("./common_user_phrases.txt", "r") as f:
    COMMON_USER_PHRASES = set(f.read().splitlines())


def remove_punct_and_articles(s, lowecase=True):
    articles = ["a", "an", "the"]
    if lowecase:
        s = s.lower()
    no_punct = "".join([c for c in s if c not in string.punctuation])
    no_articles = " ".join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
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


def lemmatize_substr(text):
    lemm_text = ""
    if text:
        pr_text = nlp(text)
        processed_tokens = []
        for token in pr_text:
            if token.tag_ in ["NNS", "NNP"] and inflect_engine.singular_noun(token.text):
                processed_tokens.append(inflect_engine.singular_noun(token.text))
            else:
                processed_tokens.append(token.text)
        lemm_text = " ".join(processed_tokens)
    return lemm_text


bad_answers = [
    "You can now put your wizarding world knowledge to the test with the official Harry Potter "
    'quiz. Just say: "Play the Harry Potter Quiz."',
    "I can provide information, music, news, weather, and more.",
    'For the latest in politics and other news, try asking "Alexa, play my Flash Briefing."',
    "I don't have an opinion on that.",
    "[GetMusicDetailsIntent:Music]",
    "Thank you!",
    "Thanks!",
    "That's really nice, thanks.",
    "That's nice of you to say.",
    "Kazuo Ishiguro, Gretchen Mol, Benjamin Wadsworth, Johann Mühlegg, Ramkumar Ramanathan" " and others.",
    "I didn't catch that. Please say that again.",
    "Okay.",
]
bad_subanswers = [
    "let's talk about",
    "i have lots of",
    "world of warcraft",
    " wow ",
    " ok is",
    "coolness is ",
    "about nice",
    '"let\'s talk" is a 2002 drama',
    "visit amazon.com/",
    "alexa, play my flash briefing.",
    "amazon alexa",
    "past tense",
    "plural form",
    "singular form",
    "present tense",
    "future tense",
    "bob cut",
    "movie theater",
    "alexa app",
    "more news",
    "be here when you need me",
    "the weeknd",
    "faktas",
    "fact about amazing",
    "also called movie or motion picture",
    "known as eugen warming",
    "select a chat program that fits your needs",
    "is usually defined as a humorous anecdote or remark intended to provoke laughter",
    "joke is a display of humour in which words are used within a specific",
    "didn't catch that",
    "say that again",
    "try again",
    "really nice to meet you too",
    "like to learn about how I can help",
    "sorry",
    "i don't under",
    "ask me whatever you like",
    "i don’t know that",
    "initialism for laughing out loud",
    "gamelistintent",
    "listintent",
    "try asking",
    "missed part",
    "try saying",
    " hey is a ",
    "didn't hear that",
    "try that again",
]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time()
    dialogs = request.json["dialogs"]
    responses = []

    questions = []
    dialog_ids = []
    subjects = []
    for i, dialog in enumerate(dialogs):
        curr_uttr = dialog["human_utterances"][-1]
        curr_uttr_rewritten = curr_uttr["annotations"]["sentrewrite"]["modified_sents"][-1]
        curr_uttr_clean = remove_punct_and_articles(curr_uttr_rewritten)
        if curr_uttr_clean in COMMON_USER_PHRASES:
            # do not add any fact about ... and
            # replace human utterance by special string
            # cobotqa will respond with ''
            questions.append(f"[common_phrase_replaced: {curr_uttr_clean}]")
            dialog_ids += [i]
            subjects.append(None)
            continue
        # fix to question what is fact, cobotqa gives random fact on such question
        what_is_fact = "what is fact"
        if remove_punct_and_articles(curr_uttr_rewritten)[-len(what_is_fact) :] == what_is_fact:
            curr_uttr_rewritten = "definition of fact"
        questions.append(curr_uttr_rewritten)
        dialog_ids += [i]
        subjects.append(None)  # to separate facts about entities from normal responses by Cobotqa

        facts_questions = []
        facts_dialog_ids = []
        fact_entities = []

        entities = []
        for _ in range(N_FACTS_TO_CHOSE):
            for ent in get_entities(curr_uttr, only_named=True, with_labels=True):
                if ent["text"].lower() not in UNIGRAMS and not (
                    ent["text"].lower() == "alexa" and curr_uttr["text"].lower()[:5] == "alexa"
                ):
                    entities.append(ent["text"].lower())
                    facts_questions.append("Fact about {}".format(ent["text"]))
                    facts_dialog_ids += [i]
                    fact_entities.append(ent["text"])
            if len(entities) == 0:
                for ent in get_entities(curr_uttr, only_named=False, with_labels=False):
                    if ent.lower() not in UNIGRAMS:
                        if ent in entities + ["I", "i"]:
                            pass
                        else:
                            facts_questions.append("Fact about {}".format(ent))
                            facts_dialog_ids += [i]
                            fact_entities.append(ent)

        if len(facts_questions) > 6:
            ids = np.random.choice(np.arange(len(facts_questions)), size=6)
            facts_questions = np.array(facts_questions)[ids].tolist()
            facts_dialog_ids = np.array(facts_dialog_ids)[ids].tolist()
            fact_entities = np.array(fact_entities)[ids].tolist()

        questions.extend(facts_questions)
        dialog_ids.extend(facts_dialog_ids)
        subjects.extend(fact_entities)

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
        fun_fact_q = "Fun fact about"
        if (
            fun_fact_q in questions[i]
            and " fun" not in questions[i][len(fun_fact_q) :].lower()
            and "Fun is defined by the Oxford English Dictionary as" in response
        ):
            response = ""

        if len(response) > 0 and "skill://amzn1" not in response:
            sentences = sent_tokenize(response.replace(".,", "."))
            full_resp = response
            response = " ".join(sentences)
            if full_resp in bad_answers or any(
                [bad_substr.lower() in full_resp.lower() for bad_substr in bad_subanswers]
            ):
                response = ""
        else:
            response = ""
        responses += [response]

    dialog_ids = np.array(dialog_ids)
    responses = np.array(responses)
    questions = np.array(questions)
    subjects = np.array(subjects)

    final_responses = []
    for i, dialog in enumerate(dialogs):
        resp_cands = list(responses[dialog_ids == i])
        resp_questions = list(questions[dialog_ids == i])
        resp_subjects = list(subjects[dialog_ids == i])

        curr_resp = {"facts": []}
        for resp_cand, resp_subj, question in zip(resp_cands, resp_subjects, resp_questions):
            if resp_subj is None:
                # resp_cand can be ""
                curr_resp["response"] = re.sub(COBOTQA_EXTRA_WORDS, "", resp_cand).strip()
            elif resp_cand:
                curr_resp["facts"].append({"entity": resp_subj, "fact": resp_cand})
            if resp_subj and resp_subj.lower() in TRAVEL_FACTS:
                for fact in TRAVEL_FACTS[resp_subj.lower()]:
                    fact.replace("%", " percent")
                    fact.replace("ºC", " Celsius")
                    fact.replace("ºF", " Fahrenheit")
                    fact.replace("°C", " Celsius")
                    fact.replace("°F", " Fahrenheit")
                    is_not_too_simple = not TOO_SIMPLE_TRAVEL_FACTS.search(fact)
                    if {"entity": resp_subj, "fact": fact} not in curr_resp["facts"] and is_not_too_simple:
                        curr_resp["facts"].append({"entity": resp_subj, "fact": fact})
            if resp_subj and resp_subj.lower() in FOOD_FACTS:
                for fact in FOOD_FACTS[resp_subj.lower()]:
                    if {"entity": resp_subj, "fact": fact} not in curr_resp["facts"]:
                        curr_resp["facts"].append({"entity": resp_subj, "fact": fact})
            if resp_subj:
                if resp_subj.lower() in ANIMALS_FACTS:
                    for fact in ANIMALS_FACTS[resp_subj.lower()]:
                        if {"entity": resp_subj, "fact": fact} not in curr_resp["facts"]:
                            curr_resp["facts"].append({"entity": resp_subj, "fact": fact})
                lemm_resp_subj = lemmatize_substr(resp_subj.lower())
                logger.info(f"cobot_qa, lemm_resp_subj {lemm_resp_subj}")
                if lemm_resp_subj in ANIMALS_FACTS:
                    for fact in ANIMALS_FACTS[lemm_resp_subj]:
                        if {"entity": lemm_resp_subj, "fact": fact} not in curr_resp["facts"]:
                            curr_resp["facts"].append({"entity": lemm_resp_subj, "fact": fact})

        # store only 5 facts maximum
        curr_resp["facts"] = (
            list(np.random.choice(curr_resp["facts"], size=5)) if len(curr_resp["facts"]) > 5 else curr_resp["facts"]
        )
        for curr_resp_item in curr_resp["facts"]:
            curr_resp_item["fact"] = re.sub(COBOTQA_EXTRA_WORDS, "", curr_resp_item["fact"]).strip()

        final_responses.append(curr_resp)
    total_time = time() - st_time
    logger.info(f"cobotqa-annotator exec time: {total_time:.3f}s")
    return jsonify(final_responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
