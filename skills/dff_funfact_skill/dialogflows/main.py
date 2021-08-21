import logging

from dff import CompositeDialogueFlow, DialogueFlow

from dff import dialogflow_extension

import dialogflows.flows.funfact as funfact_flow
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)

composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)

composite_dialogflow.add_component(funfact_flow.dialogflow, scopes.FUNFACT)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)

##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

for node in [scopes.State.USR_ROOT, scopes.State.USR_ERR]:
    simplified_dialogflow.add_user_serial_transitions(
        node,
        {(scopes.FUNFACT, funfact_flow.State.USR_START): funfact_flow.funfact_request},
    )

composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
