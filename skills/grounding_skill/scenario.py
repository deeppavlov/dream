import json
import logging
import random
import sentry_sdk
from os import getenv

from common.constants import MUST_CONTINUE
from common.greeting import GREETING_QUESTIONS
from common.link import skills_phrases_map, link_to_skill2key_words
from common.grounding import what_we_talk_about, are_we_recorded, MANY_INTERESTING_QUESTIONS
from common.sensitive import is_sensitive_topic_and_request
from common.universal_templates import is_any_question_sentence_in_utterance
from common.utils import get_topics, get_intents, get_entities, is_toxic_or_blacklisted_utterance, is_no
from utils import (
    MIDAS_INTENT_ACKNOWLEDGMENTS,
    get_midas_intent_acknowledgement,
    reformulate_question_to_statement,
    INTENT_DICT,
    DA_TOPIC_DICT,
    COBOT_TOPIC_DICT,
    get_entity_name,
    get_midas_analogue_intent_for_any_intent,
)

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

SUPER_CONF = 1.0
ALMOST_SUPER_CONF = 0.99
UNIVERSAL_RESPONSE_CONFIDENCE = 0.7
UNIVERSAL_RESPONSE_LOW_CONFIDENCE = 0.6
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

with open("universal_intent_responses.json", "r") as f:
    UNIVERSAL_INTENT_RESPONSES = json.load(f)


def are_we_recorded_response(dialog):
    attr = {}
    human_attr = {}
    bot_attr = {}
    if are_we_recorded(dialog["human_utterances"][-1]):
        reply, confidence = PRIVACY_REPLY, 1
        attr = {"can_continue": MUST_CONTINUE}
    else:
        reply, confidence = "", 0
    return reply, confidence, human_attr, bot_attr, attr


def collect_topics_entities_intents(dialog):
    if len(dialog["human_utterances"]) > 1:
        prev_human_uttr = dialog["human_utterances"][-2]
        intent_list = get_intents(prev_human_uttr, which="cobot_dialogact_intents")
        da_topic_list = get_topics(prev_human_uttr, which="cobot_dialogact_topics")
        cobot_topic_list = get_topics(prev_human_uttr, which="cobot_topics")

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
        what_do_you_mean_intent = (
            dialog["human_utterances"][-1]
            .get("annotations", {})
            .get("intent_catcher", {})
            .get("what_are_you_talking_about", {})
            .get("detected", False)
        )
        # if detect_interrupt(dialog['human_utterances'][-1]['text']):
        #     reply, confidence = REPEAT_PHRASE, SUPER_CONF
        # elif detect_end_but(dialog['human_utterances'][-1]['text']):
        #     reply, confidence = BUT_PHRASE, SUPER_CONF
        # elif detect_end_because(dialog['human_utterances'][-1]['text']):
        #     reply, confidence = BECAUSE_PHRASE, SUPER_CONF
        # elif detect_end_when(dialog['human_utterances'][-1]['text']):
        #     reply, confidence = WHEN_PHRASE, SUPER_CONF
        if not (what_we_talk_about(dialog["human_utterances"][-1]) or what_do_you_mean_intent):
            reply, confidence = "", 0
        elif len(dialog.get("human_utterances", [])) < 2:
            reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
        else:
            # collect prev current intents, topics
            intent_list, da_topic_list, cobot_topic_list = collect_topics_entities_intents(dialog)
            # get prev entity_name
            prev_annotations = (
                dialog["human_utterances"][-2].get("annotations", {}) if len(dialog["human_utterances"]) > 1 else {}
            )
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
                if what_we_talk_about(dialog["human_utterances"][-1]):
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
    """Generate acknowledgement for human questions.

    Returns:
        string acknowledgement (templated acknowledgement from `midas_acknowledgements.json` file,
        confidence (default ACKNOWLEDGEMENT_CONF),
        human attributes (empty),
        bot attributes (empty),
        attributes (with response parts set to acknowledgement)
    """
    curr_intents = get_intents(dialog["human_utterances"][-1], probs=False, which="all")
    curr_intents = list(
        set(
            [
                get_midas_analogue_intent_for_any_intent(intent)
                for intent in curr_intents
                if get_midas_analogue_intent_for_any_intent(intent) is not None
            ]
        )
    )
    curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGMENTS]
    ackn_response = ""
    attr = {}
    human_attr = {}
    bot_attr = {}
    curr_human_entities = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
    contains_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    # we generate acknowledgement ONLY if we have some entities!
    if curr_considered_intents and len(curr_human_entities) and contains_question:
        # can generate acknowledgement
        is_need_nounphrase_intent = any([intent in curr_intents for intent in ["open_question_opinion"]])
        if is_need_nounphrase_intent:
            curr_nounphrase = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
            curr_nounphrase = curr_nounphrase[-1] if len(curr_nounphrase) > 0 and curr_nounphrase[-1] else ""
            if curr_nounphrase:
                ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_nounphrase)
        else:
            # to reformulate question, we take only the last human sentence
            last_human_sent = (
                dialog["human_utterances"][-1]
                .get("annotations", {})
                .get("sentseg", {})
                .get("segments", [dialog["human_utterances"][-1]["text"]])[-1]
            )
            curr_reformulated_question = reformulate_question_to_statement(last_human_sent)
            ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_reformulated_question)
        attr = {"response_parts": ["acknowledgement"]}
    elif contains_question:
        ackn_response = random.choice(MANY_INTERESTING_QUESTIONS)
        attr = {"response_parts": ["acknowledgement"]}
    elif not contains_question and "opinion" in curr_considered_intents:
        ackn_response = get_midas_intent_acknowledgement("opinion", "")

    return ackn_response, ACKNOWLEDGEMENT_CONF, human_attr, bot_attr, attr


