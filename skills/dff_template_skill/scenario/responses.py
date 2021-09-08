import logging
import random
import sentry_sdk
from os import getenv

from common.constants import MUST_CONTINUE
from common.greeting import GREETING_QUESTIONS
from common.link import link_to_skill2key_words
from common.grounding import what_we_talk_about, are_we_recorded, MANY_INTERESTING_QUESTIONS
from common.sensitive import is_sensitive_topic_and_request
from common.universal_templates import is_any_question_sentence_in_utterance
from common.utils import get_entities, is_toxic_or_blacklisted_utterance, is_no

from .utils import MIDAS_INTENT_ACKNOWLEDGMENTS, get_midas_intent_acknowledgement

from .responses_utils import (PRIVACY_REPLY,
                              DONTKNOW_PHRASE,
                              SUPER_CONF,
                              ALMOST_SUPER_CONF,
                              UNIVERSAL_RESPONSE_CONF,
                              UNIVERSAL_RESPONSE_LOW_CONF,
                              ACKNOWLEDGEMENT_CONF,
                              DONTKNOW_CONF,
                              LINKTO_QUESTIONS_LOWERCASED,
                              UNIVERSAL_INTENT_RESPONSES)
from .responses_utils import get_what_do_you_mean_intent, get_bot_based_on_skill_reply, get_current_intents, \
    generate_acknowledgement, get_unused_reply, get_bot_based_on_topic_or_intent_reply

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def are_we_recorded_response(dialog):
    """
      Returns:
          reply PRIVACY_REPLY or (empty),
          confidence 1.0 or 0.0,
          human attributes (empty),
          bot attributes (empty),
          attributes MUST_CONTINUE or (empty)
      """
    attr = {}
    if are_we_recorded(dialog["human_utterances"][-1]):
        reply, confidence = PRIVACY_REPLY, 1
        attr = {"can_continue": MUST_CONTINUE}
    else:
        reply, confidence = "", 0
    return reply, confidence, {}, {}, attr


def what_do_you_mean_response(dialog):
    """Generate response when we are asked about subject of the dialog
      Returns:
          template phrase based on previous skill or intent or topic
          confidence (can be 0.0, DONTKNOW_CONF, UNIVERSAL_RESPONSE_CONF, SUPER_CONF)
          human attributes (empty),
          bot attributes (empty),
          attributes (empty or MUST_CONTINUE)
      """
    attr = {}
    try:
        what_do_you_mean_intent = get_what_do_you_mean_intent(dialog["human_utterances"][-1])
        if not (what_we_talk_about(dialog["human_utterances"][-1]) or what_do_you_mean_intent):
            reply, confidence = "", 0
        elif len(dialog.get("human_utterances", [])) < 2:
            reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
        else:
            reply = get_bot_based_on_skill_reply(dialog.get("bot_utterances", []))
            if reply is None:
                reply = get_bot_based_on_topic_or_intent_reply(
                    dialog["human_utterances"][-2] if len(dialog["human_utterances"]) > 1 else [])
            if reply is None:
                reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
            else:
                if what_we_talk_about(dialog["human_utterances"][-1]):
                    confidence = SUPER_CONF
                    attr = {"can_continue": MUST_CONTINUE}
                else:
                    # what_do_you_mean_intent but not regexp
                    confidence = UNIVERSAL_RESPONSE_CONF
    except Exception as e:
        logger.exception("exception in grounding skill")
        logger.info(str(e))
        sentry_sdk.capture_exception(e)
        reply = ""
        confidence = 0

    return reply, confidence, {}, {}, attr


def generate_acknowledgement_response(dialog):
    """Generate acknowledgement for human questions.

    Returns:
        string acknowledgement (templated acknowledgement from `midas_acknowledgements.json` file,
        confidence (default ACKNOWLEDGEMENT_CONF),
        human attributes (empty),
        bot attributes (empty),
        attributes (with response parts set to acknowledgement)
    """
    curr_intents = get_current_intents(dialog["human_utterances"][-1])
    curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGMENTS]

    ackn_response = ""
    attr = {}
    curr_human_entities = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
    contains_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    # we generate acknowledgement ONLY if we have some entities!
    if curr_considered_intents and len(curr_human_entities) and contains_question:
        # can generate acknowledgement
        ackn_response, attr = generate_acknowledgement(dialog["human_utterances"][-1],
                                                       curr_intents,
                                                       curr_considered_intents)
    elif contains_question:
        ackn_response = random.choice(MANY_INTERESTING_QUESTIONS)
        attr = {"response_parts": ["acknowledgement"]}
    elif not contains_question and "opinion" in curr_considered_intents:
        ackn_response = get_midas_intent_acknowledgement("opinion", "")

    return ackn_response, ACKNOWLEDGEMENT_CONF, {}, {}, attr


