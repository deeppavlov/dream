# %%
import random
import os
import logging


import requests
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.greeting as common_greeting
import common.link as common_link


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))



logger = logging.getLogger(__name__)

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98


##################################################################################################################
# utils
##################################################################################################################




##################################################################################################################
# link_to by enity
##################################################################################################################

def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""
