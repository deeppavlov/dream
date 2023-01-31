import logging
import random
import requests
import sentry_sdk
from os import getenv
from typing import Tuple

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.greeting as common_greeting
import common.link as common_link
from common.constants import MUST_CONTINUE, CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from common.emotion import is_positive_regexp_based, is_negative_regexp_based
from common.universal_templates import HEALTH_PROBLEMS, COMPILE_SOMETHING
from df_engine.core import Actor, Context


sentry_sdk.init(getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

LANGUAGE = getenv("LANGUAGE", "EN")

REPLY_TYPE = Tuple[str, float, dict, dict, dict]
DIALOG_BEGINNING_START_CONFIDENCE = 0.9
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.9
MIDDLE_CONFIDENCE = 0.85
GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS[LANGUAGE])

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


def compose_topic_offering(ctx: Context, actor: Actor, excluded_skills=None) -> str:
    logger.debug("compose_topic_offering")
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
    logger.debug("offer_topic")
    if excluded_skills is None:
        excluded_skills = int_ctx.get_disliked_skills(ctx, actor)

    offer_topic_choose = compose_topic_offering(ctx, actor, excluded_skills=excluded_skills)
    # if int_cnd.is_passive_user(ctx, actor, history_len=2):
    #     # linkto to particular skill
    #     offer_topic_choose = compose_topic_offering(ctx, actor, excluded_skills=excluded_skills)
    # else:
    #     # what do you want to talk about?
    #     offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE]["what_to_talk_about"])
    greeting_step_id = GREETING_STEPS.index("what_to_talk_about")
    logger.debug(f"Assign greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    return offer_topic_choose


def greeting_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    """
    Returns:
        reply PRIVACY_REPLY or (empty),
        confidence 1.0 or 0.0,
        human attributes (empty),
        bot attributes (empty),
        attributes MUST_CONTINUE or (empty)
    """
    logger.debug("greeting_response")
    bot_utt = int_ctx.get_last_bot_utterance(ctx, actor)["text"].lower()
    if common_greeting.GREETINGS_BY_HUMAN.match(int_ctx.get_last_human_utterance(ctx, actor)["text"]):
        int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    else:
        int_ctx.set_confidence(ctx, actor, HIGH_CONFIDENCE)
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)

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
        after_hello_resp = random.choice(common_greeting.HOW_ARE_YOU_RESPONSES[LANGUAGE])
    elif which_start == "what_is_your_name":
        after_hello_resp = random.choice(common_greeting.WHAT_IS_YOUR_NAME_RESPONSES[LANGUAGE])
    # elif which_start == "starter_genre":
    #     after_hello_resp = starter_flow.genre_response(ctx, actor)
    # elif which_start == "starter_weekday":
    #     after_hello_resp = starter_flow.weekday_response(ctx, actor)
    else:
        # what_to_talk_about
        after_hello_resp = offer_topic(ctx, actor)
        # set_confidence
        int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)

    if "seems like alexa decided to turn me on" in bot_utt:
        reply = after_hello_resp
    else:
        reply = f"{common_greeting.HI_THIS_IS_DREAM[LANGUAGE]} {after_hello_resp}"
    return reply


