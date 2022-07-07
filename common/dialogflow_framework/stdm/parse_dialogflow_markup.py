import inspect
import logging
import random
import re
import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
from dff import CompositeDialogueFlow, DialogueFlow
from dff import dialogflow_extension
from common.dialogflow_framework.extensions import intents
from common.dialogflow_framework.extensions import priorities
from common.dialogflow_framework.stdm.key_words import (
    TRANSITIONS,
    GLOBAL_TRANSITIONS,
    GRAPH,
    RESPONSE,
    PROCESSING,
    forward,
    back,
    repeat,
    previous,
)
from common.utils import is_yes

logger = logging.getLogger(__name__)


def check_condition(vars, condition):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    if callable(condition):
        flag = condition(vars)
    elif isinstance(condition, str):
        if re.findall(condition, user_uttr["text"], re.IGNORECASE):
            flag = True
    elif isinstance(condition, re.Pattern):
        if re.findall(condition, user_uttr["text"]):
            flag = True
    elif condition == intents.yes_intent(vars) and is_yes(user_uttr):
        flag = True
    elif condition == intents.always_true(vars):
        flag = True
    return flag


def check_complex_condition(vars, complex_condition):
    flag = False
    if isinstance(complex_condition, list):
        aggregate, conditions = complex_condition
        cond_results = []
        for condition in conditions:
            cond_res = check_condition(vars, condition)
            cond_results.append(cond_res)
        flag = aggregate(cond_results)
    else:
        flag = check_condition(vars, complex_condition)
    return flag


def general_request(complex_condition, destination_state):
    def request(ngrams, vars):
        flag = check_complex_condition(vars, complex_condition)
        logger.info(f"{destination_state} request={flag}")
        return flag

    return request


def general_request_to_prev(previous_cond, cur_state):
    def request(ngrams, vars):
        flag = False
        last_state = condition_utils.get_last_state(vars)
        second_last_state = condition_utils.get_n_last_state(vars, 2)
        for state, condition in previous_cond.items():
            if (
                str(last_state).split(".")[-1].lower() == state
                and str(second_last_state).split(".")[-1].lower() == cur_state
            ):
                flag = check_complex_condition(vars, condition)
            if flag:
                break
        logger.info(f"{cur_state} to_previous_state_request={flag}")
        return flag

    return request


def response_aux(vars, response_info):
    response = ""
    if isinstance(response_info, str):
        response = response_info
    elif callable(response_info):
        response = response_info(vars)
    return response


def set_attr(vars, conf, cont_flag):
    state_utils.set_confidence(vars, confidence=conf)
    state_utils.set_can_continue(vars, continue_flag=cont_flag)


def general_response(state, state_info):
    response_info = state_info[RESPONSE]

    def response_func(vars):
        if isinstance(response_info, list):
            chosen_response = random.choice(response_info)
            response = response_aux(vars, chosen_response)
        else:
            response = response_aux(vars, response_info)

        processing_info = state_info.get(PROCESSING, [])
        for processing_func in processing_info:
            if "response" in inspect.getfullargspec(processing_func).args:
                response = processing_func(vars, response)
            else:
                processing_func(vars)
        logger.info(f"{state} response, {response}")
        set_attr(vars, 1.0, common_constants.MUST_CONTINUE)
        return response

    return response_func


def preprocess_to_states(df_name, to_states):
    to_states_list = []
    if callable(to_states):
        to_states = to_states()
    to_states = list(to_states.items())
    for n, (destination_state, complex_condition) in enumerate(to_states):
        if isinstance(destination_state, str):
            to_states_list.append([destination_state, priorities.middle, -n, complex_condition])
        elif isinstance(destination_state, tuple):
            if len(destination_state) == 1:
                to_states_list.append([destination_state, priorities.middle, -n, complex_condition])
            elif len(destination_state) == 2 and isinstance(destination_state[-1], (int, float)):
                to_states_list.append([(df_name, destination_state[0]), destination_state[-1], -n, complex_condition])
            elif len(destination_state) == 2 and not isinstance(destination_state[-1], (int, float)):
                to_states_list.append([destination_state, priorities.middle, -n, complex_condition])
            elif len(destination_state) == 3 and isinstance(destination_state[-1], (int, float)):
                to_states_list.append([destination_state[:2], destination_state[-1], -n, complex_condition])
    return to_states_list


