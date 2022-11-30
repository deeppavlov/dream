import json
import random

from common.link import skills_phrases_map
from common.utils import get_topics, get_intents, get_entities
from .utils import (
    get_midas_intent_acknowledgement,
    reformulate_question_to_statement,
    INTENT_DICT,
    DA_TOPIC_DICT,
    COBOT_TOPIC_DICT,
    get_entity_name,
    get_midas_analogue_intent_for_any_intent,
)

SUPER_CONF = 1.0
ALMOST_SUPER_CONF = 0.9
UNIVERSAL_RESPONSE_CONF = 0.7
UNIVERSAL_RESPONSE_LOW_CONF = 0.6
DONTKNOW_CONF = 0.5
ACKNOWLEDGEMENT_CONF = 0.5
DONTKNOW_PHRASE = "Seems like I have no idea what we are talking about."
PRIVACY_REPLY = (
    "I am designed to protect your privacy, so I only listen after your device "
    "detects the wake word or if the action button is pushed. On Echo "
    "devices, you will always know when your request is being processed because "
    "a blue light indicator will appear or an audio tone will sound. You can "
    "learn more by visiting amazon.com/alexaprivacy."
)

INTENTS_BY_POPULARITY = list(INTENT_DICT.keys())[::-1]
DA_TOPICS_BY_POPULARITY = list(DA_TOPIC_DICT.keys())[::-1]
COBOT_TOPICS_BY_POPULARITY = list(COBOT_TOPIC_DICT.keys())[::-1]
LINKTO_QUESTIONS_LOWERCASED = [
    question.lower() for set_of_quests in skills_phrases_map.values() for question in set_of_quests
]

with open("./data/universal_intent_responses.json", "r") as f:
    UNIVERSAL_INTENT_RESPONSES = json.load(f)


#####################################################################
# 					For what_do_you_mean_response					#
#####################################################################
def get_what_do_you_mean_intent(last_human_utterance):
    return (
        last_human_utterance.get("annotations", {})
        .get("intent_catcher", {})
        .get("what_are_you_talking_about", {})
        .get("detected", False)
    )


def get_bot_based_on_skill_reply(bot_utterances):
    if len(bot_utterances) > 0:
        if bot_utterances[-1]["active_skill"] == "meta_script_skill":
            return "I was asking you about some unknown for me human stuff."
        if bot_utterances[-1]["active_skill"] == "comet_dialog_skill":
            return "I was trying to give a comment based on some commonsense knowledge."
    return None


def get_bot_based_on_topic_or_intent_reply(prev_human_utterance):
    reply = None
    # collect prev current intents, topics
    intent_list, da_topic_list, cobot_topic_list = collect_topics_entities_intents(prev_human_utterance)
    # get prev entity_name
    prev_annotations = prev_human_utterance.get("annotations", {}) if len(prev_human_utterance) > 1 else {}
    entity_name = get_entity_name(prev_annotations)

    for intent in INTENTS_BY_POPULARITY:  # start from least popular
        if intent in intent_list and reply is None and len(entity_name) > 0:
            reply = INTENT_DICT[intent].replace("ENTITY_NAME", entity_name)
    if len(entity_name) > 0 and reply is None:
        reply = f"We are discussing {entity_name}, aren't we?"
    for topic in DA_TOPICS_BY_POPULARITY:  # start from least popular
        if topic in da_topic_list and reply is None:
            reply = DA_TOPIC_DICT[topic]
    for topic in COBOT_TOPICS_BY_POPULARITY:  # start from least popular
        if topic in cobot_topic_list and reply is None:
            reply = COBOT_TOPIC_DICT[topic]
    return reply


#####################################################################
# 				For generate_acknowledgement_response				#
#####################################################################
def collect_topics_entities_intents(prev_human_utterance):
    if len(prev_human_utterance) > 1:
        intent_list = get_intents(prev_human_utterance, which="cobot_dialogact_intents")
        da_topic_list = get_topics(prev_human_utterance, which="cobot_dialogact_topics")
        cobot_topic_list = get_topics(prev_human_utterance, which="cobot_topics")

        intent_list = list(set(intent_list))
        da_topic_list = list(set(da_topic_list))
        cobot_topic_list = list(set(cobot_topic_list))
    else:
        intent_list, da_topic_list, cobot_topic_list = [], [], []

    return intent_list, da_topic_list, cobot_topic_list


def get_current_intents(last_human_utterances):
    curr_intents = get_intents(last_human_utterances, probs=False, which="all")
    return list(
        set(
            [
                get_midas_analogue_intent_for_any_intent(intent)
                for intent in curr_intents
                if get_midas_analogue_intent_for_any_intent(intent) is not None
            ]
        )
    )


def get_last_human_sent(last_human_utterances):
    return (
        last_human_utterances.get("annotations", {})
        .get("sentseg", {})
        .get("segments", [last_human_utterances["text"]])[-1]
    )


def generate_acknowledgement(last_human_utterances, curr_intents, curr_considered_intents):
    ackn_response = ""
    is_need_nounphrase_intent = any([intent in curr_intents for intent in ["open_question_opinion"]])
    if is_need_nounphrase_intent:
        curr_nounphrase = get_entities(last_human_utterances, only_named=False, with_labels=False)
        curr_nounphrase = curr_nounphrase[-1] if len(curr_nounphrase) > 0 and curr_nounphrase[-1] else ""
        if curr_nounphrase:
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_nounphrase)
    else:
        # to reformulate question, we take only the last human sentence
        last_human_sent = get_last_human_sent(last_human_utterances)
        curr_reformulated_question = reformulate_question_to_statement(last_human_sent)
        ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_reformulated_question)

    return ackn_response


#####################################################################
# 					For generate_universal_response					#
#####################################################################
def get_unused_reply(intent, used_universal_intent_responses):
    available_resps = list(set(UNIVERSAL_INTENT_RESPONSES[intent]).difference(set(used_universal_intent_responses)))
    available_resps = sorted(available_resps)
    if available_resps:
        reply = random.choice(available_resps)
    else:
        reply = random.choice(UNIVERSAL_INTENT_RESPONSES[intent])
    return reply
