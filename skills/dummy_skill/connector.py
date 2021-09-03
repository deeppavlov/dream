#!/usr/bin/env python

import asyncio
import csv
import json
import logging
import random
import re
import time
from collections import defaultdict
from copy import deepcopy
from os import getenv
from random import choice
from typing import Callable, Dict

import sentry_sdk

from common.link import (
    LIST_OF_SCRIPTED_TOPICS,
    SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED,
    DFF_WIKI_LINKTO,
    skills_phrases_map,
    compose_linkto_with_connection_phrase,
)
from common.sensitive import is_sensitive_situation
from common.universal_templates import opinion_request_question, is_switch_topic, if_choose_topic
from common.utils import get_topics, get_entities, is_no, get_intents, is_yes


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))

ASK_QUESTION_PROB = 0.7
LINK_TO_PROB = 0.5
LINK_TO_PHRASES = sum([list(list_el) for list_el in skills_phrases_map.values()], [])

np_remove_list = [
    "'s",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "you're",
    "you've",
    "you'll",
    "you'd",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "she's",
    "her",
    "hers",
    "herself",
    "it",
    "it's",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "that'll",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "don't",
    "should",
    "should've",
    "now",
    "d",
    "ll",
    "m",
    "o",
    "re",
    "ve",
    "y",
    "ain",
    "aren",
    "aren't",
    "couldn",
    "couldn't",
    "didn",
    "didn't",
    "doesn",
    "doesn't",
    "hadn",
    "hadn't",
    "hasn",
    "hasn't",
    "haven",
    "haven't",
    "isn",
    "isn't",
    "ma",
    "mightn",
    "mightn't",
    "mustn",
    "mustn't",
    "needn",
    "needn't",
    "shan",
    "shan't",
    "shouldn",
    "shouldn't",
    "wasn",
    "wasn't",
    "weren",
    "weren't",
    "won",
    "won't",
    "wouldn",
    "wouldn't",
    "my name",
    "your name",
    "wow",
    "yeah",
    "yes",
    "ya",
    "cool",
    "okay",
    "more",
    "some more",
    " a lot",
    "a bit",
    "another one",
    "something else",
    "something",
    "anything",
    "someone",
    "anyone",
    "play",
    "mean",
    "a lot",
    "a little",
    "a little bit",
]

np_ignore_list = [
    "boring",
    "radio",
    "type",
    "call",
    "fun",
    "fall",
    "name",
    "names",
    "lgbtq families",
    "day",
    "murder",
    "amazon",
    "take",
    "interest",
    "days",
    "year",
    "years",
    "sort",
    "fan",
    "going",
    "death",
    "part",
    "end",
    "watching",
    "thought",
    "thoughts",
    "man",
    "men",
    "listening",
    "big fan",
    "fans",
    "rapping",
    "reading",
    "going",
    "thing",
    "hanging",
    "best thing",
    "wife",
    "things",
    "nothing",
    "everything",
]

with open("skills/dummy_skill/google-english-no-swears.txt", "r") as f:
    TOP_FREQUENT_UNIGRAMS = f.read().splitlines()[:1000]

np_ignore_expr = re.compile(
    "(" + "|".join([r"\b%s\b" % word for word in np_ignore_list + TOP_FREQUENT_UNIGRAMS]) + ")", re.IGNORECASE
)
np_remove_expr = re.compile("(" + "|".join([r"\b%s\b" % word for word in np_remove_list]) + ")", re.IGNORECASE)
rm_spaces_expr = re.compile(r"\s\s+")
ASK_ME_QUESTION_PATTERN = re.compile(
    r"^(do you have (a )?question|(can you|could you)?ask me (something|anything|[a-z ]+question))", re.IGNORECASE
)