def clarify_event_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("clarify_event_response")
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    reply = random.choice(["Cool! Tell me about it.", "Great! What is it?"])
    greeting_step_id = GREETING_STEPS.index("recent_personal_events")
    logger.debug(f"Assign greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    return reply


def false_positive_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("false_positive_response")
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    reply = "Hi! Seems like Alexa decided to turn me on. Do you want to chat with me?"
    return reply


def bye_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("bye_response")
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    reply = "Sorry, bye. #+#exit"
    return reply


def how_are_you_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("how_are_you_response")
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    how_bot_is_doing_resp = random.choice(common_greeting.HOW_BOT_IS_DOING_RESPONSES[LANGUAGE])

    question_about_activities = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE]["recent_personal_events"])
    reply = (
        f"{how_bot_is_doing_resp} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES[LANGUAGE])} "
        f"{question_about_activities}"
    )
    greeting_step_id = GREETING_STEPS.index("recent_personal_events")
    logger.debug(f"Assign greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    return reply


def health_problems(ctx: Context, actor: Actor):
    logger.debug("health_problems")
    if HEALTH_PROBLEMS.search(int_ctx.get_last_human_utterance(ctx, actor)["text"]):
        return True
    return False


def how_human_is_doing_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("how_human_is_doing_response")
    usr_sentiment = int_ctx.get_human_sentiment(ctx, actor)
    _no_entities = len(int_ctx.get_nounphrases_from_human_utterance(ctx, actor)) == 0
    _no_requests = int_cnd.no_requests(ctx, actor)
    _is_unhealthy = health_problems(ctx, actor)
    if is_positive_regexp_based(int_ctx.get_last_human_utterance(ctx, actor)):
        int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
        user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS[LANGUAGE])
    elif _is_unhealthy or is_negative_regexp_based(int_ctx.get_last_human_utterance(ctx, actor)):
        int_ctx.set_confidence(ctx, actor, HIGH_CONFIDENCE)
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
        user_mood_acknowledgement = (
            f"{random.choice(common_greeting.BAD_MOOD_REACTIONS[LANGUAGE])} "
            f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP[LANGUAGE])}"
        )
    else:
        if _no_entities and _no_requests and usr_sentiment != "negative":
            # we do not set super conf for negative responses because we hope that emotion_skill will respond
            int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
            int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
        else:
            int_ctx.set_confidence(ctx, actor, HIGH_CONFIDENCE)
            int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)

        if usr_sentiment == "positive":
            user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS[LANGUAGE])
        elif usr_sentiment == "negative":
            user_mood_acknowledgement = (
                f"{random.choice(common_greeting.BAD_MOOD_REACTIONS[LANGUAGE])} "
                f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP[LANGUAGE])}"
            )
        else:
            user_mood_acknowledgement = int_cnd.get_not_used_and_save_sentiment_acknowledgement(
                ctx, actor, sentiment="neutral", lang=LANGUAGE
            )

    question_about_activities = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE]["recent_personal_events"])
    reply = (
        f"{user_mood_acknowledgement} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES[LANGUAGE])} "
        f"{question_about_activities}"
    )
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    greeting_step_id = GREETING_STEPS.index("recent_personal_events")
    logger.debug(f"Assign greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    return reply


def offer_topics_choice_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("offer_topics_choice_response")
    int_ctx.set_confidence(ctx, actor, HIGH_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    reply = offer_topic(ctx, actor)
    return reply


def offered_topic_choice_declined_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("offered_topic_choice_declined_response")
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    greeting_step_id = 0
    # what do you want to talk about?
    offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE]["what_to_talk_about"])

    logger.debug(f"Assign greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, sentiment="neutral", lang=LANGUAGE)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)
    reply = f"{ack} {offer_topic_choose}"
    return reply


def std_greeting_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("std_greeting_response")

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
        logger.debug("nothing OR no requests and no entities")
        if _friendship_was_active and greeting_step_id >= 1:
            ack = random.choice(
                common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY[LANGUAGE][GREETING_STEPS[greeting_step_id - 1]]
            )
            int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
            int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
            int_ctx.set_confidence(ctx, actor, MIDDLE_CONFIDENCE)
            int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    elif not _no_requests and len(_entities) > 0:
        logger.debug("no requests but entities")
        # user wants to talk about something particular. We are just a dummy response, if no appropriate
        if _friendship_was_active:
            ack = random.choice(
                common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY[LANGUAGE]["what_do_you_do_on_weekdays"]
            )
            sent_ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
            ack = f"{sent_ack} {ack}"
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
        int_ctx.set_confidence(ctx, actor, MIDDLE_CONFIDENCE)
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    else:
        logger.debug("other cases")
        if len(_entities) == 0 or _no_requests:
            int_ctx.set_confidence(ctx, actor, HIGH_CONFIDENCE)
        else:
            int_ctx.set_confidence(ctx, actor, MIDDLE_CONFIDENCE)
        # some request by user detected OR no requests but some entities detected
        if _friendship_was_active and GREETING_STEPS[greeting_step_id] == "recent_personal_events":
            ack = random.choice(common_greeting.INTERESTING_PERSON_THANKS_FOR_CHATTING[LANGUAGE])
        else:
            ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)

    if health_problems(ctx, actor):
        ack = "I'm so sorry to hear that. Hope, everything will be fine soon."

    if greeting_step_id == 0 or GREETING_STEPS[greeting_step_id] == "what_to_talk_about":
        logger.debug("step-id=0 or what_to_talk_about")
        if LANGUAGE == "EN":
            prev_active_skills = [uttr.get("active_skill", "") for uttr in int_ctx.get_bot_utterances(ctx, actor)][-5:]
            disliked_skills = int_ctx.get_disliked_skills(ctx, actor)
            body = offer_topic(ctx, actor, excluded_skills=prev_active_skills + disliked_skills)
        else:
            body = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE]["what_to_talk_about"])
    else:
        logger.debug("choose according to step-id")
        body = random.choice(common_greeting.GREETING_QUESTIONS[LANGUAGE][GREETING_STEPS[greeting_step_id]])

    logger.debug(f"Assign in std_greeting_response greeting_step_id to {greeting_step_id + 1}")
    int_ctx.save_to_shared_memory(ctx, actor, greeting_step_id=greeting_step_id + 1)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    reply = f"{ack} {body}"
    return reply


