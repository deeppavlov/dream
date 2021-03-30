# %%
import random
import re
import os
import logging
from enum import Enum, auto

import numpy as np
import requests
import sentry_sdk

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.utils as common_utils
import common.greeting as common_greeting
import common.link as common_link
import dialogflows.scopes as scopes
import dialogflows.flows.weekend as weekend_flow

from dialogflows.flows.shared import link_to_by_enity_request
from dialogflows.flows.shared import link_to_by_enity_response


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)


class State(Enum):
    USR_START = auto()

    SYS_HELLO = auto()
    USR_HELLO_AND_CONTNIUE = auto()
    SYS_USR_ASKS_BOT_HOW_ARE_YOU = auto()
    SYS_USR_ANSWERS_HOW_IS_HE_DOING = auto()
    USR_HOW_BOT_IS_DOING_AND_OFFER_LIST_ACTIVITIES = auto()
    SYS_SHARE_LIST_ACTIVITIES = auto()

    SYS_STD_GREETING = auto()
    USR_STD_GREETING = auto()

    SYS_NEW_ENTITIES_IS_NEEDED_FOR = auto()
    USR_NEW_ENTITIES_IS_NEEDED_FOR = auto()
    SYS_CLOSED_ANSWER = auto()
    USR_CLOSED_ANSWER = auto()
    SYS_LINK_TO_BY_ENITY = auto()
    USR_LINK_TO_BY_ENITY = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98

# %%


def compose_topic_offering(excluded_skills=[]):
    ask_about_topic = random.choice(common_greeting.GREETING_QUESTIONS["what_to_talk_about"])
    offer_topics_template = random.choice(common_greeting.TOPIC_OFFERING_TEMPLATES)

    available_topics = [topic for skill_name, topic in common_link.LIST_OF_SCRIPTED_TOPICS.items()
                        if skill_name not in excluded_skills]

    topics = np.random.choice(available_topics, size=2, replace=False)
    offer_topics = offer_topics_template.replace("TOPIC1", topics[0]).replace("TOPIC2", topics[1])

    response = f"{ask_about_topic} {offer_topics}"
    return response


##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extention.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################
# utils
##################################################################################################################
std_acknowledgements = {
    "neutral": ["Ok. ", "Oh. ", "Huh. ", "Well. ", "Gotcha. ", "Hmm. ", "Aha. "],
    "positive": ["Sounds cool! ", "Great! ", "Wonderful! "],
    "negative": ["Huh... ", "Sounds sad... ", "Sorry... "],
}


def get_sentiment_acknowledgement(vars, acknowledgements=None):
    acknowledgements = std_acknowledgements.update(acknowledgements) if acknowledgements else std_acknowledgements
    return acknowledgements.get(state_utils.get_human_sentiment(vars), [""])


# curl -H "Content-Type: application/json" -XPOST http://0.0.0.0:8088/respond \
#   -d '{"text":["Hello, my dog [MASK] cute"]}'
def masked_lm(templates=["Hello, it's [MASK] dog."], prob_threshold=0.0, probs_flag=False):
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


def set_confidence_by_universal_policy(vars):
    if not condition_utils.is_begin_of_dialog(vars, begin_dialog_n=10):
        state_utils.set_confidence(vars, 0)
    elif condition_utils.is_first_our_response(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        state_utils.set_can_continue(vars)
    elif not condition_utils.is_interrupted(vars) and common_greeting.dont_tell_you_answer(
        state_utils.get_last_human_utterance(vars)
    ):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE)
        state_utils.set_can_continue(vars)
    elif not condition_utils.is_interrupted(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
    else:
        state_utils.set_confidence(vars, MIDDLE_DIALOG_START_CONFIDENCE)
        state_utils.set_can_continue(vars)


##################################################################################################################
# std hello
##################################################################################################################

def hello_request(ngrams, vars):
    # SYS_HELLO
    flag = True
    flag = flag and len(vars["agent"]["dialog"]["human_utterances"]) == 1
    flag = flag and not condition_utils.is_lets_chat_about_topic(vars)
    return flag


def hello_response(vars):
    # USR_HELLO_AND_CONTNIUE
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars)
        which_start = random.choice(["how_are_you",
                                     "what_is_your_name",
                                     "what_to_talk_about"])
        if which_start == "how_are_you":
            after_hello_resp = random.choice(common_greeting.HOW_ARE_YOU_RESPONSES)
        elif which_start == "what_is_your_name":
            after_hello_resp = random.choice(common_greeting.WHAT_IS_YOUR_NAME_RESPONSES)
        else:
            # what_to_talk_about
            greeting_step_id = 0
            after_hello_resp = compose_topic_offering(excluded_skills=[])
            # set_confidence
            set_confidence_by_universal_policy(vars)
            state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1)

        return f"{common_greeting.HI_THIS_IS_ALEXA} {after_hello_resp}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0.)
        return error_response(vars)


##################################################################################################################
# bot asks: how are you
##################################################################################################################
HOW_ARE_YOU_TEMPLATE = re.compile(
    r"(how are you|what about you|how about you|and you|how you doing)",
    re.IGNORECASE)


