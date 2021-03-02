from typing import List
import logging
import os
import collections


import en_core_web_sm
import sentry_sdk
from nltk.stem import WordNetLemmatizer

import common.utils as utils

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

ENCOUNTERS_MAX_LEN = 3
ENTITY_MAX_NO = 10

logger = logging.getLogger(__name__)

spacy_nlp = en_core_web_sm.load()

wnl = WordNetLemmatizer()


class HumanEntityEncounter:
    def __init__(
        self,
        human_utterance_index: int,
        full_name: List[str],
        previous_skill_name: str,
        next_skill_name: str,
        sentiment: str,
        emotions: List,
        intents: List,
        topics: List,
        pos: List[str],
    ):
        self.human_utterance_index = human_utterance_index
        self.full_name = full_name
        self.previous_skill_name = previous_skill_name
        self.next_skill_name = next_skill_name
        self.sentiment = sentiment
        self.emotions = emotions
        self.intents = intents
        self.topics = topics
        self.pos = pos

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


class BotEntityEncounter:
    def __init__(
        self,
        human_utterance_index: int,
        full_name: str,
        skill_name: str,
        next_user_sentiment: str,
        next_user_emotions: List,
        next_user_intents: List,
        next_user_topics: List,
        pos: List[str],
    ):
        self.human_utterance_index = human_utterance_index
        self.full_name = full_name
        self.skill_name = skill_name
        self.next_user_sentiment = next_user_sentiment
        self.next_user_emotions = next_user_emotions
        self.next_user_intents = next_user_intents
        self.next_user_topics = next_user_topics
        self.pos = pos

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


class Entity:
    def __init__(self, name=None, raw_data=None):
        if name:
            self.name = name
            self.human_encounters = []
            self.bot_encounters = []
        else:
            try:
                assert isinstance(raw_data, dict)
                assert isinstance(raw_data["name"], str)
                assert isinstance(raw_data["human_encounters"], list)
                assert isinstance(raw_data["bot_encounters"], list)
                self.name = raw_data["name"]
                self.human_encounters = [
                    HumanEntityEncounter(**encounter) for encounter in raw_data["human_encounters"]
                ]
                self.bot_encounters = [BotEntityEncounter(**encounter) for encounter in raw_data["bot_encounters"]]
            except Exception as exc:
                logger.exception(exc)
                sentry_sdk.capture_exception(exc)
                self.name = "#LOAD_ENTITY_ERROR"
                self.human_encounters = []
                self.bot_encounters = []

        self.human_encounters = collections.deque(self.human_encounters, maxlen=ENCOUNTERS_MAX_LEN)
        self.bot_encounters = collections.deque(self.bot_encounters, maxlen=ENCOUNTERS_MAX_LEN)

    def __iter__(self):
        for x, y in self.__dict__.items():
            if x in ["human_encounters", "bot_encounters"]:
                yield x, [dict(i) for i in y]
            else:
                yield x, y

    def add_human_encounters(self, human_utters, bot_utters, human_utter_index):
        human_utter = human_utters[-1]
        bot_utter = bot_utters[0] if bot_utters else {}
        entities = parse_entities(human_utter["text"])
        entities = [ent for ent in entities if self.name in wnl.lemmatize(ent["text"], "n")]

        active_skill = bot_utter.get("active_skill", "pre_start")
        sentiment = utils.get_sentiment(human_utter, probs=False)[0]
        emotions = utils.get_emotions(human_utter)
        intents = utils.get_intents(human_utter)
        topics = utils.get_topics(human_utter)
        for entity in entities:
            hee = HumanEntityEncounter(
                human_utterance_index=human_utter_index,
                full_name=entity["text"],
                previous_skill_name=active_skill,
                next_skill_name="",
                sentiment=sentiment,
                emotions=emotions,
                intents=intents,
                topics=topics,
                pos=entity["pos"],
            )
            self.human_encounters.append(hee)

    def add_bot_encounters(self, human_utters, bot_utters, human_utter_index):
        human_utter = human_utters[-1]
        bot_utter = bot_utters[0] if bot_utters else {}
        entities = parse_entities(bot_utter["text"])
        entities = [ent for ent in entities if self.name in wnl.lemmatize(ent["text"], "n")]

        active_skill = bot_utter.get("active_skill", "pre_start")
        next_user_sentiment = utils.get_sentiment(human_utter, probs=False)[0]
        next_user_emotions = utils.get_emotions(human_utter)
        next_user_intents = utils.get_intents(human_utter)
        next_user_topics = utils.get_topics(human_utter)
        for entity in entities:
            bee = BotEntityEncounter(
                human_utterance_index=human_utter_index,
                full_name=entity["text"],
                skill_name=active_skill,
                next_user_sentiment=next_user_sentiment,
                next_user_emotions=next_user_emotions,
                next_user_intents=next_user_intents,
                next_user_topics=next_user_topics,
                pos=entity["pos"],
            )
            self.bot_encounters.append(bee)

    def update_human_encounters(self, human_utters, bot_utters, human_utter_index):
        bot_utter = bot_utters[0] if bot_utters else {}
        active_skill = bot_utter.get("active_skill", "pre_start" if len(human_utters) == 1 else "unknown")
        encounters = [
            encounter for encounter in self.human_encounters if human_utter_index - 1 == encounter.human_utterance_index
        ]
        for encounter in encounters:
            encounter.next_skill_name = active_skill

    def get_last_utterance_index(self):
        utterance_indexes = [
            encounter.human_utterance_index
            for encounter in list(self.human_encounters)[-1:] + list(self.bot_encounters)[-1:]
        ]
        max_utterance_index = max(utterance_indexes) if utterance_indexes else -1
        return max_utterance_index


