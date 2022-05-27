import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp


import common.constants as common_constants
from common.have_fun import HAVE_FUN_PATTERN

import common.set_goal_flag as goal_status
from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_OFFERED


from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from df_engine.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("jokes", "intro"): cnd.regexp(HAVE_FUN_PATTERN),
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("jokes", "intro"): cnd.regexp(HAVE_FUN_PATTERN)
            },
        },
        "fallback": {
            RESPONSE: "Sorry, but I don't understand what you've just said :(",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(0.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.CAN_NOT_CONTINUE),
            },
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "jokes": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "intro": {
            RESPONSE: "I know some good jokes, maybe they will make you smile! Want to try?", 
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"Q0": int_cnd.is_yes_vars},
        },
        "Q0": {
            RESPONSE: "{Q0}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A0":  cnd.true()},
        },
        "A0": {
            RESPONSE: "{A0}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q1": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q1": {
            RESPONSE: "{Q1}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A1":  cnd.true()},
        },
        "A1": {
            RESPONSE: "{A1}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q2": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q2": {
            RESPONSE: "{Q2}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A2":  cnd.true()},
        },
        "A2": {
            RESPONSE: "{A2}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q3": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q3": {
            RESPONSE: "{Q3}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A3":  cnd.true()},
        },
        "A3": {
            RESPONSE: "{A3}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q4": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q4": {
            RESPONSE: "{Q4}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A4":  cnd.true()},
        },
        "A4": {
            RESPONSE: "{A4}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q5": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q5": {
            RESPONSE: "{Q5}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A5":  cnd.true()},
        },
        "A5": {
            RESPONSE: "{A5}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q6": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q6": {
            RESPONSE: "{Q6}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A6":  cnd.true()},
        },
        "A6": {
            RESPONSE: "{A6}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q7": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q7": {
            RESPONSE: "{Q7}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A7":  cnd.true()},
        },
        "A7": {
            RESPONSE: "{A7}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q8": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q8": {
            RESPONSE: "{Q8}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A8":  cnd.true()},
        },
        "A8": {
            RESPONSE: "{A8}. Do you want to hear more?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "Q9": int_cnd.is_yes_vars,
                "ask_opinion": int_cnd.is_no_vars
            },
        },
        "Q9": {
            RESPONSE: "{Q9}",
            PROCESSING: {
                "extract_jokes": loc_prs.extract_jokes(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"A9":  cnd.true()},
        },
        "A9": {
            RESPONSE: "{A9}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "ask_opinion": cnd.true()
            },
        },
        "ask_opinion": {
            RESPONSE: "Did you like my jokes?",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "liked_jokes": int_cnd.is_yes_vars,
                "not_liked_jokes": int_cnd.is_no_vars
            },
        },
        "liked_jokes": {
            RESPONSE: "That's great!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "not_liked_jokes": {
            RESPONSE: "Oh... I hope I'll make you laugh next time.",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_NOT_ACHIEVED)
            }
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
