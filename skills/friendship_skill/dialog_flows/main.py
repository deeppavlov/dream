from enum import Enum, auto

from emora_stdm import CompositeDialogueFlow, DialogueFlow


import utils.stdm.dialog_flow_extention as dialog_flow_extention
import dialog_flows.components.greeting as greeting_component
import dialog_flows.components_names as components_names


class State(Enum):
    USR_START = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


composite_dialog_flow = CompositeDialogueFlow(
    State.USR_START,
    system_error_state=State.SYS_ERR,
    user_error_state=State.USR_ERR,
    initial_speaker=DialogueFlow.Speaker.USER,
)


composite_dialog_flow.add_component(greeting_component.dialog_flow, components_names.GREETING)

dialog_flow = composite_dialog_flow.component(components_names.MAIN)
simplified_dialog_flow = dialog_flow_extention.DFEasyFilling(dialog_flow)


##################################################################################################################
# greeting
##################################################################################################################


def greeting_request(ngrams, vars):
    flag = True
    return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

simplified_dialog_flow.add_user_transition(
    State.USR_START,
    (components_names.GREETING, greeting_component.State.USR_START),
    greeting_request,
)

simplified_dialog_flow.add_user_transition(
    State.USR_ERR,
    (components_names.GREETING, greeting_component.State.USR_START),
    greeting_request,
)

simplified_dialog_flow.add_system_transition(
    State.SYS_ERR,
    (components_names.GREETING, greeting_component.State.USR_START),
    greeting_request,
)