def parse_dialogflow(df_name, scenario, df_global_to_states, previous_cond):
    graph = scenario[GRAPH]
    states = list(graph.keys())
    sys_usr_states = {}
    for state in states:
        sys_state = f"State.SYS_{state.upper()}"
        usr_state = f"State.USR_{state.upper()}"
        sys_usr_states[state] = (sys_state, usr_state)

    next_states = {}
    for i in range(len(states) - 1):
        next_states[states[i]] = states[i + 1]
    prev_states = {}
    for i in range(1, len(states)):
        prev_states[states[i]] = states[i - 1]

    global_to_states_list = []
    for df, global_to_states in df_global_to_states.items():
        global_to_states_list += [[df] + state_info for state_info in preprocess_to_states(df, global_to_states)]

    simplified_dialog_flow = dialogflow_extension.DFEasyFilling("State.USR_START")
    simplified_dialog_flow.set_error_successor("State.USR_START", "State.SYS_ERR")
    transitions_dict = {}

    if global_to_states_list:
        global_to_states_list = sorted(global_to_states_list, key=lambda x: (x[2], x[3]), reverse=True)
        for source_df, destination_state, *_, complex_condition in global_to_states_list:
            request_function = general_request(complex_condition, destination_state)
            if isinstance(destination_state, str) and source_df == df_name:
                transitions_dict[sys_usr_states[destination_state][0]] = request_function
            elif isinstance(destination_state, tuple):
                if len(destination_state) == 1:
                    transitions_dict[(destination_state[0], "State.USR_START")] = request_function
                elif len(destination_state) == 2:
                    dest_df, dest_df_state = destination_state
                    if dest_df_state == "root" and dest_df != df_name:
                        transitions_dict[(dest_df, "State.USR_START")] = request_function
                    elif dest_df == df_name and dest_df_state != "root":
                        transitions_dict[f"State.SYS_{dest_df_state.upper()}"] = request_function
                    elif dest_df != df_name and dest_df_state != "root":
                        transitions_dict[(dest_df, f"State.SYS_{dest_df_state.upper()}")] = request_function
        simplified_dialog_flow.add_user_serial_transitions("State.USR_START", transitions_dict)
    else:
        transitions_dict[sys_usr_states[states[0]][1]] = intents.always_true
        simplified_dialog_flow.add_user_serial_transitions("State.USR_START", transitions_dict)

    for state in graph:
        to_states = graph[state].get(TRANSITIONS, {})
        to_states_list = preprocess_to_states(df_name, to_states)
        for keyword in [forward, back, repeat, previous]:
            if keyword in graph[state]:
                complex_condition = graph[state][keyword]
                to_states_list.append([df_name, keyword, priorities.middle, 0, complex_condition])
        cur_and_global_list = to_states_list + global_to_states_list
        if cur_and_global_list:
            cur_and_global_list = sorted(cur_and_global_list, key=lambda x: (x[2], x[3]), reverse=True)
            transitions_dict = {}
            for source_df, destination_state, *_, complex_condition in cur_and_global_list:
                request_function = general_request(complex_condition, destination_state)
                if destination_state == "forward":
                    transitions_dict[f"State.SYS_{next_states[state].upper()}"] = request_function
                elif destination_state == "back":
                    transitions_dict[f"State.SYS_{prev_states[state].upper()}"] = request_function
                elif destination_state == "repeat":
                    transitions_dict[f"State.SYS_{state.upper()}"] = request_function
                elif destination_state != previous and isinstance(destination_state, str) and source_df == df_name:
                    transitions_dict[sys_usr_states[destination_state][0]] = request_function
                elif isinstance(destination_state, tuple):
                    if len(destination_state) == 1:
                        transitions_dict[(destination_state[0], "State.USR_START")] = request_function
                    elif len(destination_state) == 2:
                        dest_df, dest_df_state = destination_state
                        if dest_df_state == "root":
                            transitions_dict[(dest_df, "State.USR_START")] = request_function
                        else:
                            transitions_dict[(dest_df, f"State.SYS_{dest_df_state.upper()}")] = request_function
                transitions_dict[f"State.SYS_{state.upper()}"] = general_request_to_prev(previous_cond, state)

        simplified_dialog_flow.add_user_serial_transitions(sys_usr_states[state][1], transitions_dict)
        response_func = general_response(state, graph[state])
        simplified_dialog_flow.add_system_transition(sys_usr_states[state][0], sys_usr_states[state][1], response_func)

        simplified_dialog_flow.set_error_successor(sys_usr_states[state][0], "State.SYS_ERR")
        simplified_dialog_flow.set_error_successor(sys_usr_states[state][1], "State.SYS_ERR")

    dialogflow = simplified_dialog_flow.get_dialogflow()
    return dialogflow


