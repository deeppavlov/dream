import logging

from dff import CompositeDialogueFlow, DialogueFlow

from dff import dialogflow_extension

import dialogflows.flows.animals as animals_flow
import dialogflows.flows.my_pets as my_pets_flow
import dialogflows.flows.user_pets as user_pets_flow
import dialogflows.flows.wild_animals as wild_animals_flow
from dialogflows.flows.animals_states import State as AS
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)

composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)

composite_dialogflow.add_component(animals_flow.dialogflow, scopes.ANIMALS)
composite_dialogflow.add_component(my_pets_flow.dialogflow, scopes.MY_PETS)
composite_dialogflow.add_component(user_pets_flow.dialogflow, scopes.USER_PETS)
composite_dialogflow.add_component(wild_animals_flow.dialogflow, scopes.WILD_ANIMALS)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# greeting
##################################################################################################################


def animals_request(ngrams, vars):
    flag = True
    logger.info(f"animals_request={flag}")
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
            (scopes.ANIMALS, AS.USR_START): animals_request,
        },
    )
simplified_dialogflow.set_error_successor(scopes.State.USR_ROOT, scopes.State.SYS_ERR)
simplified_dialogflow.set_error_successor(scopes.State.USR_ERR, scopes.State.SYS_ERR)
simplified_dialogflow.add_system_transition(
    scopes.State.SYS_ERR,
    scopes.State.USR_ROOT,
    animals_flow.error_response,
)
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