prohibited_nouns = ["kind", "sort"]


def parse_entities(text):
    doc = spacy_nlp(text)
    entities = [[]]
    for token in reversed(doc):
        if token.pos_ == "NOUN" or (entities[-1] and (token.pos_ == "ADJ" or str(token) == "of")):
            entities[-1] += [token]
        else:
            entities += [[]]
    entities = [list(reversed(ent)) for ent in entities if ent]
    # "of" problem decision
    for ent in entities:
        of_indexes = [-1] + [index for index, token in enumerate(ent) if str(token) == "of"] + [len(ent)]
        segments = []
        for start_index, end_index in zip(of_indexes, of_indexes[1:]):
            start_index += 1
            segments += [ent[start_index:end_index]]
        for _ in range(len(segments) - 1):
            segments[-2] = segments[-1] + segments[-2]
            segments.pop()
        assert len(segments) == 1
        ent.clear()
        ent += segments[0]
    # drop prohibited nouns
    entities = [[token for token in ent if str(token) not in prohibited_nouns] for ent in entities]

    full_names = [[str(token) for token in ent] for ent in entities]
    poses = [[token.pos_ for token in ent] for ent in entities]
    entities = [{"text": " ".join(entity).replace(".", ""), "pos": pos} for entity, pos in zip(full_names, poses)]
    entities = [entity for entity in entities if len(entity["text"]) > 2]
    return entities


def parse_short_entities(text):
    entities = [ent["text"].split() for ent in parse_entities(text)]
    return [wnl.lemmatize(ent[-1], "n") for ent in entities if ent]


def is_entity(text):
    return bool(parse_short_entities(text))


def load_raw_entities(raw_entities):
    entities = {entity_name: Entity(raw_data=entity_raw_data) for entity_name, entity_raw_data in raw_entities.items()}
    entities = {entity_name: ent for entity_name, ent in entities.items() if "_ERROR" not in ent.name}
    entities = {entity_name: ent for entity_name, ent in entities.items() if "." not in entity_name}
    entities = {entity_name: ent for entity_name, ent in entities.items() if len(entity_name) > 2}
    return entities


def update_entities(dialog, human_utter_index, entities={}):
    old_entities = list(entities)
    human_utterances = dialog["human_utterances"]
    bot_utterances = dialog["bot_utterances"]

    # add/update bot entities
    if bot_utterances:
        bot_short_entities = parse_short_entities(bot_utterances[-1]["text"])
        bot_entities = {
            entity_name: entities.get(entity_name, Entity(entity_name)) for entity_name in bot_short_entities
        }
        entities.update(bot_entities)
        [ent.add_bot_encounters(human_utterances, bot_utterances, human_utter_index) for ent in bot_entities.values()]

    # add/update human entities
    human_short_entities = parse_short_entities(human_utterances[-1]["text"])
    human_entities = {
        entity_name: entities.get(entity_name, Entity(entity_name)) for entity_name in human_short_entities
    }
    entities.update(human_entities)
    [ent.add_human_encounters(human_utterances, bot_utterances, human_utter_index) for ent in human_entities.values()]

    # update previus human entities
    if len(human_utterances) == 2:
        short_human_entities = parse_short_entities(human_utterances[-2]["text"])
        new_human_entities = {
            entity_name: Entity(entity_name) for entity_name in short_human_entities if entity_name not in old_entities
        }
        entities.update(new_human_entities)
        [ent.add_human_encounters(human_utterances, [], human_utter_index - 1) for ent in new_human_entities.values()]
        [
            entities[entity_name].update_human_encounters(human_utterances, bot_utterances, human_utter_index)
            for entity_name in short_human_entities
        ]
    index2entity = {
        entity.get_last_utterance_index(): {entity_name: entity} for entity_name, entity in entities.items()
    }
    recent_indexes = sorted(index2entity)[-ENTITY_MAX_NO:]
    entities = {}
    [entities.update(index2entity[i]) for i in recent_indexes]
    return entities


def get_new_human_entities(entities, human_utterance_index):
    entities = {
        entity_name: ent
        for entity_name, ent in entities.items()
        if len(ent.human_encounters) == 1 and ent.human_encounters[-1].human_utterance_index == human_utterance_index
    }
    return entities


def get_time_sorted_human_entities(entities):
    entities = {entity_name: ent for entity_name, ent in entities.items() if len(ent.human_encounters) == 1}
    sorted_entities = sorted(
        entities, key=lambda entity_name: entities[entity_name].human_encounters[-1].human_utterance_index
    )
    return {entity_name: entities[entity_name] for entity_name in sorted_entities}
