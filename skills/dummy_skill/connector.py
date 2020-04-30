#!/usr/bin/env python

import asyncio
import csv
import json
import logging
import re
import time
from collections import defaultdict
import random
from random import choice
from typing import Callable, Dict
from copy import deepcopy

from common.universal_templates import opinion_request_question
from common.link import link_to, high_rated_skills_for_linking
import sentry_sdk
from os import getenv


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv('SENTRY_DSN'))

ASK_QUESTION_PROB = 0.7
ASK_NORMAL_QUESTION_PROB = 0.5
LINK_TO_PROB = 0.5

np_remove_list = ["'s", 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
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

np_ignore_list = ["boring", "radio", "type", "call", "fun", "fall", "name", "names", "lgbtq families", "day", "murder",
                  "amazon", "take", "interest", "days", "year", "years", "sort", "fan", "going", "death", "part", "end",
                  "watching", "thought", "thoughts", "man", "men", "listening", "big fan", "fans", "rapping", "reading",
                  "going", "thing", "hanging", "best thing", "wife", "things", "nothing", "everything"]

with open("skills/dummy_skill/google-english-no-swears.txt", "r") as f:
    TOP_FREQUENT_UNIGRAMS = f.read().splitlines()[:1000]

np_ignore_expr = re.compile("(" + "|".join([r'\b%s\b' % word for word in np_ignore_list + TOP_FREQUENT_UNIGRAMS]) + ")",
                            re.IGNORECASE)
np_remove_expr = re.compile("(" + "|".join([r'\b%s\b' % word for word in np_remove_list]) + ")", re.IGNORECASE)
rm_spaces_expr = re.compile(r'\s\s+')

donotknow_answers = [
    "What do you want to talk about?",
    "I am a bit confused. What would you like to chat about?",
    "Sorry, probably, I didn't get what you meant. What do you want to talk about?",
    "Sorry, I didn't catch that. What would you like to chat about?"
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
facts_generator = RandomTopicResponder("skills/dummy_skill/facts_with_topics.csv", 'topic', 'fact')


def get_link_to_question(dialog):
    """Generate `link_to` question updating bot attributes to one of the skills
        which were not active for the last [5] turns.

    Args:
        dialog: dp-agent dialog instance

    Returns:
        tuple of linked question and updated bot attributes with saved link to `used_links`
    """
    # get previous active skills
    bot_attr = deepcopy(dialog["bot"]["attributes"])
    bot_attr["used_links"] = bot_attr.get("used_links", defaultdict(list))

    # dummy skill gets only 5 last turns, so we do not repeat skill for 5 turns
    prev_active_skills = set([uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]
                              if uttr.get("active_skill", "") != ""])
    # remove prev active skills from those we can link to
    available_links = list(set(high_rated_skills_for_linking).difference(prev_active_skills))
    if len(available_links) > 0:
        # if we still have skill to link to, try to generate linking question
        link = link_to(available_links, used_links=bot_attr["used_links"])
        bot_attr["used_links"][link["skill"]] = bot_attr["used_links"].get(link["skill"], []) + [link['phrase']]
        linked_question = link["phrase"]
    else:
        linked_question = ""

    return linked_question, bot_attr


def generate_question_not_from_last_responses(dialog):
    linked_question, bot_attr = get_link_to_question(dialog)

    if len(linked_question) > 0 and random.random() < LINK_TO_PROB:
        result = linked_question
    else:
        result = "What would you like to talk about?"
    return result


class DummySkillConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            dialog = deepcopy(payload['payload']["dialogs"][0])

            curr_topics = dialog["utterances"][-1]["annotations"]["cobot_topics"].get("text", [])
            curr_nounphrases = dialog["utterances"][-1]["annotations"]["cobot_nounphrases"]

            if len(curr_topics) == 0:
                curr_topics = ["Phatic"]
            logger.info(f"Found topics: {curr_topics}")
            for i in range(len(curr_nounphrases)):
                np = re.sub(np_remove_expr, "", curr_nounphrases[i])
                np = re.sub(rm_spaces_expr, " ", np)
                if re.search(np_ignore_expr, np):
                    curr_nounphrases[i] = ""
                else:
                    curr_nounphrases[i] = np.strip()

            curr_nounphrases = [np for np in curr_nounphrases if len(np) > 0]

            logger.info(f"Found nounphrases: {curr_nounphrases}")

            cands = []
            confs = []
            human_attrs = []
            bot_attrs = []
            attrs = []

            cands += [choice(donotknow_answers)]
            confs += [0.5]
            attrs += [{"type": "dummy"}]
            human_attrs += [{}]
            bot_attrs += [{}]

            if len(dialog["utterances"]) > 14:
                questions_same_nps = []
                for i, nphrase in enumerate(curr_nounphrases):
                    for q_id in NP_QUESTIONS.get(nphrase, []):
                        questions_same_nps += [QUESTIONS_MAP[str(q_id)]]

                if len(questions_same_nps) > 0:
                    logger.info("Found special nounphrases for questions. Return question with the same nounphrase.")
                    cands += [choice(questions_same_nps)]
                    confs += [0.5]
                    attrs += [{"type": "nounphrase_question"}]
                    human_attrs += [{}]
                    bot_attrs += [{}]
                else:
                    if random.random() < ASK_NORMAL_QUESTION_PROB:
                        logger.info("No special nounphrases for questions. Return question of the same topic.")
                        cands += [questions_generator.get_random_text(curr_topics)]
                        confs += [0.5]
                        attrs += [{"type": "topic_question"}]
                        human_attrs += [{}]
                        bot_attrs += [{}]
                    else:
                        logger.info("No special nounphrases for questions. Return link-to question.")
                        question, bot_attr = generate_question_not_from_last_responses(dialog)
                        cands += [question]
                        confs += [0.55]
                        attrs += [{"type": "normal_question"}]
                        human_attrs += [{}]
                        bot_attrs += [bot_attr]
            else:
                logger.info("Dialog begins. No special nounphrases for questions. Return link-to question.")
                question, bot_attr = generate_question_not_from_last_responses(dialog)
                cands += [question]
                confs += [0.55]
                attrs += [{"type": "normal_question"}]
                human_attrs += [{}]
                bot_attrs += [bot_attr]

            link_to_question, bot_attr = get_link_to_question(dialog)
            if link_to_question:
                cands += [link_to_question]
                confs += [0.05]  # Use it only as response selector retrieve skill output modifier
                attrs += [{"type": "link_to_for_response_selector"}]
                human_attrs += [{}]
                bot_attrs += [bot_attr]

            facts_same_nps = []
            for i, nphrase in enumerate(curr_nounphrases):
                for fact_id in NP_FACTS.get(nphrase, []):
                    facts_same_nps += [
                        f"Well, now that you've mentioned {nphrase}, I've remembered this. {FACTS_MAP[str(fact_id)]}. "
                        f"{(opinion_request_question() if random.random() < ASK_QUESTION_PROB else '')}"]

            if len(facts_same_nps) > 0:
                logger.info("Found special nounphrases for facts. Return fact with the same nounphrase.")
                cands += [choice(facts_same_nps)]
                confs += [0.5]
                attrs += [{"type": "nounphrase_fact"}]
                human_attrs += [{}]
                bot_attrs += [{}]

            total_time = time.time() - st_time
            logger.info(f'dummy_skill exec time: {total_time:.3f}s')
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=[cands, confs, human_attrs, bot_attrs, attrs]
            ))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=e
            ))
