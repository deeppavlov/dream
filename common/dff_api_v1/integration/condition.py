import logging
import re

from nltk.stem import WordNetLemmatizer

from dff.script import Context
from dff.pipeline import Pipeline

import common.greeting as common_greeting
import common.utils as common_utils
import common.universal_templates as universal_templates
import common.dff_api_v1.integration.context as int_ctx
from common.acknowledgements import GENERAL_ACKNOWLEDGEMENTS
from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from .facts_utils import provide_facts_request

logger = logging.getLogger(__name__)

wnl = WordNetLemmatizer()


#  vars is described in README.md


def was_clarification_request(ctx: Context, _) -> bool:
    flag = ctx.misc["agent"]["clarification_request_flag"] if not ctx.validation else False
    logger.debug(f"was_clarification_request = {flag}")
    return bool(flag)


def is_opinion_request(ctx: Context, pipeline: Pipeline) -> bool:
    flag = common_utils.is_opinion_request(int_ctx.get_last_human_utterance(ctx, pipeline))
    logger.debug(f"is_opinion_request = {flag}")
    return bool(flag)


def is_opinion_expression(ctx: Context, pipeline: Pipeline) -> bool:
    flag = common_utils.is_opinion_expression(int_ctx.get_last_human_utterance(ctx, pipeline))
    logger.debug(f"is_opinion_expression = {flag}")
    return bool(flag)


def is_previous_turn_dff_suspended(ctx: Context, _) -> bool:
    flag = ctx.misc["agent"].get("previous_turn_dff_suspended", False) if not ctx.validation else False
    logger.debug(f"is_previous_turn_dff_suspended = {flag}")
    return bool(flag)


def is_current_turn_dff_suspended(ctx: Context, _) -> bool:
    flag = ctx.misc["agent"].get("current_turn_dff_suspended", False) if not ctx.validation else False
    logger.debug(f"is_current_turn_dff_suspended = {flag}")
    return bool(flag)


def is_switch_topic(ctx: Context, pipeline: Pipeline) -> bool:
    flag = universal_templates.is_switch_topic(int_ctx.get_last_human_utterance(ctx, pipeline))
    logger.debug(f"is_switch_topic = {flag}")
    return bool(flag)


def is_question(ctx: Context, pipeline: Pipeline) -> bool:
    text = int_ctx.get_last_human_utterance(ctx, pipeline)["text"]
    flag = common_utils.is_question(text)
    logger.debug(f"is_question = {flag}")
    return bool(flag)


def is_lets_chat_about_topic_human_initiative(ctx: Context, pipeline: Pipeline) -> bool:
    flag = universal_templates.if_chat_about_particular_topic(
        int_ctx.get_last_human_utterance(ctx, pipeline), int_ctx.get_last_bot_utterance(ctx, pipeline)
    )
    logger.debug(f"is_lets_chat_about_topic_human_initiative = {flag}")
    return bool(flag)


def is_lets_chat_about_topic(ctx: Context, pipeline: Pipeline) -> bool:
    flag = is_lets_chat_about_topic_human_initiative(ctx, pipeline)

    last_human_uttr = int_ctx.get_last_human_utterance(ctx, pipeline)
    last_bot_uttr_text = int_ctx.get_last_bot_utterance(ctx, pipeline)["text"]
    is_bot_initiative = bool(re.search(universal_templates.COMPILE_WHAT_TO_TALK_ABOUT, last_bot_uttr_text))
    flag = flag or (is_bot_initiative and not common_utils.is_no(last_human_uttr))
    logger.debug(f"is_lets_chat_about_topic = {flag}")
    return bool(flag)


def is_begin_of_dialog(ctx: Context, pipeline: Pipeline, begin_dialog_n=10) -> bool:
    flag = int_ctx.get_human_utter_index(ctx, pipeline) < begin_dialog_n
    logger.debug(f"is_begin_of_dialog = {flag}")
    return bool(flag)


def is_interrupted(ctx: Context, pipeline: Pipeline) -> bool:
    flag = (
        int_ctx.get_human_utter_index(ctx, pipeline) - int_ctx.get_previous_human_utter_index(ctx, pipeline)
    ) != 1 and not was_clarification_request(ctx, pipeline)
    logger.debug(f"is_interrupted = {flag}")
    return bool(flag)


def is_long_interrupted(ctx: Context, pipeline: Pipeline, how_long=3) -> bool:
    flag = (
        int_ctx.get_human_utter_index(ctx, pipeline) - int_ctx.get_previous_human_utter_index(ctx, pipeline)
    ) > how_long and not was_clarification_request(ctx, pipeline)
    logger.debug(f"is_long_interrupted = {flag}")
    return bool(flag)


def is_new_human_entity(ctx: Context, pipeline: Pipeline) -> bool:
    new_entities = int_ctx.get_new_human_labeled_noun_phrase(ctx, pipeline)
    flag = bool(new_entities)
    logger.debug(f"is_new_human_entity = {flag}")
    return bool(flag)


def is_last_state(ctx: Context, pipeline: Pipeline, state) -> bool:
    flag = False
    if not ctx.validation:
        history = list(int_ctx.get_history(ctx, pipeline).items())
        if history:
            history_sorted = sorted(history, key=lambda x: x[0])
            last_state = history_sorted[-1][1]
            if last_state == state:
                flag = True
    return bool(flag)


def is_first_time_of_state(ctx: Context, pipeline: Pipeline, state) -> bool:
    flag = state not in list(int_ctx.get_history(ctx, pipeline).values())
    logger.debug(f"is_first_time_of_state {state} = {flag}")
    return bool(flag)


