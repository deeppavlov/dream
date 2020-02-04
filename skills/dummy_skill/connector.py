#!/usr/bin/env python

import asyncio
import csv
import json
import logging
import re
import time
from collections import defaultdict
from random import choice
from typing import Callable, Dict

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


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

np_ignore_expr = re.compile(r'\b(' + '|'.join(np_ignore_list) + r')\b')
rm_spaces_expr = re.compile(r'\s\s+')

donotknow_answers = [
    "I really do not know what to answer.",
    "Sorry, probably, I didn't get what you meant.",
    "I didn't get it. Sorry.",
    "Let's talk about something else."
]

with open("skills/dummy_skill/questions_map.json", "r") as f:
    QUESTIONS_MAP = json.load(f)

with open("skills/dummy_skill/nounphrases_questions_map.json", "r") as f:
    NP_QUESTIONS = json.load(f)

with open("skills/dummy_skill/facts_map.json", "r") as f:
    FACTS_MAP = json.load(f)

with open("skills/dummy_skill/nounphrases_facts_map.json", "r") as f:
    NP_FACTS = json.load(f)


class RandomTopicResponder:
    def __init__(self, filename, topic, text):
        self.topic_phrases = defaultdict(list)
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.topic_phrases[row[topic]].append(row[text])
        self.current_index = {k: 0 for k in self.topic_phrases.keys()}
        self.topics = set(self.topic_phrases.keys())

    def get_random_text(self, topics):
        available_topics = self.topics.intersection(set(topics))
        if not available_topics:
            return ''

        selected_topic = choice(list(available_topics))
        result = self.topic_phrases[selected_topic][self.current_index[selected_topic]]

        self.current_index[selected_topic] += 1
        if self.current_index[selected_topic] >= len(self.topic_phrases[selected_topic]):
            self.current_index[selected_topic] = 0
        return result


questions_generator = RandomTopicResponder("skills/dummy_skill/questions_with_topics.csv", 'topic', 'question')
facts_generator = RandomTopicResponder("skills/dummy_skill/facts_with_topics.csv", 'cobot_topic', 'title')


class DummySkillConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            dialog = payload['payload']["dialogs"][0]

            curr_topics = dialog["utterances"][-1]["annotations"]["cobot_topics"].get("text", [])
            curr_nounphrases = dialog["utterances"][-1]["annotations"]["cobot_nounphrases"]

            if len(curr_topics) == 0:
                curr_topics = ["Phatic"]
            logger.info(f"Found topics: {curr_topics}")
            for i in range(len(curr_nounphrases)):
                curr_nounphrases[i] = re.sub(rm_spaces_expr, ' ',
                                             re.sub(np_ignore_expr, ' ', curr_nounphrases[i])).strip()

            logger.info(f"Found nounphrases: {curr_nounphrases}")

            cands = []
            confs = []
            attrs = []

            cands += [choice(donotknow_answers)]
            confs += [0.5]
            attrs += [{"type": "dummy"}]

            questions_same_nps = []
            for i, nphrase in enumerate(curr_nounphrases):
                for q_id in NP_QUESTIONS.get(nphrase, []):
                    questions_same_nps += [QUESTIONS_MAP[str(q_id)]]

            if len(questions_same_nps) > 0:
                logger.info("Found special nounphrases for questions. Return question with the same nounphrase.")
                cands += [choice(questions_same_nps)]
                confs += [0.7]
                attrs += [{"type": "nounphrase_question"}]
            else:
                logger.info("No special nounphrases for questions. Return question of the same topic.")
                cands += [questions_generator.get_random_text(curr_topics)]
                confs += [0.6]
                attrs += [{"type": "topic_question"}]

            facts_same_nps = []
            for i, nphrase in enumerate(curr_nounphrases):
                for fact_id in NP_FACTS.get(nphrase, []):
                    facts_same_nps += [FACTS_MAP[str(fact_id)]]

            if len(facts_same_nps) > 0:
                logger.info("Found special nounphrases for facts. Return fact with the same nounphrase.")
                cands += [choice(facts_same_nps) + ". What do you think about it?"]
                confs += [0.7]
                attrs += [{"type": "nounphrase_fact"}]
            '''
            else:
                logger.info("No special nounphrases for facts. Return fact of the same topic.")
                cands += [f"Listen what I found on Reddit: {facts_generator.get_random_text(curr_topics)}"
                          f". What do you think about it?"]
                confs += [0.6]
                attrs += [{"type": "topic_fact"}]
            '''

            total_time = time.time() - st_time
            logger.info(f'dummy_skill exec time: {total_time:.3f}s')
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=[cands, confs, attrs]
            ))
        except Exception as e:
            logger.exception(e)
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=e
            ))