def get_unused_response(intent, used_universal_intent_responses):
    available_resps = list(set(UNIVERSAL_INTENT_RESPONSES[intent]).difference(set(used_universal_intent_responses)))
    if available_resps:
        reply = random.choice(available_resps)
    else:
        reply = random.choice(UNIVERSAL_INTENT_RESPONSES[intent])
    return reply


def generate_universal_response(dialog):
    curr_intents = get_intents(dialog["human_utterances"][-1], probs=False, which="all")
    curr_intents = list(
        set(
            [
                get_midas_analogue_intent_for_any_intent(intent)
                for intent in curr_intents
                if get_midas_analogue_intent_for_any_intent(intent) is not None
            ]
        )
    )
    human_attr = {}
    human_attr["grounding_skill"] = dialog["human"]["attributes"].get("grounding_skill", {})
    human_attr["grounding_skill"]["used_universal_intent_responses"] = human_attr["grounding_skill"].get(
        "used_universal_intent_responses", []
    )
    bot_attr = {}
    attr = {}
    reply = ""
    confidence = 0.0
    ackn, _, _, _, _ = generate_acknowledgement(dialog)
    is_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    for intent in curr_intents:
        if intent in UNIVERSAL_INTENT_RESPONSES:
            reply = get_unused_response(intent, human_attr["grounding_skill"]["used_universal_intent_responses"])
            human_attr["grounding_skill"]["used_universal_intent_responses"] += [reply]
            confidence = UNIVERSAL_RESPONSE_CONFIDENCE
            attr = {"response_parts": ["body"], "type": "universal_response"}
            # we prefer the first found intent, as it should be semantic request
            break
    if reply == "":
        if is_question:
            reply = get_unused_response(
                "open_question_opinion", human_attr["grounding_skill"]["used_universal_intent_responses"]
            )
            human_attr["grounding_skill"]["used_universal_intent_responses"] += [reply]
            confidence = UNIVERSAL_RESPONSE_LOW_CONFIDENCE
            attr = {"response_parts": ["body"], "type": "universal_response"}
    if is_question and is_sensitive_topic_and_request(dialog["human_utterances"][-1]):
        # if question in sensitive situation - answer with confidence 0.99
        confidence = ALMOST_SUPER_CONF
    if ackn and not is_toxic_or_blacklisted_utterance(dialog["human_utterances"][-1]):
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
    confidence = 0.0
    attr = {}
    human_attr = {}
    bot_attr = {}
    if prev_was_linkto and prev_prev_was_linkto and human_is_no and prev_human_is_no:
        offer = random.choice(GREETING_QUESTIONS["what_to_talk_about"])
        topics_to_offer = ", ".join(sum(link_to_skill2key_words.values(), []))
        reply = f"Okay then. {offer} {topics_to_offer}?"
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
            is_toxic = (
                is_toxic_or_blacklisted_utterance(dialog["human_utterances"][-2])
                if len(dialog["human_utterances"]) > 1
                else False
            )

            reply, confidence, human_attr, bot_attr, attr = are_we_recorded_response(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"Grounding skill are_we_recorded: {reply}")

            reply, confidence, human_attr, bot_attr, attr = what_do_you_mean_response(dialog)
            if reply and confidence and not is_toxic:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"Grounding skill what_do_you_mean: {reply}")

            # ACKNOWLEDGEMENT HYPOTHESES for current utterance
            reply, confidence, human_attr, bot_attr, attr = generate_acknowledgement(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"Grounding skill acknowledgement: {reply}")

            # UNIVERSAL INTENT RESPONSES
            reply, confidence, human_attr, bot_attr, attr = generate_universal_response(dialog)
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"Grounding skill universal_response: {reply}")

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