def generate_universal_response(dialog):
    """
        Returns:
          string from universal_intent_responses file filtered with intent, 
          confidence (can be UNIVERSAL_RESPONSE_CONF, UNIVERSAL_RESPONSE_LOW_CONF, ALMOST_SUPER_CONF),
          human attributes (used universal intent responses), # for now not used
          bot attributes (empty),
          attributes (response parts)
      """
    curr_intents = get_current_intents(dialog["human_utterances"][-1])
    # currently unused this part because it's specific formatter need to be implemented
    human_attr = {}
    human_attr["grounding_skill"] = {}  # dialog["human"]["attributes"].get("grounding_skill", {})
    human_attr["grounding_skill"]["used_universal_intent_responses"] = []  # human_attr["grounding_skill"].get(
    #     "used_universal_intent_responses", []
    # )
    attr = {}
    reply = ""
    confidence = 0.0
    ackn, _, _, _, _ = generate_acknowledgement_response(dialog)
    is_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    def universal_response(intent):
        nonlocal reply, human_attr, attr
        # for now return random reply UNIVERSAL_INTENT_RESPONSES
        reply = get_unused_reply(intent, human_attr["grounding_skill"]["used_universal_intent_responses"])
        human_attr["grounding_skill"]["used_universal_intent_responses"] += [reply]
        attr = {"response_parts": ["body"], "type": "universal_response"}

    for intent in curr_intents:
        if intent in UNIVERSAL_INTENT_RESPONSES:
            universal_response(intent)
            confidence = UNIVERSAL_RESPONSE_CONF
            # we prefer the first found intent, as it should be semantic request
            break
    if reply == "":
        if is_question:
            universal_response("open_question_opinion")
            confidence = UNIVERSAL_RESPONSE_LOW_CONF
    if is_question and is_sensitive_topic_and_request(dialog["human_utterances"][-1]):
        # if question in sensitive situation - answer with confidence 0.99
        confidence = ALMOST_SUPER_CONF
    if ackn and not is_toxic_or_blacklisted_utterance(dialog["human_utterances"][-1]):
        reply = f"{ackn} {reply}"
        attr["response_parts"] = ["acknowlegdement", "body"]
    return reply, confidence, human_attr, {}, attr


def ask_for_topic_after_two_no_in_a_row_to_linkto_response(dialog):
    """
      Returns:
          greeting phrase - suggesting topics to talk about,
          confidence (0.0 or SUPER_CONF),
          human attributes (empty),
          bot attributes (empty),
          attributes (empty of MUST_CONTINUE)
      """
    prev_bot_uttr = dialog["bot_utterances"][-1]["text"].lower() if len(dialog["bot_utterances"]) else ""
    prev_prev_bot_uttr = dialog["bot_utterances"][-2]["text"].lower() if len(dialog["bot_utterances"]) > 1 else ""
    prev_was_linkto = any([question in prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    prev_prev_was_linkto = any([question in prev_prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    human_is_no = is_no(dialog["human_utterances"][-1])
    prev_human_is_no = is_no(dialog["human_utterances"][-2] if len(dialog["human_utterances"]) > 1 else {})

    reply = ""
    confidence = 0.0
    attr = {}
    if prev_was_linkto and prev_prev_was_linkto and human_is_no and prev_human_is_no:
        offer = random.choice(GREETING_QUESTIONS["what_to_talk_about"])
        topics_to_offer = ", ".join(sum(link_to_skill2key_words.values(), []))
        reply = f"Okay then. {offer} {topics_to_offer}?"
        confidence = SUPER_CONF
        attr = {"can_continue": MUST_CONTINUE}
    return reply, confidence, {}, {}, attr
