# %%
import os
import re
import logging
from os import getenv
from enum import Enum, auto

import sentry_sdk

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.condition as condition_utils
import common.dialogflow_framework.utils.state as state_utils

import dialogflows.scopes as scopes

from common.utils import get_types_from_annotations
from common.celebrities import talk_about_celebrity
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_CONTINUE_SCENARIO_DONE
from CoBotQA.cobotqa_service import send_cobotqa

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

ENTITY_LINKING_URL = getenv("ENTITY_LINKING_URL")
assert ENTITY_LINKING_URL is not None

CONF_HIGH = 0.95
CONF_MEDIUM = 0.85
CONF_LOW = 0.75


class State(Enum):
    USR_START = auto()
    USR_FAVOURITE_CELEBRITY = auto()
    USR_ASK_ANOTHER_FACT = auto()
    USR_ANSWERS_QUESTION = auto()
    USR_TELLS_SOMETHING = auto()
    USR_TELLS_A_FILM = auto()
    USR_YESNO_1 = auto()
    USR_YESNO_2 = auto()

    SYS_GIVE_A_FACT = auto()
    SYS_EXIT = auto()
    SYS_ASKS_A_FACT = auto()
    SYS_ASKS_A_FILM = auto()
    SYS_GOTO_CELEBRITY = auto()
    SYS_CELEBRITY_FIRST_MENTIONED = auto()
    SYS_CELEBRITY_TELL_OTHERJOBS = auto()
    SYS_TALK_ABOUT_CELEBRITY = auto()
    SYS_ACKNOWLEDGE_LINKTO_CELEBRITY = auto()
    SYS_ERR = auto()


dontwant_regex = re.compile(r"(not like|not want to talk|not want to hear|not concerned about|"
                            r"over the |stop talking about|no more |do not watch|"
                            r"not want to listen)", re.IGNORECASE)

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
# ....
##################################################################################################################
# std greeting
##################################################################################################################

def default_condition_request(ngram, vars):
    flag = True
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    flag = flag and not condition_utils.is_question(vars)
    return flag


def yes_request(ngrams, vars):
    flag = condition_utils.is_yes_vars(vars)
    logger.info(f'yes_request: {flag}')
    return flag


