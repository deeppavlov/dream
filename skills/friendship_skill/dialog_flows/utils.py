import logging
import pathlib


import common.entity_utils as entity_utils
import common.constants as common_constants
import common.utils as common_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

banned_nouns_file = pathlib.Path("/src/programy_storage/sets/banned_noun.txt")
BANNED_NOUNS = [noun.strip() for noun in banned_nouns_file.open().readlines() if "#" not in noun]

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7


#  vars is described in README.md


def get_entities(vars):
    agent = vars["agent"]
    return entity_utils.load_raw_entities(agent.get("entities", {}))


def get_new_human_entities(vars):
    agent = vars["agent"]
    human_utter_index = agent["human_utter_index"]
    entities = get_entities(vars)
    return entity_utils.get_new_human_entities(entities, human_utter_index)


def get_sentiment(vars):
    sentiment = common_utils.get_sentiment(vars["agent"]["dialog"]["human_utterances"][-1], probs=False)[0]
    return sentiment


def get_shared_memory(vars):
    return vars["agent"]["shared_memory"]


def get_used_links(vars):
    return vars["agent"]["used_links"]


def get_last_user_utterance(vars):
    return vars["agent"]["dialog"]["human_utterances"][-1]


def save_to_shared_memory(vars, **kwargs):
    vars["agent"]["shared_memory"].update(kwargs)


def save_used_links(vars, used_links):
    vars["agent"]["used_links"] = used_links


def set_confidence(vars, confidence=DIALOG_BEGINNING_CONTINUE_CONFIDENCE):
    vars["agent"]["response"] = {"confidence": confidence}


def set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE):
    vars["agent"]["response"] = {"can_continue": continue_flag}
