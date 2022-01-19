import logging
import re

from nltk.stem import WordNetLemmatizer

from df_engine.core import Context, Actor

import common.utils as common_utils
import common.universal_templates as universal_templates
import common.dff.integration.context as int_ctx
from common.acknowledgements import GENERAL_ACKNOWLEDGEMENTS

logger = logging.getLogger(__name__)

wnl = WordNetLemmatizer()


#  vars is described in README.md


def was_clarification_request(ctx: Context, actor: Actor) -> bool:
    flag = ctx.misc["agent"]["clarification_request_flag"]
    logger.debug(f"was_clarification_request = {flag}")
    return bool(flag)


def is_opinion_request(ctx: Context, actor: Actor) -> bool:
    flag = common_utils.is_opinion_request(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
    logger.debug(f"is_opinion_request = {flag}")
    return bool(flag)


def is_opinion_expression(ctx: Context, actor: Actor) -> bool:
    flag = common_utils.is_opinion_expression(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
    logger.debug(f"is_opinion_expression = {flag}")
    return bool(flag)


def is_previous_turn_dff_suspended(ctx: Context, actor: Actor) -> bool:
    flag = ctx.misc["agent"].get("previous_turn_dff_suspended", False)
    logger.debug(f"is_previous_turn_dff_suspended = {flag}")
    return bool(flag)


def is_current_turn_dff_suspended(ctx: Context, actor: Actor) -> bool:
    flag = ctx.misc["agent"].get("current_turn_dff_suspended", False)
    logger.debug(f"is_current_turn_dff_suspended = {flag}")
    return bool(flag)


def is_switch_topic(ctx: Context, actor: Actor) -> bool:
    flag = universal_templates.is_switch_topic(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
    logger.debug(f"is_switch_topic = {flag}")
    return bool(flag)


def is_question(ctx: Context, actor: Actor) -> bool:
    text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    flag = common_utils.is_question(text)
    logger.debug(f"is_question = {flag}")
    return bool(flag)


def is_lets_chat_about_topic_human_initiative(ctx: Context, actor: Actor) -> bool:
    flag = universal_templates.if_chat_about_particular_topic(
        int_ctx.get_last_human_utterance(ctx, actor), int_ctx.get_last_bot_utterance(ctx, actor)
    )
    logger.debug(f"is_lets_chat_about_topic_human_initiative = {flag}")
    return bool(flag)


def is_lets_chat_about_topic(ctx: Context, actor: Actor) -> bool:
    flag = is_lets_chat_about_topic_human_initiative(ctx, actor)

    last_human_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    last_bot_uttr_text = int_ctx.get_last_bot_utterance(ctx, actor)["text"]
    is_bot_initiative = bool(re.search(universal_templates.COMPILE_WHAT_TO_TALK_ABOUT, last_bot_uttr_text))
    flag = flag or (is_bot_initiative and not common_utils.is_no(last_human_uttr))
    logger.debug(f"is_lets_chat_about_topic = {flag}")
    return bool(flag)


def is_begin_of_dialog(ctx: Context, actor: Actor, begin_dialog_n=10) -> bool:
    flag = int_ctx.get_human_utter_index(ctx, actor) < begin_dialog_n
    logger.debug(f"is_begin_of_dialog = {flag}")
    return bool(flag)


def is_interrupted(ctx: Context, actor: Actor) -> bool:
    flag = (
        int_ctx.get_human_utter_index(ctx, actor) - int_ctx.get_previous_human_utter_index(ctx, actor)
    ) != 1 and not was_clarification_request(ctx, actor)
    logger.debug(f"is_interrupted = {flag}")
    return bool(flag)


def is_long_interrupted(ctx: Context, actor: Actor, how_long=3) -> bool:
    flag = (
        int_ctx.get_human_utter_index(ctx, actor) - int_ctx.get_previous_human_utter_index(ctx, actor)
    ) > how_long and not was_clarification_request(ctx, actor)
    logger.debug(f"is_long_interrupted = {flag}")
    return bool(flag)


def is_new_human_entity(ctx: Context, actor: Actor) -> bool:
    new_entities = int_ctx.get_new_human_labeled_noun_phrase(ctx, actor)
    flag = bool(new_entities)
    logger.debug(f"is_new_human_entity = {flag}")
    return bool(flag)


def is_last_state(ctx: Context, actor: Actor, state) -> bool:
    flag = False
    history = list(ctx.misc["agent"]["history"].items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        last_state = history_sorted[-1][1]
        if last_state == state:
            flag = True
    return bool(flag)


def is_first_time_of_state(ctx: Context, actor: Actor, state) -> bool:
    flag = state not in list(ctx.misc["agent"]["history"].values())
    logger.debug(f"is_first_time_of_state {state} = {flag}")
    return bool(flag)


def if_was_prev_active(ctx: Context, actor: Actor) -> bool:
    flag = False
    skill_uttr_indices = set(ctx.misc["agent"]["history"].keys())
    human_uttr_index = str(ctx.misc["agent"]["human_utter_index"] - 1)
    if human_uttr_index in skill_uttr_indices:
        flag = True
    return bool(flag)


def is_plural(word) -> bool:
    lemma = wnl.lemmatize(word, "n")
    plural = True if word is not lemma else False
    return plural


def is_first_our_response(ctx: Context, actor: Actor) -> bool:
    flag = len(list(ctx.misc["agent"]["history"].values())) == 0
    logger.debug(f"is_first_our_response = {flag}")
    return bool(flag)


def is_no_human_abandon(ctx: Context, actor: Actor) -> bool:
    """Is dialog breakdown in human utterance or no. Uses MIDAS hold/abandon classes."""
    midas_classes = common_utils.get_intents(int_ctx.get_last_human_utterance(ctx, actor), which="midas")
    if "abandon" not in midas_classes:
        return True
    return False


def no_special_switch_off_requests(ctx: Context, actor: Actor) -> bool:
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    """
    intents_by_catcher = common_utils.get_intents(
        int_ctx.get_last_human_utterance(ctx, actor), probs=False, which="intent_catcher"
    )
    is_high_priority_intent = any([intent not in common_utils.service_intents for intent in intents_by_catcher])
    is_switch = is_switch_topic(ctx, actor)
    is_lets_chat = is_lets_chat_about_topic_human_initiative(ctx, actor)

    if not (is_high_priority_intent or is_switch or is_lets_chat):
        return True
    return False


def no_requests(ctx: Context, actor: Actor) -> bool:
    """Function to determine if
    - user didn't asked to switch topic,
    - user didn't ask to talk about something particular,
    - user didn't requested high priority intents (like what_is_your_name)
    - user didn't requested any special intents
    - user didn't ask questions
    """
    contain_no_special_requests = no_special_switch_off_requests(ctx, actor)

    request_intents = [
        "opinion_request",
        "topic_switching",
        "lets_chat_about",
        "what_are_you_talking_about",
        "Information_RequestIntent",
        "Topic_SwitchIntent",
        "Opinion_RequestIntent",
    ]
    intents = common_utils.get_intents(int_ctx.get_last_human_utterance(ctx, actor), which="all")
    is_not_request_intent = all([intent not in request_intents for intent in intents])
    is_no_question = "?" not in int_ctx.get_last_human_utterance(ctx, actor)["text"]

    if contain_no_special_requests and is_not_request_intent and is_no_question:
        return True
    return False


def is_yes_vars(ctx: Context, actor: Actor) -> bool:
    flag = True
    flag = flag and common_utils.is_yes(int_ctx.get_last_human_utterance(ctx, actor))
    return bool(flag)


def is_no_vars(ctx: Context, actor: Actor) -> bool:
    flag = True
    flag = flag and common_utils.is_no(int_ctx.get_last_human_utterance(ctx, actor))
    return bool(flag)


def is_do_not_know_vars(ctx: Context, actor: Actor) -> bool:
    flag = True
    flag = flag and common_utils.is_donot_know(int_ctx.get_last_human_utterance(ctx, actor))
    return bool(flag)


def is_passive_user(ctx: Context, actor: Actor, history_len=2) -> bool:
    """Check history_len last human utterances on the number of tokens.
    If number of tokens in ALL history_len uterances is <= 3 tokens, then consider user passive - return True.
    """
    user_utterances = ctx.misc["agent"]["dialog"]["human_utterances"][-history_len:]
    user_utterances = [utt["text"] for utt in user_utterances]

    uttrs_lens = [len(uttr.split()) <= 5 for uttr in user_utterances]
    if all(uttrs_lens):
        return True
    return False


def get_not_used_and_save_sentiment_acknowledgement(ctx: Context, actor: Actor):
    sentiment = int_ctx.get_human_sentiment(ctx, actor)
    if is_yes_vars(ctx, actor) or is_no_vars(ctx, actor):
        sentiment = "neutral"

    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    last_acknowledgements = shared_memory.get("last_acknowledgements", [])

    ack = common_utils.get_not_used_template(
        used_templates=last_acknowledgements, all_templates=GENERAL_ACKNOWLEDGEMENTS[sentiment]
    )

    used_acks = last_acknowledgements + [ack]
    int_ctx.save_to_shared_memory(ctx, actor, last_acknowledgements=used_acks[-2:])
    return ack