def new_entities_is_needed_for_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("new_entities_is_needed_for_response")
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
    body = "Tell me more about that."

    int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)
    int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    reply = " ".join([ack, body])
    return reply


def closed_answer_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("closed_answer_response")
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
    body = ""

    int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)
    int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    reply = " ".join([ack, body])
    return reply


# curl -H "Content-Type: application/json" -XPOST http://0.0.0.0:8088/respond \
#   -d '{"text":["Hello, my dog [MASK] cute"]}'
MASKED_LM_SERVICE_URL = getenv("MASKED_LM_SERVICE_URL")


def masked_lm(templates=None, prob_threshold=0.0, probs_flag=False):
    logger.debug("masked_lm")
    templates = ["Hello, it's [MASK] dog."] if templates is None else templates
    request_data = {"text": templates}
    try:
        predictions_batch = requests.post(MASKED_LM_SERVICE_URL, json=request_data, timeout=1.5).json()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        predictions_batch = {}
    logger.debug(f"predictions_batch = {predictions_batch}")
    tokens_batch = []
    for predictions in predictions_batch.get("predicted_tokens", [[]] * len(templates)):
        tokens = {}
        if predictions and predictions[0]:
            one_mask_predictions = predictions[0]
            for token, prob in one_mask_predictions.items():
                if prob_threshold < prob:
                    tokens[token] = prob
        tokens_batch += [tokens if probs_flag else list(tokens)]
    return tokens_batch


def link_to_by_enity_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("link_to_by_enity_response")
    try:
        ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)
        entities = int_ctx.get_new_human_labeled_noun_phrase(ctx, actor)
        if entities:
            logger.debug("entities detected")
            logger.debug(f"entities= {entities}")
            tgt_entity = list(entities)[-1]
            logger.debug(f"tgt_entity= {tgt_entity}")
            if tgt_entity in sum(link_to_skill2key_words.values(), []):
                skill_names = [skill for skill, key_words in link_to_skill2key_words.items() if tgt_entity in key_words]
            else:
                link_to_skills = {
                    link_to_skill: f"I [MASK] interested in both {key_words[0]} and {tgt_entity}."
                    for link_to_skill, key_words in link_to_skill2key_words.items()
                }
                link_to_skill_scores = masked_lm(list(link_to_skills.values()), probs_flag=True)
                link_to_skill_scores = {
                    topic: max(*list(score.values()), 0) if score else 0
                    for topic, score in zip(link_to_skills, link_to_skill_scores)
                }
                skill_names = sorted(link_to_skill_scores, key=lambda x: link_to_skill_scores[x])[-2:]
        else:
            logger.debug("no entities detected")
            skill_names = [random.choice(list(link_to_skill2key_words))]

        # used_links
        link = int_ctx.get_new_link_to(ctx, actor, skill_names)

        # our body now contains prompt-question already!
        body = random.choice(link_to_skill2i_like_to_talk.get(link["skill"], [""]))
        int_cnd.set_conf_and_can_cont_by_universal_policy(ctx, actor)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        int_ctx.set_confidence(ctx, actor, 0)
        return ""
