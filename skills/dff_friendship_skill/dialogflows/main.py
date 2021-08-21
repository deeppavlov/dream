import logging

from dff import CompositeDialogueFlow, DialogueFlow


from dff import dialogflow_extension

import dialogflows.flows.greeting as greeting_flow
import dialogflows.flows.starter as starter_flow
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
composite_dialogflow.add_component(starter_flow.dialogflow, scopes.STARTER)
composite_dialogflow.add_component(weekend_flow.dialogflow, scopes.WEEKEND)


dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# greeting
##################################################################################################################


def greeting_request(ngrams, vars):
    flag = True
    logger.info(f"greeting_request={flag}")
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
            (scopes.WEEKEND, weekend_flow.State.USR_START): weekend_flow.std_weekend_request,
            (scopes.GREETING, greeting_flow.State.USR_START): greeting_request,
        },
    )
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
