# %%
import os
import logging
from enum import Enum, auto

import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils

import dialogflows.scopes as scopes


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


class State(Enum):
    USR_START = auto()
    SYS_HI = auto()
    USR_HI = auto()

    SYS_OK = auto()
    USR_OK = auto()

    SYS_YES = auto()
    USR_YES = auto()

    SYS_NO = auto()
    USR_NO = auto()
    #

    SYS_GLOBAL1 = auto()
    USR_GLOBAL1 = auto()
    SYS_GLOBAL2 = auto()
    USR_GLOBAL2 = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


# %%

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
# ....

##################################################################################################################
# std greeting
##################################################################################################################


def hi_request(ngrams, vars):
    flag = True
    logger.info(f"exec hi_request={flag}")
    return flag


def hi_response(vars):
    logger.info("exec hi_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: How are you?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# ok
##################################################################################################################


def ok_request(ngrams, vars):
    flag = True
    flag = flag and "ok" in state_utils.get_last_human_utterance(vars)["text"]
    logger.info(f"exec ok_request={flag}")
    return flag


def ok_response(vars):
    logger.info("exec ok_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: It's cool"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# yes
##################################################################################################################


def yes_request(ngrams, vars):
    flag = True
    flag = flag and "yes" in state_utils.get_last_human_utterance(vars)["text"]
    logger.info(f"exec yes_request={flag}")
    return flag


def yes_response(vars):
    logger.info("exec yes_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: yes is your answer"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# no
##################################################################################################################


def no_request(ngrams, vars):
    flag = True
    flag = flag and "no" in state_utils.get_last_human_utterance(vars)["text"]
    logger.info(f"exec no_request={flag}")
    return flag


def no_response(vars):
    logger.info("exec no_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: no is your answer"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# global
##################################################################################################################


def global1_request(ngrams, vars):
    flag = True
    flag = flag and "global1" in state_utils.get_last_human_utterance(vars)["text"]
    logger.info(f"exec global1_request={flag}")
    return flag


def global1_response(vars):
    logger.info("exec global1_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: global1 is your answer"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


def global2_request(ngrams, vars):
    flag = True
    logger.info(f"exec global2_request={flag}")
    return flag


def global2_response(vars):
    logger.info("exec global2_response")
    try:
        state_utils.set_confidence(vars)
        return "greeting: global2 is your answer"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return error_response(vars)


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    logger.info("exec error_response")
    state_utils.set_confidence(vars, 0)
    return "Sorry"


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START
# ######### transition State.USR_START -> State.SYS_HI if hi_request==True (request returns only bool values) ####
simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_HI: hi_request,
    },
)
# ######### if all *_request==False then transition State.USR_START -> State.SYS_ERR  #########
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_HI

# ######### transition State.SYS_HI -> State.USR_HI and return text from hi_response  #########
simplified_dialogflow.add_system_transition(State.SYS_HI, State.USR_HI, hi_response)

# ######### transition State.USR_HI -> 3 different nodes accordings with order, because for all impotance==1.0 ######
simplified_dialogflow.add_user_serial_transitions(
    State.USR_HI,
    {
        State.SYS_OK: ok_request,  # first place
        State.SYS_YES: yes_request,  # second place
        State.SYS_NO: no_request,  # third place, only if others are False
    },
)
# ######### set low level impotance for all *_request #########
# simplified_dialogflow.add_user_serial_transitions(
#     State.USR_HI,
#     {
#         State.SYS_OK: ok_request,
#         State.SYS_YES: yes_request,
#         State.SYS_NO: no_request,
#     },
#     default_importance=0.7
# )
# ######### different impotance for all ############
# simplified_dialogflow.add_user_serial_transitions(
#     State.USR_HI,
#     {
#         State.SYS_OK: (ok_request, 1.1),
#         State.SYS_YES: (yes_request, 1.2),
#         State.SYS_NO: (no_request, 1.3),
#     },
# )


simplified_dialogflow.set_error_successor(State.USR_HI, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_OK, State.USR_OK, ok_response)
simplified_dialogflow.add_system_transition(State.SYS_YES, State.USR_YES, yes_response)
# simplified_dialogflow.add_system_transition(State.SYS_NO, State.USR_NO, no_response)

##################################################################################################################
#  global
# ######### regulary global transition definition #########
# simplified_dialogflow.add_global_user_serial_transitions(
#     {
#         State.SYS_GLOBAL1: global1_request,
#         State.SYS_GLOBAL2: global2_request,
#     }
# )
# ######### also you can use importance for set prioriry ######
# simplified_dialogflow.add_global_user_serial_transitions(
#     {
#         State.SYS_GLOBAL1: global1_request,
#         State.SYS_GLOBAL2: global2_request,
#     },
#     default_importance=2.0,
# )
#  ######### or #########
simplified_dialogflow.add_global_user_serial_transitions(
    {
        State.SYS_GLOBAL1: (global1_request, 2.0),
        State.SYS_GLOBAL2: (global2_request, 0.5),
    },
)


simplified_dialogflow.add_system_transition(State.SYS_GLOBAL1, State.USR_START, global1_response)
simplified_dialogflow.add_system_transition(State.SYS_GLOBAL2, State.USR_START, global2_response)

##################################################################################################################
#  SYS_ERR
# ######### We can use global transition for State.SYS_ERR #########
simplified_dialogflow.add_global_user_serial_transitions(
    {
        State.SYS_ERR: (lambda x, y: True, -1.0),
    },
)
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
