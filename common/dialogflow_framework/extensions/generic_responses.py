from common.speech_functions.generic_responses import (
    sys_response_to_speech_function_request,
    usr_response_to_speech_function_response,
)
from dff import TRANSITIONS, GLOBAL_TRANSITIONS, GRAPH, RESPONSE, repeat


def create_new_flow(**kwargs):
    if "priority" in kwargs:
        generic_response_state = ("generic_response", kwargs["priority"])
    else:
        generic_response_state = "generic_response"
    new_flow = {
        GLOBAL_TRANSITIONS: {
            generic_response_state: sys_response_to_speech_function_request,
        },
        GRAPH: {
            "generic_response": {
                RESPONSE: usr_response_to_speech_function_response,
                TRANSITIONS: {repeat(): sys_response_to_speech_function_request},
            }
        },
    }
    if "escape_conditions" in kwargs:
        new_flow[GRAPH][generic_response_state][TRANSITIONS] = kwargs["escape_conditions"]

    return new_flow
