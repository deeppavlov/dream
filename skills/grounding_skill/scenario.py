import json
import logging
import random
import sentry_sdk
from os import getenv

from common.constants import MUST_CONTINUE
from common.greeting import GREETING_QUESTIONS
from common.link import skills_phrases_map
from common.grounding import what_we_talk_about
from common.universal_templates import is_any_question_sentence_in_utterance
from common.utils import get_topics, get_intents, get_entities, get_toxic, is_no
from utils import MIDAS_INTENT_ACKNOWLEDGMENETS, get_midas_intent_acknowledgement, reformulate_question_to_statement, \
    INTENT_DICT, DA_TOPIC_DICT, COBOT_TOPIC_DICT, get_entity_name

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SUPER_CONF = 1.
UNIVERSAL_RESPONSE_CONFIDENCE = 0.7
UNIVERSAL_RESPONSE_LOW_CONFIDENCE = 0.6
DONTKNOW_CONF = 0.5
ACKNOWLEDGEMENT_CONF = 0.5
DONTKNOW_PHRASE = "Seems like I have no idea what we are talking about."

INTENTS_BY_POPULARITY = list(INTENT_DICT.keys())[::-1]
DA_TOPICS_BY_POPULARITY = list(DA_TOPIC_DICT.keys())[::-1]
COBOT_TOPICS_BY_POPULARITY = list(COBOT_TOPIC_DICT.keys())[::-1]
LINKTO_QUESTIONS_LOWERCASED = [question.lower() for set_of_quests in skills_phrases_map.values()
                               for question in set_of_quests]

with open("universal_intent_responses.json", "r") as f:
    UNIVERSAL_INTENT_RESPONSES = json.load(f)


def collect_topics_entities_intents(dialog):
    if len(dialog['human_utterances']) > 1:
        prev_human_uttr = dialog['human_utterances'][-2]
        intent_list = get_intents(prev_human_uttr, which='cobot_dialogact_intents')
        da_topic_list = get_topics(prev_human_uttr, which='cobot_dialogact_topics')
        cobot_topic_list = get_topics(prev_human_uttr, which='cobot_topics')

        intent_list = list(set(intent_list))
        da_topic_list = list(set(da_topic_list))
        cobot_topic_list = list(set(cobot_topic_list))
    else:
        intent_list, da_topic_list, cobot_topic_list = [], [], []

    return intent_list, da_topic_list, cobot_topic_list


def what_do_you_mean_response(dialog):
    attr = {}
    human_attr = {}
    bot_attr = {}
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
            # collect prev current intents, topics
            intent_list, da_topic_list, cobot_topic_list = collect_topics_entities_intents(dialog)
            # get prev entity_name
            prev_annotations = dialog['human_utterances'][-2].get(
                'annotations', {}) if len(dialog['human_utterances']) > 1 else {}
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
                if what_we_talk_about(dialog['human_utterances'][-1]):
                    confidence = SUPER_CONF
                    attr = {"can_continue": MUST_CONTINUE}
                else:
                    # what_do_you_mean_intent but not regexp
                    confidence = UNIVERSAL_RESPONSE_CONFIDENCE
                    attr = {}
    except Exception as e:
        logger.exception("exception in grounding skill")
        logger.info(str(e))
        sentry_sdk.capture_exception(e)
        reply = ""
        confidence = 0

    return reply, confidence, human_attr, bot_attr, attr


def generate_acknowledgement(dialog):
    curr_intents = get_intents(dialog['human_utterances'][-1], probs=False, which='midas')
    curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGMENETS]
    ackn_response = ""
    attr = {}
    human_attr = {}
    bot_attr = {}

    if curr_considered_intents:
        # can generate acknowledgement
        is_need_nounphrase_intent = any([intent in curr_intents for intent in ["open_question_opinion"]])
        if is_need_nounphrase_intent:
            curr_nounphrase = get_entities(dialog['human_utterances'][-1], only_named=False, with_labels=False)
            curr_nounphrase = curr_nounphrase[-1] if len(curr_nounphrase) > 0 and curr_nounphrase[-1] else ""
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_nounphrase)
        else:
            curr_reformulated_question = reformulate_question_to_statement(
                dialog['human_utterances'][-1]["text"])
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1],
                                                             curr_reformulated_question)
        attr = {"response_parts": ["acknowledgement"]}
    return ackn_response, ACKNOWLEDGEMENT_CONF, human_attr, bot_attr, attr


def get_unused_response(intent, used_universal_intent_responses):
    available_resps = list(set(UNIVERSAL_INTENT_RESPONSES[intent]).difference(set(used_universal_intent_responses)))
    if available_resps:
        reply = random.choice(available_resps)
    else:
        reply = random.choice(UNIVERSAL_INTENT_RESPONSES[intent])
    return reply


