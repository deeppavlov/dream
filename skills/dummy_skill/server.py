#!/usr/bin/env python

import logging
import time
import numpy as np
import re
import json
import pandas as pd

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

np_ignore_list = ["'s", 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
                  "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
                  'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their',
                  'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those',
                  'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                  'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
                  'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before',
                  'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                  'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
                  'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
                  'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
                  "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
                  "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven',
                  "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't",
                  'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
                  'wouldn', "wouldn't", "my name", "your name", "wow", "yeah", "yes", "ya", "cool", "okay", "more",
                  "some more", " a lot", "a bit", "another one", "something else", "something", "anything",
                  "someone", "anyone", "play", "mean", "a lot", "a little", "a little bit"]

donotknow_answers = np.array(["I really do not know what to answer.",
                              "Sorry, probably, I didn't get what you meant.",
                              "I didn't get it. Sorry.",
                              "Let's talk about something else."])

QUESTIONS = pd.read_csv("./questions_with_topics.csv")
FACTS = pd.read_csv("./facts_with_topics.csv")

QUESTIONS_MAP = json.load(open("questions_map.json", "r"))
NP_QUESTIONS = json.load(open("nounphrases_questions_map.json", "r"))
FACTS_MAP = json.load(open("facts_map.json", "r"))
NP_FACTS = json.load(open("nounphrases_facts_map.json", "r"))


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_confidences = []
    final_responses = []
    final_attributes = []

    for dialog in dialogs_batch:
        curr_topics = dialog["utterances"][-1]["annotations"]["cobot_topics"].get("text", [])
        curr_nounphrases = dialog["utterances"][-1]["annotations"]["cobot_nounphrases"]

        if len(curr_topics) == 0:
            curr_topics = ["Phatic"]
        logger.info(f"Found topics: {curr_topics}")
        for i, _ in enumerate(curr_nounphrases):
            for ignore_np in np_ignore_list:
                curr_nounphrases[i] = re.sub(r"\s\s+", " ",
                                             re.sub(r"\b" + ignore_np + r"\b", "",
                                                    curr_nounphrases[i])).strip()
        logger.info(f"Found nounphrases: {curr_nounphrases}")

        cands = []
        confs = []
        attrs = []

        cands += [np.random.choice(donotknow_answers)]
        confs += [0.5]
        attrs += [{"type": "dummy"}]

        questions_same_nps = []
        for i, nphrase in enumerate(curr_nounphrases):
            for q_id in NP_QUESTIONS.get(nphrase, []):
                questions_same_nps += [QUESTIONS_MAP[str(q_id)]]

        if len(questions_same_nps) > 0:
            logger.info("Found special nounphrases for questions. Return question with the same nounphrase.")
            cands += [np.random.choice(questions_same_nps)]
            confs += [0.7]
            attrs += [{"type": "nounphrase_question"}]
        else:
            logger.info("No special nounphrases for questions. Return question of the same topic.")
            questions_with_the_same_topics = QUESTIONS.loc[np.any([QUESTIONS["topic"] == t
                                                                   for t in curr_topics], axis=0), "question"]
            if len(questions_with_the_same_topics) == 0:
                questions_with_the_same_topics = QUESTIONS.loc[np.any([QUESTIONS["topic"] == t
                                                                       for t in ["Phatic"]], axis=0), "question"]
            cands += [np.random.choice(questions_with_the_same_topics)]
            confs += [0.6]
            attrs += [{"type": "topic_question"}]

        facts_same_nps = []
        for i, nphrase in enumerate(curr_nounphrases):
            for fact_id in NP_FACTS.get(nphrase, []):
                facts_same_nps += [FACTS_MAP[str(fact_id)]]

        if len(facts_same_nps) > 0:
            logger.info("Found special nounphrases for facts. Return fact with the same nounphrase.")
            cands += [np.random.choice(facts_same_nps) + " What do you think about it?"]
            confs += [0.7]
            attrs += [{"type": "nounphrase_fact"}]
        else:
            logger.info("No special nounphrases for facts. Return fact of the same topic.")
            facts_with_the_same_topics = FACTS.loc[np.any([FACTS["cobot_topic"] == t
                                                           for t in curr_topics], axis=0), "title"]
            if len(facts_with_the_same_topics) == 0:
                facts_with_the_same_topics = FACTS.loc[np.any([FACTS["cobot_topic"] == t
                                                               for t in ["Phatic"]], axis=0), "title"]
            cands += ["Listen what I found on Reddit: " + np.random.choice(
                facts_with_the_same_topics) + " What do you think about it?"]
            confs += [0.6]
            attrs += [{"type": "topic_fact"}]

        final_responses.append(cands)
        final_confidences.append(confs)
        final_attributes.append(attrs)

    total_time = time.time() - st_time
    logger.info(f'dummy_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences, final_attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
