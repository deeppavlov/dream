import logging

import common.entity_utils as entity_utils
import common.constants as common_constants
import common.utils as common_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


#  vars is described in README.md


def get_labeled_noun_phrase(vars):
    agent = vars["agent"]
    return entity_utils.load_raw_entities(agent.get("entities", {}))


def get_new_human_labeled_noun_phrase(vars):
    agent = vars["agent"]
    human_utter_index = agent["human_utter_index"]
    entities = get_labeled_noun_phrase(vars)
    return entity_utils.get_new_human_entities(entities, human_utter_index)


def get_human_sentiment(vars):
    sentiment = common_utils.get_sentiment(vars["agent"]["dialog"]["human_utterances"][-1], probs=False)[0]
    return sentiment


def get_shared_memory(vars):
    return vars["agent"]["shared_memory"]


def get_used_links(vars):
    return vars["agent"]["used_links"]


def get_human_utter_index(vars):
    return vars["agent"]["human_utter_index"]


def get_previous_human_utter_index(vars):
    return vars["agent"]["previous_human_utter_index"]


def get_last_human_utterance(vars):
    return vars["agent"]["dialog"]["human_utterances"][-1]


def get_last_bot_utterance(vars):
    if vars["agent"]["dialog"]["bot_utterances"]:
        return vars["agent"]["dialog"]["bot_utterances"][-1]
    else:
        return {"text": "", "annotations": {}}


def save_to_shared_memory(vars, **kwargs):
    vars["agent"]["shared_memory"].update(kwargs)


def save_used_links(vars, used_links):
    vars["agent"]["used_links"] = used_links


def set_confidence(vars, confidence=1.0):
    vars["agent"]["response"].update({"confidence": confidence})


def set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE):
    vars["agent"]["response"].update({"can_continue": continue_flag})


def get_named_entities_from_human_utterance(vars):
    # ent is a dict! ent = {"text": "London":, "type": "LOC"}
    entities = []
    for ents in vars["agent"]["dialog"]["human_utterances"][-1].get("annotations", {}).get("ner", []):
        if not ents:
            continue
        for ent in ents:
            entities.append(ent)
    return entities


def get_nounphrases_from_human_utterance(vars):
    nps = vars["agent"]["dialog"]["human_utterances"][-1].get("annotations", {}).get("cobot_nounphrases", [])
    return nps