def yes_actor_request(ngrams, vars):
    flag = condition_utils.is_yes_vars(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    is_actor = shared_memory.get("actor", False)
    flag = flag and is_actor
    return flag


def no_request(ngrams, vars):
    flag = condition_utils.is_no_vars(vars)
    logger.info(f'no_request: {flag}')
    return flag


def dont_want_request(ngrams, vars):
    human_utterance_text = state_utils.get_last_human_utterance(vars)['text'].lower()
    flag = bool(re.search(dontwant_regex, human_utterance_text))
    logger.info(f'dont_want_request: {flag}')
    return flag


def talk_about_celebrity_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    bot_utterance = state_utils.get_last_bot_utterance(vars)
    flag = talk_about_celebrity(human_utterance, bot_utterance)
    logger.info(f'talk_about_celebrity_request: {flag}')
    return flag


def give_fact_request(ngrams, vars):
    bot_utterance = state_utils.get_last_bot_utterance(vars)
    flag = all([bot_utterance['active_skill'] == 'celebrity_skill',
                condition_utils.is_yes_vars(vars),
                celebrity_in_any_phrase_request(ngrams, vars)])
    logger.info(f'give_fact: {flag}')
    return flag


def celebrity_in_phrase_request(ngrams, vars, use_only_last_utt=True):
    flag = bool(get_celebrity(vars, use_only_last_utt=use_only_last_utt)[0])
    logger.info(f'celebrity_in_phrase_request : {flag}')
    return flag


def celebrity_in_any_phrase_request(ngrams, vars):
    flag = celebrity_in_phrase_request(ngrams, vars, use_only_last_utt=False)
    logger.info(f'celebrity_in_any_phrase_request : {flag}')
    return flag


def get_cobot_fact(celebrity_name, given_facts):
    logger.debug(f'Calling cobot_fact for {celebrity_name} {given_facts}')
    answer = send_cobotqa(f'fact about {celebrity_name}')
    if answer is None:
        logger.debug('Answer from cobotqa not obtained')
        return None
    for phrase_ in ['This might answer your question', 'According to Wikipedia']:
        if phrase_ in answer:
            answer = answer.split(phrase_)[1]
    logger.debug(f'Answer from cobot_fact obtained {answer}')
    if answer not in given_facts:
        return answer
    else:
        return ''


def get_celebrity(vars, exclude_types=False, use_only_last_utt=False):
    # if 'agent' not in vars:
    #     vars = {'agent': vars}
    shared_memory = state_utils.get_shared_memory(vars)
    last_utterance_with_celebrity = shared_memory.get("last_utterance_with_celebrity", {"annotations": {}, "text": ""})
    dialog = vars["agent"]['dialog']
    if use_only_last_utt:
        utterances_to_iterate = [state_utils.get_last_human_utterance(vars)]
    else:
        utterances_to_iterate = dialog["human_utterances"][::-1] + [last_utterance_with_celebrity]
    texts_to_iterate = [j['text'] for j in utterances_to_iterate]
    logger.debug(f'Calling get_celebrity on {texts_to_iterate} exclude_types {exclude_types} {use_only_last_utt}')
    raw_profession_list = ['Q33999',  # actor
                           "Q10800557",  # film actor
                           "Q10798782",  # television actor
                           "Q2405480",  # voice actor
                           'Q17125263',  # youtuber
                           'Q245068',  # comedian
                           'Q2066131',  # sportsman
                           'Q947873',  # television presenter
                           'Q2405480',  # comedian
                           'Q211236',  # celebrity
                           'Q177220']  # singer
    actor_profession_list = raw_profession_list[:4]
    mentioned_otherjobs = shared_memory.get('mentioned_otherjobs', [])
    if exclude_types:
        raw_profession_list = raw_profession_list + mentioned_otherjobs
    for human_utterance in utterances_to_iterate:
        celebrity_name, celebrity_type, celebrity_raw_type = get_types_from_annotations(
            human_utterance['annotations'], tocheck_relation='occupation',
            types=raw_profession_list, exclude_types=exclude_types)
        if exclude_types:
            state_utils.save_to_shared_memory(vars, mentioned_otherjobs=[celebrity_raw_type])
        if celebrity_name is not None:
            logger.debug(f'Answer for get_celebrity exclude_types {exclude_types} : {celebrity_name} {celebrity_type}')
            state_utils.save_to_shared_memory(vars, last_utterance_with_celebrity=human_utterance)
            met_actor = celebrity_raw_type in actor_profession_list
            state_utils.save_to_shared_memory(vars, actor=met_actor)
            return celebrity_name, celebrity_type
    logger.debug(f'For get_celebrity no answer obtained')
    return None, None


def propose_celebrity_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_HIGH)
    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
    try:
        celebrity, celebrity_name = get_celebrity(vars)
        assert celebrity and celebrity_name
        answer = f'{celebrity} is an amazing {celebrity_name} ! May I tell you something about this person?'
        return answer
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def celebrity_fact_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_HIGH)
    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
    try:
        logger.debug('Getting celebrity facts')
        celebrity_name, celebrity_type = get_celebrity(vars)
        shared_memory = state_utils.get_shared_memory(vars)
        given_facts = shared_memory.get('given_facts', [])
        logger.debug(f'Given facts in memory {given_facts}')
        num_attempts = 2
        curr_fact = ''
        next_fact = shared_memory.get('next_fact', '')
        for _ in range(num_attempts):
            if next_fact:
                curr_fact = next_fact
                next_fact = ''
            if not curr_fact:
                curr_fact = get_cobot_fact(celebrity_name, given_facts)
            if not next_fact:
                next_fact = get_cobot_fact(celebrity_name, given_facts + [curr_fact])
        if not next_fact:
            celebrity_name, celebrity_otherjob = get_celebrity(vars, exclude_types=True)
            next_fact = f'{celebrity_name} is also a {celebrity_otherjob}.'
        assert curr_fact
        reply = f'{curr_fact}'
        if next_fact:
            reply = f'{reply} May I tell you another fact about this {celebrity_type}?'
        state_utils.save_to_shared_memory(vars, given_facts=given_facts + [curr_fact], next_fact=next_fact)
        logger.debug(f'In function celebrity_fact_response answer {reply}')
        return reply
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def celebrity_otherjob_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_HIGH)
    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
    try:
        celebrity_name, celebrity_otherjob = get_celebrity(vars, exclude_types=True)
        assert celebrity_otherjob and celebrity_name
        reply = f'{celebrity_name} is also a {celebrity_otherjob}. May I tell you something else about this person?'
        state_utils.set_confidence(vars, confidence=CONF_HIGH)
        state_utils.set_can_continue(vars)
        return reply
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def info_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_MEDIUM)
    state_utils.set_can_continue(vars)
    return 'Could you please tell me more about this person?'


