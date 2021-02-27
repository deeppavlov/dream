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
    for ent in vars["agent"]["dialog"]["human_utterances"][-1].get("annotations", {}).get("ner", []):
        if not ent:
            continue
        ent = ent[0]
        entities.append(ent)
    return entities


def get_nounphrases_from_human_utterance(vars):
    nps = vars["agent"]["dialog"]["human_utterances"][-1].get("annotations", {}).get("cobot_nounphrases", [])
    return nps


def is_no_human_dialog_breakdown(vars):
    """Is dialog breakdown in human utterance or no.
    Pay attention that dialog breakdown does not mean that user changed topic completely.
    For example,
    bot: what did you like most in Vietnam?
    human: very tasty fruits -> dialog breakdown!
    """
    no_db_proba = get_last_human_utterance(vars).get("annotations", {}).get(
        "dialog_breakdown", {}).get("no_breakdown", 0.)
    if no_db_proba > 0.5:
        return True
    return False


def no_dialog_breakdown_or_no_requests(vars):
    """Function to determine if user didn't asked to switch topic, user didn't ask to talk about something particular,
        user didn't requested some special intents (like what_is_your_name, what_are_you_talking_about),
        user didn't asked or requested something, OR no dialog breakdown in conversation.
    """
    no_db = is_no_human_dialog_breakdown(vars)
    intents = common_utils.get_intents(get_last_human_utterance(vars), which="all")
    intents_by_catcher = common_utils.get_intents(get_last_human_utterance(vars), probs=False, which="intent_catcher")
    is_high_priority_intent = any([intent not in common_utils.service_intents for intent in intents_by_catcher])

    request_intents = ["opinion_request", "topic_switching", "lets_chat_about", "what_are_you_talking_about",
                       "Information_RequestIntent", "Topic_SwitchIntent", "Opinion_RequestIntent"]
    is_not_request_intent = all([intent not in request_intents for intent in intents])
    is_no_question = "?" not in get_last_human_utterance(vars)["text"]

    if not is_high_priority_intent and (no_db or (is_not_request_intent and is_no_question)):
        return True
    return False