def how_are_you_request(ngrams, vars):
    # SYS_USR_ASKS_BOT_HOW_ARE_YOU
    if HOW_ARE_YOU_TEMPLATE.search(state_utils.get_last_human_utterance(vars)["text"]):
        return True
    return False


def how_are_you_response(vars):
    # USR_HOW_BOT_IS_DOING_AND_OFFER_LIST_ACTIVITIES
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars)
        how_bot_is_doing_resp = random.choice(common_greeting.HOW_BOT_IS_DOING_RESPONSES)
        return f"{how_bot_is_doing_resp} {common_greeting.LIST_ACTIVITIES_OFFER}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0.)
        return error_response(vars)


##################################################################################################################
# user answers how is he/she doing
##################################################################################################################
POSITIVE_RESPONSE = re.compile(
    r"(happy|good|okay|great|yeah|cool|awesome|perfect|nice|well|ok|fine|neat|swell|peachy|excellent|splendid"
    r"|super|classy|tops|famous|superb|incredible|tremendous|class|crackajack|crackerjack)",
    re.IGNORECASE)
NEGATIVE_RESPONSE = re.compile(
    r"(sad|pity|bad|tired|poor|ill|low|inferior|miserable|naughty|nasty|foul|ugly|grisly|harmful|sick|sore"
    r"|diseased|ailing|spoiled|depraved|tained|damaged|awry|badly|sadly|wretched|awful|terrible|depressed)",
    re.IGNORECASE)


def positive_or_negative_request(ngrams, vars):
    # SYS_USR_ANSWERS_HOW_IS_HE_DOING
    usr_sentiment = state_utils.get_human_sentiment(vars)
    pos_temp = POSITIVE_RESPONSE.search(state_utils.get_last_human_utterance(vars)["text"])
    neg_temp = NEGATIVE_RESPONSE.search(state_utils.get_last_human_utterance(vars)["text"])
    if usr_sentiment in ["positive", "negative"] or pos_temp or neg_temp:
        return True
    return False


def how_human_is_doing_response(vars):
    # USR_STD_GREETING
    try:
        usr_sentiment = state_utils.get_human_sentiment(vars)
        state_utils.set_can_continue(vars)

        if POSITIVE_RESPONSE.search(state_utils.get_last_human_utterance(vars)["text"]):
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS)
        elif NEGATIVE_RESPONSE.search(state_utils.get_last_human_utterance(vars)["text"]):
            state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
            user_mood_acknowledgement = f"{random.choice(common_greeting.BAD_MOOD_REACTIONS)} " \
                                        f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP)}"
        elif usr_sentiment == "positive":
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            user_mood_acknowledgement = random.choice(common_greeting.GOOD_MOOD_REACTIONS)
        elif usr_sentiment == "negative":
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            user_mood_acknowledgement = f"{random.choice(common_greeting.BAD_MOOD_REACTIONS)} " \
                                        f"{random.choice(common_greeting.GIVE_ME_CHANCE_TO_CHEER_UP)}"
        else:
            state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
            user_mood_acknowledgement = "Okay."

        greeting_step_id = 0
        offer_topic_choose = compose_topic_offering(excluded_skills=[])
        state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1)

        return f"{user_mood_acknowledgement} {offer_topic_choose}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0.)
        return error_response(vars)


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


def share_list_activities_response(vars):
    # USR_STD_GREETING
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars)
        greeting_step_id = 0
        offer_topic_choose = compose_topic_offering(excluded_skills=[])
        state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1)

        return f"{common_greeting.LIST_ACTIVITIES_RESPONSE} {offer_topic_choose}"

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0.)
        return error_response(vars)


##################################################################################################################
# std greeting
##################################################################################################################
# std greeting
# from common.utils import get_skill_outputs_from_dialog, get_outputs_with_response_from_dialog, get_not_used_template

GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)
COMMENTS = {
    "neutral": ["Ok. ", "Oh. ", "Huh. ", "Well. ", "Gotcha. ", "Hmm. ", "Aha. "],
    "positive": ["Sounds cool! ", "Great! ", "Wonderful! "],
    "negative": ["Huh... ", "Sounds sad... ", "Sorry... "],
}


