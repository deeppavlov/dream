import logging

from emora_stdm import CompositeDialogueFlow, DialogueFlow


import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention

import dialogflows.flows.food as food_flow
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(food_flow.dialogflow, scopes.FOOD)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extention.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# food
##################################################################################################################


def food_request(ngrams, vars):
    flag = True
    logger.info(f"food_request={flag}")
    return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

for node in [scopes.State.USR_ROOT, scopes.State.USR_ERR]:
    simplified_dialogflow.add_user_serial_transitions(
        node,
        {(scopes.FOOD, food_flow.State.USR_START): food_request},
    )
simplified_dialogflow.set_error_successor(scopes.State.USR_ROOT, scopes.State.SYS_ERR)
simplified_dialogflow.set_error_successor(scopes.State.USR_ERR, scopes.State.SYS_ERR)
simplified_dialogflow.add_system_transition(
    scopes.State.SYS_ERR,
    scopes.State.USR_ROOT,
    food_flow.error_response,
)
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
