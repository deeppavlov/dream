import logging
import random
import sentry_sdk
from os import getenv
from typing import Any, Tuple

from df_engine.core import Actor, Context
import common.dff.integration.response as int_rsp
from common.constants import MUST_CONTINUE, CAN_NOT_CONTINUE
from common.greeting import GREETING_QUESTIONS
from common.link import link_to_skill2key_words
from common.grounding import what_we_talk_about, are_we_recorded, MANY_INTERESTING_QUESTIONS
from common.sensitive import is_sensitive_topic_and_request
from common.universal_templates import is_any_question_sentence_in_utterance
from common.utils import get_entities, is_toxic_or_badlisted_utterance, is_no

from .utils import MIDAS_INTENT_ACKNOWLEDGEMENTS, get_midas_intent_acknowledgement
from .responses_utils import (
    PRIVACY_REPLY,
    DONTKNOW_PHRASE,
    SUPER_CONF,
    ALMOST_SUPER_CONF,
    UNIVERSAL_RESPONSE_CONF,
    UNIVERSAL_RESPONSE_LOW_CONF,
    ACKNOWLEDGEMENT_CONF,
    DONTKNOW_CONF,
    LINKTO_QUESTIONS_LOWERCASED,
    UNIVERSAL_INTENT_RESPONSES,
)
from .responses_utils import (
    get_what_do_you_mean_intent,
    get_bot_based_on_skill_reply,
    get_current_intents,
    generate_acknowledgement,
    get_unused_reply,
    get_bot_based_on_topic_or_intent_reply,
)

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGE = getenv("LANGUAGE", "EN")
REPLY_TYPE = Tuple[str, float, dict, dict, dict]


def grounding_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

    def gathering_responses(reply, confidence, human_attr, bot_attr, attr, name):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]
            logger.info(f"Grounding skill {name}: {reply}")

    if "agent" in ctx.misc:
        dialog = ctx.misc["agent"]["dialog"]

        is_toxic = (
            is_toxic_or_badlisted_utterance(dialog["human_utterances"][-2])  # ???
            if len(dialog["human_utterances"]) > 1
            else False
        )
        reply, confidence, human_attr, bot_attr, attr = are_we_recorded_response(ctx)
        gathering_responses(reply, confidence, human_attr, bot_attr, attr, "are_we_recorded")

        if not is_toxic:
            reply, confidence, human_attr, bot_attr, attr = what_do_you_mean_response(ctx)
            gathering_responses(reply, confidence, human_attr, bot_attr, attr, "what_do_you_mean")

        reply, confidence, human_attr, bot_attr, attr = generate_acknowledgement_response(ctx)
        gathering_responses(reply, confidence, human_attr, bot_attr, attr, "acknowledgement_response")

        reply, confidence, human_attr, bot_attr, attr = generate_universal_response(ctx)
        gathering_responses(reply, confidence, human_attr, bot_attr, attr, "universal_response")

        reply, confidence, human_attr, bot_attr, attr = ask_for_topic_after_two_no_in_a_row_to_linkto_response(ctx)
        gathering_responses(reply, confidence, human_attr, bot_attr, attr, '2 "no" detected')

    # to pass assert  "Got empty replies"
    if len(curr_responses) == 0:
        gathering_responses(" ", 0.01, {}, {}, {}, "empty_response")
    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)


def are_we_recorded_response(ctx: Context) -> REPLY_TYPE:
    """
    Returns:
        reply PRIVACY_REPLY or (empty),
        confidence 1.0 or 0.0,
        human attributes (empty),
        bot attributes (empty),
        attributes MUST_CONTINUE or (empty)
    """
    last_human_utterance = ctx.last_request
    if are_we_recorded(last_human_utterance):
        reply, confidence = PRIVACY_REPLY, 1
        attr = {"can_continue": MUST_CONTINUE}
    else:
        reply, confidence = "", 0
        attr = {"can_continue": CAN_NOT_CONTINUE}
    logger.info(f"are_we_recorded_response: {reply} + {attr}")
    return reply, confidence, {}, {}, attr


def what_do_you_mean_response(ctx: Context) -> REPLY_TYPE:
    """Generate response when we are asked about subject of the dialog
    Returns:
        template phrase based on previous skill or intent or topic
        confidence (can be 0.0, DONTKNOW_CONF, UNIVERSAL_RESPONSE_CONF, SUPER_CONF)
        human attributes (empty),
        bot attributes (empty),
        attributes (empty or MUST_CONTINUE)
    """
    dialog = ctx.misc["agent"]["dialog"]
    attr = {"can_continue": CAN_NOT_CONTINUE}
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
                    dialog["human_utterances"][-2] if len(dialog["human_utterances"]) > 1 else {}
                )
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

    logger.info(f"what_do_you_mean_response: {reply} + {attr}")
    return reply, confidence, {}, {}, attr


