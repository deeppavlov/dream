import json
import logging
import random
import sentry_sdk
from collections import defaultdict
from os import getenv

from common.grounding import what_we_talk_about
from common.utils import get_topics, get_intents
from utils import MIDAS_INTENT_ACKNOWLEDGMENETS, get_midas_intent_acknowledgement, reformulate_question_to_statement, \
    INTENT_DICT, DA_TOPIC_DICT, COBOT_TOPIC_DICT, get_entity_name

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONF = 0.99
UNIVERSAL_RESPONSE_CONFIDENCE = 0.8
DONTKNOW_CONF = 0.5
ACKNOWLEDGEMENT_CONF = 0.5
DONTKNOW_PHRASE = "Seems like I have no idea what we are talking about."

INTENTS_BY_POPULARITY = list(INTENT_DICT.keys())[::-1]
DA_TOPICS_BY_POPULARITY = list(DA_TOPIC_DICT.keys())[::-1]
COBOT_TOPICS_BY_POPULARITY = list(COBOT_TOPIC_DICT.keys())[::-1]

with open("universal_intent_responses.json", "r") as f:
    UNIVERSAL_INTENT_RESPONSES = json.load(f)


def collect_topics_entities_intents(dialog):
    intent_list = get_intents(dialog['human_utterances'][-2], which='cobot_dialogact_intents')
    da_topic_list = get_topics(dialog['human_utterances'][-2], which='cobot_dialogact_topics')
    cobot_topic_list = get_topics(dialog['human_utterances'][-2], which='cobot_topics')

    intent_list = list(set(intent_list))
    da_topic_list = list(set(da_topic_list))
    cobot_topic_list = list(set(cobot_topic_list))

    return intent_list, da_topic_list, cobot_topic_list


def what_do_you_mean_response(dialog):
    try:
        what_do_you_mean_intent = dialog["human_utterances"][-1].get(
            "annotations", {}).get(
            "intent_catcher", {}).get(
            "what_are_you_talking_about", {}).get(
            "detected", False)
        if not (what_we_talk_about(dialog['human_utterances'][-1]) or what_do_you_mean_intent):
            reply, confidence = '', 0
        elif len(dialog.get('human_utterances', [])) < 2:
            reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
        else:
            logger.debug('Running grounding skill')
            # collect prev current intents, topics
            intent_list, da_topic_list, cobot_topic_list = collect_topics_entities_intents(dialog)
            # get prev entity_name
            prev_annotations = dialog['human_utterances'][-2].get('annotations', {})
            entity_name = get_entity_name(prev_annotations)

            reply = None
            if len(dialog.get("bot_utterances", [])) > 0:
                if dialog["bot_utterances"][-1]["active_skill"] == "meta_script_skill":
                    reply = "I was asking you about some unknown for me human stuff."
                if dialog["bot_utterances"][-1]["active_skill"] == "comet_dialog_skill":
                    reply = "I was trying to give a comment based on some commonsense knowledge."
            if reply is None:
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
            if reply is None:
                reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
            else:
                confidence = DEFAULT_CONF
            logger.info(f'Grounding skill output: {reply} {confidence}')
    except Exception as e:
        logger.exception("exception in grounding skill")
        logger.info(str(e))
        sentry_sdk.capture_exception(e)
        reply = ""
        confidence = 0

    return reply, confidence


def generate_acknowledgement(dialog):
    curr_intents = get_intents(dialog['human_utterances'][-1], probs=False, which='midas')
    curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGMENETS]
    ackn_response = ""

    if curr_considered_intents:
        # can generate acknowledgement
        is_need_nounphrase_intent = any([intent in curr_intents for intent in ["open_question_opinion"]])
        if is_need_nounphrase_intent:
            curr_nounphrase = dialog['human_utterances'][-1]["annotations"].get("cobot_nounphrases", [])
            curr_nounphrase = curr_nounphrase[-1] if len(curr_nounphrase) > 0 and curr_nounphrase[-1] else ""
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_nounphrase)
        else:
            curr_reformulated_question = reformulate_question_to_statement(
                dialog['human_utterances'][-1]["text"])
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1],
                                                             curr_reformulated_question)
    return ackn_response, ACKNOWLEDGEMENT_CONF


def generate_universal_response(dialog):
    curr_intents = get_intents(dialog['human_utterances'][-1], probs=False, which='midas')
    human_attr = dialog["human"]["attributes"]
    human_attr["grouding_skill"] = human_attr.get("grouding_skill", {})
    human_attr["grouding_skill"]["used_universal_intent_responses"] = human_attr["grouding_skill"].get(
        "used_universal_intent_responses", [])
    bot_attr = {}
    attr = {}
    reply = ""
    confidence = 0.

    for intent in curr_intents:
        if intent in UNIVERSAL_INTENT_RESPONSES:
            available_resps = list(set(UNIVERSAL_INTENT_RESPONSES[intent]).difference(
                set(human_attr["grouding_skill"]["used_universal_intent_responses"])))
            if available_resps:
                reply = random.choice(available_resps)
                human_attr["grouding_skill"]["used_universal_intent_responses"] += [reply]
            else:
                reply = random.choice(UNIVERSAL_INTENT_RESPONSES[intent])
            confidence = UNIVERSAL_RESPONSE_CONFIDENCE
            attr = {"response_parts": ["body"]}
            # we prefer the first found intent, as it should be semantic request
            break

    return reply, confidence, human_attr, bot_attr, attr


class GroundingSkillScenario:

    def __init__(self):
        pass

    def __call__(self, dialogs):
        texts = []
        confidences = []
        human_attributes, bot_attributes, attributes = [], [], []
        for dialog in dialogs:
            curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

            bot_attr = {}
            human_attr = dialog["human"]["attributes"]
            human_attr["used_links"] = human_attr.get("used_links", defaultdict(list))
            attr = {}

            # what do you mean response
            reply, confidence = what_do_you_mean_response(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]

            # ACKNOWLEDGEMENT HYPOTHESES for current utterance
            reply, confidence = generate_acknowledgement(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [{}]
                curr_bot_attrs += [{}]
                curr_attrs += [{"response_parts": ["acknowledgement"]}]

            # UNIVERSAL INTENT RESPONSES
            reply, confidence, human_attr, bot_attr, attr = generate_universal_response(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]

            texts.append(curr_responses)
            confidences.append(curr_confidences)
            human_attributes.append(curr_human_attrs)
            bot_attributes.append(curr_bot_attrs)
            attributes.append(curr_attrs)

        return texts, confidences, human_attributes, bot_attributes, attributes