donotknow_answers = [
    "What do you want to talk about?",
    "I am a bit confused. What would you like to chat about?",
    "Sorry, probably, I didn't get what you meant. What do you want to talk about?",
    "Sorry, I didn't catch that. What would you like to chat about?",
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
        with open(filename, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.topic_phrases[row[topic]].append(row[text])
        self.current_index = {k: 0 for k in self.topic_phrases.keys()}
        self.topics = set(self.topic_phrases.keys())

    def get_random_text(self, topics):
        available_topics = self.topics.intersection(set(topics))
        if not available_topics:
            return ""

        selected_topic = choice(list(available_topics))
        result = self.topic_phrases[selected_topic][self.current_index[selected_topic]]

        self.current_index[selected_topic] += 1
        if self.current_index[selected_topic] >= len(self.topic_phrases[selected_topic]):
            self.current_index[selected_topic] = 0
        return result


questions_generator = RandomTopicResponder("skills/dummy_skill/questions_with_topics.csv", "topic", "question")
facts_generator = RandomTopicResponder("skills/dummy_skill/facts_with_topics.csv", "topic", "fact")


def get_link_to_question(dialog, all_prev_active_skills):
    """Generate `link_to` question updating bot attributes to one of the skills
        which were not active for the last [5] turns.

    Args:
        dialog: dp-agent dialog instance

    Returns:
        tuple of linked question and updated bot attributes with saved link to `used_links`
    """
    # get previous active skills
    human_attr = {}
    human_attr["used_links"] = dialog["human"]["attributes"].get("used_links", {})
    human_attr["used_wiki_topics"] = dialog["human"]["attributes"].get("used_wiki_topics", [])
    human_attr["disliked_skills"] = dialog["human"]["attributes"].get("disliked_skills", [])
    human_attr["prelinkto_connections"] = dialog["human"]["attributes"].get("prelinkto_connections", [])
    from_skill = None
    for from_skill in all_prev_active_skills[::-1][:5]:
        if from_skill in LIST_OF_SCRIPTED_TOPICS.keys():
            break
    # remove prev active skills from those we can link to
    available_links = list(set(SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED).difference(all_prev_active_skills))
    # use recommended skills
    # recommended_skills = dialog["human_utterances"][-1].get("annotations", []).get("topic_recommendation", [])
    # if len(set(available_links).intersection(recommended_skills)) > 0:
    #     available_links = list(set(recommended_skills).intersection(available_links))

    all_wiki_topics = set(DFF_WIKI_LINKTO.keys())
    available_wiki_topics = list(all_wiki_topics.difference(set(human_attr["used_wiki_topics"])))
    available_best_wiki_topics = list(set(["art", "love", "anime"]).difference(set(human_attr["used_wiki_topics"])))

    if len(available_links) > 0:
        # if we still have skill to link to, try to generate linking question
        # {'phrase': result, 'skill': linkto_dict["skill"], "connection_phrase": connection}
        if len(available_best_wiki_topics) > 0 and random.uniform(0, 1) < 0.2:
            chosen_topic = random.choice(available_best_wiki_topics)
            linked_question = DFF_WIKI_LINKTO[chosen_topic]
        else:
            link = compose_linkto_with_connection_phrase(
                available_links,
                human_attributes=human_attr,
                recent_active_skills=all_prev_active_skills,
                from_skill=from_skill,
            )
            human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(link["skill"], []) + [link["phrase"]]
            human_attr["prelinkto_connections"] += [link.get("connection_phrase", "")]
            linked_question = link["phrase"]
    elif len(available_wiki_topics) > 0:
        chosen_topic = random.choice(available_wiki_topics)
        linked_question = DFF_WIKI_LINKTO[chosen_topic]
    else:
        linked_question = ""

    return linked_question, human_attr


def generate_question_not_from_last_responses(dialog, all_prev_active_skills):
    linked_question, human_attr = get_link_to_question(dialog, all_prev_active_skills)

    if len(linked_question) > 0:
        result = linked_question
    else:
        result = ""
    return result, human_attr


class DummySkillConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            dialog = deepcopy(payload["payload"]["dialogs"][0])
            is_sensitive_case = is_sensitive_situation(dialog["human_utterances"][-1])
            all_prev_active_skills = payload["payload"]["all_prev_active_skills"][0]

            curr_topics = get_topics(dialog["human_utterances"][-1], which="cobot_topics")
            curr_nounphrases = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)

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

            if len(dialog["utterances"]) > 14 and not is_sensitive_case:
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

            link_to_question, human_attr = get_link_to_question(dialog, all_prev_active_skills)
            if link_to_question:
                _prev_bot_uttr = dialog["bot_utterances"][-2]["text"] if len(dialog["bot_utterances"]) > 1 else ""
                _bot_uttr = dialog["bot_utterances"][-1]["text"] if len(dialog["bot_utterances"]) > 0 else ""
                _prev_active_skill = (
                    dialog["bot_utterances"][-1]["active_skill"] if len(dialog["bot_utterances"]) > 0 else ""
                )

                _no_to_first_linkto = any([phrase in _bot_uttr for phrase in LINK_TO_PHRASES])
                _no_to_first_linkto = _no_to_first_linkto and all(
                    [phrase not in _prev_bot_uttr for phrase in LINK_TO_PHRASES]
                )
                _no_to_first_linkto = _no_to_first_linkto and is_no(dialog["human_utterances"][-1])
                _no_to_first_linkto = _no_to_first_linkto and _prev_active_skill != "dff_friendship_skill"

                _if_switch_topic = is_switch_topic(dialog["human_utterances"][-1])
                bot_uttr_dict = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
                _if_choose_topic = if_choose_topic(dialog["human_utterances"][-1], bot_uttr_dict)
                _is_ask_me_something = ASK_ME_QUESTION_PATTERN.search(dialog["human_utterances"][-1]["text"])

                if len(dialog["human_utterances"]) > 1:
                    _was_cant_do = "cant_do" in get_intents(dialog["human_utterances"][-2]) and (
                        len(curr_nounphrases) == 0 or is_yes(dialog["human_utterances"][-1])
                    )
                    _was_cant_do_stop_it = "cant_do" in get_intents(dialog["human_utterances"][-2]) and is_no(
                        dialog["human_utterances"][-1]
                    )
                else:
                    _was_cant_do = False
                    _was_cant_do_stop_it = False

                if _was_cant_do_stop_it:
                    link_to_question = "Sorry, bye! #+#exit"
                    confs += [1.0]  # finish dialog request
                elif _no_to_first_linkto:
                    confs += [0.99]
                elif _is_ask_me_something or _if_switch_topic or _was_cant_do or _if_choose_topic:
                    confs += [1.0]  # Use it only as response selector retrieve skill output modifier
                else:
                    confs += [0.05]  # Use it only as response selector retrieve skill output modifier
                cands += [link_to_question]
                attrs += [{"type": "link_to_for_response_selector"}]
                human_attrs += [human_attr]
                bot_attrs += [{}]

            facts_same_nps = []
            for i, nphrase in enumerate(curr_nounphrases):
                for fact_id in NP_FACTS.get(nphrase, []):
                    facts_same_nps += [
                        f"Well, now that you've mentioned {nphrase}, I've remembered this. {FACTS_MAP[str(fact_id)]}. "
                        f"{(opinion_request_question() if random.random() < ASK_QUESTION_PROB else '')}"
                    ]

            if len(facts_same_nps) > 0 and not is_sensitive_case:
                logger.info("Found special nounphrases for facts. Return fact with the same nounphrase.")
                cands += [choice(facts_same_nps)]
                confs += [0.5]
                attrs += [{"type": "nounphrase_fact"}]
                human_attrs += [{}]
                bot_attrs += [{}]

            cands = ["----------PHRASE--------------"]
            confs = [0.5]
            attrs = [{"type": "nounphrase_fact"}]
            human_attrs = [{}]
            bot_attrs = [{}]
            total_time = time.time() - st_time
            logger.info(f"dummy_skill exec time: {total_time:.3f}s")
            asyncio.create_task(
                callback(task_id=payload["task_id"], response=[cands, confs, human_attrs, bot_attrs, attrs])
            )
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=e))