def generate_acknowledgement_response(ctx: Context) -> REPLY_TYPE:
    """Generate acknowledgement for human questions.

    Returns:
        string acknowledgement (templated acknowledgement from `midas_acknowledgements.json` file,
        confidence (default ACKNOWLEDGEMENT_CONF),
        human attributes (empty),
        bot attributes (empty),
        attributes (with response parts set to acknowledgement)
    """
    dialog = ctx.misc["agent"]["dialog"]
    curr_intents = get_current_intents(dialog["human_utterances"][-1])
    curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGEMENTS]
    attr = {}
    ackn_response = ""
    curr_human_entities = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
    contains_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    # we generate acknowledgement ONLY if we have some entities!
    if curr_considered_intents and len(curr_human_entities) and contains_question:
        # can generate acknowledgement
        ackn_response = generate_acknowledgement(dialog["human_utterances"][-1], curr_intents, curr_considered_intents)
        attr = {"response_parts": ["acknowledgement"]}
    elif contains_question:
        ackn_response = random.choice(MANY_INTERESTING_QUESTIONS)
        attr = {"response_parts": ["acknowledgement"]}
    elif not contains_question and "opinion" in curr_considered_intents:
        ackn_response = get_midas_intent_acknowledgement("opinion", "")
        attr = {"response_parts": ["acknowledgement"]}

    attr["can_continue"] = CAN_NOT_CONTINUE
    logger.info(f"generate_acknowledgement_response: {ackn_response} + {attr}")
    return ackn_response, ACKNOWLEDGEMENT_CONF, {}, {}, attr


def generate_universal_response(ctx: Context) -> REPLY_TYPE:
    """
    Returns:
      string from universal_intent_responses file filtered with intent,
      confidence (can be UNIVERSAL_RESPONSE_CONF, UNIVERSAL_RESPONSE_LOW_CONF, ALMOST_SUPER_CONF),
      human attributes (used universal intent responses), # for now not used
      bot attributes (empty),
      attributes (response parts)
    """
    dialog = ctx.misc["agent"]["dialog"]
    curr_intents = get_current_intents(dialog["human_utterances"][-1])
    # currently unused this part because it's specific formatter need to be implemented
    human_attr = {}
    human_attr["dff_grounding_skill"] = ctx.misc.get("dff_grounding_skill", {})
    human_attr["dff_grounding_skill"]["used_universal_intent_responses"] = human_attr["dff_grounding_skill"].get(
        "used_universal_intent_responses", []
    )
    reply = ""
    confidence = 0.0
    ackn, _, _, _, attr = generate_acknowledgement_response(ctx)
    is_question = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])

    def universal_response(intent):
        nonlocal reply, human_attr, attr
        # for now return random reply UNIVERSAL_INTENT_RESPONSES
        reply = get_unused_reply(intent, human_attr["dff_grounding_skill"]["used_universal_intent_responses"])
        human_attr["dff_grounding_skill"]["used_universal_intent_responses"] += [reply]
        attr = {"can_continue": CAN_NOT_CONTINUE, "response_parts": ["body"], "type": "universal_response"}
        return reply, attr

    ctx.misc["dff_grounding_skill"] = human_attr["dff_grounding_skill"]

    for intent in curr_intents:
        if intent in UNIVERSAL_INTENT_RESPONSES:
            reply, attr = universal_response(intent)
            confidence = UNIVERSAL_RESPONSE_CONF
            # we prefer the first found intent, as it should be semantic request
            break
    if reply == "":
        if is_question:
            reply, attr = universal_response("open_question_opinion")
            confidence = UNIVERSAL_RESPONSE_LOW_CONF
    if is_question and is_sensitive_topic_and_request(dialog["human_utterances"][-1]):
        # if question in sensitive situation - answer with confidence 0.99
        confidence = ALMOST_SUPER_CONF
    if ackn and not is_toxic_or_badlisted_utterance(dialog["human_utterances"][-1]):
        reply = f"{ackn} {reply}"
        attr["response_parts"] = ["acknowledgement", "body"]

    attr["can_continue"] = CAN_NOT_CONTINUE
    logger.info(f"generate_universal_response: {reply} + {attr}")
    return reply, confidence, human_attr, {}, attr


def ask_for_topic_after_two_no_in_a_row_to_linkto_response(ctx: Context) -> REPLY_TYPE:
    """
    Returns:
        greeting phrase - suggesting topics to talk about,
        confidence (0.0 or SUPER_CONF),
        human attributes (empty),
        bot attributes (empty),
        attributes (empty of MUST_CONTINUE)
    """
    dialog = ctx.misc["agent"]["dialog"]
    prev_bot_uttr = dialog["bot_utterances"][-1]["text"].lower() if len(dialog["bot_utterances"]) else ""
    prev_prev_bot_uttr = dialog["bot_utterances"][-2]["text"].lower() if len(dialog["bot_utterances"]) > 1 else ""
    prev_was_linkto = any([question in prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    prev_prev_was_linkto = any([question in prev_prev_bot_uttr for question in LINKTO_QUESTIONS_LOWERCASED])
    human_is_no = is_no(dialog["human_utterances"][-1])
    prev_human_is_no = is_no(dialog["human_utterances"][-2] if len(dialog["human_utterances"]) > 1 else {})

    reply = ""
    confidence = 0.0
    attr = {"can_continue": CAN_NOT_CONTINUE}
    if prev_was_linkto and prev_prev_was_linkto and human_is_no and prev_human_is_no:
        offer = random.choice(GREETING_QUESTIONS[LANGUAGE]["what_to_talk_about"])
        topics_to_offer = ", ".join(sum(link_to_skill2key_words.values(), []))
        reply = f"Okay then. {offer} {topics_to_offer}?"
        confidence = SUPER_CONF
        attr = {"can_continue": MUST_CONTINUE}
    logger.info(f"ask_for_topic_after_two_no_in_a_row_to_linkto_response: {reply} + {attr}")
    return reply, confidence, {}, {}, attr