def if_was_prev_active(ctx: Context, pipeline: Pipeline) -> bool:
    flag = False
    skill_uttr_indices = set(int_ctx.get_history(ctx, pipeline).keys())
    if not ctx.validation:
        human_uttr_index = str(ctx.misc["agent"]["human_utter_index"] - 1)
        if human_uttr_index in skill_uttr_indices:
            flag = True
    return bool(flag)


def is_plural(word) -> bool:
    lemma = wnl.lemmatize(word, "n")
    plural = True if word is not lemma else False
    return plural


def is_first_our_response(ctx: Context, pipeline: Pipeline) -> bool:
    flag = len(list(int_ctx.get_history(ctx, pipeline).values())) == 0
    logger.debug(f"is_first_our_response = {flag}")
    return bool(flag)


def is_no_human_abandon(ctx: Context, pipeline: Pipeline) -> bool:
    """Is dialog breakdown in human utterance or no. Uses MIDAS hold/abandon classes."""
    midas_classes = common_utils.get_intents(int_ctx.get_last_human_utterance(ctx, pipeline), which="midas")
    if "abandon" not in midas_classes:
        return True
    return False


def no_special_switch_off_requests(ctx: Context, pipeline: Pipeline) -> bool:
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    """
    intents_by_catcher = common_utils.get_intents(
        int_ctx.get_last_human_utterance(ctx, pipeline), probs=False, which="intent_catcher"
    )
    is_high_priority_intent = any([intent not in common_utils.service_intents for intent in intents_by_catcher])
    is_switch = is_switch_topic(ctx, pipeline)
    is_lets_chat = is_lets_chat_about_topic_human_initiative(ctx, pipeline)

    if not (is_high_priority_intent or is_switch or is_lets_chat):
        return True
    return False


def no_requests(ctx: Context, pipeline: Pipeline) -> bool:
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    - user didn't requested any special intents
    - user didn't ask questions
    """
    contain_no_special_requests = no_special_switch_off_requests(ctx, pipeline)

    request_intents = [
        "opinion_request",
        "topic_switching",
        "lets_chat_about",
        "what_are_you_talking_about",
        "Information_RequestIntent",
        "Topic_SwitchIntent",
        "Opinion_RequestIntent",
    ]
    intents = common_utils.get_intents(int_ctx.get_last_human_utterance(ctx, pipeline), which="all")
    is_not_request_intent = all([intent not in request_intents for intent in intents])
    is_no_question = "?" not in int_ctx.get_last_human_utterance(ctx, pipeline)["text"]

    if contain_no_special_requests and is_not_request_intent and is_no_question:
        return True
    return False


def is_yes_vars(ctx: Context, pipeline: Pipeline) -> bool:
    flag = True
    flag = flag and common_utils.is_yes(int_ctx.get_last_human_utterance(ctx, pipeline))
    return bool(flag)


def is_no_vars(ctx: Context, pipeline: Pipeline) -> bool:
    flag = True
    flag = flag and common_utils.is_no(int_ctx.get_last_human_utterance(ctx, pipeline))
    return bool(flag)


def is_do_not_know_vars(ctx: Context, pipeline: Pipeline) -> bool:
    flag = True
    flag = flag and common_utils.is_donot_know(int_ctx.get_last_human_utterance(ctx, pipeline))
    return bool(flag)


def is_passive_user(ctx: Context, pipeline: Pipeline, passive_threshold=3, history_len=2) -> bool:
    """Check history_len last human utterances on the number of tokens.
    If number of tokens in ALL history_len uterances is less or equal than the given threshold,
    then consider user passive - return True.
    """
    user_utterances = int_ctx.get_human_utterances(ctx, pipeline)[-history_len:]
    user_utterances = [utt["text"] for utt in user_utterances]

    uttrs_lens = [len(uttr.split()) <= passive_threshold for uttr in user_utterances]
    if all(uttrs_lens):
        return True
    return False


def get_not_used_and_save_sentiment_acknowledgement(ctx: Context, pipeline: Pipeline, sentiment=None, lang="EN"):
    if sentiment is None:
        sentiment = int_ctx.get_human_sentiment(ctx, pipeline)
        if is_yes_vars(ctx, pipeline) or is_no_vars(ctx, pipeline):
            sentiment = "neutral"

    shared_memory = int_ctx.get_shared_memory(ctx, pipeline)
    last_acknowledgements = shared_memory.get("last_acknowledgements", [])

    ack = common_utils.get_not_used_template(
        used_templates=last_acknowledgements, all_templates=GENERAL_ACKNOWLEDGEMENTS[lang][sentiment]
    )

    used_acks = last_acknowledgements + [ack]
    int_ctx.save_to_shared_memory(ctx, pipeline, last_acknowledgements=used_acks[-2:])
    return ack


def set_conf_and_can_cont_by_universal_policy(ctx: Context, pipeline: Pipeline):
    DIALOG_BEGINNING_START_CONFIDENCE = 0.98
    DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
    DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
    MIDDLE_DIALOG_START_CONFIDENCE = 0.7

    if not is_begin_of_dialog(ctx, pipeline, begin_dialog_n=10):
        confidence = 0.0
        can_continue_flag = CAN_NOT_CONTINUE
    elif is_first_our_response(ctx, pipeline):
        confidence = DIALOG_BEGINNING_START_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
    elif not is_interrupted(ctx, pipeline) and common_greeting.dont_tell_you_answer(
        int_ctx.get_last_human_utterance(ctx, pipeline)
    ):
        confidence = DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
    elif not is_interrupted(ctx, pipeline):
        confidence = DIALOG_BEGINNING_CONTINUE_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
    else:
        confidence = MIDDLE_DIALOG_START_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO

    int_ctx.set_can_continue(ctx, pipeline, can_continue_flag)
    int_ctx.set_confidence(ctx, pipeline, confidence)


def facts(ctx, pipeline):
    return provide_facts_request(ctx, pipeline)