def acknowledge_and_link_to_celebrity_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_MEDIUM)
    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
    return f"Sounds interesting. But let's talk about something else. {favourite_celebrity_response(vars)}"


def link_to_celebrity_response(vars):
    return f"OK. {favourite_celebrity_response(vars)}"


def ask_film_response(vars):
    state_utils.set_confidence(vars, confidence=CONF_MEDIUM)
    state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO_DONE)
    return "What is your favourite film with this actor?"


def favourite_celebrity_response(vars):
    try:
        celebrity_questions = ["What is your favourite celebrity?",
                               "What celebrity was the first one you really loved?",
                               "Whom do you follow on Facebook?"]
        confidences = [CONF_HIGH, CONF_MEDIUM, CONF_LOW]  # we becone less confident by the flow
        shared_memory = state_utils.get_shared_memory(vars)
        asked_questions = shared_memory.get('asked_questions', [])
        for i, celebrity_question in enumerate(celebrity_questions):
            if celebrity_question not in asked_questions:
                state_utils.save_to_shared_memory(vars, asked_questions=asked_questions + [celebrity_question])
                confidence = confidences[i]
                state_utils.set_confidence(vars, confidence=confidence)
                if i == 0:
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
                else:
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO_DONE)
                return celebrity_question
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
    return error_response(vars)


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return "Sorry"


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START
# TO ADD TRANSITIONS!!!!
simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_CELEBRITY_FIRST_MENTIONED: celebrity_in_phrase_request,
        State.SYS_TALK_ABOUT_CELEBRITY: talk_about_celebrity_request
    },
)

simplified_dialogflow.add_system_transition(State.SYS_TALK_ABOUT_CELEBRITY, State.USR_FAVOURITE_CELEBRITY,
                                            favourite_celebrity_response)
simplified_dialogflow.add_system_transition(State.SYS_CELEBRITY_FIRST_MENTIONED, State.USR_YESNO_1,
                                            propose_celebrity_response)
simplified_dialogflow.add_user_serial_transitions(
    State.USR_FAVOURITE_CELEBRITY,
    {
        State.SYS_CELEBRITY_FIRST_MENTIONED: celebrity_in_any_phrase_request,
        State.SYS_EXIT: dont_want_request,
        State.SYS_ASKS_A_FACT: default_condition_request
    },
)

simplified_dialogflow.add_system_transition(State.SYS_ASKS_A_FACT, State.USR_TELLS_SOMETHING,
                                            info_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ANSWERS_QUESTION,
    {
        State.SYS_EXIT: dont_want_request,
        State.SYS_ACKNOWLEDGE_LINKTO_CELEBRITY: default_condition_request
    },
)

simplified_dialogflow.add_system_transition(State.SYS_ACKNOWLEDGE_LINKTO_CELEBRITY, State.USR_FAVOURITE_CELEBRITY,
                                            acknowledge_and_link_to_celebrity_response)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_YESNO_1,
    {
        State.SYS_CELEBRITY_TELL_OTHERJOBS: yes_request,  # function calling
        State.SYS_EXIT: dont_want_request,
        State.SYS_GOTO_CELEBRITY: no_request
    },
)
##################################################################################################################
#  SYS_HI

simplified_dialogflow.add_system_transition(State.SYS_CELEBRITY_TELL_OTHERJOBS, State.USR_YESNO_2,
                                            celebrity_otherjob_response)
simplified_dialogflow.add_system_transition(State.SYS_GOTO_CELEBRITY, State.USR_FAVOURITE_CELEBRITY,
                                            link_to_celebrity_response)
simplified_dialogflow.add_user_serial_transitions(
    State.USR_YESNO_2,
    {
        State.SYS_ASKS_A_FILM: yes_actor_request,
        State.SYS_GIVE_A_FACT: yes_request,
        State.SYS_EXIT: dont_want_request,
        State.SYS_GOTO_CELEBRITY: no_request
    },
)
simplified_dialogflow.add_system_transition(State.SYS_GIVE_A_FACT, State.USR_ASK_ANOTHER_FACT, celebrity_fact_response)
simplified_dialogflow.add_system_transition(State.SYS_ASKS_A_FILM, State.USR_TELLS_A_FILM, ask_film_response)


for state_ in State:
    simplified_dialogflow.set_error_successor(state_, State.SYS_ERR)

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
##################################################################################################################
#  Compile and get dialogflow
##################################################################################################################
# do not foget this line
dialogflow = simplified_dialogflow.get_dialogflow()
