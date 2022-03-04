# %%
import random
import re
import os
import logging
from enum import Enum, auto

import requests
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.emotion import is_positive_regexp_based, is_negative_regexp_based
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.greeting as common_greeting
from common.universal_templates import COMPILE_SOMETHING, HEALTH_PROBLEMS
import dialogflows.scopes as scopes
from dialogflows.flows.starter_states import State as StarterState
import dialogflows.flows.weekend as weekend_flow
import dialogflows.flows.starter as starter_flow

from dialogflows.flows.shared import (
    link_to_by_enity_request,
    link_to_by_enity_response,
    link_to_skill2i_like_to_talk,
    set_confidence_by_universal_policy,
    error_response,
    link_to_skill2key_words,
)


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)


GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)


class State(Enum):
    USR_START = auto()

    SYS_FP = auto()
    USR_FP = auto()
    SYS_USER_WANTS_TALK = auto()
    SYS_USER_DOESNT_WANT_TALK = auto()
    USR_TURN_OFF = auto()

    SYS_HELLO = auto()
    USR_HELLO_AND_CONTNIUE = auto()
    SYS_USR_ASKS_BOT_HOW_ARE_YOU = auto()
    SYS_USR_ANSWERS_HOW_IS_HE_DOING = auto()

    SYS_WHAT_DO_YOU_DO = auto()
    USR_FREE_TIME = auto()

    SYS_STD_GREETING = auto()
    USR_STD_GREETING = auto()

    SYS_NEW_ENTITIES_IS_NEEDED_FOR = auto()
    USR_NEW_ENTITIES_IS_NEEDED_FOR = auto()
    SYS_CLOSED_ANSWER = auto()
    USR_CLOSED_ANSWER = auto()
    SYS_LINK_TO_BY_ENITY = auto()
    USR_LINK_TO_BY_ENITY = auto()
    SYS_OFFERED_TOPICS_DECLINED = auto()
    SYS_OFFER_TOPICS = auto()
    SYS_ASKED_EVENTS_AND_YES_INTENT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
MIDDLE_CONFIDENCE = 0.95

# %%


def compose_topic_offering(vars, excluded_skills=None):
    excluded_skills = [] if excluded_skills is None else excluded_skills

    available_skill_names = [
        skill_name for skill_name in link_to_skill2key_words.keys() if skill_name not in excluded_skills
    ]
    if state_utils.get_age_group(vars) == "kid":
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
    state_utils.save_to_shared_memory(vars, offered_topics=link_to_skill2key_words.get(skill_name, skill_name))

    return response


def offered_topic_choice_declined_request(ngrams, vars):
    # SYS_OFFERED_TOPICS_DECLINED
    prev_bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    # asked what to talk about
    shared_memory = state_utils.get_shared_memory(vars)
    greeting_step_id = shared_memory.get("greeting_step_id", 0)
    was_linking_topic_offering = (
        GREETING_STEPS[greeting_step_id - 1] == "what_to_talk_about" if greeting_step_id > 0 else False
    )
    user_asked_for_topic = any(
        [resp.lower() in prev_bot_uttr.lower() for resp in common_greeting.GREETING_QUESTIONS["what_to_talk_about"]]
    )

    was_active = "dff_friendship_skill" == state_utils.get_last_bot_utterance(vars).get("active_skill", "")
    # offered choice between two topics
    offered_topics = shared_memory.get("offered_topics", [])
    # and user declined
    declined = condition_utils.is_no_vars(vars)
    if was_active and offered_topics and was_linking_topic_offering and not user_asked_for_topic and declined:
        # was offered particular linking question, and user said no
        return True
    return False


def asked_for_events_and_got_yes_request(ngrams, vars):
    # SYS_ASKED_EVENTS_AND_YES_INTENT
    prev_bot_uttr = state_utils.get_last_bot_utterance(vars).get("text", "")
    was_event_question = any(
        [resp.lower() in prev_bot_uttr.lower() for resp in common_greeting.GREETING_QUESTIONS["recent_personal_events"]]
    )

    agreed = condition_utils.is_yes_vars(vars)
    entities = state_utils.get_nounphrases_from_human_utterance(vars)
    if was_event_question and agreed and len(entities) == 0:
        return True
    return False


