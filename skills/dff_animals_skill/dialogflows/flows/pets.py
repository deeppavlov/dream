import logging
import random
import os
import re
import sentry_sdk
from enum import Enum, auto

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no
from common.animals import MY_CAT, MY_DOG

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

question_cat = "Would you like to learn more about my cat?"
question_dog = "Would you like to learn more about my dog?"

CONF_1 = 1.0


class State(Enum):
    USR_START = auto()
    #
    SYS_MY_CAT_1 = auto()
    SYS_MY_DOG_1 = auto()
    #
    USR_MY_CAT_1 = auto()
    USR_MY_DOG_1 = auto()
    #
    SYS_MY_CAT_2 = auto()
    SYS_MY_DOG_2 = auto()
    #
    USR_MY_CAT_2 = auto()
    USR_MY_DOG_2 = auto()
    #
    SYS_MY_CAT_3 = auto()
    SYS_MY_DOG_3 = auto()
    #
    USR_MY_CAT_3 = auto()
    USR_MY_DOG_3 = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


def my_cat_1_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_cat = shared_memory.get("told_about_cat", False)
    have_cat = re.findall(r"(do|did) you have (a )?(cat)s?", text)
    if (not isno or have_cat) and not told_about_cat:
        flag = True
    logger.info(f"my_cat_1_request={flag}")
    return flag


def my_dog_1_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_dog = shared_memory.get("told_about_dog", False)
    have_dog = re.findall(r"(do|did) you have (a )?(dog)s?", text)
    if (not isno or have_dog) and not told_about_dog:
        flag = True
    logger.info(f"my_dog_1_request={flag}")
    return flag


def my_cat_2_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_cat_2_request={flag}")
    return flag


def my_dog_2_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_dog_2_request={flag}")
    return flag


def my_cat_3_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_cat_3_request={flag}")
    return flag


def my_dog_3_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_dog_3_request={flag}")
    return flag


def my_cat_1_response(vars):
    random.shuffle(MY_CAT)
    fact = MY_CAT[0]
    response = " ".join([fact, question_cat])
    state_utils.save_to_shared_memory(vars, told_about_cat=True)
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def my_cat_2_response(vars):
    fact = MY_CAT[1]
    response = " ".join([fact, question_cat])
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def my_cat_3_response(vars):
    fact = MY_CAT[2]
    response = " ".join([fact, question_cat])
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def my_dog_1_response(vars):
    random.shuffle(MY_DOG)
    fact = MY_DOG[0]
    response = " ".join([fact, question_dog])
    state_utils.save_to_shared_memory(vars, told_about_dog=True)
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def my_dog_2_response(vars):
    fact = MY_DOG[1]
    response = " ".join([fact, question_dog])
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def my_dog_3_response(vars):
    fact = MY_DOG[2]
    response = " ".join([fact, question_dog])
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(State.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_MY_CAT_1: my_cat_1_request,
        State.SYS_MY_DOG_1: my_dog_1_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MY_CAT_1, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MY_DOG_1, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(State.SYS_MY_CAT_1, State.USR_MY_CAT_1, my_cat_1_response, )
simplified_dialog_flow.add_system_transition(State.SYS_MY_DOG_1, State.USR_MY_DOG_1, my_dog_1_response, )

simplified_dialog_flow.set_error_successor(State.USR_MY_CAT_1, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_MY_DOG_1, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_MY_CAT_1,
    {
        State.SYS_MY_CAT_2: my_cat_2_request,
        State.SYS_MY_DOG_1: my_dog_1_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_MY_DOG_1,
    {
        State.SYS_MY_DOG_2: my_dog_2_request,
        State.SYS_MY_CAT_1: my_cat_1_request,
    },
)

simplified_dialog_flow.set_error_successor(State.SYS_MY_CAT_2, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MY_DOG_2, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(State.SYS_MY_CAT_2, State.USR_MY_CAT_2, my_cat_2_response, )
simplified_dialog_flow.add_system_transition(State.SYS_MY_DOG_2, State.USR_MY_DOG_2, my_dog_2_response, )

simplified_dialog_flow.set_error_successor(State.USR_MY_CAT_2, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_MY_DOG_2, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_MY_CAT_2,
    {
        State.SYS_MY_CAT_3: my_cat_3_request,
        State.SYS_MY_DOG_1: my_dog_1_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_MY_DOG_2,
    {
        State.SYS_MY_DOG_3: my_dog_3_request,
        State.SYS_MY_CAT_1: my_cat_1_request,
    },
)

simplified_dialog_flow.set_error_successor(State.SYS_MY_CAT_3, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MY_DOG_3, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(State.SYS_MY_CAT_3, State.USR_MY_CAT_3, my_cat_3_response, )
simplified_dialog_flow.add_system_transition(State.SYS_MY_DOG_3, State.USR_MY_DOG_3, my_dog_3_response, )

simplified_dialog_flow.set_error_successor(State.USR_MY_CAT_3, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_MY_DOG_3, State.SYS_ERR)
