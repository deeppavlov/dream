import logging
import random
import sentry_sdk
from os import getenv
from typing import Any, Tuple

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
import common.greeting as common_greeting
from common.constants import MUST_CONTINUE, CAN_CONTINUE_SCENARIO,CAN_NOT_CONTINUE
from common.emotion import is_positive_regexp_based, is_negative_regexp_based
from common.link import link_to_skill2key_words, link_to_skill2i_like_to_talk
from common.universal_templates import HEALTH_PROBLEMS, COMPILE_SOMETHING
from df_engine.core import Actor, Context


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

REPLY_TYPE = Tuple[str, float, dict, dict, dict]
DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
MIDDLE_CONFIDENCE = 0.95
GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)


def compose_topic_offering(ctx: Context, actor: Actor, excluded_skills=None) -> str:
    excluded_skills = [] if excluded_skills is None else excluded_skills

    available_skill_names = [
        skill_name for skill_name in link_to_skill2key_words.keys() if skill_name not in excluded_skills
    ]
    if int_ctx.get_age_group(ctx, actor) == "kid":
        available_skill_names = [
            "game_cooperative_skill",
            "dff_animals_skill",
            "dff_food_skill",
            "superheroes",
            "school",
        ]  # for small talk skill
    if len(available_skill_names) == 0:
        available_skill_names = link_to_skill2key_words.keys()

    skill_name = random.choice(available_skill_names)
    if skill_name in link_to_skill2i_like_to_talk:
        response = random.choice(link_to_skill2i_like_to_talk[skill_name])
    else:
        response = f"Would you like to talk about {skill_name}?"
    int_ctx.save_to_shared_memory(ctx, actor, offered_topics=link_to_skill2key_words.get(skill_name, skill_name))

    return response


def offer_topic(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    if excluded_skills is None:
        excluded_skills = int_ctx.get_disliked_skills(ctx, actor)

    offer_topic_choose = compose_topic_offering(ctx, actor, excluded_skills=excluded_skills)
    # if int_cnd.is_passive_user(ctx, actor, history_len=2):
    #     # linkto to particular skill
    #     offer_topic_choose = compose_topic_offering(ctx, actor, excluded_skills=excluded_skills)
    # else:
    #     # what do you want to talk about?
    #     offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS["what_to_talk_about"])

    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=GREETING_STEPS.index("what_to_talk_about") + 1)
    return offer_topic_choose


def greeting_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    """
    Returns:
        reply PRIVACY_REPLY or (empty),
        confidence 1.0 or 0.0,
        human attributes (empty),
        bot attributes (empty),
        attributes MUST_CONTINUE or (empty)
    """
    bot_utt = int_ctx.get_last_bot_utterance(ctx, actor)["text"].lower()
    if int_cnd.is_lets_chat_about_topic(ctx, actor):
        confidence = HIGH_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
    else:
        confidence = SUPER_CONFIDENCE
        can_continue_flag = MUST_CONTINUE
    which_start = random.choice(
        [
            # "starter_weekday",
            # "starter_genre",
            "how_are_you",
            # "what_is_your_name",
            # "what_to_talk_about"
        ]
    )
    int_ctx.save_to_shared_memory(ctx, actor, greeting_type=which_start)
    if which_start == "how_are_you":
        after_hello_resp = random.choice(common_greeting.HOW_ARE_YOU_RESPONSES)
    elif which_start == "what_is_your_name":
        after_hello_resp = random.choice(common_greeting.WHAT_IS_YOUR_NAME_RESPONSES)
    # elif which_start == "starter_genre":
    #     after_hello_resp = starter_flow.genre_response(ctx, actor)
    # elif which_start == "starter_weekday":
    #     after_hello_resp = starter_flow.weekday_response(ctx, actor)
    else:
        # what_to_talk_about
        after_hello_resp = offer_topic(ctx, actor)
        # set_confidence
        confidence, can_continue_flag = int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)

    if "seems like alexa decided to turn me on" in bot_utt:
        reply = after_hello_resp
    else:
        reply = f"{common_greeting.HI_THIS_IS_ALEXA} {after_hello_resp}"

    attr = {"can_continue": can_continue_flag}

    return reply, confidence, {}, {}, attr


def clarify_event_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = SUPER_CONFIDENCE
    can_continue_flag = MUST_CONTINUE
    reply = random.choice(["Cool! Tell me about it.", "Great! What is it?"])
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def false_positive_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = SUPER_CONFIDENCE
    can_continue_flag = MUST_CONTINUE
    reply = "Hi! Seems like Alexa decided to turn me on. Do you want to chat with me?"
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def bye_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = SUPER_CONFIDENCE
    can_continue_flag = CAN_NOT_CONTINUE
    reply = "Sorry, bye. #+#exit"
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def how_are_you_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = SUPER_CONFIDENCE
    can_continue_flag = MUST_CONTINUE
    how_bot_is_doing_resp = random.choice(common_greeting.HOW_BOT_IS_DOING_RESPONSES)

    question_about_activities = random.choice(common_greeting.GREETING_QUESTIONS["recent_personal_events"])
    reply = (
        f"{how_bot_is_doing_resp} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES)} "
        f"{question_about_activities}"
    )
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def health_problems(ctx: Context, actor: Actor):
    if HEALTH_PROBLEMS.search(int_ctx.get_last_human_utterance(ctx, actor)["text"]):
        return True
    return False