def clarify_event_response(vars):
    # USR_STD_GREETING
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, MUST_CONTINUE)
        response = random.choice(["Cool! Tell me about it.", "Great! What is it?"])
        state_utils.save_to_shared_memory(vars, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def offer_topic_response_part(vars, excluded_skills=None):
    if excluded_skills is None:
        excluded_skills = state_utils.get_disliked_skills(vars)

    offer_topic_choose = compose_topic_offering(vars, excluded_skills=excluded_skills)
    # if condition_utils.is_passive_user(vars, history_len=2):
    #     # linkto to particular skill
    #     offer_topic_choose = compose_topic_offering(vars, excluded_skills=excluded_skills)
    # else:
    #     # what do you want to talk about?
    #     offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS["what_to_talk_about"])

    state_utils.save_to_shared_memory(vars, greeting_step_id=GREETING_STEPS.index("what_to_talk_about") + 1)
    return offer_topic_choose


##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extension.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################
# utils
##################################################################################################################


# curl -H "Content-Type: application/json" -XPOST http://0.0.0.0:8088/respond \
#   -d '{"text":["Hello, my dog [MASK] cute"]}'
def masked_lm(templates=None, prob_threshold=0.0, probs_flag=False):
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


##################################################################################################################
# std false positive turn on handling
##################################################################################################################


def false_positive_request(ngrams, vars):
    # SYS_FP
    flag = (
        bool(re.search(common_greeting.FALSE_POSITIVE_TURN_ON_RE, state_utils.get_last_human_utterance(vars)["text"]))
        and state_utils.get_human_utter_index(vars) == 0
    )
    return flag


def false_positive_response(vars):
    # USR_FP
    state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
    state_utils.set_can_continue(vars, MUST_CONTINUE)
    return "Hi! Seems like Alexa decided to turn me on. Do you want to chat with me?"


def bye_response(vars):
    state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
    state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
    return f"Sorry, bye. #+#exit"


##################################################################################################################
# std hello
##################################################################################################################


def hello_request(ngrams, vars):
    # SYS_HELLO
    flag = True
    flag = flag and len(vars["agent"]["dialog"]["human_utterances"]) == 1
    flag = flag
    return flag


def hello_response(vars):
    # USR_HELLO_AND_CONTNIUE
    bot_utt = state_utils.get_last_bot_utterance(vars)["text"].lower()
    try:
        if condition_utils.is_lets_chat_about_topic(vars):
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        else:
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, MUST_CONTINUE)
        which_start = random.choice(
            [
                # "starter_weekday",
                # "starter_genre",
                "how_are_you",
                # "what_is_your_name",
                # "what_to_talk_about"
            ]
        )
        state_utils.save_to_shared_memory(vars, greeting_type=which_start)
        if which_start == "how_are_you":
            after_hello_resp = random.choice(common_greeting.HOW_ARE_YOU_RESPONSES)
        elif which_start == "what_is_your_name":
            after_hello_resp = random.choice(common_greeting.WHAT_IS_YOUR_NAME_RESPONSES)
        elif which_start == "starter_genre":
            after_hello_resp = starter_flow.genre_response(vars)
        elif which_start == "starter_weekday":
            after_hello_resp = starter_flow.weekday_response(vars)
        else:
            # what_to_talk_about
            after_hello_resp = offer_topic_response_part(vars)
            # set_confidence
            set_confidence_by_universal_policy(vars)
        if "seems like alexa decided to turn me on" in bot_utt:
            return after_hello_resp
        else:
            return f"{common_greeting.HI_THIS_IS_ALEXA} {after_hello_resp}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# bot asks: how are you
##################################################################################################################
HOW_ARE_YOU_TEMPLATE = re.compile(r"(how are you|what about you|how about you|and you|how you doing)", re.IGNORECASE)
HOW_ARE_YOU_PRECISE_TEMPLATE = re.compile(
    r"(how (are )?you( doing)?( today)?|how are things|what('s| is| us) up)(\?|$)", re.IGNORECASE
)
ANY_YOU_TEMPLATE = re.compile(r"\b(you|your|yours|yourself)\b", re.IGNORECASE)


