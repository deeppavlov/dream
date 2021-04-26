import logging

from emora_stdm import CompositeDialogueFlow, DialogueFlow


import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention

import dialogflows.flows.gossip as gossip_flow
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(gossip_flow.dialogflow, scopes.GOSSIP)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extention.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

for node in [scopes.State.USR_ROOT, scopes.State.USR_ERR]:
    simplified_dialogflow.add_user_serial_transitions(
        node,
        {
            (scopes.GOSSIP, gossip_flow.State.USR_START): gossip_flow.sys_topic_to_event_request,
            # (scopes.GOSSIP, gossip_flow.State.USR_START): gossip_request,
        },
    )
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