def how_human_is_doing_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    usr_sentiment = int_ctx.get_human_sentiment(ctx, actor)
    _no_entities = len(int_ctx.get_nounphrases_from_human_utterance(ctx, actor)) == 0
    _no_requests = int_cnd.no_requests(ctx, actor)
    _is_unhealthy = health_problems(ctx, actor)
    if is_positive_regexp_based(int_ctx.get_last_human_utterance(ctx, actor)):
        confidence = SUPER_CONFIDENCE
        can_continue_flag = MUST_CONTINUE
        user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS)
    elif _is_unhealthy or is_negative_regexp_based(int_ctx.get_last_human_utterance(ctx, actor)):
        confidence = HIGH_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
        user_mood_acknowledgement = (
            f"{random.choice(common_greeting.BAD_MOOD_REACTIONS)} "
            f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP)}"
        )
        int_ctx.add_acknowledgement_to_response_parts(ctx, actor)
    else:
        if _no_entities and _no_requests and usr_sentiment != "negative":
            # we do not set super conf for negative responses because we hope that emotion_skill will respond
            confidence = SUPER_CONFIDENCE
            can_continue_flag = MUST_CONTINUE
        else:
            confidence = HIGH_CONFIDENCE
            can_continue_flag = CAN_CONTINUE_SCENARIO

        if usr_sentiment == "positive":
            user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS)
        elif usr_sentiment == "negative":
            user_mood_acknowledgement = (
                f"{random.choice(common_greeting.BAD_MOOD_REACTIONS)} "
                f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP)}"
            )
        else:
            user_mood_acknowledgement = "Okay."

    question_about_activities = random.choice(common_greeting.GREETING_QUESTIONS["recent_personal_events"])
    reply = (
        f"{user_mood_acknowledgement} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES)} "
        f"{question_about_activities}"
    )
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def offer_topics_choice_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = HIGH_CONFIDENCE
    can_continue_flag = CAN_CONTINUE_SCENARIO
    reply = offer_topic(ctx, actor)
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def offered_topic_choice_declined_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    confidence = SUPER_CONFIDENCE
    can_continue_flag = MUST_CONTINUE
    greeting_step_id = 0
    # what do you want to talk about?
    offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS["what_to_talk_about"])
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    reply = f"Okay. {offer_topic_choose}"
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def std_greeting_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:

    shared_memory = int_ctx.get_shared_memory(ctx, actor)

    greeting_step_id = shared_memory.get("greeting_step_id", 0)

    _friendship_was_active = "dff_friendship_skill" == int_ctx.get_last_bot_utterance(ctx, actor).get(
        "active_skill", ""
    )
    _entities = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
    _no_requests = int_cnd.no_requests(ctx, actor)
    _nothing_dont_know = COMPILE_SOMETHING.search(int_ctx.get_last_human_utterance(ctx, actor)["text"])

    # acknowledgement, confidences
    if _nothing_dont_know or (_no_requests and len(_entities) == 0):
        if _friendship_was_active and greeting_step_id >= 1:
            ack = random.choice(
                common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY[GREETING_STEPS[greeting_step_id - 1]]
            )
            confidence = SUPER_CONFIDENCE
            can_continue_flag = MUST_CONTINUE
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(vars)
            confidence = MIDDLE_CONFIDENCE
            can_continue_flag = CAN_CONTINUE_SCENARIO
        int_ctx.add_acknowledgement_to_response_parts(ctx, actor)
    elif not _no_requests and len(_entities) > 0:
        # user wants to talk about something particular. We are just a dummy response, if no appropriate
        if _friendship_was_active:
            ack = random.choice(
                common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY["what_do_you_do_on_weekdays"]
            )
            sent_ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor)
            ack = f"{sent_ack} {ack}"
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor)
        confidence = MIDDLE_CONFIDENCE
        can_continue_flag = CAN_CONTINUE_SCENARIO
        int_ctx.add_acknowledgement_to_response_parts(ctx, actor)
    else:
        if len(_entities) == 0 or _no_requests:
            confidence = HIGH_CONFIDENCE
        else:
            confidence = MIDDLE_CONFIDENCE
        # some request by user detected OR no requests but some entities detected
        if _friendship_was_active and GREETING_STEPS[greeting_step_id] == "recent_personal_events":
            ack = random.choice(common_greeting.INTERESTING_PERSON_THANKS_FOR_CHATTING)
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor)
        can_continue_flag = CAN_CONTINUE_SCENARIO

    if health_problems(ctx, actor):
        ack = f"I'm so sorry to hear that. Hope, everything will be fine soon."
        int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    if greeting_step_id == 0 or GREETING_STEPS[greeting_step_id] == "what_to_talk_about":
        prev_active_skills = [uttr.get("active_skill", "") for uttr in int_ctx.get_bot_utterances(ctx, actor)][
            -5:
        ]
        disliked_skills = int_ctx.get_disliked_skills(ctx, actor)
        body = offer_topic(ctx, actor, excluded_skills=prev_active_skills + disliked_skills)
    else:
        body = random.choice(common_greeting.GREETING_QUESTIONS[GREETING_STEPS[greeting_step_id]])

    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)

    reply = f"{ack} {body}"
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def new_entities_is_needed_for_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor)
    body = "Tell me more about that."

    confidence, can_continue_flag = int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)
    can_continue_flag = CAN_NOT_CONTINUE

    reply = " ".join([ack, body])
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr


def closed_answer_response(ctx: Context, actor: Actor, *args, **kwargs) -> REPLY_TYPE:
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor)
    body = ""

    confidence, can_continue_flag = int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)
    can_continue_flag = CAN_NOT_CONTINUE

    reply = " ".join([ack, body])
    attr = {"can_continue": can_continue_flag}
    return reply, confidence, {}, {}, attr