def generate_universal_response(dialog):
    curr_intents = get_intents(dialog['human_utterances'][-1], probs=False, which='midas')
    human_attr = {}
    human_attr["grounding_skill"] = dialog["human"]["attributes"].get("grounding_skill", {})
    human_attr["grounding_skill"]["used_universal_intent_responses"] = human_attr["grounding_skill"].get(
        "used_universal_intent_responses", [])
    bot_attr = {}
    attr = {}
    reply = ""
    confidence = 0.
    ackn, _, _, _, _ = generate_acknowledgement(dialog)

    for intent in curr_intents:
        if intent in UNIVERSAL_INTENT_RESPONSES:
            reply = get_unused_response(intent, human_attr["grounding_skill"]["used_universal_intent_responses"])
            human_attr["grounding_skill"]["used_universal_intent_responses"] += [reply]
            confidence = UNIVERSAL_RESPONSE_CONFIDENCE
            attr = {"response_parts": ["body"], "type": "universal_response"}
            # we prefer the first found intent, as it should be semantic request
            break
    if reply == "":
        if is_any_question_sentence_in_utterance(dialog['human_utterances'][-1]):
            reply = get_unused_response("open_question_opinion",
                                        human_attr["grounding_skill"]["used_universal_intent_responses"])
            human_attr["grounding_skill"]["used_universal_intent_responses"] += [reply]
            confidence = UNIVERSAL_RESPONSE_LOW_CONFIDENCE
            attr = {"response_parts": ["body"], "type": "universal_response"}
    if ackn and reply:
        reply = f"{ackn} {reply}"
        attr["response_parts"] = ["acknowlegdement", "body"]
    return reply, confidence, human_attr, bot_attr, attr


def ask_for_topic_after_two_no_in_a_row_to_linkto(dialog):
    prev_bot_uttr = dialog["bot_utterances"][-1]["text"].lower() if len(dialog["bot_utterances"]) else ""
    prev_prev_bot_uttr = dialog["bot_utterances"][-2]["text"].lower() if len(dialog["bot_utterances"]) > 1 else ""
    prev_was_linkto = any([question in prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    prev_prev_was_linkto = any([question in prev_prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    human_is_no = is_no(dialog["human_utterances"][-1])
    prev_human_is_no = is_no(dialog["human_utterances"][-2] if len(dialog["human_utterances"]) > 1 else {})

    reply = ""
    confidence = 0.
    attr = {}
    human_attr = {}
    bot_attr = {}
    if prev_was_linkto and prev_prev_was_linkto and human_is_no and prev_human_is_no:
        offer = random.choice(GREETING_QUESTIONS["what_to_talk_about"])
        reply = f"Okay then. {offer}"
        confidence = SUPER_CONF
        attr = {"can_continue": MUST_CONTINUE}
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

            # what do you mean response
            if len(dialog['human_utterances']) > 1:
                prev_human_uttr = dialog['human_utterances'][-2]
                toxic_result = get_toxic(prev_human_uttr, probs=False)
                default_blacklist = {'inappropriate': False, 'profanity': False, 'restricted_topics': False}
                blacklist_result = prev_human_uttr.get("annotations", {}).get('blacklisted_words', default_blacklist)
                is_toxic = toxic_result or blacklist_result['profanity'] or blacklist_result['inappropriate']
            else:
                is_toxic = False

            reply, confidence, human_attr, bot_attr, attr = what_do_you_mean_response(dialog)
            if reply and confidence and not is_toxic:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f'Grounding skill what_do_you_mean: {reply}')

            # ACKNOWLEDGEMENT HYPOTHESES for current utterance
            # reply, confidence, human_attr, bot_attr, attr = generate_acknowledgement(dialog)
            # if reply and confidence:
            #     curr_responses += [reply]
            #     curr_confidences += [confidence]
            #     curr_human_attrs += [human_attr]
            #     curr_bot_attrs += [bot_attr]
            #     curr_attrs += [attr]
            #     logger.info(f'Grounding skill acknowledgement: {reply}')

            # UNIVERSAL INTENT RESPONSES
            reply, confidence, human_attr, bot_attr, attr = generate_universal_response(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f'Grounding skill universal_response: {reply}')

            # two 'no' in a row to linkto questions
            reply, confidence, human_attr, bot_attr, attr = ask_for_topic_after_two_no_in_a_row_to_linkto(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f'Grounding skill 2 "no" detected: {reply}')

            texts.append(curr_responses)
            confidences.append(curr_confidences)
            human_attributes.append(curr_human_attrs)
            bot_attributes.append(curr_bot_attrs)
            attributes.append(curr_attrs)

        return texts, confidences, human_attributes, bot_attributes, attributes