def how_are_you_request(ngrams, vars):
    # SYS_USR_ASKS_BOT_HOW_ARE_YOU
    prev_frindship_skill = state_utils.get_last_bot_utterance(vars).get("active_skill", "") == "dff_friendship_skill"
    how_are_you_found = HOW_ARE_YOU_TEMPLATE.search(state_utils.get_last_human_utterance(vars)["text"])
    how_are_you_precise_found = HOW_ARE_YOU_PRECISE_TEMPLATE.search(state_utils.get_last_human_utterance(vars)["text"])
    how_are_you_by_bot_found = HOW_ARE_YOU_TEMPLATE.search(state_utils.get_last_bot_utterance(vars)["text"])
    any_you_in_user = ANY_YOU_TEMPLATE.search(state_utils.get_last_human_utterance(vars)["text"])

    if how_are_you_precise_found:
        return True
    elif prev_frindship_skill and (how_are_you_found or (how_are_you_by_bot_found and any_you_in_user)):
        return True
    return False


def how_are_you_response(vars):
    # USR_STD_GREETING
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, MUST_CONTINUE)
        how_bot_is_doing_resp = random.choice(common_greeting.HOW_BOT_IS_DOING_RESPONSES)

        question_about_activities = random.choice(common_greeting.GREETING_QUESTIONS["recent_personal_events"])
        response = (
            f"{how_bot_is_doing_resp} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES)} "
            f"{question_about_activities}"
        )
        state_utils.save_to_shared_memory(vars, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user answers how is he/she doing and asks what do you do on weekdays
##################################################################################################################


def positive_or_negative_request(ngrams, vars):
    # SYS_USR_ANSWERS_HOW_IS_HE_DOING
    usr_sentiment = state_utils.get_human_sentiment(vars)
    pos_temp = is_positive_regexp_based(state_utils.get_last_human_utterance(vars))
    neg_temp = is_negative_regexp_based(state_utils.get_last_human_utterance(vars))

    bot_asked_how_are_you = any(
        [resp in state_utils.get_last_bot_utterance(vars)["text"] for resp in common_greeting.HOW_ARE_YOU_RESPONSES]
    )
    if bot_asked_how_are_you and (usr_sentiment in ["positive", "negative"] or pos_temp or neg_temp):
        return True
    return False


def health_problems(vars):
    if HEALTH_PROBLEMS.search(state_utils.get_last_human_utterance(vars)["text"]):
        return True
    return False


def no_requests_request(ngrams, vars):
    return condition_utils.no_requests(vars)


def no_special_switch_off_requests_request(ngrams, vars):
    return condition_utils.no_special_switch_off_requests(vars)


def how_human_is_doing_response(vars):
    # USR_STD_GREETING
    try:
        usr_sentiment = state_utils.get_human_sentiment(vars)
        _no_entities = len(state_utils.get_nounphrases_from_human_utterance(vars)) == 0
        _no_requests = condition_utils.no_requests(vars)
        _is_unhealthy = health_problems(vars)
        if is_positive_regexp_based(state_utils.get_last_human_utterance(vars)):
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, MUST_CONTINUE)
            user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS)
        elif _is_unhealthy or is_negative_regexp_based(state_utils.get_last_human_utterance(vars)):
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            user_mood_acknowledgement = (
                f"{random.choice(common_greeting.BAD_MOOD_REACTIONS)} "
                f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP)}"
            )
            state_utils.add_acknowledgement_to_response_parts(vars)
        else:
            if _no_entities and _no_requests and usr_sentiment != "negative":
                # we do not set super conf for negative responses because we hope that emotion_skill will respond
                state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

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
        response = (
            f"{user_mood_acknowledgement} {random.choice(common_greeting.WHAT_DO_YOU_DO_RESPONSES)} "
            f"{question_about_activities}"
        )
        state_utils.save_to_shared_memory(vars, greeting_step_id=GREETING_STEPS.index("recent_personal_events") + 1)
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# bot offers topics to discuss
##################################################################################################################


