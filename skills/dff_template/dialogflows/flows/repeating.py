# %%
import os
import logging
from enum import Enum, auto
import pathlib

import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.programy.model as programy_model
import dialogflows.scopes as scopes


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)

aiml_dir = pathlib.Path(__file__).parent.parent / "programy_storage/categories"


class State(Enum):
    USR_START = auto()
    SYS_PROGRAMY = auto()
    USR_PROGRAMY = auto()
    SYS_ERR = auto()


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
# programy
##################################################################################################################


configuration_files = programy_model.get_configuration_files(aiml_dirs=[aiml_dir])
model = programy_model.get_programy_model(configuration_files)


def programy_request(ngrams, vars):
    flag = True
    human_text = state_utils.get_last_human_utterance(vars)["text"]
    flag = flag and bool(model([human_text]))
    return flag


def programy_response(vars):
    try:
        human_text = state_utils.get_last_human_utterance(vars)["text"]
        response = model([human_text])
        state_utils.set_confidence(vars)
        return response
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

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_PROGRAMY: programy_request,
    },
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_PROGRAMY,
    {
        State.SYS_PROGRAMY: programy_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialogflow.add_system_transition(State.SYS_PROGRAMY, State.USR_PROGRAMY, programy_response)


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
