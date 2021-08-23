from typing import List
import logging
import os
import collections


import en_core_web_sm
import sentry_sdk
from nltk.stem import WordNetLemmatizer

from common.utils import get_entities
from common.universal_templates import get_entities_with_attitudes

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
        previous_skill_name: str = "",
        **kwargs
    ):
        self.human_utterance_index = human_utterance_index
        self.full_name = full_name
        self.previous_skill_name = previous_skill_name

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


class BotEntityEncounter:
    def __init__(
        self,
        human_utterance_index: int,
        full_name: str,
        skill_name: str,
        **kwargs
    ):
        self.human_utterance_index = human_utterance_index
        self.full_name = full_name
        self.skill_name = skill_name

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


class Entity:
    def __init__(self, name=None, raw_data=None):
        if name:
            self.name = name
            self.human_encounters = []
            self.bot_encounters = []
            self.human_attitude = None
            self.bot_attitude = None
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
                self.human_attitude = raw_data.get("human_attitude", None)
                self.bot_attitude = raw_data.get("bot_attitude", None)
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

    def add_human_attitude(self, attitude):
        self.human_attitude = attitude

    def add_bot_attitude(self, attitude):
        self.bot_attitude = attitude

    def add_human_encounters(self, human_utters, bot_utters, human_utter_index):
        human_utter = human_utters[-1]
        bot_utter = bot_utters[0] if bot_utters else {}
        entities = get_entities(human_utter, only_named=False, with_labels=False)
        entities = [ent for ent in entities if self.name in wnl.lemmatize(ent, "n")]

        active_skill = bot_utter.get("active_skill", "pre_start")
        for entity in entities:
            hee = HumanEntityEncounter(
                human_utterance_index=human_utter_index,
                full_name=entity,
                previous_skill_name=active_skill,
            )
            self.human_encounters.append(hee)

    def add_bot_encounters(self, human_utters, bot_utters, human_utter_index):
        bot_utter = bot_utters[0] if bot_utters else {}
        entities = get_entities(bot_utter, only_named=False, with_labels=False)
        entities = [ent for ent in entities if self.name in wnl.lemmatize(ent, "n")]

        active_skill = bot_utter.get("active_skill", "pre_start")
        for entity in entities:
            bee = BotEntityEncounter(
                human_utterance_index=human_utter_index,
                full_name=entity,
                skill_name=active_skill,
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


def parse_entities_with_attitude(annotated_uttr: dict, prev_annotated_uttr: dict):
    entities_with_attitude = get_entities_with_attitudes(annotated_uttr, prev_annotated_uttr)
    entities_with_attitude = {
        "like": [wnl.lemmatize(ent, "n") for ent in entities_with_attitude["like"]],
        "dislike": [wnl.lemmatize(ent, "n") for ent in entities_with_attitude["dislike"]],
    }
    return entities_with_attitude


def load_raw_entities(raw_entities):
    entities = {entity_name: Entity(raw_data=entity_raw_data) for entity_name, entity_raw_data in raw_entities.items()}
    entities = {entity_name: ent for entity_name, ent in entities.items() if "_ERROR" not in ent.name}
    entities = {entity_name: ent for entity_name, ent in entities.items() if "." not in entity_name}
    entities = {entity_name: ent for entity_name, ent in entities.items() if len(entity_name) > 2}
    return entities


def update_entities(dialog, human_utter_index, entities=None):
    entities = {} if entities is None else entities
    old_entities = list(entities)
    human_utterances = dialog["human_utterances"]
    bot_utterances = dialog["bot_utterances"]

    # add/update bot entities
    if bot_utterances:
        bot_entities_with_attitude = parse_entities_with_attitude(
            bot_utterances[-1], human_utterances[-2] if len(human_utterances) > 1 else {})
        for attitude in ["like", "dislike"]:
            bot_short_entities = bot_entities_with_attitude[attitude]
            bot_entities = {
                entity_name: entities.get(entity_name, Entity(entity_name)) for entity_name in bot_short_entities
            }
            entities.update(bot_entities)
            [ent.add_bot_encounters(human_utterances, bot_utterances, human_utter_index)
             for ent in bot_entities.values()]
            [ent.add_bot_attitude(attitude) for ent in bot_entities.values()]

    # add/update human entities
    human_entities_with_attitude = parse_entities_with_attitude(
        human_utterances[-1], bot_utterances[-1] if len(bot_utterances) else {})
    for attitude in ["like", "dislike"]:
        human_short_entities = human_entities_with_attitude[attitude]
        human_entities = {
            entity_name: entities.get(entity_name, Entity(entity_name)) for entity_name in human_short_entities
        }
        entities.update(human_entities)
        [ent.add_human_encounters(human_utterances, bot_utterances, human_utter_index)
         for ent in human_entities.values()]
        [ent.add_human_attitude(attitude) for ent in human_entities.values()]

    # update previus human entities
    if len(human_utterances) == 2:
        human_entities_with_attitude = parse_entities_with_attitude(
            human_utterances[-2], bot_utterances[-2] if len(bot_utterances) > 1 else {})
        for attitude in ["like", "dislike"]:
            short_human_entities = human_entities_with_attitude[attitude]
            new_human_entities = {
                entity_name: Entity(entity_name)
                for entity_name in short_human_entities if entity_name not in old_entities
            }
            entities.update(new_human_entities)
            [ent.add_human_encounters(human_utterances, [], human_utter_index - 1)
             for ent in new_human_entities.values()]
            [ent.add_human_attitude(attitude) for ent in new_human_entities.values()]
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