def offer_topics_choice_response(vars):
    # TODO
    try:
        offer_topic_choose = offer_topic_response_part(vars)
        state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
        return f"{offer_topic_choose}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def offered_topic_choice_declined_response(vars):
    # USR_STD_GREETING
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, MUST_CONTINUE)
        greeting_step_id = 0
        # what do you want to talk about?
        offer_topic_choose = random.choice(common_greeting.GREETING_QUESTIONS["what_to_talk_about"])
        state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1)

        return f"Okay. {offer_topic_choose}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# bot asks: how do you spend your free time
##################################################################################################################


def was_what_do_you_do_request(ngrams, vars):
    bot_uttr_text = state_utils.get_last_bot_utterance(vars).get("text", "")
    if condition_utils.no_requests(vars) and any(
        [phrase in bot_uttr_text for phrase in common_greeting.GREETING_QUESTIONS["what_do_you_do_on_weekdays"]]
    ):
        return True
    return False


##################################################################################################################
# bot shares list activities
##################################################################################################################


def is_yes_request(ngrams, vars):
    if condition_utils.is_yes_vars(vars):
        return True
    return False


def is_no_request(ngrams, vars):
    if condition_utils.is_no_vars(vars):
        return True
    return False


def not_is_no_request(ngrams, vars):
    if not condition_utils.is_no_vars(vars):
        return True
    return False


##################################################################################################################
# std greeting
##################################################################################################################
# std greeting
# from common.utils import get_skill_outputs_from_dialog, get_outputs_with_response_from_dialog, get_not_used_template


def std_greeting_request(ngrams, vars):
    flag = True
    # flag = flag and not condition_utils.is_new_human_entity(vars)
    # flag = flag and not condition_utils.is_switch_topic(vars)
    # flag = flag and not condition_utils.is_opinion_request(vars)
    # flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    # flag = flag and not condition_utils.is_question(vars)
    # flag = flag and condition_utils.is_begin_of_dialog(vars)
    if flag:
        shared_memory = state_utils.get_shared_memory(vars)
        flag = flag and shared_memory.get("greeting_step_id", 0) < len(GREETING_STEPS)
    logger.info(f"std_greeting_request={flag}")
    return flag


def std_greeting_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        greeting_step_id = shared_memory.get("greeting_step_id", 0)

        _friendship_was_active = "dff_friendship_skill" == state_utils.get_last_bot_utterance(vars).get(
            "active_skill", ""
        )
        _entities = state_utils.get_nounphrases_from_human_utterance(vars)
        _no_requests = condition_utils.no_requests(vars)
        _nothing_dont_know = COMPILE_SOMETHING.search(state_utils.get_last_human_utterance(vars)["text"])

        # acknowledgement, confidences
        if _nothing_dont_know or (_no_requests and len(_entities) == 0):
            if _friendship_was_active and greeting_step_id >= 1:
                ack = random.choice(
                    common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY[GREETING_STEPS[greeting_step_id - 1]]
                )
                state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
                state_utils.set_can_continue(vars, MUST_CONTINUE)
            else:
                ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
                state_utils.set_confidence(vars, confidence=MIDDLE_CONFIDENCE)
                state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            state_utils.add_acknowledgement_to_response_parts(vars)
        elif not _no_requests and len(_entities) > 0:
            # user wants to talk about something particular. We are just a dummy response, if no appropriate
            if _friendship_was_active:
                ack = random.choice(
                    common_greeting.AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY["what_do_you_do_on_weekdays"]
                )
                sent_ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
                ack = f"{sent_ack} {ack}"
            else:
                ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
            state_utils.set_confidence(vars, confidence=MIDDLE_CONFIDENCE)
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
            state_utils.add_acknowledgement_to_response_parts(vars)
        else:
            if len(_entities) == 0 or _no_requests:
                state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            else:
                state_utils.set_confidence(vars, confidence=MIDDLE_CONFIDENCE)
            # some request by user detected OR no requests but some entities detected
            if _friendship_was_active and GREETING_STEPS[greeting_step_id] == "recent_personal_events":
                ack = random.choice(common_greeting.INTERESTING_PERSON_THANKS_FOR_CHATTING)
            else:
                ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
            state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)

        if health_problems(vars):
            ack = f"I'm so sorry to hear that. Hope, everything will be fine soon."
            state_utils.add_acknowledgement_to_response_parts(vars)

        if greeting_step_id == 0 or GREETING_STEPS[greeting_step_id] == "what_to_talk_about":
            prev_active_skills = [uttr.get("active_skill", "") for uttr in vars["agent"]["dialog"]["bot_utterances"]][
                -5:
            ]
            disliked_skills = state_utils.get_disliked_skills(vars)
            body = offer_topic_response_part(vars, excluded_skills=prev_active_skills + disliked_skills)
        else:
            body = random.choice(common_greeting.GREETING_QUESTIONS[GREETING_STEPS[greeting_step_id]])

        state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1)

        return f"{ack} {body}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# new_entities_is_needed_for
