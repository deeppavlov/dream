import re

from df_engine.core import Actor, Context

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.greeting as common_greeting
import common.link as common_link
from common.emotion import is_positive_regexp_based, is_negative_regexp_based


GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)
link_to_skill2key_words = {
    skill_name: common_link.link_to_skill2key_words[skill_name]
    for skill_name in common_link.link_to_skill2key_words
    if skill_name in common_link.SKILLS_FOR_LINKING
}

link_to_skill2i_like_to_talk = {
    skill_name: common_link.link_to_skill2i_like_to_talk[skill_name]
    for skill_name in common_link.link_to_skill2i_like_to_talk
    if skill_name in common_link.SKILLS_FOR_LINKING
}


def offered_topic_choice_declined_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:

    prev_bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor)["text"]
    # asked what to talk about
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    greeting_step_id = shared_memory.get("greeting_step_id", 0)
    was_linking_topic_offering = (
        GREETING_STEPS[greeting_step_id - 1] == "what_to_talk_about" if greeting_step_id > 0 else False
    )
    user_asked_for_topic = any(
        [resp.lower() in prev_bot_uttr.lower() for resp in common_greeting.GREETING_QUESTIONS["what_to_talk_about"]]
    )

    was_active = "dff_friendship_skill" == int_ctx.get_last_bot_utterance(ctx, actor).get("active_skill", "")
    # offered choice between two topics
    offered_topics = shared_memory.get("offered_topics", [])
    # and user declined
    declined = int_cnd.is_no_vars(ctx, actor)
    if was_active and offered_topics and was_linking_topic_offering and not user_asked_for_topic and declined:
        # was offered particular linking question, and user said no
        return True
    return False


def asked_for_events_and_got_yes_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor).get("text", "")
    was_event_question = any(
        [resp.lower() in prev_bot_uttr.lower() for resp in common_greeting.GREETING_QUESTIONS["recent_personal_events"]]
    )

    agreed = int_cnd.is_yes_vars(ctx, actor)
    entities = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
    if was_event_question and agreed and len(entities) == 0:
        return True
    return False


def false_positive_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = (
        bool(re.search(common_greeting.FALSE_POSITIVE_TURN_ON_RE, int_ctx.get_last_human_utterance(ctx, actor)["text"]))
        and int_ctx.get_human_utter_index(ctx, actor) == 0
    )
    return flag


def hello_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = True
    flag = flag and len(int_ctx.get_human_utterances(ctx, actor)) == 1
    flag = flag
    return flag


def how_are_you_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_frindship_skill = int_ctx.get_last_bot_utterance(ctx, actor).get("active_skill", "") == "dff_friendship_skill"
    how_are_you_found = common_greeting.HOW_ARE_YOU_TEMPLATE.search(
        int_ctx.get_last_human_utterance(ctx, actor)["text"]
    )
    how_are_you_precise_found = common_greeting.HOW_ARE_YOU_PRECISE_TEMPLATE.search(
        int_ctx.get_last_human_utterance(ctx, actor)["text"]
    )
    how_are_you_by_bot_found = common_greeting.HOW_ARE_YOU_TEMPLATE.search(
        int_ctx.get_last_bot_utterance(ctx, actor)["text"]
    )
    any_you_in_user = common_greeting.ANY_YOU_TEMPLATE.search(int_ctx.get_last_human_utterance(ctx, actor)["text"])

    if how_are_you_precise_found:
        return True
    elif prev_frindship_skill and (how_are_you_found or (how_are_you_by_bot_found and any_you_in_user)):
        return True
    return False


def positive_or_negative_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    # SYS_USR_ANSWERS_HOW_IS_HE_DOING
    usr_sentiment = int_ctx.get_human_sentiment(ctx, actor)
    pos_temp = is_positive_regexp_based(int_ctx.get_last_human_utterance(ctx, actor))
    neg_temp = is_negative_regexp_based(int_ctx.get_last_human_utterance(ctx, actor))

    bot_asked_how_are_you = any(
        [resp in int_ctx.get_last_bot_utterance(ctx, actor)["text"] for resp in common_greeting.HOW_ARE_YOU_RESPONSES]
    )
    if bot_asked_how_are_you and (usr_sentiment in ["positive", "negative"] or pos_temp or neg_temp):
        return True
    return False


def no_requests_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return int_cnd.no_requests(ctx, actor)


def no_special_switch_off_requests_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return int_cnd.no_special_switch_off_requests(ctx, actor)


def was_what_do_you_do_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    bot_uttr_text = int_ctx.get_last_bot_utterance(ctx, actor).get("text", "")
    if int_cnd.no_requests(ctx, actor) and any(
        [phrase in bot_uttr_text for phrase in common_greeting.GREETING_QUESTIONS["what_do_you_do_on_weekdays"]]
    ):
        return True
    return False


def is_yes_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if int_cnd.is_yes_vars(ctx, actor):
        return True
    return False


def is_no_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if int_cnd.is_no_vars(ctx, actor):
        return True
    return False


def not_is_no_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not int_cnd.is_no_vars(ctx, actor):
        return True
    return False


def std_greeting_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = True
    # flag = flag and not condition_utils.is_new_human_entity(vars)
    # flag = flag and not condition_utils.is_switch_topic(vars)
    # flag = flag and not condition_utils.is_opinion_request(vars)
    # flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    # flag = flag and not condition_utils.is_question(vars)
    # flag = flag and condition_utils.is_begin_of_dialog(vars)
    if flag:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        flag = flag and shared_memory.get("greeting_step_id", 0) < len(GREETING_STEPS)

    return flag


def new_entities_is_needed_for_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = True
    # what is the state in here?
    # flag = flag and int_cnd.is_first_time_of_state(ctx, actor, State.SYS_NEW_ENTITIES_IS_NEEDED_FOR)
    flag = flag and not int_cnd.is_switch_topic(ctx, actor)
    flag = flag and not int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)
    flag = flag and int_cnd.is_new_human_entity(ctx, actor)

    return flag


def closed_answer_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = True
    flag = flag and not int_cnd.is_switch_topic(ctx, actor)
    flag = flag and not int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return flag


def link_to_by_enity_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = True
    flag = flag and not int_cnd.is_switch_topic(ctx, actor)
    flag = flag and not int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return flag