def start_request(ngrams, vars):
    flag = True
    logger.info(f"start_request={flag}")
    return flag


def error_response(vars):
    state_utils.save_to_shared_memory(vars, start=False)
    state_utils.set_confidence(vars, 0)
    return ""


def collect_previous_cond(composite_scenario):
    conditions = {}
    for dialogflow_name, dialogflow_scenario in composite_scenario.items():
        graph = dialogflow_scenario.get(GRAPH, {})
        for state, state_info in graph.items():
            to_states = state_info.get(TRANSITIONS, {})
            for dest_state, condition in to_states.items():
                if dest_state == "previous":
                    conditions[state] = condition
    return conditions


def make_composite_dialogflow(composite_scenario):
    global_to_states = {}
    for df in composite_scenario:
        if GLOBAL_TRANSITIONS in composite_scenario[df]:
            global_to_states[df] = composite_scenario[df][GLOBAL_TRANSITIONS]
    previous_cond = collect_previous_cond(composite_scenario)
    dialogflow_dict = {}
    dialogflows_names = list(composite_scenario.keys())
    for dialogflow_name, dialogflow_scenario in composite_scenario.items():
        dialogflow = parse_dialogflow(dialogflow_name, dialogflow_scenario, global_to_states, previous_cond)
        dialogflow_dict[dialogflow_name] = dialogflow

    composite_dialogflow = CompositeDialogueFlow(
        "State.USR_ROOT",
        system_error_state="State.SYS_ERR",
        user_error_state="State.USR_ERR",
        initial_speaker=DialogueFlow.Speaker.USER,
    )

    for dialogflow_name, dialogflow in dialogflow_dict.items():
        composite_dialogflow.add_component(dialogflow, dialogflow_name)

    dialogflow = composite_dialogflow.component("SYSTEM")
    simplified_dialogflow = dialogflow_extension.DFEasyFilling(dialogflow=dialogflow)

    for node in ["State.USR_ROOT", "State.USR_ERR"]:
        simplified_dialogflow.add_user_serial_transitions(
            node,
            {
                (dialogflows_names[0], "State.USR_START"): start_request,
            },
        )
    simplified_dialogflow.set_error_successor("State.USR_ROOT", "State.SYS_ERR")
    simplified_dialogflow.set_error_successor("State.USR_ERR", "State.SYS_ERR")
    simplified_dialogflow.add_system_transition(
        "State.SYS_ERR",
        "State.USR_ROOT",
        error_response,
    )
    composite_dialogflow.set_controller("SYSTEM")
    composite_dialogflow._controller = simplified_dialogflow.get_dialogflow()

    return composite_dialogflow
