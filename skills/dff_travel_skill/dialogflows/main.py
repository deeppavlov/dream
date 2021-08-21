import logging

from dff import CompositeDialogueFlow, DialogueFlow


from dff import dialogflow_extension

import dialogflows.flows.travel as travel_flow
import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)


composite_dialogflow = CompositeDialogueFlow(
    scopes.State.USR_ROOT,
    system_error_state=scopes.State.SYS_ERR,
    user_error_state=scopes.State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialogflow.add_component(travel_flow.dialogflow, scopes.TRAVEL)

dialogflow = composite_dialogflow.component(scopes.MAIN)
simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)


##################################################################################################################
# travel
##################################################################################################################


def travel_request(ngrams, vars):
    have_bot_been_in = travel_flow.have_bot_been_in_request(ngrams, vars)
    user_have_been_in = travel_flow.user_have_been_in_request(ngrams, vars)
    user_mention_named_entity_loc = travel_flow.user_mention_named_entity_loc_request(ngrams, vars)
    lets_chat_about_travel = travel_flow.lets_chat_about_travelling_request(ngrams, vars)
    user_likes_travelling = travel_flow.like_about_travelling_request(ngrams, vars)
    user_dislikes_travelling = travel_flow.dislike_about_travelling_request(ngrams, vars)
    cond1 = have_bot_been_in or user_have_been_in or user_mention_named_entity_loc
    cond2 = lets_chat_about_travel or user_likes_travelling or user_dislikes_travelling
    flag = True
    flag = flag and (cond1 or cond2)
    logger.info(f"travel_request={flag}")
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
            (scopes.TRAVEL, travel_flow.State.USR_START): travel_request,
        },
    )
simplified_dialogflow.set_error_successor(scopes.State.USR_ROOT, scopes.State.SYS_ERR)
simplified_dialogflow.set_error_successor(scopes.State.USR_ERR, scopes.State.SYS_ERR)
simplified_dialogflow.add_system_transition(
    scopes.State.SYS_ERR,
    scopes.State.USR_ROOT,
    travel_flow.error_response,
)
composite_dialogflow.set_controller("SYSTEM")
composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()
