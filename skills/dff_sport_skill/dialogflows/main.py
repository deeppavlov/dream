import logging

from dff import CompositeDialogueFlow, DialogueFlow


from dff import dialogflow_extension

import dialogflows.flows.sport as sport_flow
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(sport_flow.dialogflow, scopes.SPORT)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# SPORT
##################################################################################################################


def sport_request(ngrams, vars):
    flag = True
    logger.info(f"sport_request={flag}")

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
            (scopes.SPORT, sport_flow.State.USR_START): sport_request,
        },
    )
simplified_dialogflow.set_error_successor(scopes.State.USR_ROOT, scopes.State.SYS_ERR)
simplified_dialogflow.set_error_successor(scopes.State.USR_ERR, scopes.State.SYS_ERR)
simplified_dialogflow.add_system_transition(
    scopes.State.SYS_ERR,
    scopes.State.USR_ROOT,
    sport_flow.error_response,
)
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
