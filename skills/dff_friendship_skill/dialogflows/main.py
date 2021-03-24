import logging

import re

from emora_stdm import CompositeDialogueFlow, DialogueFlow


import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils

import dialogflows.flows.greeting as greeting_flow
import dialogflows.flows.weekend as weekend_flow

import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(greeting_flow.dialogflow, scopes.GREETING)
composite_dialogflow.add_component(weekend_flow.dialogflow, scopes.WEEKEND)


dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extention.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# greeting
##################################################################################################################


def greeting_request(ngrams, vars):
    flag = True
    logger.info(f"greeting_request={flag}")
    return flag


##################################################################################################################
# weekend
##################################################################################################################


patterns_bot = ["chat about", "talk about", "on your mind"]
re_patterns_bot = re.compile("(" + "|".join(patterns_bot) + ")", re.IGNORECASE)

patterns_human = ["no idea", "don't know", "nothing", "anything", "your favorite topic"]
re_patterns_human = re.compile("(" + "|".join(patterns_human) + ")", re.IGNORECASE)


def weekend_request(ngrams, vars):
    flag = False

    # ok we start with the idea that user has no idea what to talk about
    last_bot_text = state_utils.get_last_bot_utterance(vars)["text"]
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(re_patterns_bot, last_bot_text) and re.search(re_patterns_human, human_text))

    logger.info(f"weekend_request={flag}")
    return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

for node in [scopes.State.USR_ROOT, scopes.State.USR_ERR]:
    simplified_dialogflow.add_user_serial_transitions(
        node,
        {
            (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_request,
            (scopes.GREETING, greeting_flow.State.USR_START): greeting_request,
        },
    )
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