def std_greeting_request(ngrams, vars):
    flag = True
    flag = flag and not condition_utils.is_new_human_entity(vars)
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_opinion_request(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    flag = flag and not condition_utils.is_question(vars)
    flag = flag and condition_utils.is_begin_of_dialog(vars)
    if flag:
        shared_memory = state_utils.get_shared_memory(vars)
        flag = flag and shared_memory.get("greeting_step_id", 0) < len(GREETING_STEPS)
    logger.info(f"std_greeting_request={flag}")
    return flag


def std_greeting_response(vars):
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        greeting_step_id = shared_memory.get("greeting_step_id", 0)
        last_acknowledgements = shared_memory.get("last_acknowledgements", [])
        sentiment = state_utils.get_human_sentiment(vars)

        # get ack, body
        ack = common_utils.get_not_used_template(
            used_templates=last_acknowledgements, all_templates=COMMENTS[sentiment]
        )
        if greeting_step_id == 0:
            prev_active_skills = [uttr.get("active_skill", "")
                                  for uttr in vars["agent"]["dialog"]["bot_utterances"]][-5:]
            body = compose_topic_offering(excluded_skills=prev_active_skills)
        else:
            body = random.choice(common_greeting.GREETING_QUESTIONS[GREETING_STEPS[greeting_step_id]])

        # set_confidence
        set_confidence_by_universal_policy(vars)
        state_utils.save_to_shared_memory(vars, greeting_step_id=greeting_step_id + 1, last_acknowledgements=[ack])

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
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
        ack = random.choice(get_sentiment_acknowledgement(vars))
        body = "Tell me more about that."
        # new_entities = state_utils.get_new_human_labeled_noun_phrase(vars)
        # new_entity = list(new_entities)[0]

        # new_entity = new_entity if condition_utils.is_plural(new_entity) else f"a {new_entity}"
        # template = f"So you mentioned {new_entity}. Does it [MASK] for you? Tell me why?"
        # tokens = masked_lm([template], prob_threshold=0.05)[0]
        # logger.debug(f"tokens = {tokens}")

        # if tokens:
        #     body = f"So you mentioned {new_entity}. Does it {random.choice(tokens)} for you? Tell me why?"
        #     set_confidence_by_universal_policy(vars)
        # else:
        #     ack = ""
        #     body = ""
        #     state_utils.set_confidence(vars, 0)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
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
    ack = random.choice(get_sentiment_acknowledgement(vars))
    body = ""
    set_confidence_by_universal_policy(vars)
    return " ".join([ack, body])


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


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
        State.SYS_HELLO: hello_request,
        State.SYS_STD_GREETING: std_greeting_request,
        State.SYS_NEW_ENTITIES_IS_NEEDED_FOR: new_entities_is_needed_for_request,
        State.SYS_LINK_TO_BY_ENITY: link_to_by_enity_request,
        (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_HELLO

simplified_dialogflow.add_system_transition(State.SYS_HELLO, State.USR_HELLO_AND_CONTNIUE, hello_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_HELLO_AND_CONTNIUE,
    {
        State.SYS_STD_GREETING: std_greeting_request,
        State.SYS_USR_ASKS_BOT_HOW_ARE_YOU: how_are_you_request,
        State.SYS_USR_ANSWERS_HOW_IS_HE_DOING: positive_or_negative_request,
        (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HELLO_AND_CONTNIUE, State.SYS_ERR)


##################################################################################################################
#  SYS_USR_ASKS_BOT_HOW_ARE_YOU

simplified_dialogflow.add_system_transition(State.SYS_USR_ASKS_BOT_HOW_ARE_YOU,
                                            State.USR_HOW_BOT_IS_DOING_AND_OFFER_LIST_ACTIVITIES,
                                            how_are_you_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_HOW_BOT_IS_DOING_AND_OFFER_LIST_ACTIVITIES,
    {
        State.SYS_SHARE_LIST_ACTIVITIES: is_yes_request,
        (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HOW_BOT_IS_DOING_AND_OFFER_LIST_ACTIVITIES, State.SYS_ERR)

##################################################################################################################
#  SYS_SHARE_LIST_ACTIVITIES

simplified_dialogflow.add_system_transition(State.SYS_SHARE_LIST_ACTIVITIES,
                                            State.USR_STD_GREETING,
                                            share_list_activities_response)

##################################################################################################################
#  SYS_USR_ANSWERS_HOW_IS_HE_DOING

simplified_dialogflow.add_system_transition(State.SYS_USR_ANSWERS_HOW_IS_HE_DOING,
                                            State.USR_STD_GREETING,
                                            how_human_is_doing_response)

##################################################################################################################
#  SYS_STD_GREETING

simplified_dialogflow.add_system_transition(State.SYS_STD_GREETING, State.USR_STD_GREETING, std_greeting_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_STD_GREETING,
    {
        State.SYS_NEW_ENTITIES_IS_NEEDED_FOR: new_entities_is_needed_for_request,
        State.SYS_LINK_TO_BY_ENITY: link_to_by_enity_request,
        (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
    },
)


simplified_dialogflow.set_error_successor(State.USR_STD_GREETING, State.SYS_ERR)


##################################################################################################################
#  SYS_NEW_ENTITIES_IS_NEEDED_FOR
simplified_dialogflow.add_system_transition(
    State.SYS_NEW_ENTITIES_IS_NEEDED_FOR,
    State.USR_NEW_ENTITIES_IS_NEEDED_FOR,
    new_entities_is_needed_for_response,
)
simplified_dialogflow.set_error_successor(State.SYS_NEW_ENTITIES_IS_NEEDED_FOR, State.SYS_ERR)


simplified_dialogflow.add_user_transition(
    State.USR_NEW_ENTITIES_IS_NEEDED_FOR,
    State.SYS_CLOSED_ANSWER,
    closed_answer_request,
)


simplified_dialogflow.set_error_successor(State.USR_NEW_ENTITIES_IS_NEEDED_FOR, State.SYS_ERR)
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
