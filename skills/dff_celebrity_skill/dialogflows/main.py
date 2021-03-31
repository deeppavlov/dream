import logging

from emora_stdm import CompositeDialogueFlow, DialogueFlow
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention

import dialogflows.flows.celebrity as celebrity_flow
import dialogflows.scopes as scopes
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(celebrity_flow.dialogflow, scopes.CELEBRITY)


dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extention.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# greeting
##################################################################################################################


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

for node in [scopes.State.USR_ROOT, scopes.State.USR_ERR]:
    simplified_dialogflow.add_user_serial_transitions(
        node,
        {
            (scopes.CELEBRITY, celebrity_flow.State.USR_FAVOURITE_CELEBRITY):
                celebrity_flow.celebrity_in_phrase_request,
            (scopes.CELEBRITY, celebrity_flow.State.USR_YESNO_1): celebrity_flow.celebrity_in_any_phrase_request,
            (scopes.CELEBRITY, celebrity_flow.State.USR_START): celebrity_flow.default_condition_request
        },
    )
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