##################################################################################################################


def new_entities_is_needed_for_request(ngrams, vars):
    flag = True
    flag = flag and condition_utils.is_first_time_of_state(vars, State.SYS_NEW_ENTITIES_IS_NEEDED_FOR)
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    flag = flag and condition_utils.is_new_human_entity(vars)
    logger.info(f"new_entities_is_needed_for_request={flag}")
    return flag


# curl  -H "Content-Type: application/json" -XPOST http://0.0.0.0:8065/comet \
#       -d '{"input": "cars", "category": "DesireOf"}'
def new_entities_is_needed_for_response(vars):
    try:
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
        body = "Tell me more about that."
        state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# closed answer
##################################################################################################################


def closed_answer_request(ngrams, vars):
    flag = True
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    logger.info(f"closed_answer_request={flag}")
    return flag


def closed_answer_response(vars):
    ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)
    body = ""

    set_confidence_by_universal_policy(vars)
    state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
    return " ".join([ack, body])


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_FP: false_positive_request,
        State.SYS_HELLO: hello_request,
        State.SYS_USR_ASKS_BOT_HOW_ARE_YOU: how_are_you_request,
        State.SYS_STD_GREETING: std_greeting_request,
        State.SYS_CLOSED_ANSWER: new_entities_is_needed_for_request,
        State.SYS_LINK_TO_BY_ENITY: link_to_by_enity_request,
        (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_FP

simplified_dialogflow.add_system_transition(State.SYS_FP, State.USR_FP, false_positive_response)
simplified_dialogflow.set_error_successor(State.SYS_FP, State.SYS_ERR)


simplified_dialogflow.add_user_serial_transitions(
    State.USR_FP,
    {State.SYS_USER_WANTS_TALK: not_is_no_request, State.SYS_USER_DOESNT_WANT_TALK: is_no_request},
)
simplified_dialogflow.set_error_successor(State.USR_FP, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_USER_WANTS_TALK, State.USR_HELLO_AND_CONTNIUE, hello_response)
simplified_dialogflow.set_error_successor(State.SYS_USER_WANTS_TALK, State.SYS_ERR)


simplified_dialogflow.add_system_transition(State.SYS_USER_DOESNT_WANT_TALK, State.USR_TURN_OFF, bye_response)
simplified_dialogflow.set_error_successor(State.SYS_USER_DOESNT_WANT_TALK, State.SYS_ERR)


##################################################################################################################
#  SYS_HELLO

simplified_dialogflow.add_system_transition(State.SYS_HELLO, State.USR_HELLO_AND_CONTNIUE, hello_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_HELLO_AND_CONTNIUE,
    {
        # State.SYS_STD_GREETING: std_greeting_request,
        (scopes.STARTER, StarterState.USR_START): starter_flow.starter_request,  # ["starter_genre", "starter_weekday"]
        State.SYS_USR_ASKS_BOT_HOW_ARE_YOU: how_are_you_request,
        State.SYS_USR_ANSWERS_HOW_IS_HE_DOING: no_requests_request,
        # (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HELLO_AND_CONTNIUE, State.SYS_ERR)

##################################################################################################################
#  SYS_USR_ASKS_BOT_HOW_ARE_YOU

simplified_dialogflow.add_system_transition(
    State.SYS_USR_ASKS_BOT_HOW_ARE_YOU, State.USR_STD_GREETING, how_are_you_response
)

##################################################################################################################
#  SYS_USR_ANSWERS_HOW_IS_HE_DOING

simplified_dialogflow.add_system_transition(
    State.SYS_USR_ANSWERS_HOW_IS_HE_DOING, State.USR_STD_GREETING, how_human_is_doing_response
)

##################################################################################################################
#  SYS_STD_GREETING

simplified_dialogflow.add_system_transition(State.SYS_STD_GREETING, State.USR_STD_GREETING, std_greeting_response)

##################################################################################################################
#  USR_STD_GREETING

simplified_dialogflow.add_user_serial_transitions(
    State.USR_STD_GREETING,
    {
        # State.SYS_OFFER_TOPICS: was_what_do_you_do_request,
        State.SYS_OFFERED_TOPICS_DECLINED: offered_topic_choice_declined_request,
        State.SYS_ASKED_EVENTS_AND_YES_INTENT: asked_for_events_and_got_yes_request,
        State.SYS_STD_GREETING: std_greeting_request,
    },
)

simplified_dialogflow.set_error_successor(State.USR_STD_GREETING, State.SYS_ERR)

##################################################################################################################
#  SYS_OFFER_TOPICS

simplified_dialogflow.add_system_transition(
    State.SYS_OFFER_TOPICS, State.USR_STD_GREETING, offer_topics_choice_response
)
##################################################################################################################
#  SYS_ASKED_EVENTS_AND_YES_INTENT

simplified_dialogflow.add_system_transition(
    State.SYS_ASKED_EVENTS_AND_YES_INTENT, State.USR_STD_GREETING, clarify_event_response
)
##################################################################################################################
#  SYS_OFFERED_TOPICS_DECLINED

simplified_dialogflow.add_system_transition(
    State.SYS_OFFERED_TOPICS_DECLINED, State.USR_STD_GREETING, offered_topic_choice_declined_response
)

##################################################################################################################
# #  SYS_NEW_ENTITIES_IS_NEEDED_FOR
# simplified_dialogflow.add_system_transition(
#     State.SYS_NEW_ENTITIES_IS_NEEDED_FOR,
#     State.USR_NEW_ENTITIES_IS_NEEDED_FOR,
#     new_entities_is_needed_for_response,
# )
# simplified_dialogflow.set_error_successor(State.SYS_NEW_ENTITIES_IS_NEEDED_FOR, State.SYS_ERR)


# simplified_dialogflow.add_user_transition(
#     State.USR_NEW_ENTITIES_IS_NEEDED_FOR,
#     State.SYS_CLOSED_ANSWER,
#     closed_answer_request,
# )


# simplified_dialogflow.set_error_successor(State.USR_NEW_ENTITIES_IS_NEEDED_FOR, State.SYS_ERR)
##################################################################################################################
#  SYS_CLOSED_ANSWER

simplified_dialogflow.add_system_transition(
    State.SYS_CLOSED_ANSWER,
    State.USR_CLOSED_ANSWER,
    closed_answer_response,
)

simplified_dialogflow.add_user_transition(
    State.USR_CLOSED_ANSWER,
    State.SYS_LINK_TO_BY_ENITY,
    link_to_by_enity_request,
)
simplified_dialogflow.set_error_successor(State.USR_CLOSED_ANSWER, State.SYS_ERR)

##################################################################################################################
#  SYS_LINK_TO_BY_ENITY

simplified_dialogflow.add_system_transition(
    State.SYS_LINK_TO_BY_ENITY,
    State.USR_LINK_TO_BY_ENITY,
    link_to_by_enity_response,
)

simplified_dialogflow.add_user_transition(
    State.USR_LINK_TO_BY_ENITY,
    State.SYS_STD_GREETING,
    std_greeting_request,
)
simplified_dialogflow.set_error_successor(State.USR_LINK_TO_BY_ENITY, State.SYS_ERR)


##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)


dialogflow = simplified_dialogflow.get_dialogflow()
